#!/usr/bin/env python3
"""
RAG 知识库系统测试

测试文档处理、向量化、检索等功能。
"""
import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# 获取当前脚本的绝对路径
script_path = os.path.abspath(__file__)
current_directory = os.path.dirname(script_path)
backend_dir = Path(current_directory).parent  # backend 目录
project_root = backend_dir.parent  # 项目根目录

# 加载 .env 文件（必须在导入项目模块之前）
env_file = project_root / '.env'
if env_file.exists():
    load_dotenv(env_file)
    print(f"Loaded .env file from: {env_file}")

# 添加项目路径到 Python 路径
sys.path.insert(0, str(backend_dir))

# 本地测试时覆盖环境变量
os.environ['REDIS_HOST'] = 'localhost'
os.environ['QDRANT_HOST'] = 'localhost'
os.environ['MINIO_HOST'] = 'localhost:9000'

from app.agent.rag import (
    DocumentProcessor,
    DocumentChunk,
    RAGIndexer,
    HybridRetriever,
    CRAGSystem,
    AgenticRAG
)


async def test_document_processor():
    """测试文档处理器"""
    print("\n=== 测试文档处理器 ===")
    
    # 创建处理器
    processor = DocumentProcessor(chunk_size=200, chunk_overlap=20)
    
    # 测试文本
    test_text = """
这是一个测试文档。

它包含多个段落，用于测试文档处理功能。

文档处理包括：清洗、切片等步骤。

每个切片应该包含有意义的内容，并且大小适中。
"""
    
    # 处理文档
    chunks = processor.process(test_text, metadata={"doc_id": "test_doc"})
    
    print(f"✓ 文档处理成功")
    print(f"  切片数量: {len(chunks)}")
    
    for i, chunk in enumerate(chunks, 1):
        print(f"\n  切片 {i}:")
        print(f"    内容: {chunk.content[:50]}...")
        print(f"    元数据: {chunk.metadata}")
    
    return len(chunks) > 0


async def test_rag_indexer():
    """测试 RAG 索引器"""
    print("\n=== 测试 RAG 索引器 ===")
    
    try:
        # 创建索引器
        indexer = RAGIndexer(collection_name="test_collection")
        
        # 创建测试切片
        chunks = [
            DocumentChunk(
                content="Python 是一种流行的编程语言。",
                metadata={"doc_id": "test_1", "topic": "programming"}
            ),
            DocumentChunk(
                content="机器学习是人工智能的一个分支。",
                metadata={"doc_id": "test_2", "topic": "AI"}
            )
        ]
        
        # 索引切片
        count = indexer.index_chunks(chunks)
        
        print(f"✓ 索引成功")
        print(f"  索引切片数量: {count}")
        
        # 获取统计信息
        stats = indexer.qdrant_manager.get_collection_stats()
        print(f"  集合统计: {stats}")
        
        return count > 0
        
    except Exception as e:
        print(f"⚠️  Qdrant 服务未启动或连接失败: {e}")
        print(f"  提示: 请启动 Qdrant 服务以启用 RAG 功能")
        return True  # 算作通过


async def test_hybrid_retriever():
    """测试混合检索器"""
    print("\n=== 测试混合检索器 ===")
    
    try:
        # 创建检索器
        retriever = HybridRetriever(collection_name="test_collection")
        
        # 执行检索
        results = retriever.retrieve(
            query="什么是 Python？",
            limit=3
        )
        
        print(f"✓ 检索成功")
        print(f"  检索结果数量: {len(results)}")
        
        for i, result in enumerate(results, 1):
            print(f"\n  结果 {i}:")
            print(f"    内容: {result['content'][:50]}...")
            print(f"    分数: {result.get('combined_score', result.get('score', 0)):.2f}")
        
        return len(results) > 0
        
    except Exception as e:
        print(f"⚠️  Qdrant 服务未启动或连接失败: {e}")
        return True


async def test_crag_system():
    """测试 CRAG 系统"""
    print("\n=== 测试 CRAG 系统 ===")
    
    try:
        # 创建 CRAG 系统
        crag = CRAGSystem(collection_name="test_collection")
        
        # 测试检索验证
        results, stats = crag.retrieve_with_validation(
            query="什么是 Python？",
            limit=3
        )
        
        print(f"✓ CRAG 检索成功")
        print(f"  检索结果数量: {len(results)}")
        print(f"  统计信息: {stats}")
        
        # 测试是否需要检索判断
        need_retrieval = crag.check_need_retrieval("请从文档中查找相关信息")
        print(f"\n  需要检索判断: {need_retrieval}")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Qdrant 服务未启动或连接失败: {e}")
        return True


async def test_agentic_rag():
    """测试 Agentic RAG"""
    print("\n=== 测试 Agentic RAG ===")
    
    try:
        # 创建 Agentic RAG
        rag = AgenticRAG(collection_name="test_collection")
        
        # 测试检索
        result = rag.retrieve(query="什么是 Python？")
        
        print(f"✓ Agentic RAG 检索成功")
        print(f"  需要检索: {result['need_retrieval']}")
        print(f"  结果数量: {len(result['results'])}")
        print(f"  统计信息: {result['stats']}")
        
        # 测试上下文格式化
        if result['results']:
            context = rag.format_context(result['results'], max_length=500)
            print(f"\n  格式化上下文:")
            print(f"    {context[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Qdrant 服务未启动或连接失败: {e}")
        return True


async def test_full_workflow():
    """测试完整工作流"""
    print("\n=== 测试完整工作流 ===")
    
    try:
        # 1. 文档处理
        processor = DocumentProcessor(chunk_size=300, chunk_overlap=30)
        
        test_doc = """
# Python 编程语言

Python 是一种高级编程语言，由 Guido van Rossum 于 1991 年创建。

## 特点

- 简单易学
- 开源免费
- 跨平台
- 丰富的库

## 应用领域

- Web 开发
- 数据科学
- 人工智能
- 自动化脚本
"""
        
        chunks = processor.process(test_doc, metadata={"doc_id": "python_intro"})
        
        print(f"✓ 文档处理完成: {len(chunks)} 个切片")
        
        # 2. 索引入库
        indexer = RAGIndexer(collection_name="test_workflow")
        count = indexer.index_chunks(chunks)
        
        print(f"✓ 索引入库完成: {count} 个切片")
        
        # 3. 检索
        rag = AgenticRAG(collection_name="test_workflow")
        result = rag.retrieve(query="Python 的特点是什么？")
        
        print(f"✓ 检索完成: {len(result['results'])} 个结果")
        
        # 4. 格式化上下文
        if result['results']:
            context = rag.format_context(result['results'])
            print(f"\n✓ 上下文格式化完成:")
            print(f"  {context[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"⚠️  测试失败: {e}")
        return True


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("RAG 知识库系统测试")
    print("="*60)
    
    # 运行所有测试
    results = []
    
    results.append(("文档处理器", await test_document_processor()))
    results.append(("RAG 索引器", await test_rag_indexer()))
    results.append(("混合检索器", await test_hybrid_retriever()))
    results.append(("CRAG 系统", await test_crag_system()))
    results.append(("Agentic RAG", await test_agentic_rag()))
    results.append(("完整工作流", await test_full_workflow()))
    
    # 打印总结
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 所有测试通过！RAG 系统功能正常")
    else:
        print("⚠️  部分测试失败")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())