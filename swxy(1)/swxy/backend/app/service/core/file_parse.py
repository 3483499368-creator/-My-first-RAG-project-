import xxhash
import datetime
import os
import re
import logging
from service.core.rag.app.naive import chunk
from service.core.rag.utils.es_conn import ESConnection
from service.core.rag.nlp.model import generate_embedding
from service.core.rag.nlp import naive_merge, tokenize_chunks
from typing import List, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)

def dummy(prog=None, msg=""):
    pass


def _parse_pdf_with_pdfplumber(file_path: str):
    """降级方案：pdfplumber 逐页提取文本 → naive_merge → tokenize_chunks。
    与 chunk() 返回结构一致：list[dict]，包含 docnm_kwd / title_tks / content_with_weight 等。
    """
    try:
        import pdfplumber
        from service.core.rag.nlp import rag_tokenizer
    except Exception as e:
        raise RuntimeError(f"pdfplumber 或 rag_tokenizer 不可用: {e}")

    # 1. 提取纯文本
    buffer = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            if t.strip():
                buffer.append(t)
    full_text = "\n".join(buffer)
    if not full_text.strip():
        return []

    # 2. 元数据
    pure_name = os.path.basename(file_path)
    doc = {
        "docnm_kwd": pure_name,
        "title_tks": rag_tokenizer.tokenize(re.sub(r"\.[a-zA-Z]+$", "", pure_name)),
    }
    doc["title_sm_tks"] = rag_tokenizer.fine_grained_tokenize(doc["title_tks"])

    # 3. 按行切 sections，结构同 naive.py: list[(text, "")]
    lines = [ln.strip() for ln in full_text.split("\n") if ln.strip()]
    sections = [(ln, "") for ln in lines]

    # 4. 合并成 chunk（128 token 窗口，默认分隔符），再 tokenize 出 content_ltks/content_sm_ltks
    chunks = naive_merge(sections, 128, "\n!?。；！？")
    tokenized = tokenize_chunks(chunks, doc, False, None)
    return tokenized


def parse(file_path):
    """解析文件 → 返回 Chunk 列表。
    PDF 采用三级降级：PlainParser → pdfplumber → DeepDOC Pdf()。
    其他格式走 RAGFlow 原始 chunk() 逻辑。
    """
    filename_lower = str(file_path).lower()

    # 对 PDF 走定制降级逻辑，避免默认 DeepDOC 需要的 OCR/布局模型缺失直接炸
    if filename_lower.endswith(".pdf"):
        pure_name = os.path.basename(file_path)
        # Level 1: PlainParser
        try:
            from service.core.deepdoc.parser.pdf_parser import PlainParser
            logger.info(f"[PDF L1 PlainParser] 解析: {pure_name}")
            return chunk(
                file_path,
                callback=dummy,
                parser_config={
                    "chunk_token_num": 128,
                    "delimiter": "\n!?。；！？",
                    "layout_recognize": "Plain Text",
                },
            )
        except Exception as e1:
            logger.warning(f"[PDF L1 PlainParser] 失败: {e1}")

        # Level 2: pdfplumber 直接提取文本
        try:
            logger.info(f"[PDF L2 pdfplumber] 解析: {pure_name}")
            return _parse_pdf_with_pdfplumber(file_path)
        except Exception as e2:
            logger.warning(f"[PDF L2 pdfplumber] 失败: {e2}")

        # Level 3: DeepDOC（最后的选择，需要下载模型）
        logger.info(f"[PDF L3 DeepDOC] 回退尝试: {pure_name}")
        return chunk(file_path, callback=dummy)

    # 其他文件直接走默认逻辑
    return chunk(file_path, callback=dummy)

def batch_generate_embeddings(texts: List[str], batch_size: int = 10) -> List[List[float]]:
    """
    批量生成文本的向量嵌入
    
    Args:
        texts: 文本列表
        batch_size: 批处理大小（阿里云DashScope限制为10）
    
    Returns:
        向量列表
    """
    try:
        # 直接使用批量处理功能
        embeddings = generate_embedding(texts)
        return embeddings if embeddings is not None else []
    except Exception as e:
        print(f"批量生成向量失败: {e}")
        return []

