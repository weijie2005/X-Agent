#!/usr/bin/env python3
"""测试知识库检索功能"""
import sys
sys.path.insert(0, '/home/s8066/agent-project/backend')

from app.agent.rag.agentic_rag import AgenticRAG

# 测试检索
kb_id = "f2e8a382-037c-4483-a37f-81a0b2adde1d"
collection_name = "kb_c8e09d410e20"

print(f"测试知识库检索: {collection_name}")
print("=" * 60)

rag = AgenticRAG(collection_name=collection_name)

query = "Python有哪些主要特点？"
print(f"查询: {query}")
print()

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