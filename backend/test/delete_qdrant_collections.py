#!/usr/bin/env python3
"""
删除 Qdrant 集合

用于清理旧的集合，以便重新创建。
"""
import sys
import os
from pathlib import Path

# 获取当前脚本的绝对路径
script_path = os.path.abspath(__file__)
current_directory = os.path.dirname(script_path)
backend_dir = Path(current_directory).parent  # backend 目录

# 添加项目路径到 Python 路径
sys.path.insert(0, str(backend_dir))

from qdrant_client import QdrantClient
from app.config import get_settings

settings = get_settings()

client = QdrantClient(
    host=settings.QDRANT_HOST,
    port=settings.QDRANT_PORT
)

# 删除测试集合
for collection_name in ["test_collection", "test_workflow", "rag_knowledge_base"]:
    try:
        client.delete_collection(collection_name)
        print(f"✓ Deleted collection: {collection_name}")
    except Exception as e:
        print(f"⚠️  Failed to delete {collection_name}: {e}")

print("\nDone!")