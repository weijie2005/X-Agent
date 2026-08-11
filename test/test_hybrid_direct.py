#!/usr/bin/env python3
"""直接使用HybridRetriever测试"""
import sys
sys.path.insert(0, '/home/s8066/agent-project/backend')

from app.agent.rag.hybrid_retriever import HybridRetriever

collection_name = "kb_c8e09d410e20"

queries = [
    "查询一下我的成绩",
    "高等数学成绩",
    "Python应用成绩"
]

retriever = HybridRetriever(collection_name=collection_name)

print("直接使用HybridRetriever测试")
print("=" * 60)

for query in queries:
    print(f"\n查询: {query}")
    print("-" * 40)
    
    results = retriever.retrieve(query, limit=3, score_threshold=0.1)
    
    print(f"检索结果数量: {len(results)}")
    
    if results:
        for i, result in enumerate(results, 1):
            score = result.get('combined_score', result.get('score', 0))
            content = result.get('content', '')[:150]
            print(f"  结果{i}: 分数={score:.4f}")
            print(f"         内容={content}...")
    else:
        print("  无结果")