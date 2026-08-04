
---

说明：本文根据AI搜题答题系统（swxy）项目代码复盘整理。结构为：先概括面试流程并列出面试官问题，再逐题整理"面试官问题、我的回答、我的回答的问题、标准回答"，最后汇总面试官反馈和后续补强清单。文中所有数据结构、字段名、权重参数均来自项目真实代码，避免编造实现细节。

## 一、面试基本信息

- 公司：待补充
- 岗位：Python后端/全栈工程师 / AI应用开发工程师
- 面试轮次：待补充
- 算法题：待补充
- 算法结果：待补充
- 项目重点：AI搜题答题系统（RAG知识库 + 混合检索 + SSE流式问答）

**本场主要考察内容：**

1. RAG完整数据流（文档上传 → 解析切分 → 向量化 → 索引 → 检索 → 重排 → 生成）
2. 前后端交互（SSE流式协议、JWT认证、请求/响应格式）
3. 混合检索设计（关键词检索 vs 向量检索、融合权重、重排策略）
4. Elasticsearch索引设计（动态模板、dense_vector、自定义相似度脚本）
5. Redis缓存设计（Key格式、TTL、快速解析内容缓存）
6. PostgreSQL表结构（6张核心表的设计逻辑、外键、索引）
7. Chunk切分与存储结构（字段名、分词方式、向量维度）
8. 引用标注机制（答案与检索Chunk的关联方式）
9. Docker Compose多容器编排（FastAPI + PG + ES + Redis）
10. 是否真正理解RAGFlow框架二次开发的代码

---

## 二、面试流程概括

面试开始后，先完成一道算法题。算法题结束后，面试官查看简历，选择AI搜题答题系统进行深入考察。

项目介绍过程中，面试官不会重点询问宏观的RAG或大模型概念，而是持续追问工程实现细节，包括：

- 前端聊天界面如何与后端建立流式连接；
- SSE事件有哪几种类型，分别携带什么数据；
- 文档上传后完整处理链路（保存→解析→切Chunk→向量化→写ES）；
- Chunk具体怎么切，多大，哪些字段存ES；
- ES索引名怎么命名，动态模板匹配规则是什么；
- 关键词检索和向量检索的融合权重是多少，为什么这样设置；
- 重排阶段用的是什么模型，权重怎么调；
- 答案中的引用标注 ##1$$ 是怎么生成的，匹配阈值是多少；
- JWT Token包含哪些字段，有效期多久；
- Redis缓存了什么，Key是什么格式，TTL多久；
- PostgreSQL有哪几张表，主键分别是什么类型，为什么sessions.user_id是VARCHAR而users.id是INT；
- 快速解析和知识库上传两种文档处理方式有什么区别；
- Docker Compose中几个服务的启动顺序和依赖关系。

---

## 三、面试官问题完整列表

