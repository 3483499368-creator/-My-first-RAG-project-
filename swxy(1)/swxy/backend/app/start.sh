#!/bin/bash

echo "=== 应用启动脚本 ==="

# 等待数据库就绪
echo "等待数据库连接..."
python -c "
import time
import os
import psycopg2
from psycopg2 import OperationalError

max_retries = 30
retry_count = 0

while retry_count < max_retries:
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        conn.close()
        print('数据库连接成功!')
        break
    except OperationalError:
        retry_count += 1
        print(f'等待数据库... ({retry_count}/{max_retries})')
        time.sleep(2)
else:
    print('数据库连接失败!')
    exit(1)
"

# 清理 Python 缓存（每次启动都清理，避免卷挂载导致的 .pyc 不同步问题）
echo "清理 Python 缓存..."
find /app -name '__pycache__' -exec rm -rf {} + 2>/dev/null
find /app -name '*.pyc' -delete 2>/dev/null
echo "缓存清理完成."

# 检查并运行数据库迁移（调用独立的 Python 脚本，避免 bash 内嵌 python 换行符问题）
echo "检查数据库迁移状态..."
python run_migration.py

echo "启动应用服务..."
exec "$@"
