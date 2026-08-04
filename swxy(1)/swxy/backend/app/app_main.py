from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from router import chat_rt
from router import user_rt
from router import history_rt
# ============= 强制使用本地 NLTK 数据 =============
import os
import nltk

# 1. 设置环境变量，告诉 NLTK 数据目录
os.environ['NLTK_DATA'] = '/usr/local/nltk_data'

# 2. 手动添加路径到搜索列表最前面
nltk.data.path.insert(0, '/usr/local/nltk_data')

# 3. 禁用 NLTK 的自动下载器（防止任何网络请求）
nltk.downloader._DOWNLOADERS = {}  # 清空下载器

# 4. 尝试加载 wordnet，如果失败则打印错误但不触发下载
try:
    from nltk.corpus import wordnet
    # 测试加载是否成功
    wordnet.synsets('test')
    print("✅ wordnet 加载成功")
except LookupError as e:
    print(f"❌ wordnet 加载失败 (LookupError): {e}")
except Exception as e:
    print(f"❌ wordnet 加载失败: {e}")
# ==================================================

# 从环境变量获取 root_path
root_path = os.getenv("ROOT_PATH", "http://localhost:8000")

app = FastAPI(root_path=root_path)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源，生产环境中应该设置具体的源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)

app.include_router(chat_rt.router)
app.include_router(user_rt.router)
app.include_router(history_rt.router)

if __name__=='__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    