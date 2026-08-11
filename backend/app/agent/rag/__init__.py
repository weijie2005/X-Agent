"""
RAG 知识库系统模块

实现生产级 Agentic RAG，解决文档问答、幻觉、多跳推理。

核心组件：
1. DocumentProcessor: 文档处理（解析、清洗、切片）
2. RAGIndexer: 文档索引（向量化、入库）
3. HybridRetriever: 混合检索（语义+关键词+重排）
4. CRAGSystem: CRAG纠错（验证、丢弃、补搜）
5. AgenticRAG: Agentic RAG（自主判断、多轮检索）

分割策略：
- SemanticTextSplitter: 语义分割（基于句子、段落）
- RecursiveCharacterTextSplitter: 递归字符分割（LangChain 方法）
- HybridTextSplitter: 混合分割（推荐）
"""
from app.agent.rag.document_processor import (
    DocumentProcessor,
    DocumentChunk,
    DocumentCleaner,
    TextSplitter
)
from app.agent.rag.document_splitter_advanced import (
    SemanticTextSplitter,
    RecursiveCharacterTextSplitter,
    HybridTextSplitter
)
from app.agent.rag.embedding_engine import (
    EmbeddingEngine,
    QdrantManager,
    RAGIndexer
)
from app.agent.rag.hybrid_retriever import (
    HybridRetriever,
    KeywordSearcher,
    ResultReranker
)
from app.agent.rag.crag_system import (
    CRAGSystem,
    RetrievalValidator
)
from app.agent.rag.agentic_rag import AgenticRAG

__all__ = [
    # 文档处理
    "DocumentProcessor",
    "DocumentChunk",
    "DocumentCleaner",
    "TextSplitter",
    # 高级分割器
    "SemanticTextSplitter",
    "RecursiveCharacterTextSplitter",
    "HybridTextSplitter",
    # 向量化
    "EmbeddingEngine",
    "QdrantManager",
    "RAGIndexer",
    # 混合检索
    "HybridRetriever",
    "KeywordSearcher",
    "ResultReranker",
    # CRAG
    "CRAGSystem",
    "RetrievalValidator",
    # Agentic RAG
    "AgenticRAG",
]