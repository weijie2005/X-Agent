"""
提示词工程系统

本模块实现了新版提示词工程架构：
- 结构化系统 Prompt
- 动态上下文注入
- 角色约束
- 输出格式强制规范

设计原则：
- 模板化：使用模板引擎管理提示词
- 动态化：根据上下文动态生成提示词
- 结构化：强制输出格式，便于解析
- 可配置：支持多角色、多场景配置

使用方式：
    from app.agent.prompts.prompt_engine import PromptEngine
    
    engine = PromptEngine()
    
    # 生成系统提示词
    system_prompt = engine.build_system_prompt(
        role="assistant",
        context={"user_name": "张三"}
    )
"""
from typing import Dict, Any, List, Optional
from string import Template
import json
from datetime import datetime


class PromptTemplates:
    """
    提示词模板库
    
    存储所有预定义的提示词模板。
    """
    
    # ==================== 系统提示词模板 ====================
    
    SYSTEM_PROMPT_BASE = """
你是一个专业的 AI 助手，具有以下能力和特点：

## 核心能力
1. **智能对话**：理解用户意图，提供准确、有帮助的回答
2. **工具调用**：根据需要调用计算器、搜索引擎、代码执行等工具
3. **记忆管理**：记住用户偏好和历史对话，提供个性化服务
4. **自我反思**：检查回答的准确性，避免错误和幻觉

## 行为准则
- 准确性优先：确保回答准确、可靠
- 用户友好：用清晰、易懂的语言回答
- 工具优先：遇到计算、搜索等任务时优先使用工具
- 承认限制：不确定时明确说明，不编造信息

## 输出格式
- 使用 Markdown 格式
- 代码块使用正确的语法高亮
- 复杂内容使用列表和表格组织

## 图表生成规则

### ECharts 图表（统计图表）
当需要展示数据可视化时，使用 ECharts 图表。格式如下：

```echarts
{
  "title": {"text": "图表标题"},
  "xAxis": {"type": "category", "data": ["数据1", "数据2"]},
  "yAxis": {"type": "value"},
  "series": [{"data": [100, 200], "type": "bar"}]
}
```

**支持的图表类型**：
- `type: "bar"` - 柱状图
- `type: "line"` - 折线图
- `type: "pie"` - 饼图
- `type: "scatter"` - 散点图
- `type: "radar"` - 雷达图

**重要**：
1. 必须使用有效的 JSON 格式（双引号、正确的逗号）
2. 不要输出 HTML 代码，只输出 JSON 配置
3. 图表会自动在聊天区渲染，无需用户手动运行

### Mermaid 图表（流程图/架构图）
当需要展示流程、架构、关系时，使用 Mermaid 图表。格式如下：

```mermaid
graph TD
    A[开始] --> B{判断}
    B -->|是| C[结束]
    B -->|否| D[继续]
```

**支持的图表类型**：
- `graph TD` - 流程图（自上而下）
- `sequenceDiagram` - 时序图
- `classDiagram` - 类图
- `stateDiagram` - 状态图

**示例场景**：
- 用户问"帮我分析销售数据" → 返回 ECharts 柱状图或折线图
- 用户问"画一个登录流程图" → 返回 Mermaid 流程图
- 用户问"展示市场份额" → 返回 ECharts 饼图
"""
    
    SYSTEM_PROMPT_WITH_CONTEXT = """
$base_prompt

## 当前上下文
- **用户**：$user_name
- **会话时间**：$current_time
- **对话主题**：$conversation_topic
- **用户意图**：$user_intent

## 可用工具
$available_tools

## 工具调用规则
当需要使用工具时，请按以下JSON格式输出（不要输出其他内容）：
```json
{
    "need_tool": true,
    "tool_name": "工具名称",
    "tool_args": {"参数名": "参数值"}
}
```

**何时调用工具**：
- 需要实时信息（天气、新闻、股价等）→ 使用 web_search 工具
- 需要数学计算 → 使用 calculator 工具
- 需要执行代码 → 使用 python_executor 工具

**重要：知识库优先原则**：
- 如果系统提示词中包含"相关知识库内容"，说明已经从知识库检索到相关信息
- 此时应该基于知识库内容回答，不要尝试访问本地文件或使用document_parser工具
- document_parser工具仅用于解析用户明确指定的本地文件路径

**何时不调用工具**：
- 简单的问候和闲聊
- 通用知识问答
- 不需要实时信息的任务
- 已经从知识库检索到相关信息的情况

如果不需要调用工具，直接回答用户问题即可。

## 记忆提示
$memory_hints
"""
    
    # ==================== 角色约束模板 ====================
    
    ROLE_CONSTRAINTS = {
        "assistant": {
            "name": "AI 助手",
            "personality": "友好、专业、乐于助人",
            "expertise": "通用知识、问题解答、任务协助",
            "communication_style": "清晰、准确、有逻辑"
        },
        "expert": {
            "name": "领域专家",
            "personality": "严谨、深入、专业",
            "expertise": "特定领域深度知识",
            "communication_style": "专业术语、深入分析"
        },
        "teacher": {
            "name": "教师",
            "personality": "耐心、鼓励、循循善诱",
            "expertise": "知识传授、学习指导",
            "communication_style": "通俗易懂、举例说明"
        }
    }
    
    # ==================== 工具调用提示词 ====================
    
    TOOL_CALL_PROMPT = """
根据用户输入，判断是否需要调用工具。

可用工具：
$tool_descriptions

工具调用规则：
1. 计算问题 → 使用 calculator 工具
2. 需要实时信息 → 使用 web_search 工具
3. 需要执行代码 → 使用 python_executor 工具
4. 不确定时 → 不调用工具，直接回答

如果需要调用工具，请按以下格式输出：
```json
{
    "need_tool": true,
    "tool_name": "工具名称",
    "tool_args": {"参数名": "参数值"}
}
```

如果不需要调用工具，请输出：
```json
{
    "need_tool": false
}
```
"""
    
    # ==================== 反思机制提示词 ====================
    
    REFLECTION_PROMPT = """
请检查你的回答是否符合以下标准：

## 准确性检查
- 信息是否准确？
- 是否有事实性错误？
- 是否存在幻觉或编造的内容？

## 完整性检查
- 是否完整回答了用户的问题？
- 是否遗漏了重要信息？

## 相关性检查
- 回答是否与用户问题相关？
- 是否有偏离主题的内容？

## 格式检查
- 格式是否清晰易读？
- 代码块是否正确？
- 列表和表格是否合理？

如果发现问题，请指出并提供修正建议。
如果回答合格，请确认"回答合格"。
"""
    
    # ==================== 输出格式规范 ====================
    
    OUTPUT_FORMAT_SPEC = """
## 输出格式规范

### 文本内容
- 使用 Markdown 格式
- 重要内容使用 **粗体** 或 `代码` 标记
- 长文本使用分段和列表组织

### 代码块
```语言名称
代码内容
```

### 列表
- 无序列表使用 `-` 或 `*`
- 有序列表使用数字 `1. 2. 3.`

### 表格
| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 内容 | 内容 | 内容 |

### JSON 输出（工具调用时）
```json
{
    "key": "value"
}
```
"""


