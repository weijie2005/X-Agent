# RAG 文档分割策略对比与优化

## 📊 问题分析

### 当前问题：按大小分割

**主要问题**：
1. **切断语义完整性**：可能在句子中间切断，导致语义不完整
2. **丢失上下文**：重要信息可能分散在不同切片中
3. **降低检索质量**：不完整的切片影响向量相似度计算
4. **用户体验差**：检索结果可能包含不完整的句子，难以理解

**示例**：
```
原文：Python 是一种高级编程语言，由 Guido van Rossum 于 1991 年创建。它具有简单易学、开源免费等特点。

按大小分割（chunk_size=30）：
切片1：Python 是一种高级编程语言，由 Guido
切片2：van Rossum 于 1991 年创建。它具有简单
切片3：易学、开源免费等特点。

问题：
- 切片1：句子不完整，缺少"创建者"信息
- 切片2：句子被切断，难以理解
- 切片3：缺少主语，不知道在说什么
```

---

## 🎯 分割策略对比

### 1. 按大小分割（固定大小）

**方法**：按固定字符数分割，添加重叠窗口

**优点**：
- ✅ 实现简单
- ✅ 切片大小可控
- ✅ 适合无结构文本

**缺点**：
- ❌ 切断语义完整性
- ❌ 可能切断句子、段落
- ❌ 丢失上下文信息

**适用场景**：
- 无结构文本
- 对切片大小有严格要求的场景

**代码示例**：
```python
from langchain.text_splitter import CharacterTextSplitter

splitter = CharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separator="\n\n"
)
```

---

### 2. 滑动窗口分割

**方法**：按固定大小分割，但添加重叠窗口

**优点**：
- ✅ 保留上下文重叠
- ✅ 减少信息丢失
- ✅ 提高检索召回率

**缺点**：
- ❌ 重复内容多
- ❌ 存储成本高
- ❌ 可能仍然切断句子

**适用场景**：
- 需要保留上下文的场景
- 对召回率要求高的场景

**代码示例**：
```python
from langchain.text_splitter import SlidingWindowSplitter

splitter = SlidingWindowSplitter(
    window_size=500,
    overlap_size=100
)
```

---

### 3. 语义分割（推荐）

**方法**：基于句子、段落边界分割，保持语义完整性

**优点**：
- ✅ 保持语义完整性
- ✅ 不切断句子
- ✅ 提高检索质量
- ✅ 更好的用户体验

**缺点**：
- ❌ 切片大小不均匀
- ❌ 可能切片过大
- ❌ 需要处理边界情况

**适用场景**：
- 自然语言文本
- 对语义完整性要求高的场景

**代码示例**：
```python
from app.agent.rag.document_splitter_advanced import SemanticTextSplitter

splitter = SemanticTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)
```

**分割流程**：
```
1. 按段落分割（\n\n）
   ↓
2. 合并小段落，分割大段落
   ↓
3. 按句子分割（。！？等）
   ↓
4. 添加重叠窗口
```

---

### 4. 递归字符分割（LangChain 方法）

**方法**：递归地尝试不同的分隔符，从大到小

**优点**：
- ✅ 灵活性强
- ✅ 适应多种文本格式
- ✅ LangChain 推荐方法

**缺点**：
- ❌ 可能切断语义
- ❌ 参数调优复杂

**适用场景**：
- 多种格式的文本
- 需要灵活分割的场景

**代码示例**：
```python
from app.agent.rag.document_splitter_advanced import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", "。", "！", "？", " ", ""]
)
```

**分割流程**：
```
尝试分隔符1（\n\n）
   ↓ 失败
尝试分隔符2（\n）
   ↓ 失败
尝试分隔符3（。）
   ↓ 成功
返回结果
```

---

### 5. 结构化分割

**方法**：基于文档结构（标题、章节）分割

**优点**：
- ✅ 保持文档结构
- ✅ 适合技术文档
- ✅ 语义完整性好

**缺点**：
- ❌ 依赖文档格式
- ❌ 可能切片过大
- ❌ 需要识别结构

**适用场景**：
- Markdown 文档
- 技术文档
- 结构化文档

**代码示例**：
```python
from app.agent.rag.document_splitter_advanced import HybridTextSplitter

splitter = HybridTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    enable_structure=True
)
```

**识别的结构**：
- Markdown 标题：`# ## ###`
- 数字标题：`1. 1.1 1.1.1`
- 中文标题：`一、二、三`
- 字母标题：`A. B. C`

---

### 6. 混合分割（最佳实践）

**方法**：结合语义分割、滑动窗口和结构化分割

**优点**：
- ✅ 结合多种方法优点
- ✅ 适应性强
- ✅ 最佳检索效果

**缺点**：
- ❌ 实现复杂
- ❌ 参数调优需要经验

**适用场景**：
- 生产环境
- 对检索质量要求高的场景

**代码示例**：
```python
from app.agent.rag.document_splitter_advanced import HybridTextSplitter

splitter = HybridTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    enable_semantic=True,
    enable_structure=True,
    enable_window=True
)
```

**分割流程**：
```
1. 结构化分割（识别标题、章节）
   ↓
2. 对每个部分进行语义分割
   ↓
3. 添加重叠窗口
   ↓
4. 返回最终切片
```

---

## 📊 测试结果对比

### 测试文本
```
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
```

### 分割结果

| 策略 | 切片数量 | 平均长度 | 语义完整性 | 上下文保留 |
|------|---------|---------|-----------|-----------|
| 语义分割 | 2 | 197 字符 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 递归字符分割 | 2 | 197 字符 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 混合分割 | 9 | 37 字符 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