1. 请完成算法题（待补充）
2. 介绍一下AI搜题答题系统的完整流程，从用户打开页面到拿到答案的全链路。
3. 项目的前端和后端分别用了什么技术栈？
4. 项目是怎么部署的？Docker Compose里有几个服务？分别是什么？
5. 用户登录认证是怎么做的？JWT Token里包含什么？有效期多久？
6. 密码是怎么存储的？用了什么加密算法？
7. 文档上传接口 `/upload_files` 的完整处理流程是什么？
8. 支持哪些文档格式？Excel是怎么校验的？
9. 什么是「快速解析」 `/quick_parse`？和知识库上传有什么区别？
10. 快速解析的结果存在哪里？Redis Key是什么？TTL多久？
11. 文档解析后是怎么切分成Chunk的？Chunk大小是多少？切分规则是什么？
12. Chunk写入Elasticsearch时，索引名是怎么生成的？
13. ES索引的Mapping用了动态模板，匹配规则有哪些？举几个例子。
14. 向量字段存在ES的什么字段里？维度是多少？用的什么Embedding模型？
15. 向量相似度用的是什么计算方式？
16. 关键词检索和向量检索是怎么融合的？融合权重是多少？
17. 两路检索是并行还是串行？
18. 融合之后还有重排吗？重排用的是什么模型？重排权重是多少？
19. 重排阶段title_tks、important_kwd、question_tks的权重分别是多少？
20. 用户提问 `/chat_on_docs` 的完整处理链路是什么？
21. 后端如何向前端流式返回答案？SSE协议的事件类型有哪些？
22. 大模型回答中的引用标记 ##1$$ 是怎么生成的？匹配阈值是多少？
23. 最终回答写数据库时，保存了哪些字段？messages表的结构是什么？
24. 会话名称是怎么生成的？什么时候生成？
25. PostgreSQL一共有哪几张表？每张表的主键类型是什么？
26. users表的id是SERIAL（INT），但sessions表的user_id是VARCHAR(255)，这会不会有问题？为什么？
27. messages表的documents、recommended_questions、think字段是什么类型？为什么不用JSONB？
28. ES的自定义相似度脚本 scripted_sim 是怎么计算的？
29. 推荐问题是怎么生成的？用的什么模型？
30. 知识库检索时如果第一次结果为空，系统会怎么做？
31. 如果快速解析的内容超过4000字符，系统怎么处理？
32. 项目中哪些地方做了异常处理？举几个例子。
33. 为什么选择PostgreSQL而不是MySQL？
34. 为什么选择Elasticsearch做向量检索而不是Milvus或Chroma？
35. 为什么同时需要PostgreSQL和Elasticsearch？各自职责是什么？
36. 引用标注的匹配中，如果代码块（```）怎么处理？
37. 上传重复文件时系统怎么处理？
38. sessions表的session_id是怎么生成的？为什么是16位？
39. JWT的secret_key是怎么配置的？为什么加了一个'happy'后缀？
40. 大模型用的是什么？回答和思考过程怎么区分？

---

## 四、逐题问答整理

---

### 1. 介绍一下AI搜题答题系统的完整流程，从用户打开页面到拿到答案的全链路。

**我的回答的问题：**
1. 容易把「快速解析」和「知识库上传」两条链路混在一起讲。
2. 容易跳过中间的具体数据格式，只讲概念。
3. 没有区分哪些步骤是同步的、哪些是异步的。
4. 没有讲清楚SSE流中事件的先后顺序。

**标准回答：**

整个系统的完整流程可以分成**两条文档链路** + **一条问答链路**。我先讲文档怎么进入系统，再讲用户提问怎么得到答案。

**第一步：用户登录**
用户打开React页面，输入用户名密码 → 前端POST `/api/user/login` → 后端查询PostgreSQL的users表，用bcrypt校验密码 → 生成JWT Token（包含user_id、user_name、随机salting），有效期2天 → 返回给前端存入localStorage。

**第二步（文档链路A）：上传到知识库（长期存储）**
用户在知识库页面选择文件 → 前端调用 `/upload_files`（multipart/form-data，携带session_id和JWT）→
后端流程：
- 检查文件名是否在knowledgebases表中已存在该用户下，重复则直接报错；
- 文件保存到 `storage/file/{session_id}/{filename}`；
- 调用 `execute_insert_process()` 解析文档，切Chunk，生成Embedding，写入Elasticsearch（索引名=user_id）；
- 写入PostgreSQL的knowledgebases表（记录user_id和file_name）。

**第二步（文档链路B）：快速解析（临时会话用）**
用户在聊天页上传单份文档（≤4页）→ 前端调用 `/quick_parse` →
后端流程：
- 解析文档提取纯文本；
- 以 `session_id` 为Key存入Redis，TTL=2小时；
- 同时在document_uploads表记录上传日志。

**第三步：用户提问（问答链路）**
用户在聊天框输入问题 → 前端POST `/chat_on_docs?session_id=xxx`（JSON: `{message: "问题"}`，Header带JWT，响应类型为text/event-stream）→
后端处理：
1. JWT校验，提取user_id；
2. 调用 `retrieve_content(user_id, question)` → 从ES中按user_id为索引名，做混合检索（关键词0.05 + 向量0.95）→ 重排（关键词0.4 + 向量0.6）→ 返回Top-5 Chunk；
3. 从Redis按session_id取快速解析内容（如果有），截断到4000字符；
4. 组装Prompt（包含知识库Chunk + 快速解析内容 + 引用标注格式要求）；
5. 调用deepseek-r1模型，stream=True开启流式；
6. **SSE事件依次发送：**
   - 先发送一个 `event:message`，内容是 `{documents: [...]}`（所有检索到的文档列表，供前端展示引用卡片）；
   - 然后逐个发送模型token：`event:message {content, thinking:false}` 或 `{content, thinking:true}`（区分思考过程和正式回答）；
   - 回答结束（finish_reason=stop）后：调用qwen2.5-7b生成3个推荐问题，作为一个 `event:message {recommended_questions: [...]}` 发送；
   - 最后发送 `event:end data:[DONE]`；
7. 流结束后异步落库：
   - 调用 `write_chat_to_db()` → 插入messages表（user_question、model_answer、documents JSON、recommended_questions JSON、think JSON）；
   - 调用 `update_session_name()` → 如果该session_id还没在sessions表中，则用qwen2.5-72b生成会话名，插入sessions表。

**第四步：前端渲染**
前端用EventSource解析SSE流 → 实时拼接回答 → 遇到引用标记 ##N$$ 则转成脚注链接 → 显示推荐问题按钮。

---

### 2. 项目的前端和后端分别用了什么技术栈？

**标准回答：**

**后端技术栈：**
- Web框架：FastAPI（Python 3.x），ASGI服务器uvicorn
- 数据库ORM：SQLAlchemy + PostgreSQL 15
- 搜索引擎：Elasticsearch 8.11.3（存储Chunk + 向量检索）
- 缓存：Redis 7（存储快速解析文档内容）
- 认证：fastapi-jwt（JWT Bearer + Cookie双读取）+ bcrypt（密码哈希）
- 大模型SDK：OpenAI兼容SDK，调用DashScope的deepseek-r1、qwen2.5-7b-instruct、qwen2.5-72b-instruct
- Embedding模型：DashScope text-embedding-v3（1024维）
- 部署：Docker Compose 多容器编排

**前端技术栈：**
- 框架：React 18 + TypeScript
- 构建工具：Vite
- UI库：Ant Design
- 状态管理：（待核对，大概率是Zustand或Context）
- 流式请求：fetch + ReadableStream 处理 text/event-stream

---

### 3. 项目是怎么部署的？Docker Compose里有几个服务？分别是什么？

**标准回答：**

项目使用 `docker-compose.yml` 进行多容器部署，一共4个服务：

| 服务名 | 镜像 | 端口映射 | 主要作用 | 启动依赖 |
|--------|------|----------|----------|----------|
| swxy_api | 基于 ./app/Dockerfile 自定义构建 | 8000:8000 | FastAPI后端，uvicorn启动 | gsk_pg, es01, redis |
| es01 | docker.elastic.co/elasticsearch/elasticsearch:8.11.3 | 不对外暴露端口（内网通信） | ES向量检索和全文检索，单节点，JVM堆内存512MB | 无 |
| gsk_pg | postgres:15-alpine | 不对外暴露端口 | PostgreSQL业务数据库，初始化时执行init.sql建表 | 无 |
| redis | redis:7-alpine | 不对外暴露端口 | 缓存快速解析的文档内容 | 无 |

4个服务都在自定义的 `gsk_network` bridge网络中，互相用服务名访问（如redis:6379、es01:9200）。数据持久化通过3个named volume：gsk_esdata01、pg_data、redis_data。

后端服务还挂载了本地 `./app` 目录到容器的 `/app`，方便开发时热更新。ES的xpack.security只开了HTTP Basic认证（用户名elastic，密码从.env读取ELASTIC_PASSWORD），SSL关闭。

---

### 4. 用户登录认证是怎么做的？JWT Token里包含什么？有效期多久？

**标准回答：**

认证代码在 `service/auth.py`。

**登录流程：**
1. 前端POST用户名密码；
2. 后端从users表查询username匹配的记录；
3. 用 `verify_password(明文, password_hash)` 校验，底层是bcrypt；
4. 校验通过调用 `create_token(user_id, user_name)` 生成JWT。

**JWT Token详情：**
- 生成工具：fastapi-jwt的 `JwtAccessBearerCookie`；
- Secret Key：从环境变量 `JWT_SECRET_KEY` 读取，再拼接固定字符串 `'happy'` 作为最终密钥；
- Token主体（subject）包含3个字段：
  ```json
  {
    "user_id": 123,          // INT，users表的主键
    "user_name": "alice",    // 用户名
    "salting": "a1b2c3..."   // secrets.token_hex(16)，每次登录都不一样，防止重放
  }
  ```
- 有效期：`timedelta(days=2)`，即2天过期；
- 读取方式：请求头 Authorization: Bearer <token> 或 Cookie中读取，优先Header。

---

### 5. 文档上传接口 `/upload_files` 的完整处理流程是什么？

**标准回答：**

代码在 `router/chat_rt.py` 的 `upload_files()` 函数。完整流程：

1. **JWT校验**：从credentials提取user_id；
2. **session_id兜底**：如果没传session_id，就用user_id字符串代替；
3. **目录准备**：确保 `storage/file/{session_id}/` 目录存在；
4. **重复文件校验**：遍历所有上传文件，查询knowledgebases表中该user_id下是否已存在同名file_name，如果存在则整批直接抛400错误，**全部文件都不处理**；
5. **逐文件处理**（每个文件独立try-catch，部分失败不影响其他）：
   a. 读取文件字节流；
   b. 空文件校验，失败记入failed_files；
   c. Excel格式额外校验：.xlsx检查文件头是否以`PK`开头（ZIP格式），.xls检查是否以`\xd0\xcf\x11\xe0`或`\x09\x08`开头；
   d. 写入本地文件：`storage/file/{session_id}/{filename}`；
   e. 校验磁盘文件大小和原始字节长度是否一致；
   f. **解析写ES**：调用 `execute_insert_process(file_url, file_name, session_id)` → 解析文档 → 切Chunk → 向量化 → 写入ES；
   g. **写PG元数据**：调用 `insert_knowledgebase(user_id, file_name)` → 插入knowledgebases表。
6. **结果返回**：
   - 全部成功 → 200 status=success；
   - 部分成功 → 200 status=partial_success，返回成功和失败列表；
   - 全部失败 → 400 status=failed。

---

### 6. 什么是「快速解析」 `/quick_parse`？和知识库上传有什么区别？

**标准回答：**

| 维度 | 快速解析 `/quick_parse` | 知识库上传 `/upload_files` |
|------|------------------------|--------------------------|
| 目的 | 聊天时临时用一份文档，不长期留存 | 建立长期知识库，可跨会话使用 |
| 文档数量 | 每次1份文档 | 每次可批量多份 |
| 文档大小限制 | ≤4页（service层校验） | 无页数硬限制（但ES写入有时间成本） |
| 支持格式 | docx, pdf, txt | docx, pdf, txt, xlsx/xls（有额外文件头校验） |
| 解析结果存储 | Redis，Key=session_id，TTL=2小时 | Elasticsearch，索引名=user_id，永久存储 |
| 元数据表 | document_uploads表（仅上传日志） | knowledgebases表（用户-文件关联） |
| 切Chunk | **不切Chunk**，整段文本存Redis | 切Chunk，每Chunk生成Embedding存ES |
| 检索方式 | 不参与向量检索，直接拼到Prompt里（截断4000字） | 走混合检索（关键词+向量）+ 重排，Top-5召回 |
| 跨会话可用 | ❌ 仅当前session_id可用（Redis Key绑定） | ✅ 同一用户所有会话都能检索 |

代码对应：
- 快速解析：`service/quick_parse_service.py` + Redis的 `get_quick_parse_content()`；
- 知识库上传：`service/core/file_parse.py` 的 `execute_insert_process()`。

---

### 7. 快速解析的结果存在哪里？Redis Key是什么？TTL多久？

**标准回答：**

快速解析的纯文本内容直接存在Redis，没有加业务前缀。

- **Redis Key**：就是 `session_id` 的值（16位字符串，例如 `"a83f91c2d4e5b607"`）；
- **Value**：纯文本字符串（文档解析后的完整内容）；
- **TTL**：2小时（在 `quick_parse_service.py` 中通过 `redis_client.setex(session_id, 7200, content)` 设置）；
- **客户端配置**：host=redis（容器名），port=6379，db=0，decode_responses=True（自动把bytes转str）。

读取时调用 `get_quick_parse_content(session_id)` → `redis_client.get(session_id)`。过期自动失效，不主动删除。

> ⚠️ 潜在隐患：Key没有前缀，如果将来Redis存别的业务，容易和session_id冲突；另外不同用户如果恰好session_id碰撞（虽然概率极低）会串数据。

---

### 8. 文档解析后是怎么切分成Chunk的？Chunk大小是多少？切分规则是什么？

**标准回答（基于RAGFlow框架的默认切分）：**

切分逻辑在RAGFlow的 `service/core/rag/` 目录中，具体是分词器 `rag_tokenizer.py` + 切分器组合。项目采用的是**按Token数的滑窗切分**：

1. **预处理**：先通过PDF/DOCX解析器提取纯文本，清理换行、多余空格、页眉页脚；
2. **切分单位**：按Token数切分，**默认Chunk大小约128 Token**；
3. **切分边界**：优先在句子结束符处切分。分隔符集合：`"\n!?。；！？"`；
4. **分词方式**：双粒度分词：
   - `content_ltks`：粗粒度分词（whitespace分隔，用于全文检索）；
   - `content_sm_ltks`：细粒度分词（中文按字/词混合切）；
5. **重要字段提取**：从段落中提取 `important_kwd`（关键词数组）、`title_tks`（标题分词）、`question_tks`（如果识别为题目）。

每个Chunk在落ES前，会调用Embedding模型生成1024维向量，一并写入。

---

### 9. Chunk写入Elasticsearch时，索引名是怎么生成的？

**标准回答：**

代码在 `search_v2.py` 第27行：
```python
def index_name(uid): return f"{uid}"
```

即**Elasticsearch索引名 = 用户的tenant_id（实际就是user_id的字符串形式）**。

调用链路：
```
retrieve_content(user_id=1001, question=...)
  → dealer.retrieval(tenant_ids=user_id)
    → [index_name(tid) for tid in tenant_ids]
    → ES search 索引名为 "1001"
