#!/usr/bin/env python3
"""直接测试CRAG的retrieve_with_validation"""
import sys
sys.path.insert(0, '/home/s8066/agent-project/backend')

from app.agent.rag.crag_system import CRAGSystem

collection_name = "kb_c8e09d410e20"
query = "查询一下我的成绩"

print("直接测试CRAG的retrieve_with_validation")
print("=" * 60)
print(f"Query: {query}")
print()

crag = CRAGSystem(collection_name=collection_name)

# 使用默认阈值（0.2）
results, stats = crag.retrieve_with_validation(query, limit=5)

print(f"检索结果数量: {len(results)}")
print(f"统计信息: {stats}")
print()

if results:
    print("检索到的内容:")
    for i, result in enumerate(results[:3], 1):
        score = result.get('combined_score', result.get('score', 0))
        content = result.get('content', '')[:150]
        print(f"\n--- Result {i} ---")
        print(f"分数: {score:.4f}")
        print(f"内容: {content}...")
else:
    print("没有检索到结果")