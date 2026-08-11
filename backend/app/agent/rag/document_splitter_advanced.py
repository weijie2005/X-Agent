"""
RAG 文档分割模块（优化版）

实现多种分割策略：
1. 语义分割（基于句子、段落）
2. 滑动窗口分割（保留上下文重叠）
3. 结构化分割（基于标题、章节）
4. 递归字符分割（LangChain 方法）
5. 混合分割（推荐）
"""
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """
    文档切片
    
    存储单个文档切片的内容和元数据。
    """
    content: str
    metadata: Dict[str, Any]
    chunk_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "content": self.content,
            "metadata": self.metadata,
            "chunk_id": self.chunk_id
        }


class SemanticTextSplitter:
    """
    语义文本切片器
    
    基于句子和段落边界进行分割，保持语义完整性。
    """
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        min_chunk_size: int = 100
    ):
        """
        初始化语义切片器
        
        Args:
            chunk_size: 目标切片大小（字符数）
            chunk_overlap: 切片重叠大小（字符数）
            min_chunk_size: 最小切片大小
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        
        # 句子分隔符（优先级从高到低）
        self.sentence_separators = [
            "\n\n",  # 段落
            "\n",    # 换行
            "。",    # 中文句号
            "！",    # 中文感叹号
            "？",    # 中文问号
            "；",    # 中文分号
            "。",    # 英文句号
            "!",     # 英文感叹号
            "?",     # 英文问号
            ";",     # 英文分号
            "，",    # 中文逗号
            ",",     # 英文逗号
            " ",     # 空格
            ""       # 字符
        ]
    
    def split(self, text: str) -> List[str]:
        """
        语义分割文本
        
        Args:
            text: 原始文本
        
        Returns:
            切片列表
        """
        # 1. 先按段落分割
        paragraphs = self._split_by_paragraphs(text)
        
        # 2. 合并小段落，分割大段落
        chunks = self._merge_and_split_paragraphs(paragraphs)
        
        # 3. 添加重叠窗口
        if self.chunk_overlap > 0:
            chunks = self._add_overlap_window(chunks)
        
        return chunks
    
    def _split_by_paragraphs(self, text: str) -> List[str]:
        """
        按段落分割文本
        
        Args:
            text: 原始文本
        
        Returns:
            段落列表
        """
        # 按双换行符分割段落
        paragraphs = re.split(r'\n\s*\n', text)
        
        # 清理空白段落
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        return paragraphs
    
    def _merge_and_split_paragraphs(self, paragraphs: List[str]) -> List[str]:
        """
        合并小段落，分割大段落
        
        Args:
            paragraphs: 段落列表
        
        Returns:
            切片列表
        """
        chunks = []
        current_chunk = []
        current_size = 0
        
        for paragraph in paragraphs:
            paragraph_size = len(paragraph)
            
            # 如果段落本身超过限制，需要分割
            if paragraph_size > self.chunk_size:
                # 先保存当前切片
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = []
                    current_size = 0
                
                # 分割大段落
                sub_chunks = self._split_large_paragraph(paragraph)
                chunks.extend(sub_chunks)
            
            # 如果当前切片加上新段落不超过限制，则添加
            elif current_size + paragraph_size + 2 <= self.chunk_size:
                current_chunk.append(paragraph)
                current_size += paragraph_size + 2
            
            # 否则保存当前切片，开始新切片
            else:
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                
                current_chunk = [paragraph]
                current_size = paragraph_size
        
        # 保存最后一个切片
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks
    
    def _split_large_paragraph(self, paragraph: str) -> List[str]:
        """
        分割大段落（基于句子边界）
        
        Args:
            paragraph: 段落文本
        
        Returns:
            切片列表
        """
        # 按句子分割
        sentences = self._split_into_sentences(paragraph)
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            # 如果句子本身超过限制，按字符分割
            if sentence_size > self.chunk_size:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
                    current_size = 0
                
                # 按字符分割
                sub_chunks = self._split_by_characters(sentence)
                chunks.extend(sub_chunks)
            
            # 如果当前切片加上新句子不超过限制，则添加
            elif current_size + sentence_size + 1 <= self.chunk_size:
                current_chunk.append(sentence)
                current_size += sentence_size + 1
            
            # 否则保存当前切片，开始新切片
            else:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                
                current_chunk = [sentence]
                current_size = sentence_size
        
        # 保存最后一个切片
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        将文本分割成句子
        
        Args:
            text: 文本
        
        Returns:
            句子列表
        """
        # 使用正则表达式分割句子
        # 匹配中文和英文句子结束符
        sentence_endings = r'([。！？；。!?;])'
        
        # 分割句子
        parts = re.split(sentence_endings, text)
        
        # 合并句子结束符
        sentences = []
        for i in range(0, len(parts) - 1, 2):
            if i + 1 < len(parts):
                sentence = parts[i] + parts[i + 1]
            else:
                sentence = parts[i]
            
            if sentence.strip():
                sentences.append(sentence.strip())
        
        # 处理最后一部分（可能没有结束符）
        if len(parts) % 2 == 1 and parts[-1].strip():
            sentences.append(parts[-1].strip())
        
        return sentences if sentences else [text]
    
    def _split_by_characters(self, text: str) -> List[str]:
        """
        按字符分割文本（最后的手段）
        
        Args:
            text: 文本
        
        Returns:
            切片列表
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # 尝试在单词边界处分割
            if end < len(text):
                # 向后查找空格或标点符号
                while end < len(text) and text[end] not in ' \n\t,.;!?，。；！？':
                    end += 1
                
                # 如果找不到边界，强制分割
                if end >= len(text):
                    end = start + self.chunk_size
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end
        
        return chunks
    
    def _add_overlap_window(self, chunks: List[str]) -> List[str]:
        """
        添加重叠窗口（滑动窗口）
        
        Args:
            chunks: 切片列表
        
        Returns:
            带重叠的切片列表
        """
        if len(chunks) <= 1:
            return chunks
        
        overlapped_chunks = []
        
        for i, chunk in enumerate(chunks):
            # 第一个切片，不需要前重叠
            if i == 0:
                overlapped_chunks.append(chunk)
                continue
            
            # 获取前一个切片的末尾部分作为重叠
            prev_chunk = chunks[i - 1]
            overlap_text = prev_chunk[-self.chunk_overlap:] if len(prev_chunk) > self.chunk_overlap else prev_chunk
            
            # 添加重叠部分
            overlapped_chunk = overlap_text + " " + chunk
            overlapped_chunks.append(overlapped_chunk)
        
        return overlapped_chunks


class RecursiveCharacterTextSplitter:
    """
    递归字符文本切片器（LangChain 方法）
    
    递归地尝试不同的分隔符，从大到小。
    """
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: Optional[List[str]] = None
    ):
        """
        初始化递归字符切片器
        
        Args:
            chunk_size: 切片大小
            chunk_overlap: 切片重叠大小
            separators: 分隔符列表（按优先级排序）
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # 默认分隔符（从大到小）
        self.separators = separators or [
            "\n\n",  # 段落
            "\n",    # 换行
            "。",    # 中文句号
            "！",    # 中文感叹号
            "？",    # 中文问号
            "；",    # 中文分号
            "。",    # 英文句号
            "!",     # 英文感叹号
            "?",     # 英文问号
            ";",     # 英文分号
            " ",     # 空格
            ""       # 字符
        ]
    
    def split(self, text: str) -> List[str]:
        """
        递归分割文本
        
        Args:
            text: 原始文本
        
        Returns:
            切片列表
        """
        return self._split_text_recursive(text, self.separators)
    
    def _split_text_recursive(
        self,
        text: str,
        separators: List[str]
    ) -> List[str]:
        """
        递归分割文本
        
        Args:
            text: 文本
            separators: 分隔符列表
        
        Returns:
            切片列表
        """
        # 如果文本足够小，直接返回
        if len(text) <= self.chunk_size:
            return [text] if text.strip() else []
        
        # 尝试每个分隔符
        for separator in separators:
            if separator == "":
                # 最后的手段：按字符分割
                return self._split_by_characters(text)
            
            # 检查分隔符是否在文本中
            if separator in text:
                # 按分隔符分割
                splits = text.split(separator)
                
                # 合并小的分割部分
                chunks = []
                current_chunk = []
                current_size = 0
                
                for split in splits:
                    split = split.strip()
                    if not split:
                        continue
                    
                    split_size = len(split)
                    
                    # 如果分割部分本身超过限制，递归分割
                    if split_size > self.chunk_size:
                        # 先保存当前切片
                        if current_chunk:
                            chunks.append(separator.join(current_chunk))
                            current_chunk = []
                            current_size = 0
                        
                        # 递归分割（使用下一个分隔符）
                        next_separators = separators[separators.index(separator) + 1:]
                        sub_chunks = self._split_text_recursive(split, next_separators)
                        chunks.extend(sub_chunks)
                    
                    # 如果当前切片加上新分割部分不超过限制，则添加
                    elif current_size + split_size + len(separator) <= self.chunk_size:
                        current_chunk.append(split)
                        current_size += split_size + len(separator)
                    
                    # 否则保存当前切片，开始新切片
                    else:
                        if current_chunk:
                            chunks.append(separator.join(current_chunk))
                        
                        current_chunk = [split]
                        current_size = split_size
                
                # 保存最后一个切片
                if current_chunk:
                    chunks.append(separator.join(current_chunk))
                
                # 如果成功分割，返回结果
                if chunks:
                    # 添加重叠
                    return self._add_overlap(chunks)
        
        # 如果所有分隔符都失败，按字符分割
        return self._split_by_characters(text)
    
    def _split_by_characters(self, text: str) -> List[str]:
        """
        按字符分割文本
        
        Args:
            text: 文本
        
        Returns:
            切片列表
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end].strip()
            
            if chunk:
                chunks.append(chunk)
            
            start = end
        
        return chunks
    
    def _add_overlap(self, chunks: List[str]) -> List[str]:
        """
        添加重叠
        
        Args:
            chunks: 切片列表
        
        Returns:
            带重叠的切片列表
        """
        if len(chunks) <= 1:
            return chunks
        
        overlapped_chunks = []
        
        for i, chunk in enumerate(chunks):
            if i == 0:
                overlapped_chunks.append(chunk)
                continue
            
            # 获取前一个切片的末尾部分
            prev_chunk = chunks[i - 1]
            overlap_text = prev_chunk[-self.chunk_overlap:] if len(prev_chunk) > self.chunk_overlap else prev_chunk
            
            # 添加重叠部分
            overlapped_chunk = overlap_text + " " + chunk
            overlapped_chunks.append(overlapped_chunk)
        
        return overlapped_chunks


class HybridTextSplitter:
    """
    混合文本切片器（推荐）
    
    结合语义分割、滑动窗口和结构化分割的优点。
    """
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        enable_semantic: bool = True,
        enable_structure: bool = True,
        enable_window: bool = True
    ):
        """
        初始化混合切片器
        
        Args:
            chunk_size: 目标切片大小
            chunk_overlap: 切片重叠大小
            enable_semantic: 是否启用语义分割
            enable_structure: 是否启用结构化分割
            enable_window: 是否启用滑动窗口
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.enable_semantic = enable_semantic
        self.enable_structure = enable_structure
        self.enable_window = enable_window
        
        # 初始化子切片器
        self.semantic_splitter = SemanticTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap if enable_window else 0
        )
        
        self.recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap if enable_window else 0
        )
    
    def split(self, text: str) -> List[str]:
        """
        混合分割文本
        
        Args:
            text: 原始文本
        
        Returns:
            切片列表
        """
        # 1. 结构化分割（如果启用）
        if self.enable_structure:
            sections = self._split_by_structure(text)
            
            # 如果成功识别结构，按结构分割
            if len(sections) > 1:
                chunks = []
                for section in sections:
                    # 对每个部分进行语义分割
                    section_chunks = self.semantic_splitter.split(section)
                    chunks.extend(section_chunks)
                
                return chunks
        
        # 2. 语义分割（如果启用）
        if self.enable_semantic:
            return self.semantic_splitter.split(text)
        
        # 3. 递归字符分割（fallback）
        return self.recursive_splitter.split(text)
    
    def _split_by_structure(self, text: str) -> List[str]:
        """
        按文档结构分割（基于标题、章节）
        
        Args:
            text: 文本
        
        Returns:
            结构化切片列表
        """
        # 识别标题模式
        # Markdown 标题：# ## ### 等
        # 数字标题：1. 1.1 1.1.1 等
        # 中文标题：一、二、三 等
        
        heading_patterns = [
            r'^#{1,6}\s+.+$',           # Markdown 标题
            r'^\d+\.\s+.+$',            # 数字标题
            r'^[一二三四五六七八九十]+、.+$',  # 中文标题
            r'^[A-Z]\.\s+.+$',          # 字母标题
        ]
        
        # 按行分割
        lines = text.split('\n')
        
        sections = []
        current_section = []
        
        for line in lines:
            # 检查是否是标题
            is_heading = any(re.match(pattern, line.strip()) for pattern in heading_patterns)
            
            if is_heading and current_section:
                # 保存当前部分
                sections.append('\n'.join(current_section))
                current_section = [line]
            else:
                current_section.append(line)
        
        # 保存最后一部分
        if current_section:
            sections.append('\n'.join(current_section))
        
        # 如果没有识别到结构，返回原文
        if len(sections) <= 1:
            return [text]
        
        return sections