```

也就是说，**每个用户独占一个ES索引**，用户之间的Chunk数据物理隔离在不同索引中。好处是检索时不用额外加user_id过滤条件，坏处是用户量大时索引数多（但单用户数据量小，问题不大）。

---

### 10. ES索引的Mapping用了动态模板，匹配规则有哪些？举几个例子。

**标准回答：**

Mapping定义在 `service/core/conf/mapping.json`，全部使用 dynamic_templates（即字段按后缀名自动匹配类型），**不用手动为每个索引定义字段**。核心匹配规则：

| 后缀匹配 | ES字段类型 | 说明 |
|----------|-----------|------|
| `*_tks` | text + similarity=scripted_sim + analyzer=whitespace | 分词文本，用自定义IDF脚本计算相似度（如title_tks, question_tks） |
| `*_ltks` | text + analyzer=whitespace | 分词文本，用默认BM25相似度（如content_ltks） |
| `*_kwd / *_id / *_ids / *_uid / *_uids / uid` | keyword + similarity=boolean | 精确匹配关键词（如docnm_kwd文档名、kb_id、doc_id） |
| `*_int` | integer | 整数（如page_num_int、position_int、top_int、available_int） |
| `*_flt` | float | 浮点数（如create_timestamp_flt） |
| `*_dt / *_time / *_at` | date，格式 `yyyy-MM-dd HH:mm:ss\|\|yyyy-MM-dd\|\|...` | 日期 |
| `*_with_weight / *_list` | text，index=false，store=true | 不建倒排，只存储原始内容（如content_with_weight） |
| `*_fea` | rank_feature | 排序特征（如tag_fea） |
| `*_512_vec / *_768_vec / *_1024_vec / *_1536_vec` | dense_vector + similarity=cosine + dims=对应维度 | 稠密向量（本项目用 `q_1024_vec`，即DashScope embedding的1024维） |
| `*_nst` | nested | 嵌套对象 |
| `*_bin` | binary | 二进制 |

**举个实际Chunk的字段例子：**
```json
{
  "docnm_kwd":         "2024高数试题.pdf",   // *_kwd → keyword
  "content_ltks":       "函数 极限 连续 ...", // *_ltks → text(whitespace)
  "content_with_weight":"函数极限连续...",    // *_with_weight → text(index=false,只存)
  "title_tks":         "第一章 函数",         // *_tks → text(scripted_sim)
  "question_tks":      "求 极限 lim ...",     // *_tks → text(scripted_sim)
  "important_kwd":     ["极限","洛必达"],     // *_kwd（数组元素也是keyword）
  "page_num_int":      3,                     // *_int → integer
  "position_int":      [1, 100, 200, 50, 70], // *_int 数组
  "kb_id":             "kb_xxx",              // *_id → keyword
  "doc_id":            "doc_xxx",             // *_id → keyword
  "available_int":     1,                     // *_int → integer（软删除标记，1=可用）
  "q_1024_vec":        [0.12, -0.03, ...]     // *_1024_vec → dense_vector(1024, cosine)
}
```

---

### 11. 向量字段存在ES的什么字段里？维度是多少？用的什么Embedding模型？

**标准回答：**

- **ES字段名**：`q_1024_vec`（匹配 `*_1024_vec` 动态模板 → dense_vector）；
- **向量维度**：1024维；
- **相似度函数**：cosine余弦相似度（在mapping中写死 `similarity: "cosine"`）；
- **Embedding模型**：DashScope的 `text-embedding-v3`（通义千问的Embedding模型，输出1024维float向量）；
- **调用入口**：`search_v2.py` 的 `get_vector()` → `generate_embedding(txt)`；
- **查询向量生成时机**：用户提问时，在 `search()` 函数中用同一模型把question转成向量，再去ES做kNN检索。

---

### 12. ES的自定义相似度脚本 scripted_sim 是怎么计算的？

**标准回答：**

定义在 `mapping.json` 的 `settings.similarity.scripted_sim`：
```json
{
  "type": "scripted",
  "script": {
    "source": "double idf = Math.log(1+(field.docCount-term.docFreq+0.5)/(term.docFreq + 0.5))/Math.log(1+((field.docCount-0.5)/1.5)); return query.boost * idf * Math.min(doc.freq, 1);"
  }
}
```

这是一个**改进版的BM25-IDF**自定义脚本：
- 分子部分：`(field.docCount - term.docFreq + 0.5) / (term.docFreq + 0.5)` → 标准IDF的平滑版本；
- 分母部分：`Math.log(1 + (field.docCount-0.5)/1.5)` → 对文档总数做归一化缩放，避免大语料IDF过大；
- TF部分：`Math.min(doc.freq, 1)` → **词频截断为1**，不奖励一个词在文档中出现多次（避免关键词堆砌）；
- 最终得分：`query.boost * idf * TF(≤1)`。

适用字段：`*_tks`（title_tks、question_tks）。目的是让标题和问句中的命中词更看重"有没有"（IDF权重）而不是"出现多少次"，因为标题/问句通常很短。

---

### 13. 关键词检索和向量检索是怎么融合的？融合权重是多少？

**标准回答：**

代码在 `search_v2.py` 第108-112行：
```python
matchDense = self.get_vector(qst, emb_mdl, topk, req.get("similarity", 0.1))
fusionExpr = FusionExpr("weighted_sum", topk, {"weights": "0.05, 0.95"})
matchExprs = [matchText, matchDense, fusionExpr]
```

**融合方式：ES的weighted_sum加权求和**，不是代码层融合。

两路召回并行（ES内部同时计算）：
1. **matchText（关键词检索）**：`FulltextQueryer.question()` 生成的全文检索DSL（基于content_ltks等*_tks字段，用scripted_sim相似度）→ 权重 **0.05**；
2. **matchDense（向量检索）**：`MatchDenseExpr` 生成的kNN DSL（对 `q_1024_vec` 做cosine相似度kNN，topk=1024，similarity阈值默认0.1）→ 权重 **0.95**；
3. **fusionExpr**：ES把两路分数归一化后，按 `0.05 * 关键词分 + 0.95 * 向量分 = 最终分` 排序。

**为什么这么设置？**
因为搜题场景下，**语义相似度比字面关键词更重要**。学生的问法和题库表述经常不一样（比如"求lim"和"求极限"），所以给向量检索高权重。但保留5%的关键词权重，防止完全没有语义相似但词精确匹配的题目被漏掉（比如精确的公式编号、定理名）。

---

### 14. 融合之后还有重排吗？重排用的是什么模型？重排权重是多少？

**标准回答：**

**ES融合之后还有一次重排（Rerank）**，在Python层执行。代码在 `search_v2.py` 的 `retrieval()` 函数第367-377行：

```python
if page <= RERANK_PAGE_LIMIT:  # RERANK_PAGE_LIMIT = 3，只对前3页重排
    if sres.total > 0:
        print("重排模型。。。。")
        sim, tsim, vsim = self.rerank_by_model(
            rerank_mdl, sres, question,
            1 - vector_similarity_weight,   # tkweight = 1 - 0.6 = 0.4
            vector_similarity_weight,       # vtweight = 0.6
            rank_feature=rank_feature       # 默认 {PAGERANK_FLD: 10}
        )
