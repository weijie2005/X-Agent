#!/usr/bin/env python3
"""测试成绩查询的检索"""
import sys
sys.path.insert(0, '/home/s8066/agent-project/backend')

from app.agent.rag.agentic_rag import AgenticRAG

collection_name = "kb_c8e09d410e20"
query = "查询一下我的成绩"

print(f"测试成绩查询检索")
print("=" * 60)
print(f"Query: {query}")
print()

rag = AgenticRAG(collection_name=collection_name)

# 判断是否需要检索
should_retrieve = rag.should_retrieve(query)
print(f"是否需要检索: {should_retrieve}")
print()

if should_retrieve:
    # 执行检索
    result = rag.retrieve(query)
    
    print(f"检索结果数量: {len(result.get('results', []))}")
    print()
    
    if result.get('results'):
        print("检索到的内容:")
        for i, chunk in enumerate(result['results'][:3], 1):
            print(f"\n--- Chunk {i} ---")
            print(f"内容: {chunk.get('content', '')[:200]}...")
            print(f"分数: {chunk.get('combined_score', chunk.get('score', 0))}")
    else:
        print("没有检索到结果")
else:
    print("判断不需要检索")