#!/usr/bin/env python3
"""测试降低阈值后的检索"""
import sys
sys.path.insert(0, '/home/s8066/agent-project/backend')

from app.agent.rag.crag_system import CRAGSystem

collection_name = "kb_c8e09d410e20"
query = "Python有哪些主要特点？"

print(f"测试CRAG检索（降低阈值）")
print("=" * 60)
print(f"Collection: {collection_name}")
print(f"Query: {query}")
print()

try:
    crag = CRAGSystem(collection_name=collection_name)
    
    print("执行检索（阈值=0.3）...")
    results, stats = crag.retrieve_with_validation(
        query,
        limit=5,
        score_threshold=0.3  # 降低阈值
    )
    
    print(f"检索结果数量: {len(results)}")
    print(f"统计信息: {stats}")
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