class DocumentProcessor:
    """
    文档处理器（优化版）
    
    完整的文档处理流程：解析 → 清洗 → 切片。
    支持多种分割策略。
    """
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        split_strategy: str = "hybrid"
    ):
        """
        初始化文档处理器
        
        Args:
            chunk_size: 切片大小
            chunk_overlap: 切片重叠大小
            split_strategy: 分割策略（"semantic", "recursive", "hybrid"）
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.split_strategy = split_strategy
        
        # 根据策略选择切片器
        if split_strategy == "semantic":
            self.splitter = SemanticTextSplitter(chunk_size, chunk_overlap)
        elif split_strategy == "recursive":
            self.splitter = RecursiveCharacterTextSplitter(chunk_size, chunk_overlap)
        elif split_strategy == "hybrid":
            self.splitter = HybridTextSplitter(chunk_size, chunk_overlap)
        else:
            raise ValueError(f"Unknown split strategy: {split_strategy}")
        
        logger.info(f"Initialized DocumentProcessor with {split_strategy} strategy")
    
    def process(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """
        处理文档
        
        Args:
            text: 文档文本
            metadata: 文档元数据
        
        Returns:
            文档切片列表
        """
        if metadata is None:
            metadata = {}
        
        # 1. 清洗文档
        cleaned_text = self._clean_text(text)
        
        # 2. 切分文档
        chunks_text = self.splitter.split(cleaned_text)
        
        # 3. 创建切片对象
        chunks = []
        for i, chunk_text in enumerate(chunks_text):
            chunk_metadata = metadata.copy()
            chunk_metadata['chunk_index'] = i
            chunk_metadata['total_chunks'] = len(chunks_text)
            chunk_metadata['split_strategy'] = self.split_strategy
            
            chunk = DocumentChunk(
                content=chunk_text,
                metadata=chunk_metadata,
                chunk_id=f"{metadata.get('doc_id', 'unknown')}_{i}"
            )
            chunks.append(chunk)
        
        logger.info(f"Processed document into {len(chunks)} chunks using {self.split_strategy} strategy")
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """
        清洗文本
        
        Args:
            text: 原始文本
        
        Returns:
            清洗后的文本
        """
        # 移除特殊字符
        text = re.sub(r'\x00', '', text)  # 空字符
        text = re.sub(r'\x0c', '', text)  # 换页符
        text = re.sub(r'\ufeff', '', text)  # BOM 字符
        
        # 移除多余的空白
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        # 去除首尾空白
        text = text.strip()
        
        return text


# 使用示例
if __name__ == "__main__":
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

Python 在 Web 开发领域有 Django、Flask 等流行框架。

### 数据科学

在数据科学领域，Python 有 NumPy、Pandas、Matplotlib 等强大工具。
"""
    
    # 测试不同策略
    print("=" * 60)
    print("测试不同分割策略")
    print("=" * 60)
    
    # 1. 语义分割
    print("\n1. 语义分割策略:")
    processor_semantic = DocumentProcessor(
        chunk_size=200,
        chunk_overlap=50,
        split_strategy="semantic"
    )
    chunks_semantic = processor_semantic.process(sample_text, {"doc_id": "test"})
    
    for i, chunk in enumerate(chunks_semantic, 1):
        print(f"\n切片 {i} (长度: {len(chunk.content)}):")
        print(chunk.content[:100] + "...")
    
    # 2. 递归字符分割
    print("\n" + "=" * 60)
    print("2. 递归字符分割策略:")
    processor_recursive = DocumentProcessor(
        chunk_size=200,
        chunk_overlap=50,
        split_strategy="recursive"
    )
    chunks_recursive = processor_recursive.process(sample_text, {"doc_id": "test"})
    
    for i, chunk in enumerate(chunks_recursive, 1):
        print(f"\n切片 {i} (长度: {len(chunk.content)}):")
        print(chunk.content[:100] + "...")
    
    # 3. 混合分割（推荐）
    print("\n" + "=" * 60)
    print("3. 混合分割策略（推荐）:")
    processor_hybrid = DocumentProcessor(
        chunk_size=200,
        chunk_overlap=50,
        split_strategy="hybrid"
    )
    chunks_hybrid = processor_hybrid.process(sample_text, {"doc_id": "test"})
    
    for i, chunk in enumerate(chunks_hybrid, 1):
        print(f"\n切片 {i} (长度: {len(chunk.content)}):")
        print(chunk.content[:100] + "...")
    
    print("\n" + "=" * 60)
    print("总结:")
    print(f"  语义分割: {len(chunks_semantic)} 个切片")
    print(f"  递归字符分割: {len(chunks_recursive)} 个切片")
    print(f"  混合分割: {len(chunks_hybrid)} 个切片")
    print("=" * 60)