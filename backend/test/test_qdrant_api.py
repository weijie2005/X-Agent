#!/usr/bin/env python3
"""
测试 Qdrant API
"""
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
import uuid

# 连接 Qdrant
client = QdrantClient(host="localhost", port=6333)

print("Qdrant Client Methods:")
print([m for m in dir(client) if not m.startswith('_')])

# 测试创建集合
print("\n=== 测试创建集合 ===")
try:
    client.create_collection(
        collection_name="test_api",
        vectors_config=VectorParams(
            size=1024,
            distance=Distance.COSINE
        )
    )
    print("✓ 创建集合成功")
except Exception as e:
    print(f"✗ 创建集合失败: {e}")

# 测试插入向量
print("\n=== 测试插入向量 ===")
try:
    # 创建测试向量
    vector = [0.1] * 1024
    
    point = PointStruct(
        id=str(uuid.uuid4()),
        vector=vector,
        payload={"test": "data"}
    )
    
    client.upsert(
        collection_name="test_api",
        points=[point]
    )
    print("✓ 插入向量成功")
except Exception as e:
    print(f"✗ 插入向量失败: {e}")

# 测试搜索向量
print("\n=== 测试搜索向量 ===")
try:
    query_vector = [0.1] * 1024
    
    # 尝试不同的搜索方法
    print("\n尝试 search 方法:")
    try:
        results = client.search(
            collection_name="test_api",
            query_vector=query_vector,
            limit=5
        )
        print(f"✓ search 成功: {len(results)} 个结果")
    except AttributeError as e:
        print(f"✗ search 失败: {e}")
    
    print("\n尝试 query_points 方法:")
    try:
        results = client.query_points(
            collection_name="test_api",
            query=query_vector,
            limit=5
        )
        print(f"✓ query_points 成功: {len(results.points)} 个结果")
    except AttributeError as e:
        print(f"✗ query_points 失败: {e}")
    
except Exception as e:
    print(f"✗ 搜索向量失败: {e}")

# 清理
print("\n=== 清理 ===")
try:
    client.delete_collection("test_api")
    print("✓ 删除集合成功")
except Exception as e:
    print(f"✗ 删除集合失败: {e}")

print("\nDone!")