"""
诊断脚本：测试检索流程
"""
import sys
import json
sys.path.insert(0, '/app')

from service.core.rag.utils.es_conn import ESConnection
from service.core.rag.nlp.search_v2 import Dealer

print("=" * 60)
print("1. 检查 ES 索引和数据")
print("=" * 60)

es = ESConnection()

# 获取所有索引
indices = list(es.es.indices.get_alias(index="*").keys()) if hasattr(es.es, 'indices') else []
all_indices = list(es.es.indices.get(index="*").keys())
print(f"所有索引: {all_indices}")

# 检查每个索引的文档数
for idx in all_indices:
    try:
        count = es.es.count(index=idx).get('count', 0)
        print(f"  索引 '{idx}': {count} 个文档")
        # 获取前3个文档的字段
        if count > 0:
            res = es.es.search(index=idx, body={"query": {"match_all": {}}, "size": 2, "_source": True})
            for hit in res['hits']['hits']:
                src = hit['_source']
                print(f"    doc_id={src.get('doc_id', 'N/A')}, docnm_kwd={src.get('docnm_kwd', 'N/A')}, kb_id={src.get('kb_id', 'N/A')}")
                # 检查向量字段
                for k in src.keys():
                    if '_vec' in k:
                        print(f"      向量字段: {k}, 维度: {len(src[k]) if isinstance(src[k], list) else 'str'}")
                        break
    except Exception as e:
        print(f"  索引 '{idx}': 错误 - {e}")

print()
print("=" * 60)
print("2. 测试检索")
print("=" * 60)

# 取第一个索引进行测试
if all_indices:
    test_index = all_indices[0]
    print(f"使用索引: {test_index}")
    
    dealer = Dealer(dataStore=es)
    
    question = "世运电路2023年中报的核心观点是什么"
    
    try:
        results = dealer.retrieval(
            question=question,
            embd_mdl=None,
            tenant_ids=test_index,
            kb_ids=None,
            vector_similarity_weight=0.6,
            page=1,
            page_size=5
        )
        print(f"检索完成: total={results['total']}, chunks={len(results['chunks'])}")
        for i, chunk in enumerate(results['chunks']):
            print(f"  chunk[{i}]: similarity={chunk.get('similarity', 'N/A'):.4f}, docnm={chunk.get('docnm_kwd', 'N/A')}")
            print(f"    content: {chunk.get('content_with_weight', '')[:100]}...")
    except Exception as e:
        import traceback
        print(f"检索失败: {e}")
        traceback.print_exc()
else:
    print("没有可用的索引！")

print()
print("=" * 60)
print("3. 直接用 ES 查询测试")
print("=" * 60)

if all_indices:
    test_index = all_indices[0]
    try:
        # 直接 match_all
        res = es.es.search(index=test_index, body={"query": {"match_all": {}}, "size": 3})
        print(f"match_all 查询: {res['hits']['total']} 个结果")
        
        # 直接 match 查询文本
        res = es.es.search(index=test_index, body={
            "query": {
                "query_string": {
                    "query": "世运电路",
                    "fields": ["content_ltks", "title_tks"],
                    "minimum_should_match": "30%"
                }
            },
            "size": 3
        })
        print(f"文本查询 '世运电路': {res['hits']['total']} 个结果")
        
        # 查看文档的 mapping
        mapping = es.es.indices.get_mapping(index=test_index)
        print(f"索引 mapping 字段: {list(mapping[test_index]['mappings'].get('properties', {}).keys())}")
    except Exception as e:
        import traceback
        print(f"ES 查询失败: {e}")
        traceback.print_exc()

print()
print("完成！")