```

**实际调用 `retrieve_content()`（chat接口调用的入口）传参：**
```python
retrieve_content(indexNames, question)
  → dealer.retrieval(vector_similarity_weight=0.6, page=1, page_size=5)
```

**所以重排权重：**
- **关键词相似度权重 tkweight = 0.4**
- **向量相似度权重 vtweight = 0.6**

重排内部做了什么（`rerank_by_model`）：
1. **关键词重算 tsim**：用 `query.question()` 重新提取查询关键词 → 与Chunk的 `content_ltks + title_tks + important_kwd` 计算Jaccard/重合率；
2. **向量重算 vsim**：用 `rerank_similarity(query, chunk_texts)` 调用独立的rerank模型（DashScope的文本相似度接口），不是用ES存的向量直接算；
3. **特征分 rank_fea**：`_rank_feature_scores()` 计算TAG特征的余弦相似度 + Pagerank分 × 10；
4. **最终分**：`0.4 * (tsim + rank_fea) + 0.6 * vsim`。

然后用 `np.argsort(sim * -1)` 按最终分降序排列，截取当前页。超过第3页的内容不做重排（为了省算力），直接用ES返回的原始顺序。

---

### 15. 重排阶段title_tks、important_kwd、question_tks的权重分别是多少？

**标准回答：**

在 `rerank()` 函数（非模型版重排，sres.total=0时的降级路径）的第298-302行：

```python
content_ltks = sres.field[i][cfield].split()          # 正文分词，权重 ×1
title_tks = [t for t in sres.field[i].get("title_tks", "").split() if t]  # 标题分词 ×2
question_tks = [t for t in sres.field[i].get("question_tks", "").split() if t]  # 问句分词 ×6
important_kwd = sres.field[i].get("important_kwd", [])                     # 重要关键词 ×5
tks = content_ltks + title_tks * 2 + important_kwd * 5 + question_tks * 6
```

相当于**不同分词字段在做词袋匹配时的扩增倍数（伪造词频）**：

| 字段 | 权重倍数 | 原因 |
|------|---------|------|
| content_ltks（正文） | ×1 | 基础分 |
| title_tks（标题） | ×2 | 标题命中比正文更重要 |
| important_kwd（重要关键词） | ×5 | 人工/规则提取的核心词，权重很高 |
| question_tks（问句字段） | ×6 | 问句对问句匹配，搜题场景强信号 |

**`rerank_by_model`（模型版重排，实际走的路径）的第323-327行**，title和important_kwd不做加权：
```python
tks = content_ltks + title_tks + important_kwd   # 全部×1
```
因为模型版的向量相似度已经隐式编码了这些重要性，关键词分只做辅助。

---

### 16. 用户提问 `/chat_on_docs` 的完整处理链路是什么？

**标准回答：**

代码入口：`router/chat_rt.py` 的 `chat_on_docs()`。

1. **请求校验**：
   - JWT校验 → 提取user_id（转str）；
   - 从Query取session_id；
   - 请求体是 `{message: "用户问题"}`。

2. **知识库检索（可降级）**：
   ```python
   try:
       references = retrieve_content(user_id, question)
   except Exception as e:
       references = []  # 没有知识库也能继续聊天
   ```
   `retrieve_content()` 内部：
   - 调用 `dealer.retrieval()` → ES混合检索（关键词0.05+向量0.95）→ Top 1024候选；
   - 调用 `rerank_by_model()` → DashScope rerank模型 + 关键词重算 + 特征分 → Top-128 × 权重(0.4词 + 0.6向量)；
   - 排序截取 page_size=5 → 返回chunks列表（每个含id、document_id、document_name、content_with_weight）。

3. **构建SSE流**：
   返回 `StreamingResponse(get_chat_completion(...), media_type="text/event-stream")`，开始流式输出。

4. **`get_chat_completion()` 内部流程**：
   a. **取快速解析内容**：Redis GET session_id，拿到临时文档（如果存在）；
   b. **组装Prompt参考内容**：
      - 知识库references：按`[N] 内容`格式编号；
      - 快速解析内容：截断到4000字符，单独一段；
      - 要求大模型回答时每部分内容后标注来源 ##N$$；
   c. **调用大模型**：DashScope SDK，`model=deepseek-r1`，`stream=True`；
   d. **先发送documents事件**：第一个message事件是所有检索文档列表（含知识库Chunks + 快速解析分段），前端用来显示"参考资料"卡片；
   e. **流式转发tokens**：
      - `delta.content`有值 → 正式回答 `{role:assistant, content, thinking:false}`；
      - `delta.reasoning_content`有值 → 思考过程 `{role:assistant, content, thinking:true}`；
   f. **finish_reason=stop时**：
      - 用`qwen2.5-7b-instruct`生成3个推荐问题 → 发送一个message事件；
      - 发送`event:end data:[DONE]`；
      - **落库**：`write_chat_to_db()`写入messages表；
      - **会话名**：`update_session_name()`首次写入sessions表（用qwen2.5-72b生成会话名）。

---

### 17. 后端如何向前端流式返回答案？SSE协议的事件类型有哪些？

**标准回答：**

使用FastAPI的`StreamingResponse`，`media_type="text/event-stream"`。每个事件遵循SSE格式：
```
event: <事件类型>
data: <JSON字符串>

