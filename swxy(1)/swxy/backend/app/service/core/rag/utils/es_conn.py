#
#  Copyright 2025 The InfiniFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

import logging
import re
import time
import os
import json

import copy
from elasticsearch import Elasticsearch
from elasticsearch_dsl import UpdateByQuery, Q, Search, Index
from service.core.rag.utils import singleton
from service.core.api.utils.file_utils import get_project_base_directory
from service.core.rag.utils.doc_store_conn import MatchExpr, OrderByExpr, MatchTextExpr, MatchDenseExpr, FusionExpr
from service.core.rag.nlp import is_english
from dotenv import load_dotenv

load_dotenv()

ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
ATTEMPT_TIME = 2
PAGERANK_FLD = "pagerank_fea"
TAG_FLD = "tag_feas"

logger = logging.getLogger('ragflow.es_conn')


@singleton
class ESConnection():
    def __init__(self):
        self.info = {}
        logger.info(f"Connecting to Elasticsearch at {ES_HOST}")
        self.es = Elasticsearch(
            [ES_HOST],  # Elasticsearch URL
            basic_auth=("elastic", "infini_rag_flow"),  # 用户名和密码
            verify_certs=False,  # 禁用 SSL 证书验证
            timeout=600
        )
        logger.info("Elasticsearch connection established")

        fp_mapping = os.path.join(get_project_base_directory(), "conf", "mapping.json")
        self.mapping = json.load(open(fp_mapping, "r"))


    """
    Helper functions for search result
    """

    def getTotal(self, res):
        if isinstance(res["hits"]["total"], type({})):
            return res["hits"]["total"]["value"]
        return res["hits"]["total"]

    def getChunkIds(self, res):
        return [d["_id"] for d in res["hits"]["hits"]]

    def count_docs_by_docnm(self, index_name: str, file_name: str) -> int:
        """按文件名统计某个文件写入了多少 Chunk。
        兼容三种情况（取最大值）：
        1) docnm_kwd = 纯文件名（新代码规范写法）
        2) file_name_kwd = 纯文件名（process_items 双写字段）
        3) docnm match 查询（兼容旧 docnm=绝对路径 的数据）
        """
        import xxhash
        # 先判断索引是否存在，不存在直接返回 0
        try:
            if not self.es.indices.exists(index=index_name):
                return 0
        except Exception as e:
            logger.warning(f"count_docs_by_docnm 检查索引 {index_name} 失败: {e}")
            return 0

        pure_name = os.path.basename(file_name)
        doc_id = xxhash.xxh64(file_name.encode("utf-8")).hexdigest()

        best_count = 0
        # Query 1: docnm_kwd（两种 mapping 兼容：直接 keyword 或 .keyword 子字段）
        try:
            res = self.es.count(
                index=index_name,
                body={
                    "query": {
                        "bool": {
                            "should": [
                                {"term": {"docnm_kwd": pure_name}},
                                {"term": {"docnm_kwd.keyword": pure_name}},
                            ],
                            "minimum_should_match": 1,
                        }
                    }
                }
            )
            best_count = max(best_count, int(res.get("count", 0)))
        except Exception as e:
            logger.debug(f"count docnm_kwd={pure_name} failed: {e}")

        # Query 2: file_name_kwd（process_items 双写）
        try:
            res = self.es.count(
                index=index_name,
                body={
                    "query": {
                        "bool": {
                            "should": [
                                {"term": {"file_name_kwd": file_name}},
                                {"term": {"file_name_kwd.keyword": file_name}},
                            ],
                            "minimum_should_match": 1,
                        }
                    }
                }
            )
            best_count = max(best_count, int(res.get("count", 0)))
        except Exception as e:
            logger.debug(f"count file_name_kwd={file_name} failed: {e}")

        # Query 3: doc_id term（process_items 里按 file_name 算的 xxhash）
        try:
            res = self.es.count(
                index=index_name,
                body={
                    "query": {
                        "bool": {
                            "should": [
                                {"term": {"doc_id_kwd": doc_id}},
                                {"term": {"doc_id.keyword": doc_id}},
                            ],
                            "minimum_should_match": 1,
                        }
                    }
                }
            )
            best_count = max(best_count, int(res.get("count", 0)))
        except Exception as e:
            logger.debug(f"count doc_id_kwd/doc_id.keyword={doc_id} failed: {e}")

        # Query 4: match docnm（兜底，兼容 docnm 字段写的是绝对路径的情况）
        if best_count == 0:
            try:
                res = self.es.count(
                    index=index_name,
                    body={"query": {"match": {"docnm": pure_name}}}
                )
                best_count = max(best_count, int(res.get("count", 0)))
            except Exception as e:
                logger.debug(f"count match docnm={pure_name} failed: {e}")

        return best_count

    def getHighlight(self, res, keywords: list[str], fieldnm: str):
        ans = {}
        for d in res["hits"]["hits"]:
            hlts = d.get("highlight")
            if not hlts:
                continue
            txt = "...".join([a for a in list(hlts.items())[0][1]])
            if not is_english(txt.split()):
                ans[d["_id"]] = txt
                continue

            txt = d["_source"][fieldnm]
            txt = re.sub(r"[\r\n]", " ", txt, flags=re.IGNORECASE | re.MULTILINE)
            txts = []
            for t in re.split(r"[.?!;\n]", txt):
                for w in keywords:
                    t = re.sub(r"(^|[ .?/'\"\(\)!,:;-])(%s)([ .?/'\"\(\)!,:;-])" % re.escape(w), r"\1<em>\2</em>\3", t,
                               flags=re.IGNORECASE | re.MULTILINE)
                if not re.search(r"<em>[^<>]+</em>", t, flags=re.IGNORECASE | re.MULTILINE):
                    continue
                txts.append(t)
            ans[d["_id"]] = "...".join(txts) if txts else "...".join([a for a in list(hlts.items())[0][1]])

        return ans
    

    def getAggregation(self, res, fieldnm: str):
        agg_field = "aggs_" + fieldnm
        if "aggregations" not in res or agg_field not in res["aggregations"]:
            return list()
        bkts = res["aggregations"][agg_field]["buckets"]
        return [(b["key"], b["doc_count"]) for b in bkts]

    def getFields(self, res, fields: list[str]) -> dict[str, dict]:
        res_fields = {}
        if not fields:
            return {}
        for d in self.__getSource(res):
            m = {n: d.get(n) for n in fields if d.get(n) is not None}
            for n, v in m.items():
                if isinstance(v, list):
                    m[n] = v
                    continue
                if not isinstance(v, str):
                    m[n] = str(m[n])
                # if n.find("tks") > 0:
                #     m[n] = rmSpace(m[n])

            if m:
                res_fields[d["id"]] = m
        return res_fields


    def __getSource(self, res):
        rr = []
        for d in res["hits"]["hits"]:
            d["_source"]["id"] = d["_id"]
            d["_source"]["_score"] = d["_score"]
            rr.append(d["_source"])
        return rr

    """
    Database operations
    """
    def ensure_index(self, index_name: str):
        """确保索引存在且 mapping 正确。
        - 不存在：用 mapping.json 里的 settings/mappings 创建
        - 已存在但缺 dynamic_templates / analyzer（历史上自动推断创建过）：记录 warning，后续建议重索引修复
        返回: (created_ok, needs_reindex: bool)
        """
        try:
            if not self.es.indices.exists(index=index_name):
                body = {
                    "settings": self.mapping.get("settings", {}),
                    "mappings": self.mapping.get("mappings", {}),
                }
                self.es.indices.create(index=index_name, body=body)
                logger.info(f"[ensure_index] 新建索引 {index_name} 并应用 mapping.json")
                return True, False

            # 已存在：检查 dynamic_templates 是否生效
            cur_mapping = self.es.indices.get_mapping(index=index_name)[index_name]["mappings"]
            cur_templates = cur_mapping.get("dynamic_templates")
            expect_templates = self.mapping.get("mappings", {}).get("dynamic_templates")
            if expect_templates and (not cur_templates or len(cur_templates) != len(expect_templates)):
                logger.warning(
                    f"[ensure_index] 索引 {index_name} 已存在但 dynamic_templates 不匹配，"
                    "建议删除该索引后重新上传文档，让新数据按 mapping.json 规范创建。"
                )
                return True, True
            return True, False
        except Exception as e:
            logger.warning(f"[ensure_index] 索引 {index_name} 创建失败: {e}")
            return False, False

    def insert(self, documents: list[dict], indexName: str, knowledgebaseId: str = None) -> list[str]:
        # 插入前确保索引存在且已应用 mapping.json
        self.ensure_index(indexName)
        # Refers to https://www.elastic.co/guide/en/elasticsearch/reference/current/docs-bulk.html
        operations = []
        for d in documents:
            assert "_id" not in d
            assert "id" in d
            d_copy = copy.deepcopy(d)
            meta_id = d_copy.pop("id", "")
            operations.append(
                {"index": {"_index": indexName, "_id": meta_id}})
            operations.append(d_copy)

        res = []
        for _ in range(ATTEMPT_TIME):
            try:
                res = []
                r = self.es.bulk(index=(indexName), operations=operations,
                                 refresh=False, timeout="60s")
                if re.search(r"False", str(r["errors"]), re.IGNORECASE):
                    return res

                for item in r["items"]:
                    for action in ["create", "delete", "index", "update"]:
                        if action in item and "error" in item[action]:
                            res.append(str(item[action]["_id"]) + ":" + str(item[action]["error"]))
                return res
            except Exception as e:
                res.append(str(e))
                logger.warning("ESConnection.insert got exception: " + str(e))
                res = []
                if re.search(r"(Timeout|time out)", str(e), re.IGNORECASE):
                    res.append(str(e))
                    time.sleep(3)
                    continue
        return res
    

    def search(
            self, selectFields: list[str],
            highlightFields: list[str],
            condition: dict,
            matchExprs: list[MatchExpr],
            orderBy: OrderByExpr,
            offset: int,
            limit: int,
            indexNames: str | list[str],
            knowledgebaseIds: list[str],
            aggFields: list[str] = [],
            rank_feature: dict | None = None
    ):
        """
        Refers to https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html
        """
        if isinstance(indexNames, str):
            indexNames = indexNames.split(",")
        assert isinstance(indexNames, list) and len(indexNames) > 0
        assert "_id" not in condition

        bqry = Q("bool", must=[])
        condition["kb_id"] = knowledgebaseIds
        for k, v in condition.items():
            if k == "available_int":
                if v == 0:
                    bqry.filter.append(Q("range", available_int={"lt": 1}))
                else:
                    bqry.filter.append(
                        Q("bool", must_not=Q("range", available_int={"lt": 1})))
                continue
            if not v:
                continue
            # 对于字符串字段（kb_id / docnm_kwd / file_name_kwd / doc_id 等），
            # 同时兼容 dynamic_templates 生效（字段本身就是 keyword）和 ES 默认（text + 多字段 .keyword）两种 mapping
            _FALLBACK_KEYWORD_FIELDS = {"kb_id", "docnm_kwd", "file_name_kwd", "doc_id", "docnm"}
            if isinstance(v, list):
                if k in _FALLBACK_KEYWORD_FIELDS:
                    sub = Q("bool", should=[
                        Q("terms", **{k: v}),
                        Q("terms", **{f"{k}.keyword": v}),
                    ], minimum_should_match=1)
                    bqry.filter.append(sub)
                else:
                    bqry.filter.append(Q("terms", **{k: v}))
            elif isinstance(v, str) or isinstance(v, int):
                if k in _FALLBACK_KEYWORD_FIELDS and isinstance(v, str):
                    sub = Q("bool", should=[
                        Q("term", **{k: v}),
                        Q("term", **{f"{k}.keyword": v}),
                    ], minimum_should_match=1)
                    bqry.filter.append(sub)
                else:
                    bqry.filter.append(Q("term", **{k: v}))
            else:
                raise Exception(
                    f"Condition `{str(k)}={str(v)}` value type is {str(type(v))}, expected to be int, str or list.")

        s = Search()
        vector_similarity_weight = 0.5
        for m in matchExprs:
            if isinstance(m, FusionExpr) and m.method == "weighted_sum" and "weights" in m.fusion_params:
                assert len(matchExprs) == 3 and isinstance(matchExprs[0], MatchTextExpr) and isinstance(matchExprs[1],
                                                                                                        MatchDenseExpr) and isinstance(
                    matchExprs[2], FusionExpr)
                weights = m.fusion_params["weights"]
                vector_similarity_weight = float(weights.split(",")[1])
        for m in matchExprs:
            if isinstance(m, MatchTextExpr):
                minimum_should_match = m.extra_options.get("minimum_should_match", 0.0)
                if isinstance(minimum_should_match, float):
                    minimum_should_match = str(int(minimum_should_match * 100)) + "%"
                bqry.must.append(Q("query_string", fields=m.fields,
                                   type="best_fields", query=m.matching_text,
                                   minimum_should_match=minimum_should_match,
                                   boost=1))
                bqry.boost = 1.0 - vector_similarity_weight

            elif isinstance(m, MatchDenseExpr):
                assert (bqry is not None)
                similarity = 0.0
                if "similarity" in m.extra_options:
                    similarity = m.extra_options["similarity"]
                s = s.knn(m.vector_column_name,
                          m.topn,
                          m.topn * 2,
                          query_vector=list(m.embedding_data),
                          filter=bqry.to_dict(),
                          similarity=similarity,
                          )

        if bqry and rank_feature:
            for fld, sc in rank_feature.items():
                if fld != PAGERANK_FLD:
                    fld = f"{TAG_FLD}.{fld}"
                bqry.should.append(Q("rank_feature", field=fld, linear={}, boost=sc))

        if bqry:
            s = s.query(bqry)
        for field in highlightFields:
            s = s.highlight(field)

        if orderBy:
            orders = list()
            for field, order in orderBy.fields:
                order = "asc" if order == 0 else "desc"
                if field in ["page_num_int", "top_int"]:
                    order_info = {"order": order, "unmapped_type": "float",
                                  "mode": "avg", "numeric_type": "double"}
                elif field.endswith("_int") or field.endswith("_flt"):
                    order_info = {"order": order, "unmapped_type": "float"}
                else:
                    order_info = {"order": order, "unmapped_type": "text"}
                orders.append({field: order_info})
            s = s.sort(*orders)

        for fld in aggFields:
            s.aggs.bucket(f'aggs_{fld}', 'terms', field=fld, size=1000000)

        if limit > 0:
            s = s[offset:offset + limit]
        q = s.to_dict()
        logger.debug(f"ESConnection.search {str(indexNames)} query: " + json.dumps(q))

        for i in range(ATTEMPT_TIME):
            try:
                #print(json.dumps(q, ensure_ascii=False))
                res = self.es.search(index=indexNames,
                                     body=q,
                                     timeout="600s",
                                     # search_type="dfs_query_then_fetch",
                                     track_total_hits=True,
                                     _source=True)
                if str(res.get("timed_out", "")).lower() == "true":
                    raise Exception("Es Timeout.")
                logger.debug(f"ESConnection.search {str(indexNames)} res: " + str(res))
                return res
            except Exception as e:
                logger.exception(f"ESConnection.search {str(indexNames)} query: " + str(q))
                if str(e).find("Timeout") > 0:
                    continue
                raise e
        logger.error("ESConnection.search timeout for 3 times!")
        raise Exception("ESConnection.search timeout.")

    def delete(self, condition: dict, indexName: str, knowledgebaseId: str) -> int:
        """
        删除符合条件的文档
        
        Args:
            condition: 删除条件
            indexName: 索引名称
            knowledgebaseId: 知识库ID
            
        Returns:
            删除的文档数量
        """
        try:
            # 构建删除查询
            query = {
                "query": {
                    "bool": {
                        "must": []
                    }
                }
            }
            
            # 添加知识库ID条件
            if knowledgebaseId:
                query["query"]["bool"]["must"].append({"term": {"kb_id": knowledgebaseId}})
            
            # 添加其他条件
            for field, value in condition.items():
                if isinstance(value, list):
                    query["query"]["bool"]["must"].append({"terms": {field: value}})
                elif isinstance(value, str) and value.startswith("*") and value.endswith("*"):
                    # 通配符查询（两端都有*）
                    query["query"]["bool"]["must"].append({"wildcard": {field: value}})
                elif isinstance(value, str) and (value.startswith("*") or value.endswith("*")):
                    # 通配符查询（一端有*）
                    query["query"]["bool"]["must"].append({"wildcard": {field: value}})
                else:
                    # 精确匹配
                    query["query"]["bool"]["must"].append({"term": {field: value}})
            
            # 打印调试信息
            print(f"ES 删除查询: {json.dumps(query, ensure_ascii=False, indent=2)}")
            print(f"索引名: {indexName}")
            
            # 执行删除
            response = self.es.delete_by_query(
                index=indexName,
                body=query,
                refresh=True
            )
            
            print(f"ES 删除响应: {response}")
            
            return response["deleted"]
            
        except Exception as e:
            logger.error(f"Failed to delete documents: {str(e)}")
            print(f"ES 删除失败: {str(e)}")
            return 0