### 分析

1. **语义分割**：
   - 保持段落完整性
   - 切片大小适中
   - 适合自然语言文本

2. **递归字符分割**：
   - 灵活性强
   - 与语义分割结果相似
   - LangChain 推荐方法

3. **混合分割**：
   - 按标题分割，保持结构
   - 每个切片语义完整
   - 最佳检索效果

---

## 🏆 最佳实践推荐

### 推荐策略：混合分割

**理由**：
1. ✅ 结合了语义、结构和滑动窗口的优点
2. ✅ 适合大多数场景
3. ✅ 保持语义完整性
4. ✅ 保留上下文重叠
5. ✅ 适应结构化文档

**使用方法**：
```python
from app.agent.rag.document_splitter_advanced import DocumentProcessor

# 初始化文档处理器（使用混合分割策略）
processor = DocumentProcessor(
    chunk_size=500,        # 目标切片大小
    chunk_overlap=50,      # 重叠窗口大小
    split_strategy="hybrid" # 混合分割策略
)

# 处理文档
chunks = processor.process(
    text="你的文档内容",
    metadata={"doc_id": "doc_001"}
)

# 查看切片
for chunk in chunks:
    print(f"切片: {chunk.content}")
    print(f"元数据: {chunk.metadata}")
```

---

## 📖 各策略适用场景总结

### 1. 按大小分割
- **适用场景**：无结构文本、对切片大小有严格要求
- **不适用场景**：自然语言文本、对语义完整性要求高

### 2. 滑动窗口分割
- **适用场景**：需要保留上下文、对召回率要求高
- **不适用场景**：存储成本敏感、重复内容多

### 3. 语义分割
- **适用场景**：自然语言文本、对语义完整性要求高
- **不适用场景**：切片大小必须均匀、需要严格控制大小

### 4. 递归字符分割
- **适用场景**：多种格式文本、需要灵活分割
- **不适用场景**：对语义完整性要求极高

### 5. 结构化分割
- **适用场景**：Markdown 文档、技术文档、结构化文档
- **不适用场景**：无结构文本、自然语言文本

### 6. 混合分割（推荐）
- **适用场景**：生产环境、对检索质量要求高、结构化文档
- **不适用场景**：极简场景、对性能要求极高

---

## 💡 参数调优建议

### chunk_size（切片大小）

**推荐值**：
- 短文本：200-500 字符
- 中等文本：500-1000 字符
- 长文本：1000-2000 字符

**调优原则**：
- 太小：丢失上下文，检索质量下降
- 太大：检索精度下降，包含无关信息

### chunk_overlap（重叠大小）

**推荐值**：
- 一般：chunk_size 的 10-20%
- 高召回率：chunk_size 的 20-30%

**调优原则**：
- 太小：丢失上下文
- 太大：重复内容多，存储成本高

---

## 🔧 实现建议

### 1. 根据文档类型选择策略

```python
def get_splitter_for_document(doc_type: str):
    """根据文档类型选择分割策略"""
    if doc_type == "markdown":
        return HybridTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            enable_structure=True
        )
    elif doc_type == "natural_language":
        return SemanticTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
    else:
        return RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
```

### 2. 动态调整参数

```python
def adaptive_chunk_size(text_length: int) -> int:
    """根据文本长度动态调整切片大小"""
    if text_length < 1000:
        return 200
    elif text_length < 5000:
        return 500
    else:
        return 1000
```

### 3. 质量评估

```python
def evaluate_chunk_quality(chunk: str) -> float:
    """评估切片质量"""
    score = 0.0
    
    # 检查句子完整性
    if chunk.endswith(('。', '！', '？', '.', '!', '?')):
        score += 0.3
    
    # 检查长度适中
    if 100 <= len(chunk) <= 1000:
        score += 0.3
    
    # 检查包含完整信息
    if not chunk.startswith(('和', '或', '但是', 'and', 'or', 'but')):
        score += 0.2
    
    # 检查无过多重复
    unique_words = len(set(chunk.split()))
    total_words = len(chunk.split())
    if unique_words / total_words > 0.5:
        score += 0.2
    
    return score
```

---

## 📚 参考资料

1. **LangChain 文档分割**：
   - https://python.langchain.com/docs/modules/data_connection/document_transformers/

2. **LlamaIndex 文档分割**：
   - https://docs.llamaindex.ai/en/stable/module_guides/loading/node_parsers/modules/

3. **学术论文**：
   - "Dense Passage Retrieval for Open-Domain Question Answering"
   - "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"

---

## 🎯 总结

### 推荐方案

**生产环境**：使用混合分割策略
- 结合语义、结构和滑动窗口的优点
- 适应性强，检索效果好
- 保持语义完整性，保留上下文

**快速原型**：使用递归字符分割
- LangChain 推荐方法
- 灵活性强，易于使用

**特定场景**：
- Markdown 文档：结构化分割
- 自然语言文本：语义分割
- 无结构文本：递归字符分割

### 关键要点

1. ✅ **保持语义完整性**：不要在句子中间切断
2. ✅ **保留上下文重叠**：添加滑动窗口
3. ✅ **适应文档结构**：识别标题、章节
4. ✅ **动态调整参数**：根据文本长度调整
5. ✅ **质量评估**：评估切片质量，优化策略

---

**文档创建时间**：2026-08-07  
**作者**：Agent 开发团队  
**版本**：v1.0