```
（注意末尾两个换行符）

**按发送顺序的事件类型清单：**

| 顺序 | event | data内容 | 触发时机 |
|------|-------|---------|---------|
| 1 | `message` | `{documents: [{id, document_id, document_name, content_with_weight, ...}]}` | 流开始时，先把所有检索到的参考文档一次性发给前端（含知识库5条 + 快速解析分段） |
| 2~N | `message` | `{role: "assistant", content: "token", thinking: false}` | 大模型流式输出每一段正式回答内容（delta.content） |
| 2~N | `message` | `{role: "assistant", content: "思考...", thinking: true}` | deepseek-r1输出的<reasoning>思考过程（delta.reasoning_content） |
| N+1 | `message` | `{recommended_questions: ["问题1", "问题2", "问题3"]}` | 回答结束后，qwen2.5-7b生成的3个相关问题 |
| 最后 | `end` | `[DONE]` | 标识流完全结束 |
| 异常 | `error` | `{role: "error", content: "错误信息"}` | 任何环节抛出Exception时 |

**前端解析：** 用`fetch` + `response.body.getReader()`逐块读取，按`\n\n`切分事件，按`thinking`字段区分是灰色思考过程还是黑色正式回答。

---

### 18. 大模型回答中的引用标记 ##1$$ 是怎么生成的？匹配阈值是多少？

**标准回答：**

这是**模型输出后，代码二次注入**的，不是让模型自己加的。代码在 `search_v2.py` 的 `insert_citations()` 函数（第162-249行）。

完整步骤：

1. **切分模型回答为句子**：
   - 先按 ``` 把代码块单独切出来（代码块不做标注，避免误标）；
   - 非代码部分按正则 `[；。？!！\n]` 或 `[a-z][.?;!][ \n]` 切为句子；
   - 拼接分隔符回句子末尾，长度<5的句子跳过。

2. **向量化每个句子**：
   ```python
   ans_v, _ = embd_mdl.encode(pieces_)  # 对所有句子批量做Embedding
   ```

3. **双层循环相似度匹配**：
   对每个句子 i：
   ```python
   sim, tksim, vtsim = hybrid_similarity(
       ans_v[i],         # 句子向量
       chunk_v,          # 所有检索Chunk的向量列表
       tokenize(句子),   # 句子关键词
       chunks_tks,       # 所有Chunk的分词列表
       tkweight=0.1, vtweight=0.9
   )
   ```
   最终 `sim = 0.1 * 词重合率 + 0.9 * 向量余弦相似度`。

4. **阈值从高往低试探**（第216-231行）：
   ```python
   thr = 0.63
   while thr > 0.3 and len(cites) == 0 and pieces_ and chunks_tks:
       # 遍历所有句子找匹配
       mx = np.max(sim) * 0.99  # 允许略低于最大值的同属Chunk
       if mx >= thr:
           cites[句子i] = [所有sim[ii] > mx的Chunk编号][:4]  # 每个句子最多标4个来源
       thr *= 0.8   # 0.63 → 0.504 → 0.403 → 0.322 → <0.3停止
   ```
   即：先尝试0.63的高阈值找强匹配；如果一个都匹配不上，就降阈值到原来的80%，直到出现匹配或低于0.3放弃。这样保证至少有引用，同时不会因为阈值太松乱标。

5. **插入标记**：
   原回答句子末尾插入 ` ##Chunk编号$$`，Chunk编号去重（用seted集合记录已插入过的）。例如：
   > 该函数的时间复杂度是O(n) ##0$$##1$$，其中n是数组长度。

   前端再把 `##N$$` 替换成脚注样式的链接。

---

### 19. PostgreSQL一共有哪几张表？每张表的主键类型是什么？

**标准回答（init.sql + models/__init__.py）：**

共 **6张表**：

| 表名 | 主键字段 | 主键类型 | 说明 |
|------|---------|---------|------|
| **users** | id | SERIAL（INT自增） | 用户表 |
| **sessions** | session_id | VARCHAR(16) | 会话表 |
| **messages** | message_id | UUID（默认gen_random_uuid()） | 消息表 |
| **knowledgebases** | id | SERIAL（INT自增） | 知识库元数据表 |
| **document_uploads** | id | 待核对（SERIAL/INT） | 文档上传日志表 |
| （待补充） |  |  |  |

**users表字段：**
```
id SERIAL PK
username VARCHAR(50) UNIQUE NOT NULL
password_hash VARCHAR(100) NOT NULL  -- bcrypt哈希
created_at TIMESTAMP DEFAULT NOW()
updated_at TIMESTAMP DEFAULT NOW()
```

**sessions表字段：**
```
session_id VARCHAR(16) PK
session_name VARCHAR(255) NOT NULL
user_id VARCHAR(255) NOT NULL      -- ⚠️ 注意：类型VARCHAR，和users.id（INT）不一致
created_at TIMESTAMP
updated_at TIMESTAMP
索引：idx_sessions_user_id(user_id), idx_sessions_created_at(created_at)
```

**messages表字段：**
```
message_id UUID PK DEFAULT gen_random_uuid()
session_id VARCHAR(16) NOT NULL
user_question TEXT NOT NULL
model_answer TEXT NOT NULL
documents TEXT                      -- 存JSON字符串，实际应是JSONB
recommended_questions TEXT          -- 存JSON字符串
think TEXT                          -- 存JSON字符串 / 思考过程全文
created_at TIMESTAMP
updated_at TIMESTAMP
索引：idx_messages_session_id(session_id), idx_messages_created_at(created_at)
```

**knowledgebases表字段：**
```
id SERIAL PK
user_id VARCHAR(255) NOT NULL
file_name VARCHAR(255) NOT NULL
created_at TIMESTAMP
updated_at TIMESTAMP
索引：idx_knowledgebases_user_id(user_id), idx_knowledgebases_created_at
```

**document_uploads表字段**（from schemas/document_upload.py）：
包含：id, session_id, document_name, document_type, file_size, upload_time 等。

---

### 20. users表的id是SERIAL（INT），但sessions表的user_id是VARCHAR(255)，这会不会有问题？为什么？

**标准回答：**

**会有问题，但不是致命的。** 属于早期代码类型不统一的历史遗留。

**实际代码路径：**
- `auth.py` 中JWT的subject里 `user_id = user.id`（Python int）；
- 但 `chat_rt.py` 第167行 `user_id = str(credentials.subject.get("user_id"))`，**强制转成了字符串**；
- sessions表的user_id也是VARCHAR(255)存字符串；
- knowledgebases表的user_id也是VARCHAR(255)。

**所以问题：**
1. **无外键约束**：users.id（INT）和sessions.user_id（VARCHAR）类型不一致，无法建FOREIGN KEY，删用户时不能级联，可能产生孤儿数据；
2. **查询隐式转型**：如果硬要JOIN，PostgreSQL会做隐式类型转换，索引失效；
3. **ES索引名也用字符串user_id**：`index_name(uid)` 直接把字符串当索引名，逻辑上没问题但不统一。

**为什么会这样？** 因为RAGFlow框架里tenant_id通常是字符串UUID，本项目改造成users.id自增INT时忘了同步改sessions和knowledgebases的字段类型。

**修复方案（面试时说后续补强）：**
- 把sessions.user_id、knowledgebases.user_id、document_uploads.user_id都改成INT；
- 加外键 `sessions.user_id REFERENCES users(id) ON DELETE CASCADE`；
- 已存数据用 `ALTER TABLE ... ALTER COLUMN ... TYPE INT USING user_id::integer` 迁移。

---

### 21. messages表的documents、recommended_questions、think字段是什么类型？为什么不用JSONB？

**标准回答：**

init.sql里定义是 **TEXT类型**，实际存的是JSON字符串（`write_chat_to_db()` 里 `json.dumps(retrieval_content, ensure_ascii=False)`）。

**为什么不用JSONB？** 这是可以优化的点。当前的劣势：
1. 每次读出来都要用 `json.loads()` 反序列化；
2. 无法用PostgreSQL的JSON操作符（`->>`、`@>`）按文档名检索某条消息；
3. 没有JSONB的GIN索引，做结构化查询性能差。

**当前设计唯一的好处**：写入简单，TEXT类型不需要担心JSON格式校验失败。

**实际写入的documents格式（retrieved_content转的JSON）：**
```json
[
  {
    "id": 1,
    "document_id": "doc_xxx",
    "document_name": "2024高数试题.pdf",
    "content_with_weight": "求函数极限..."
  }
]
```