class PromptEngine:
    """
    提示词引擎
    
    负责生成和管理所有提示词。
    """
    
    def __init__(self):
        """初始化提示词引擎"""
        self.templates = PromptTemplates()
    
    def build_system_prompt(
        self,
        role: str = "assistant",
        context: Optional[Dict[str, Any]] = None,
        available_tools: Optional[List[str]] = None,
        memory_hints: Optional[str] = None
    ) -> str:
        """
        构建系统提示词
        
        Args:
            role: 角色类型（assistant/expert/teacher）
            context: 上下文信息
            available_tools: 可用工具列表
            memory_hints: 记忆提示
        
        Returns:
            完整的系统提示词
        """
        # 获取角色约束
        role_info = self.templates.ROLE_CONSTRAINTS.get(role, self.templates.ROLE_CONSTRAINTS["assistant"])
        
        # 构建基础提示词
        base_prompt = f"""
{self.templates.SYSTEM_PROMPT_BASE}

## 角色设定
- **名称**：{role_info['name']}
- **性格**：{role_info['personality']}
- **专长**：{role_info['expertise']}
- **沟通风格**：{role_info['communication_style']}
"""
        
        # 如果有上下文，添加上下文信息
        if context:
            template = Template(self.templates.SYSTEM_PROMPT_WITH_CONTEXT)
            
            # 准备模板变量
            user_name = context.get("user_name", "用户")
            current_time = context.get("current_time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            conversation_topic = context.get("conversation_topic", "未识别")
            user_intent = context.get("user_intent", "未识别")
            
            # 构建工具描述
            tools_desc = self._build_tool_descriptions(available_tools or [])
            
            # 替换模板变量
            system_prompt = template.safe_substitute(
                base_prompt=base_prompt,
                user_name=user_name,
                current_time=current_time,
                conversation_topic=conversation_topic,
                user_intent=user_intent,
                available_tools=tools_desc,
                memory_hints=memory_hints or "暂无相关记忆"
            )
            
            return system_prompt
        
        return base_prompt
    
    def build_tool_call_prompt(self, available_tools: List[str]) -> str:
        """
        构建工具调用提示词
        
        Args:
            available_tools: 可用工具列表
        
        Returns:
            工具调用提示词
        """
        tool_descriptions = self._build_tool_descriptions(available_tools)
        
        template = Template(self.templates.TOOL_CALL_PROMPT)
        return template.safe_substitute(tool_descriptions=tool_descriptions)
    
    def build_reflection_prompt(self) -> str:
        """
        构建反思提示词
        
        Returns:
            反思提示词
        """
        return self.templates.REFLECTION_PROMPT
    
    def _build_tool_descriptions(self, tools: List[str]) -> str:
        """
        构建工具描述文本
        
        Args:
            tools: 工具名称列表
        
        Returns:
            工具描述文本
        """
        if not tools:
            return "暂无可用工具"
        
        descriptions = []
        for tool in tools:
            desc = self._get_tool_description(tool)
            descriptions.append(f"- **{tool}**：{desc}")
        
        return "\n".join(descriptions)
    
    def _get_tool_description(self, tool_name: str) -> str:
        """
        获取工具描述
        
        Args:
            tool_name: 工具名称
        
        Returns:
            工具描述
        """
        tool_descriptions = {
            "calculator": "执行数学计算，支持基本运算和复杂表达式",
            "web_search": "搜索互联网获取实时信息",
            "python_executor": "执行 Python 代码，用于数据处理和计算",
            "document_parser": "解析 PDF、Word、Excel 等文档",
            "memory_search": "搜索长期记忆中的相关信息"
        }
        
        return tool_descriptions.get(tool_name, "工具功能描述待补充")
    
    def format_output(self, content: str, format_type: str = "markdown") -> str:
        """
        格式化输出内容
        
        Args:
            content: 原始内容
            format_type: 格式类型（markdown/json/text）
        
        Returns:
            格式化后的内容
        """
        if format_type == "json":
            try:
                # 尝试解析 JSON
                data = json.loads(content)
                return json.dumps(data, indent=2, ensure_ascii=False)
            except json.JSONDecodeError:
                # 如果不是有效 JSON，返回原始内容
                return content
        
        return content
    
    def inject_dynamic_context(
        self,
        prompt: str,
        context: Dict[str, Any]
    ) -> str:
        """
        注入动态上下文
        
        Args:
            prompt: 原始提示词
            context: 上下文字典
        
        Returns:
            注入上下文后的提示词
        """
        template = Template(prompt)
        
        # 添加时间戳
        context["timestamp"] = datetime.now().isoformat()
        
        return template.safe_substitute(**context)
    
    def extract_tool_call(self, text: str) -> Optional[Dict[str, Any]]:
        """
        提取工具调用信息
        
        Args:
            text: LLM 输出文本
        
        Returns:
            工具调用字典，如果不存在返回 None
        """
        parsed = StructuredOutputParser.parse_json_output(text)
        
        if parsed and parsed.get("need_tool"):
            return {
                "tool_name": parsed.get("tool_name"),
                "tool_args": parsed.get("tool_args", {})
            }
        
        return None


class StructuredOutputParser:
    """
    结构化输出解析器
    
    强制 LLM 输出结构化格式，便于后续处理。
    """
    
    @staticmethod
    def parse_json_output(text: str) -> Optional[Dict[str, Any]]:
        """
        解析 JSON 输出
        
        从文本中提取 JSON 内容。
        
        Args:
            text: 包含 JSON 的文本
        
        Returns:
            解析后的字典，如果解析失败返回 None
        """
        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # 尝试从代码块中提取
        import re
        json_pattern = r'```json\s*(.*?)\s*```'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        if matches:
            try:
                return json.loads(matches[0])
            except json.JSONDecodeError:
                pass
        
        # 尝试查找 JSON 对象
        json_pattern = r'\{[^{}]*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        return None