def process_items(items: List[Dict[str, Any]], file_name: str, index_name: str) -> List[Dict[str, Any]]:
    """
    批量处理数据项
    
    Args:
        items: 数据项列表
        file_name: 文件名
        index_name: ES索引名称
    
    Returns:
        处理后的数据项列表
    """
    try:
        # 准备批量处理的数据
        texts = [item["content_with_weight"] for item in items]
        # 批量生成向量
        embeddings = batch_generate_embeddings(texts)
        
        # 处理每个数据项
        results = []
        for item, embedding in zip(items, embeddings):
            # 生成 chunk_id
            chunck_id = xxhash.xxh64((item["content_with_weight"] + index_name).encode("utf-8")).hexdigest()

            # 构建数据字典
            d = {
                "id": chunck_id,
                "content_ltks": item["content_ltks"],
                "content_with_weight": item["content_with_weight"],
                "content_sm_ltks": item["content_sm_ltks"],
                "important_kwd": [],
                "important_tks": [],
                "question_kwd": [],
                "question_tks": [],
                "create_time": str(datetime.datetime.now()).replace("T", " ")[:19],
                "create_timestamp_flt": datetime.datetime.now().timestamp()
            }

            d["kb_id"] = index_name
            # docnm_kwd 归一化：只保留 basename，避免绝对路径导致后续 term 查询匹配不到
            raw_docnm_kwd = item.get("docnm_kwd") or file_name
            normalized_kwd = os.path.basename(raw_docnm_kwd)
            d["docnm_kwd"] = normalized_kwd
            # 兼容旧数据，再额外写一份 file_name 作为 keyword 字段
            d["file_name_kwd"] = file_name
            d["title_tks"] = item["title_tks"]
            d["doc_id"] = xxhash.xxh64(file_name.encode("utf-8")).hexdigest()
            # docnm 字段也统一只写纯文件名
            d["docnm"] = file_name
            
            # 将嵌入向量存储到字典中
            d[f"q_{len(embedding)}_vec"] = embedding
            
# content_ltks: item["content_ltks"]
# 含义：文本内容的粗粒度分词结果
# 处理：使用RAG分词器进行基础分词
# 示例：["人工智能", "是", "一门", "新兴", "技术"]
# content_with_weight: item["content_with_weight"]
# 含义：原始文本内容（带权重信息）
# 作用：保存完整的文本内容，用于显示和检索
# 示例："人工智能是一门新兴技术，在各个领域都有广泛应用。"
# content_sm_ltks: item["content_sm_ltks"]
# 含义：文本内容的细粒度分词结果
# 处理：更详细的分词，包含更多语义信息
# 示例：["人工", "智能", "是", "一门", "新兴", "的", "技术"]
# kb_id: index_name
# 含义：知识库标识符
# 作用：标识文档块属于哪个知识库
# 示例："tech_documents", "company_policies"
# docnm_kwd: item["docnm_kwd"]
# 含义：文档名称关键词
# 来源：从原始文件名提取的关键词
# 作用：用于基于文档名的检索
# title_tks: item["title_tks"]
# 含义：文档标题的分词结果
# 处理：去除文件扩展名后进行分词
# 示例：["人工智能", "技术", "报告"]
# docnm: file_name
# 含义：完整的文档文件名
# 作用：保存原始文件名，用于溯源和显示
# 示例："人工智能技术报告.pdf"

            results.append(d)

        return results

    except Exception as e:
        print(f"process_items error: {e}")
        return []

def execute_insert_process(file_path: str, file_name: str, index_name: str):
    """
    执行文档处理和插入 Elasticsearch 的函数
    
    Args:
        file_path: 文件路径
        file_name: 文件名
        index_name: ES索引名称
    """
    # 解析文档
    documents = parse(file_path)
    if not documents:
        print(f"No documents found in {file_path}")
        return

    # 批量处理文档
    processed_documents = process_items(documents, file_name, index_name)
    if not processed_documents:
        print(f"Failed to process documents from {file_path}")
        return

    # 批量插入 ES
    try:
        es_connection = ESConnection()
        es_connection.insert(documents=processed_documents, indexName=index_name)
        print(f"Successfully inserted {len(processed_documents)} documents into ES")
    except Exception as e:
        print(f"Failed to insert documents into ES: {e}")

# 测试代码
if __name__ == "__main__":
    file_path = "/mnt/d/wsl/project/gsk-poc/storage/file/【兴证电子】世运电路2023中报点评.pdf"
    session_id = "40e2743ccffa4207"
    output_file = "/mnt/d/wsl/project/gsk-poc/storage/output/result.json"

    # 如果本地文件不存在，则解析文件并保存结果
    if not os.path.exists(output_file):
        documents = parse(file_path)
        
        # 批量处理文档
        result = process_items(documents, file_path, session_id)

        # 将结果保存到本地文件
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        print(f"结果已保存到本地文件: {output_file}")
    else:
        # 如果本地文件存在，则从文件中读取结果
        with open(output_file, "r", encoding="utf-8") as f:
            result = json.load(f)
        print(f"从本地文件加载结果: {output_file}")

    # 创建 ESConnection 的实例并插入数据
    es_connection = ESConnection()
    es_connection.insert(documents=result, indexName="世运电路2023中报点评")

