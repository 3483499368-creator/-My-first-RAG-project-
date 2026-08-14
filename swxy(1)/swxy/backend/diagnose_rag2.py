import sys, os, json
sys.path.insert(0, '/app')
os.chdir('/app')

print("=" * 60)
print("诊断 RAG 检索问题")
print("=" * 60)

# 1. 检查ES连接
from service.core.rag.utils.es_conn import ESConnection
es = ESConnection()
print(f"ES连接: {es.es.ping()}")

# 2. 列出所有索引
indices = list(es.es.indices.get(index="*").keys())
print(f"所有索引: {indices}")

for idx in indices:
    count = es.es.count(index=idx).get('count', 0)
    print(f"\n索引 '{idx}': {count} 个文档")
    if count > 0:
        res = es.es.search(index=idx, body={"query": {"match_all": {}}, "size": 1})
        src = res['hits']['hits'][0]['_source']
        print(f"  字段: {list(src.keys())}")
        print(f"  docnm_kwd: {src.get('docnm_kwd')}")
        print(f"  kb_id: {src.get('kb_id')}")
        print(f"  doc_id: {src.get('doc_id')}")
        for k in src:
            if '_vec' in k:
                print(f"  向量字段: {k}, 维度: {len(src[k]) if isinstance(src[k], list) else 'N/A'}")

# 3. 测试向量生成
from service.core.rag.nlp.model import generate_embedding
try:
    emb = generate_embedding("世运电路")
    if emb is not None:
        print(f"\n向量生成成功: 维度={len(emb)}")
    else:
        print("\n向量生成返回 None!")
except Exception as e:
    print(f"\n向量生成异常: {e}")

# 4. 测试检索
from service.core.rag.nlp.search_v2 import Dealer
dealer = Dealer(dataStore=es)

for idx in indices:
    print(f"\n--- 测试索引 '{idx}' ---")
    question = "世运电路2023年中报的核心观点是什么"
    
    # 4a. 直接测试 search
    try:
        req = {
            "kb_ids": None,
            "doc_ids": None,
            "size": 128,
            "question": question,
            "vector": True,
            "topk": 1024,
            "similarity": 0.1,
            "available_int": 1,
            "page": 1
        }
        sres = dealer.search(req, [idx], None, None, False)
        print(f"  search() total: {sres.total}, ids数量: {len(sres.ids)}")
        if sres.total > 0:
            print(f"  第一个chunk的score字段: {list(sres.field[sres.ids[0]].keys())[:10]}...")
    except Exception as e:
        import traceback
        print(f"  search() 异常: {e}")
        traceback.print_exc()
    
    # 4b. 测试 retrieval
    try:
        results = dealer.retrieval(
            question=question,
            embd_mdl=None,
            tenant_ids=idx,
            kb_ids=None,
            vector_similarity_weight=0.6,
            page=1,
            page_size=5
        )
        print(f"  retrieval(): total={results['total']}, chunks={len(results['chunks'])}")
    except Exception as e:
        import traceback
        print(f"  retrieval() 异常: {e}")
        traceback.print_exc()

print("\n诊断完成!")
