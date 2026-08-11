#!/usr/bin/env python3
"""检查向量库中的数据"""
import sys
sys.path.insert(0, '/home/s8066/agent-project/backend')

from qdrant_client import QdrantClient
from app.config import get_settings

settings = get_settings()

# 连接Qdrant
client = QdrantClient(
    host=settings.QDRANT_HOST,
    port=settings.QDRANT_PORT
)

collection_name = "kb_c8e09d410e20"

print(f"检查集合: {collection_name}")
print("=" * 60)

try:
    # 获取集合信息
    collection_info = client.get_collection(collection_name)
    print(f"集合状态: {collection_info.status}")
    print(f"向量数量: {collection_info.points_count}")
    print(f"向量维度: {collection_info.config.params.vectors.size}")
    print()
    
    # 滚动获取所有点
    print("检索向量数据:")
    points, _ = client.scroll(
        collection_name=collection_name,
        limit=10,
        with_payload=True,
        with_vectors=False
    )
    
    for i, point in enumerate(points, 1):
        print(f"\n--- Point {i} ---")
        print(f"ID: {point.id}")
        print(f"Payload: {point.payload}")
        if 'text' in point.payload:
            print(f"文本内容: {point.payload['text'][:200]}...")
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()