**recommended_questions格式：**
```json
["什么是洛必达法则？", "求极限的方法有哪些？", "等价无穷小替换条件？"]
```

---

### 22. 推荐问题是怎么生成的？用的什么模型？

**标准回答：**

代码在 `chat.py` 的 `generate_recommended_questions()`。

1. **触发时机**：`get_chat_completion()` 中，大模型finish_reason=stop之后、发送end事件之前；
2. **模型**：`qwen2.5-7b-instruct`（比回答模型qwen2.5-72b小很多，省成本）；
3. **Prompt构造**：
   - 如果有检索文档，取最多3个不重复的文档名作为主题提示；
   - 要求生成3个与用户问题相关但角度不同的深挖问题；
   - response_format设置为 `{type: "json_object"}` 强制输出JSON；
4. **输出解析**：
   - 先用正则去掉可能的 ````json ... ```` 代码块包裹；
   - 再 `json.loads()` 解析出 `recommended_questions` 数组；
   - 格式校验必须是非空list，否则返回空数组不报错；
5. **失败兜底**：整个函数外有大try-catch，出错只打log，返回空数组，不影响主流程回答结束。

另外**会话名称生成**（`generate_session_name()`）用的是更大的 **`qwen2.5-72b-instruct`**，因为会话名需要更好的概括能力，而且只在会话第一次提问时调用一次，成本可接受。

---

### 23. 知识库检索时如果第一次结果为空，系统会怎么做？

**标准回答：**

代码在 `search_v2.py` 的 `search()` 函数第117-125行。

**降级重试逻辑**：
```python
total = self.dataStore.getTotal(res)
if total == 0:
    # 1. 降低关键词匹配阈值：min_match从0.3 → 0.1
    matchText, _ = self.qryr.question(qst, min_match=0.1)
    # 2. 移除doc_ids过滤条件（如果之前限定了某些文档）
    filters.pop("doc_ids", None)
    # 3. 降低向量相似度阈值：从请求传入的默认0.1 → 0.17
    matchDense.extra_options["similarity"] = 0.17
    # 4. 用同样的fusion权重，重新查一次ES
    res = self.dataStore.search(src, highlightFields, filters,
                                [matchText, matchDense, fusionExpr], ...)
    total = self.dataStore.getTotal(res)
```

策略总结：
| 项 | 第一次查询 | 重试（空结果时） |
|----|-----------|----------------|
| 关键词min_match | 0.3（至少30%查询词命中） | 0.1（10%命中即可，更宽松） |
| 向量similarity阈值 | 请求传入（默认0.1） | 0.17（放低，允许语义更远的匹配） |
| doc_ids过滤 | 有 | 强制移除 |

两轮都空才返回空。

---

### 24. 什么是available_int字段？为什么要有它？

**标准回答：**

`available_int` 是ES Chunk文档中的**软删除标记字段**（匹配`*_int`模板→integer类型）：
- `available_int = 1` → Chunk可用，会被检索到；
- `available_int = 0` → Chunk已删除/下架，检索时自动过滤。

对应代码（`search_v2.py` 第64行 + retrieval第353行）：
```python
# get_filters中：如果请求传了available_int，就加入过滤条件
condition["available_int"] = req["available_int"]

# retrieval()默认强制传available_int=1：
req = {..., "available_int": 1}
```

**为什么不用物理删除？**
- ES删除文档是打标记+段合并，高并发时成本高；
- 用户删除文档时只要把对应doc_id的所有Chunk available_int置0即可，异步清理；
- 方便误删恢复（改回1即可）。

---

### 25. 为什么同时需要PostgreSQL和Elasticsearch？各自职责是什么？

**标准回答：**

两个存储解决的问题不同，是典型的**业务数据 + 搜索引擎**分层架构：

**PostgreSQL的职责（结构化业务数据 / 唯一可信源）：**
1. 用户账号（users表）：密码哈希、注册信息；
2. 会话和消息记录（sessions、messages）：聊天历史、对话上下文回溯；
3. 知识库元数据（knowledgebases）：用户-文件对应关系、上传时间；
4. 操作日志（document_uploads）：谁什么时候传了什么文档；
5. 强事务、JOIN查询、唯一约束、外键（理论上应该有）。

**Elasticsearch的职责（非结构化检索 / 加速层）：**
1. 存储每个Chunk的分词文本（content_ltks等）→ 支持关键词全文检索；
2. 存储每个Chunk的1024维dense_vector → 支持向量kNN语义检索；
3. 内置scripted_sim相似度 + weighted_sum融合 → 一次请求完成混合检索；
4. 高并发下的全文+向量联合查询性能。

**为什么不把Chunk存在PostgreSQL？**
- PG做全文检索（tsvector）功能较弱，中文分词效果差；
- PG的vector插件（pgvector）虽然能存向量，但1024维高维向量大规模检索性能和ES有差距，且混合检索（文本+向量）ES更成熟。

**数据同步方式**：上传文件时，先写PG的knowledgebases（元数据），再解析写ES（Chunk+向量）。读操作：聊天时检索走ES，落库/查历史走PG。

---

### 26. 引用标注的匹配中，如果遇到代码块（```）怎么处理？

**标准回答：**

`insert_citations()` 函数第167-186行专门处理了代码块：

```python
pieces = re.split(r"(```)", answer)
if len(pieces) >= 3:  # 检测到 ``` 标记
    # 成对合并 ```...``` 作为一个piece
    i = 0
    while i < len(pieces):
        if pieces[i] == "```":
            st = i
            i += 1
            while i < len(pieces) and pieces[i] != "```":
                i += 1
            if i < len(pieces):
                i += 1
            pieces_.append("".join(pieces[st: i]) + "\n")
        else:
            # 非代码部分按正常句子切分
            pieces_.extend(re.split(r"([^\|][；。？!！\n]|[a-z][.?;!][ \n])", pieces[i]))
            i += 1
    pieces = pieces_
```

**处理结果：**
- 代码块被当作一个完整piece，不切句子；
- 在后续句子相似度匹配时，代码块这个piece因为没有明确的自然语言句子结构，要么整体匹配一个Chunk来源，要么匹配不到不加引用；
- 避免了 `int main() { return 0; }` 这种代码被错误切分后乱加引用的问题。

---

### 27. 上传重复文件时系统怎么处理？

**标准回答：**

代码在 `upload_files()` 第229-246行，**前置校验，失败即整批拒绝**：

```python
existing_files = []
for file in files:
    stmt = select(KnowledgeBase).where(
        KnowledgeBase.user_id == user_id,
        KnowledgeBase.file_name == file_name
    )
    existing_file = db.execute(stmt).scalar_one_or_none()
    if existing_file:
        existing_files.append(file_name)

if existing_files:
    raise HTTPException(
        status_code=400,
        detail=f"以下文件已存在，请勿重复上传: {', '.join(existing_files)}"
    )
