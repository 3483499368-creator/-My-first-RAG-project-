
from service.core.rag.nlp.search_v2 import Dealer
from service.core.rag.utils.es_conn import ESConnection

import json

# 懒加载：避免在模块导入时就连接 ES
_es_connection = None
_dealer = None

def _get_dealer():
    global _es_connection, _dealer
    if _dealer is None:
        _es_connection = ESConnection()
        _dealer = Dealer(dataStore=_es_connection)
    return _dealer


def retrieve_content(indexNames: str, question: str):

    # 懒加载获取 dealer
    dealer = _get_dealer()
    
    # 执行搜索
    results = dealer.retrieval(question = question,
                               embd_mdl = None,
                               tenant_ids = indexNames,
                               kb_ids = None,
                               vector_similarity_weight=0.6,
                               page = 1,
                               page_size = 5
    )

    # 提取 chunks 中的信息
    extracted_data = []


    for i, chunk in enumerate(results['chunks'], start=1):
        content_with_weight = chunk.get('content_with_weight', 'N/A')
        # similarity = chunk.get('similarity', 'N/A')
        # vector_similarity = chunk.get('vector_similarity', 'N/A')
        # term_similarity = chunk.get('term_similarity', 'N/A')
        doc_id = chunk.get('doc_id', 'N/A')
        docnm = chunk.get('docnm_kwd', 'N/A')
        docnm = docnm.split("/")[-1]

        message = {
            "id": i,
            "document_id": doc_id,
            "document_name": docnm,
            'content_with_weight': content_with_weight,
        }
        
        extracted_data.append(message)

    return extracted_data


if __name__ == '__main__':
    res = retrieve_content(question="世运电路成长性如何", indexNames="test01")
    print(res)
    
    # 将提取的数据写入到文件
    # with open("output.txt", "w", encoding="utf-8") as file:
    #     for data in extracted_data:
    #         file.write(f"content_with_weight: {data['content_with_weight']}\n")
    #         file.write(f"similarity: {data['similarity']}\n")
    #         file.write(f"vector_similarity: {data['vector_similarity']}\n")
    #         file.write(f"term_similarity: {data['term_similarity']}\n")
    #         file.write("\n")
    
    # print("结果已写入到 output.txt 文件中")