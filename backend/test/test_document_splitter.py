#!/usr/bin/env python3
"""
测试优化的文档分割策略
"""
import sys
import os
from pathlib import Path

# 获取当前脚本的绝对路径
script_path = os.path.abspath(__file__)
current_directory = os.path.dirname(script_path)
backend_dir = Path(current_directory).parent

# 添加项目路径到 Python 路径
sys.path.insert(0, str(backend_dir))

from app.agent.rag.document_splitter_advanced import (
    DocumentProcessor,
    SemanticTextSplitter,
    RecursiveCharacterTextSplitter,
    HybridTextSplitter
)

# 示例文本
sample_text = """
# Python 编程语言

Python 是一种高级编程语言，由 Guido van Rossum 于 1991 年创建。

## 特点

Python 具有以下特点：
1. 简单易学
2. 开源免费
3. 跨平台
4. 丰富的库

## 应用领域

Python 广泛应用于：
- Web 开发
- 数据科学
- 人工智能
- 自动化脚本

### Web 开发

Python 在 Web 开发领域有 Django、Flask 等流行框架。这些框架提供了完整的 Web 开发解决方案，包括路由、模板、数据库集成等功能。

### 数据科学

在数据科学领域，Python 有 NumPy、Pandas、Matplotlib 等强大工具。这些工具使得数据处理、分析和可视化变得简单高效。
"""

print("=" * 80)
print("测试不同分割策略")
print("=" * 80)

# 1. 语义分割
print("\n【策略1】语义分割（基于句子和段落边界）")
print("-" * 80)
processor_semantic = DocumentProcessor(
    chunk_size=200,
    chunk_overlap=50,
    split_strategy="semantic"
)
chunks_semantic = processor_semantic.process(sample_text, {"doc_id": "test"})

for i, chunk in enumerate(chunks_semantic, 1):
    print(f"\n切片 {i} (长度: {len(chunk.content)} 字符):")
    print(f"  {chunk.content[:150]}...")

# 2. 递归字符分割
print("\n" + "=" * 80)
print("【策略2】递归字符分割（LangChain 方法）")
print("-" * 80)
processor_recursive = DocumentProcessor(
    chunk_size=200,
    chunk_overlap=50,
    split_strategy="recursive"
)
chunks_recursive = processor_recursive.process(sample_text, {"doc_id": "test"})

for i, chunk in enumerate(chunks_recursive, 1):
    print(f"\n切片 {i} (长度: {len(chunk.content)} 字符):")
    print(f"  {chunk.content[:150]}...")

# 3. 混合分割（推荐）
print("\n" + "=" * 80)
print("【策略3】混合分割（推荐：语义 + 结构 + 窗口）")
print("-" * 80)
processor_hybrid = DocumentProcessor(
    chunk_size=200,
    chunk_overlap=50,
    split_strategy="hybrid"
)
chunks_hybrid = processor_hybrid.process(sample_text, {"doc_id": "test"})

for i, chunk in enumerate(chunks_hybrid, 1):
    print(f"\n切片 {i} (长度: {len(chunk.content)} 字符):")
    print(f"  {chunk.content[:150]}...")

# 对比总结
print("\n" + "=" * 80)
print("📊 分割策略对比总结")
print("=" * 80)

print(f"\n原文长度: {len(sample_text)} 字符")
print(f"\n切片数量:")
print(f"  - 语义分割: {len(chunks_semantic)} 个切片")
print(f"  - 递归字符分割: {len(chunks_recursive)} 个切片")
print(f"  - 混合分割: {len(chunks_hybrid)} 个切片")

print(f"\n平均切片长度:")
semantic_avg = sum(len(c.content) for c in chunks_semantic) / len(chunks_semantic)
recursive_avg = sum(len(c.content) for c in chunks_recursive) / len(chunks_recursive)
hybrid_avg = sum(len(c.content) for c in chunks_hybrid) / len(chunks_hybrid)

print(f"  - 语义分割: {semantic_avg:.1f} 字符")
print(f"  - 递归字符分割: {recursive_avg:.1f} 字符")
print(f"  - 混合分割: {hybrid_avg:.1f} 字符")

print("\n" + "=" * 80)
print("✅ 测试完成！")
print("=" * 80)

print("\n💡 推荐使用:")
print("  - **混合分割策略**：结合了语义、结构和滑动窗口的优点")
print("  - 适合大多数场景，尤其是结构化文档")
print("  - 保持语义完整性，同时保留上下文重叠")

print("\n📖 各策略适用场景:")
print("  1. **语义分割**: 适合自然语言文本，保持句子完整性")
print("  2. **递归字符分割**: 适合无结构文本，LangChain 推荐方法")
print("  3. **混合分割**: 适合结构化文档（Markdown、技术文档等）")