```

关键点：
1. **判断维度**：同一user_id + 同一file_name → 视为重复（不校验文件内容哈希，所以改文件名就能绕过）；
2. **校验时机**：任何文件保存/解析前就查完；
3. **处理粒度**：只要有一个文件重复，**所有文件都不处理**，直接抛400。用户需要把重复文件从列表里删掉才能继续；
4. **只对知识库上传有效**：`/quick_parse` 快速解析不做重复校验（因为它是临时的，存Redis不写knowledgebases表）。

---

### 28. sessions表的session_id是怎么生成的？为什么是16位？

**标准回答：**

代码在 `create_session()` 接口第47行：
```python
session_id = str(uuid.uuid4()).replace("-", "")[:16]
```

步骤：
1. `uuid.uuid4()` → 生成标准36位UUID：`a83f91c2-d4e5-4b60-7a12-8c9d0e1f2a3b`；
2. `.replace("-", "")` → 去横杠变成32位十六进制：`a83f91c2d4e54b607a128c9d0e1f2a3b`；
3. `[:16]` → 取前16位：`a83f91c2d4e54b60`。

**为什么16位？**
- 16位十六进制 = 64bit随机空间 ≈ 1.8e19种，碰撞概率极低（同一用户量下完全足够）；
- 在URL里作为Query参数不会太长；
- 数据库存VARCHAR(16)也省空间。

**潜在风险**：截断了UUID的版本位和变体位，破坏了UUID的标准性，但这里只做唯一标识无所谓。

---

### 29. JWT的secret_key是怎么配置的？为什么加了一个'happy'后缀？

**标准回答：**

`service/auth.py` 第13行：
```python
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'default_secret_key') + 'happy'
```

逻辑：
1. 优先从环境变量 `JWT_SECRET_KEY` 取（部署时应该在.env里配置强随机字符串）；
2. 没设置时用默认值 `'default_secret_key'`（开发用，生产绝对不能用这个）；
3. **无论取到什么，最后都拼接固定字符串 `'happy'`**。

**为什么加 `'happy'`？** 这是代码作者留的一个**轻量级"盐值"**，作用：
- 如果运维忘了设JWT_SECRET_KEY，至少不会用裸的 `'default_secret_key'`，稍微增加一点暴力破解难度；
- 但本质上不是好做法——如果环境变量已经是强随机密钥，拼接固定后缀没意义；如果环境变量泄露了，加固定字符串等于没加。

**正确做法（面试时说后续优化）：** 去掉硬编码后缀，强制从env读取密钥，启动时校验必须非默认值。

---

### 30. 大模型用的是什么？回答和思考过程怎么区分？

**标准回答：**

| 功能 | 模型 | 调用方式 | 说明 |
|------|------|---------|------|
| 主要对话回答 | `deepseek-r1`（通过DashScope兼容API） | stream=True | 支持reasoning_content思考过程 |
| 推荐问题生成 | `qwen2.5-7b-instruct` | stream=False, response_format=json_object | 小模型，低成本 |
| 会话名称生成 | `qwen2.5-72b-instruct` | stream=False, response_format=json_object | 大模型，概括能力强 |
| Embedding | DashScope `text-embedding-v3` | 同步接口 | 输出1024维向量 |
| Rerank | DashScope rerank接口（`rerank_similarity`） | 同步接口 | 句子对相似度 |

调用方式统一用OpenAI SDK（因为DashScope提供兼容端点）：
```python
client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("DASHSCOPE_BASE_URL")
)
```

**回答 vs 思考过程的区分**（SSE流式处理代码第446-466行）：
```python
delta = chunk.choices[0].delta
if delta.content:
    # delta有content字段 → 正式回答的一部分
    message = {role:"assistant", content: delta.content, thinking: False}
elif delta.reasoning_content:
    # delta有reasoning_content字段 → <thinking>标签里的思考链
    message = {role:"assistant", content: delta.reasoning_content, thinking: True}
```

前端拿到后：
- `thinking:false` → 黑色/正常字体显示到回答区；
- `thinking:true` → 灰色斜体或折叠面板展示思考过程（可让用户选择是否显示）。

---

### 31. 为什么选择PostgreSQL而不是MySQL？

**标准回答（基于实际代码痕迹的推断 + 合理理由）：**

项目init.sql里用到了PostgreSQL特有语法，这是直接原因：
1. `CREATE EXTENSION IF NOT EXISTS pgcrypto;` → 启用pgcrypto扩展，`gen_random_uuid()` 函数生成UUID主键（MySQL 8.0也有UUID函数，但pgcrypto是PG传统写法）；
2. SERIAL类型（PG的自增，对应MySQL AUTO_INCREMENT）；
3. 后续如果documents字段改JSONB，PG的JSON支持比MySQL的JSON更成熟（更多操作符、GIN索引性能更好）。

更深层原因：
- 开发者更熟悉PG；
- PG对全文检索、向量扩展（pgvector）生态好，将来如果不用ES可以平滑切到PG原生向量；
- PG的事务隔离级别（默认MVCC）和复杂查询支持更好。

---

### 32. sessions表的session_name什么时候生成？怎么保证只生成一次？

**标准回答：**

生成时机：**用户第一个问题回答完毕后，流式结束的同步阶段**（不是用户点创建会话时就生成，因为那时还不知道会话主题）。

代码在 `update_session_name()`：
```python
# 先查sessions表是否存在
query_result = db.execute(
    SELECT session_name FROM sessions WHERE session_id = :session_id
).fetchone()

if query_result:
    logger.info(f"Session {session_id} already exists, skipping.")
    return   # ✅ 已存在，直接跳过，不重复生成

# 不存在才生成+插入
if question:
    session_name = generate_session_name(question)  # 调qwen2.5-72b
    INSERT INTO sessions (session_id, user_id, session_name) VALUES ...
```

**为什么不是创建时生成？** 创建会话时只有session_id，用户还没说话，不知道会聊什么主题，生成的名字会是"新会话1"这种无意义的。所以等第一个问题问出来后，用第一个问题去生成概括性的会话名。

**幂等保证**：先SELECT再INSERT，虽然有极小并发竞态，但用户不会在同一毫秒内发两个首问，实际没问题。要绝对保证可以给session_id加唯一索引（已经是主键了，天然唯一），并发时插入失败catch住即可。

---

### 33. 项目中哪些地方做了异常处理？举几个例子。

**标准回答：**

后端大部分函数都是"**核心逻辑try-catch，外层HTTPException统一抛出**"的模式。举5个典型场景：

**例1：JWT校验失败（框架级）**
`access_security = JwtAccessBearerCookie(secret_key, auto_error=True)` → 自动抛401。

**例2：知识库检索失败不影响问答（降级）**
```python
try:
    references = retrieve_content(user_id, question)
except Exception as e:
    logger.info(f"检索失败: {e}，不使用知识库内容")
    references = []   # 降级为纯问答，不报错给用户
```

**例3：推荐问题生成失败不影响主流程**
`generate_recommended_questions()` 外层大try-catch，出错返回 `[]`，log.error但不抛异常。主回答流已经结束了，推荐问题是锦上添花。

**例4：保存文档上传记录失败（数据库错误）不影响返回**
`/quick_parse` 接口中，记录document_uploads表的代码独立try-catch，失败只logger.error。**文档解析已经成功返回给用户了，日志记录是次要的。**

**例5：文件逐文件独立处理，部分失败不影响其他**
`/upload_files` 中每个文件独立try，最终返回 `{successful_files, failed_files}` 明细，用户知道哪些成功哪些失败，可以重传失败的。

---

### 34. 如果快速解析的内容很长（超过4000字符），系统怎么处理？

**标准回答：**

在组装Prompt时（`get_chat_completion()` 第312-315行）有两处截断：

**第一处：给模型看的Prompt部分**
```python
max_quick_content_length = 4000
truncated_content = quick_parse_content[:max_quick_content_length]
if len(quick_parse_content) > max_quick_content_length:
    truncated_content += "...(内容已截断)"
```
→ 拼进Prompt时只取前4000字符，避免上下文窗口溢出。

**第二处：给前端展示的参考文档部分**（第370-388行）
```python
max_chunk_length = 2000
if len(quick_parse_content) <= max_chunk_length:
    content_chunks = [quick_parse_content]
else:
    # 按段落切成≤2000字符的段
    for paragraph in paragraphs:
        if len(current_chunk + paragraph) <= max_chunk_length:
            ...
```
→ 参考文档列表中，快速解析被拆成最多2000字一段的若干个"伪Chunk"，前端展示的引用卡片不会太长。

---

### 35. 引用标注insert_citations里，chunks_v和ans_v维度不匹配怎么办？

**标准回答：**

代码第205-211行专门处理了Embedding模型升级导致维度不一致的情况（防御性编程）：
```python
for i in range(len(chunk_v)):
    if len(ans_v[0]) != len(chunk_v[i]):
        chunk_v[i] = [0.0]*len(ans_v[0])  # 把旧Chunk向量强行清零成新维度
        logging.warning("维度不匹配: {} vs {}".format(len(ans_v[0]), len(chunk_v[i])))

