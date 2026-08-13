#!/usr/bin/env python3
"""
Alembic 迁移运行脚本
- 首次部署时自动标记 baseline (980b32f130df)
- 然后运行 upgrade head
- 任何异常都不退出，保证应用能继续启动（向下兼容）
"""

import os
import sys
from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, text


BASELINE_REVISION = "980b32f130df"


def ensure_baseline(alembic_cfg):
    """如果 alembic_version 表不存在，则标记 baseline。"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("[migration] 未找到 DATABASE_URL 环境变量，跳过迁移。")
        return False

    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'alembic_version')")
            )
            table_exists = result.scalar()

        if not table_exists:
            print("[migration] 首次部署，标记 baseline...")
            command.stamp(alembic_cfg, BASELINE_REVISION)
            print("[migration] Baseline 标记完成 ({})".format(BASELINE_REVISION))
        else:
            print("[migration] alembic_version 表已存在，跳过 baseline 标记。")
        return True
    except Exception as e:
        print("[migration] 检查/标记 baseline 失败: {}".format(e))
        return False


def run_migration():
    """运行数据库迁移（包含 baseline 检查）。"""
    try:
        alembic_cfg = Config("alembic.ini")
    except Exception as e:
        print("[migration] 加载 alembic.ini 失败: {}".format(e))
        print("[migration] 警告: 迁移失败，但应用将继续启动")
        return

    if not ensure_baseline(alembic_cfg):
        print("[migration] 警告: 迁移失败，但应用将继续启动")
        return

    try:
        print("[migration] 运行数据库迁移 (upgrade head)...")
        command.upgrade(alembic_cfg, "head")
        print("[migration] 数据库迁移完成!")
    except Exception as e:
        print("[migration] 迁移过程出错: {}".format(e))
        print("[migration] 警告: 迁移失败，但应用将继续启动")


if __name__ == "__main__":
    run_migration()
