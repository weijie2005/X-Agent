#!/usr/bin/env python3
"""详细测试检索过程"""
import sys
sys.path.insert(0, '/home/s8066/agent-project/backend')

from app.agent.rag.hybrid_retriever import HybridRetriever
from app.config import get_settings

settings = get_settings()

collection_name = "kb_c8e09d410e20"
query = "Python有哪些主要特点？"

print(f"测试检索过程")
print("=" * 60)
print(f"Collection: {collection_name}")
print(f"Query: {query}")
print()

try:
    # 创建混合检索器
    retriever = HybridRetriever(collection_name=collection_name)
    
    print("执行检索...")
    results = retriever.retrieve(query, limit=5)
    
    print(f"检索结果数量: {len(results)}")
    print()
    
    for i, result in enumerate(results, 1):
        print(f"--- Result {i} ---")
        print(f"Chunk ID: {result.get('chunk_id')}")
        print(f"Score: {result.get('score')}")
        print(f"Combined Score: {result.get('combined_score')}")
        print(f"Content: {result.get('content', '')[:200]}...")
        print()
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()