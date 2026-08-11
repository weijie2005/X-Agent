#!/usr/bin/env python3
"""测试不同查询的检索效果"""
import sys
sys.path.insert(0, '/home/s8066/agent-project/backend')

from app.agent.rag.agentic_rag import AgenticRAG

collection_name = "kb_c8e09d410e20"

queries = [
    "查询一下我的成绩",
    "我的成绩如何",
    "学生成绩表",
    "大学成绩",
    "课程成绩",
    "高等数学成绩",
    "Python成绩"
]

rag = AgenticRAG(collection_name=collection_name)

print("测试不同查询的检索效果")
print("=" * 60)

for query in queries:
    print(f"\n查询: {query}")
    print("-" * 40)
    
    result = rag.retrieve(query)
    
    print(f"检索结果数量: {len(result.get('results', []))}")
    
    if result.get('results'):
        for i, chunk in enumerate(result['results'][:2], 1):
            score = chunk.get('combined_score', chunk.get('score', 0))
            content = chunk.get('content', '')[:100]
            print(f"  结果{i}: 分数={score:.4f}, 内容={content}...")
    else:
        print("  无结果")