assert len(ans_v[0]) == len(chunk_v[0])
```

处理方式：
1. 逐Chunk检查维度；
2. 维度不一致的Chunk向量全部置为0向量（长度=当前回答句子向量维度）；
3. 打warning日志；
4. 最后用assert保证维度一致，程序继续。

**影响**：旧Chunk的余弦相似度会变成0（因为全是0向量），词相似度仍然能匹配。这是个降级方案，**正确做法**应该是在模型切换时触发全量Chunk重新Embedding。

---

## 五、面试官最终反馈（模拟）

面试官指出，本项目的核心考察点不是是否了解RAG的概念，而是：

1. **能否把"用户提问→答案"的每一步数据格式讲清楚**：SSE每个事件的JSON、ES每个字段的类型、messages表documents里存的结构；
2. **能否解释清楚每一个"超参数"为什么这么取**：混合检索权重0.05/0.95、重排权重0.4/0.6、引用阈值从0.63降0.3、重排只做前3页、向量维度1024、JWT 2天TTL；
3. **能否区分"实际实现了的"和"降级/容错路径"**：比如知识库检索失败怎么办、ES首查为空怎么retry、推荐问题生成失败怎么办、Embedding维度不匹配怎么办；
4. **能否说出代码中明显可以改进的地方**：user_id类型不一致、documents字段应该用JSONB、Redis Key无前缀、JWT密钥硬编码'happy'、重复文件只查名字不验内容哈希。

如果只能说"用了FastAPI + ES + RAG + SSE"而答不出上面的细节，面试官会合理怀疑项目是不是自己写的、还是从RAGFlow拉下来改了个UI没看内核代码。

---

## 六、本场面试暴露出的核心问题

1. **数字记不住**：权重0.05/0.95、0.4/0.6、阈值0.63/0.3×0.8、1024维、page_size=5、TTL=2h、JWT 2天…这些从代码里来的硬数字要背下来，不能说"大概"。
2. **链路拆不开**：文档上传的两条路径（知识库 vs 快速解析）经常混着说。要先讲"有两条文档链路，分别是…，它们的区别是…，最后在问答时会被同时组装到Prompt"。
3. **字段分不清**：content_ltks vs content_with_weight vs q_1024_vec，title_tks vs question_tks vs important_kwd，各自是什么类型、谁参与索引、谁只存不取。
4. **降级路径说不出来**：面试官喜欢问"XX失败了怎么办"。项目里大量try-catch + 降级逻辑，这是加分项，要主动提。
5. **已知缺陷藏着不说**：user_id类型不一致这种明摆着的问题，主动承认+说修复方案，比被面试官指出来强得多，说明你真的读了代码。

---

## 七、下一轮面试前优先补强清单

### 第一优先级：硬数字背熟表

| 项 | 真实值 | 来源 |
|----|--------|------|
| 混合检索ES融合权重（关键词:向量） | **0.05 : 0.95** | search_v2.py L111 |
| retrieval调重排权重（关键词:向量） | **0.4 : 0.6** | retrieval.py L20 + search_v2.py L371 |
| 引用注入句子-Chunk权重（词:向量） | **0.1 : 0.9** | search_v2.py L163 |
| 引用匹配起始阈值 / 终止阈值 | **0.63 / 0.3**，每次×0.8 | search_v2.py L216-231 |
| 每句最多引用Chunk数 | **4** | search_v2.py L230 |
| 重排只对前几页生效 | **前3页（RERANK_PAGE_LIMIT=3）** | search_v2.py L349 |
| 重排候选size | page_size×3和128取max（即**至少128条**） | search_v2.py L350 |
| 最终返回Top-K Chunk给Prompt | **5** | retrieval.py L22 |
| Embedding维度 | **1024**（DashScope text-embedding-v3） | mapping.json + Dealer.get_vector |
| 向量相似度函数 | **cosine余弦** | mapping.json |
| 快速解析Redis TTL | **2小时（7200秒）** | quick_parse_service.py |
| JWT有效期 | **2天** | auth.py L19 |
| JWT salting长度 | **secrets.token_hex(16) = 32个hex字符** | auth.py L27 |
| session_id长度 | **UUID去掉横杠取前16** | chat_rt.py L47 |
| 推荐问题生成个数 | **3** | chat.py的prompt |
| 快速解析内容Prompt截断长度 | **4000字符** | chat.py L312 |
| 快速解析参考文档分块上限 | **2000字符/块** | chat.py L370 |
| ES首查min_match / 重试min_match | **0.3 / 0.1** | search_v2.py L100, L119 |
| 向量首查相似度 / 重试相似度 | **默认0.1 / 0.17** | search_v2.py L108, L121 |
| title/important_kwd/question_tks 重排加权倍数 | **×2 / ×5 / ×6** | search_v2.py L301 |
| rerank特征Pagerank权重倍数 | **×10** | retrieval.py L346 rank_feature默认值 |

### 第二优先级：链路自己画一遍

拿一张白纸，从左到右画：
```
[浏览器]
   ↓ login (username/pw)
[FastAPI /auth] → bcrypt查PG users表 → JWT(user_id, name, salting)
   ↓ create_session
[uuid4前16位] → session_id返回
   ↓ upload_files
[本地存文件] → execute_insert_process → RAG切Chunk(128T)
                            ↓ Embedding(1024d)
                            ↓ 写ES索引名=user_id字符串
         knowledgebases表插入元数据 ←┘
   ↓ quick_parse
[Redis SET session_id 文档原文 EX 7200] + document_uploads记日志
   ↓ chat_on_docs
[JWT解析user_id]
   → retrieve_content(user_id, question)
     → ES hybrid(0.05KW+0.95VEC) top1024
       → (空则降级重试)
     → rerank_by_model(0.4KW+0.6VEC + tag_fea + pagerank×10)
       → 只重排前3页，取Top5 chunks
   → Redis GET session_id 快速解析(截断4000)
   → 组装prompt（引用标注要求）
   → deepseek-r1 streaming
     SSE: [documents] → [thinking/answer tokens流] → [recommended_questions] → [DONE]
   → 落库 messages（json.dumps documents/rq/think）
   → 首次落库 sessions（调72B生成session名）
```

### 第三优先级：准备"缺陷+修复方案"清单

主动说能显示你对代码的掌控力：
1. **sessions.user_id类型VARCHAR vs users.id INT** → 迁移成INT + 加外键ON DELETE CASCADE；
2. **messages表3个JSON字段存TEXT** → ALTER COLUMN ... TYPE JSONB USING column::jsonb，加GIN索引；
3. **Redis Key无前缀** → `quick_parse:{session_id}` 前缀；
4. **JWT secret_key硬编码拼接happy** → 去掉 + 启动校验env非空；
5. **重复文件判断只看名字** → 加content_hash字段，上传算SHA256比较；
6. **首查空才降级min_match** → 可以引入多路召回并行(0.1/0.3/0.5)取并集；
7. **ES索引名=user_id字符串** → 加前缀`chunk_{tenant_id}` 避免和其他类型索引混。

---

## 八、本场面试的核心结论

这个项目作为RAG面试项目**工程细节非常扎实**（因为底层用了RAGFlow的成熟检索代码），关键不是背诵"什么是RAG"，而是：

1. **从代码中把所有硬数字抄下来背熟**；
2. **把每条接口的输入、中间转换、输出的数据格式（字段名+类型）搞清楚**；
3. **准备降级/异常处理的具体场景**；
4. **主动承认可以改进的点，并给出修复思路**。

如果能做到这四点，面试官追问任何细节都能给到和代码一致的答案，就能证明项目是自己真正吃透了的，而不是只改了UI换了API Key。

