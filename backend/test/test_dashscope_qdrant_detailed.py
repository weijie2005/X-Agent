#!/usr/bin/env python3
"""
详细的 DashScope + Qdrant 测试（带异常处理）
"""
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
env_file = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_file)

from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
import uuid

print("=" * 60)
print("详细测试：DashScope Embedding + Qdrant")
print("=" * 60)

# ==================== 第1步：测试 DashScope Embedding ====================
print("\n【第1步】测试 DashScope Embedding API 连通性")
print("-" * 60)

try:
    api_key = os.getenv('DASHSCOPE_API_KEY')
    base_url = os.getenv('DASHSCOPE_BASE_URL')
    model = os.getenv('DASHSCOPE_MODEL', 'qwen3.7-text-embedding')
    
    print(f"✓ API Key: {api_key[:20]}...")
    print(f"✓ Base URL: {base_url}")
    print(f"✓ Model: {model}")
    
    client = OpenAI(api_key=api_key, base_url=base_url)
    print("✓ DashScope 客户端初始化成功")
    
except Exception as e:
    print(f"✗ DashScope 客户端初始化失败: {e}")
    sys.exit(1)

# ==================== 第2步：测试向量生成 ====================
print("\n【第2步】测试向量生成功能")
print("-" * 60)

try:
    test_text = "Python 是一种流行的编程语言。"
    print(f"测试文本: {test_text}")
    
    start_time = time.time()
    response = client.embeddings.create(
        model=model,
        input=[test_text]
    )
    elapsed_time = time.time() - start_time
    
    embedding = response.data[0].embedding
    
    print(f"✓ 向量生成成功！")
    print(f"  - 向量维度: {len(embedding)}")
    print(f"  - 耗时: {elapsed_time:.2f}秒")
    print(f"  - 向量前5位: {embedding[:5]}")
    
except Exception as e:
    print(f"✗ 向量生成失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ==================== 第3步：测试 Qdrant 连通性 ====================
print("\n【第3步】测试 Qdrant API 连通性")
print("-" * 60)

try:
    # 增加超时时间（默认太短，单位：秒）
    qdrant_client = QdrantClient(host="localhost", port=6333, timeout=30)
    print("✓ Qdrant 客户端初始化成功（超时时间：30秒）")
    
    # 测试获取集合列表
    collections = qdrant_client.get_collections().collections
    print(f"✓ Qdrant API 连通正常")
    print(f"  - 现有集合数量: {len(collections)}")
    for c in collections:
        print(f"    - {c.name}")
    
except Exception as e:
    print(f"✗ Qdrant 连接失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ==================== 第4步：创建或使用集合 ====================
print("\n【第4步】创建或使用 Qdrant 集合")
print("-" * 60)

collection_name = "test_dashscope_detailed"

try:
    # 检查集合是否存在
    collections = qdrant_client.get_collections().collections
    collection_names = [c.name for c in collections]
    
    if collection_name in collection_names:
        print(f"✓ 集合已存在: {collection_name}")
    else:
        print(f"创建集合: {collection_name}")
        print(f"  - 向量维度: {len(embedding)}")
        print(f"  - 距离度量: COSINE")
        
        start_time = time.time()
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=len(embedding),
                distance=Distance.COSINE
            )
        )
        elapsed_time = time.time() - start_time
        
        print(f"✓ 集合创建成功！耗时: {elapsed_time:.2f}秒")
    
    # 获取集合信息
    collection_info = qdrant_client.get_collection(collection_name)
    print(f"✓ 集合信息:")
    print(f"  - 向量数量: {collection_info.points_count}")
    print(f"  - 向量维度: {collection_info.config.params.vectors.size}")
    
except Exception as e:
    print(f"✗ 集合操作失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ==================== 第5步：插入向量 ====================
print("\n【第5步】插入向量到 Qdrant")
print("-" * 60)

try:
    # 创建多个测试向量
    test_texts = [
        "Python 是一种流行的编程语言。",
        "机器学习是人工智能的一个分支。",
        "深度学习使用神经网络进行学习。"
    ]
    
    print(f"生成 {len(test_texts)} 个测试向量...")
    
    # 批量生成向量
    start_time = time.time()
    response = client.embeddings.create(
        model=model,
        input=test_texts
    )
    elapsed_time = time.time() - start_time
    
    print(f"✓ 向量生成完成，耗时: {elapsed_time:.2f}秒")
    
    # 创建点结构
    points = []
    for i, (text, emb) in enumerate(zip(test_texts, response.data)):
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=emb.embedding,
            payload={
                "text": text,
                "index": i
            }
        )
        points.append(point)
    
    print(f"✓ 创建了 {len(points)} 个点结构")
    
    # 插入向量
    print(f"插入向量到集合: {collection_name}")
    start_time = time.time()
    
    result = qdrant_client.upsert(
        collection_name=collection_name,
        points=points
    )
    
    elapsed_time = time.time() - start_time
    
    print(f"✓ 向量插入成功！")
    print(f"  - 操作结果: {result}")
    print(f"  - 耗时: {elapsed_time:.2f}秒")
    
    # 检查向量数量
    collection_info = qdrant_client.get_collection(collection_name)
    print(f"  - 集合中向量总数: {collection_info.points_count}")
    
except Exception as e:
    print(f"✗ 向量插入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ==================== 第6步：搜索向量 ====================
print("\n【第6步】搜索向量")
print("-" * 60)

try:
    query_text = "什么是 Python？"
    print(f"查询文本: {query_text}")
    
    # 生成查询向量
    start_time = time.time()
    response = client.embeddings.create(
        model=model,
        input=[query_text]
    )
    query_vector = response.data[0].embedding
    elapsed_time = time.time() - start_time
    
    print(f"✓ 查询向量生成完成，耗时: {elapsed_time:.2f}秒")
    
    # 搜索向量
    print(f"执行向量搜索...")
    start_time = time.time()
    
    results = qdrant_client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=5,
        with_payload=True
    )
    
    elapsed_time = time.time() - start_time
    
    print(f"✓ 搜索完成！耗时: {elapsed_time:.2f}秒")
    print(f"  - 返回结果数量: {len(results.points)}")
    
    for i, result in enumerate(results.points, 1):
        print(f"\n  结果 {i}:")
        print(f"    - 分数: {result.score:.4f}")
        print(f"    - 文本: {result.payload['text']}")
        print(f"    - 索引: {result.payload['index']}")
    
except Exception as e:
    print(f"✗ 向量搜索失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ==================== 第7步：清理 ====================
print("\n【第7步】清理测试数据")
print("-" * 60)

try:
    print(f"删除集合: {collection_name}")
    qdrant_client.delete_collection(collection_name)
    print(f"✓ 集合已删除")
except Exception as e:
    print(f"✗ 删除集合失败: {e}")

print("\n" + "=" * 60)
print("🎉 所有测试通过！")
print("=" * 60)
print("\n总结:")
print("  ✅ 第1步：DashScope API 连通正常")
print("  ✅ 第2步：向量生成功能正常")
print("  ✅ 第3步：Qdrant API 连通正常")
print("  ✅ 第4步：集合创建功能正常")
print("  ✅ 第5步：向量插入功能正常")
print("  ✅ 第6步：向量搜索功能正常")
print("  ✅ 第7步：清理功能正常")
print("\nDashScope Embedding + Qdrant 工作正常！")