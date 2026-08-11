"""
Agent 全局状态定义

本模块定义了 LangGraph StateGraph 所需的全局状态结构。
所有 Agent 节点共享此状态，实现状态在节点间的传递和更新。

状态设计原则：
1. 不可变性：状态更新遵循不可变原则，每次更新返回新状态
2. 类型安全：使用 TypedDict 和 Annotated 确保类型安全
3. 可扩展性：状态字段可随时扩展，不影响现有节点
4. 可序列化：状态可序列化存储到 PostgreSQL checkpoint

使用方式：
    from app.agent.core.state import AgentState
    
    def my_node(state: AgentState) -> dict:
        # 读取状态
        messages = state["messages"]
        
        # 返回更新
        return {"messages": [...new_messages]}
"""
from typing import TypedDict, Annotated, List, Dict, Any, Optional, Literal
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    Agent 全局状态类
    
    这是 LangGraph StateGraph 的核心状态结构，所有节点共享此状态。
    状态字段分为以下几类：
    
    1. 对话相关：
       - messages: 完整的对话历史
       - current_input: 用户当前输入
       - current_output: Agent 当前输出
    
    2. 工具相关：
       - tool_calls: 待执行的工具调用列表
       - tool_results: 工具执行结果
       - available_tools: 可用工具列表
    
    3. 记忆相关：
       - working_memory: 工作记忆（当前上下文）
       - short_term_memory: 短期记忆摘要
       - long_term_structured: 长期结构化记忆
       - long_term_semantic: 长期语义记忆检索结果
    
    4. 执行控制：
       - iteration_count: 当前迭代次数
       - max_iterations: 最大迭代次数
       - should_continue: 是否继续执行
       - next_action: 下一步动作
    
    5. 错误处理：
       - errors: 错误信息列表
       - retry_count: 重试次数
       - max_retries: 最大重试次数
    
    6. 元数据：
       - session_id: 会话 ID
       - user_id: 用户 ID
       - metadata: 其他元数据
    """
    
    # ==================== 对话相关 ====================
    
    messages: Annotated[List[BaseMessage], add_messages]
    """
    完整的对话历史
    
    使用 add_messages reducer 确保消息按顺序追加，不会覆盖。
    包含所有角色的消息：system、user、assistant、tool。
    
    示例：
        [SystemMessage(...), HumanMessage(...), AIMessage(...)]
    """
    
    current_input: str
    """
    用户当前输入
    
    原始用户输入文本，用于后续处理和分析。
    """
    
    current_output: Optional[str]
    """
    Agent 当前输出
    
    Agent 生成的最终响应文本，将在流程结束时返回给用户。
    """
    
    reasoning_steps: Optional[List[Dict[str, Any]]]
    """
    推理步骤列表
    
    记录Agent的完整推理过程，包括：
    - 分析用户输入
    - 调用大模型进行推理
    - 决定是否需要工具调用
    - 执行工具并获取结果
    - 生成最终回答
    
    每个步骤包含：
    - step: 步骤编号
    - action: 动作描述
    - content: 详细内容
    """
    
    # ==================== 工具相关 ====================
    
    tool_calls: List[Dict[str, Any]]
    """
    待执行的工具调用列表
    
    格式：
        [
            {
                "name": "calculator",
                "args": {"expression": "2 + 2"},
                "id": "call_123"
            }
        ]
    """
    
    tool_results: List[Dict[str, Any]]
    """
    工具执行结果列表
    
    格式：
        [
            {
                "tool_call_id": "call_123",
                "name": "calculator",
                "result": "4",
                "error": None
            }
        ]
    """
    
    available_tools: List[str]
    """
    可用工具列表
    
    当前会话可用的工具名称列表，用于工具选择和权限控制。
    """
    
    # ==================== 记忆相关 ====================
    
    working_memory: Dict[str, Any]
    """
    工作记忆（进程内存 + 上下文滑动窗口）
    
    存储当前对话上下文的关键信息：
    - 最近 N 轮对话的摘要
    - 当前话题和意图
    - 临时变量和中间结果
    
    示例：
        {
            "recent_context": "用户询问了 Python 编程问题...",
            "current_topic": "Python 基础语法",
            "user_intent": "学习 Python",
            "temp_vars": {"language": "Python"}
        }
    """
    
    short_term_memory: Dict[str, Any]
    """
    短期记忆（Redis 存储）
    
    存储会话级别的临时信息，支持 TTL 过期：
    - 会话摘要
    - 提取的实体信息
    - 用户偏好（临时）
    
    示例：
        {
            "session_summary": "本次会话讨论了...",
            "entities": ["Python", "编程", "学习"],
            "user_preferences": {"language": "zh"}
        }
    """
    
    long_term_structured: Dict[str, Any]
    """
    长期结构化记忆（PostgreSQL 存储）
    
    存储持久化的结构化信息：
    - 用户长期偏好
    - 历史重要结论
    - 关键事实和知识
    
    示例：
        {
            "user_profile": {
                "name": "张三",
                "interests": ["AI", "编程"],
                "expertise_level": "intermediate"
            },
            "historical_conclusions": ["用户偏好使用 Python"],
            "key_facts": ["用户是开发者"]
        }
    """
    
    long_term_semantic: List[Dict[str, Any]]
    """
    长期语义记忆（Qdrant 向量检索）
    
    从向量数据库检索的相关对话片段和经验总结：
    
    示例：
        [
            {
                "content": "之前讨论过类似问题...",
                "score": 0.85,
                "metadata": {"session_id": "xxx", "timestamp": "..."}
            }
        ]
    """
    
    # ==================== 执行控制 ====================
    
    iteration_count: int
    """
    当前迭代次数
    
    用于控制 Agent 循环执行次数，防止无限循环。
    初始值：0，每次迭代 +1。
    """
    
    max_iterations: int
    """
    最大迭代次数
    
    Agent 执行循环的最大次数限制，默认 10。
    超过此次数将强制终止并返回当前结果。
    """
    
    should_continue: bool
    """
    是否继续执行
    
    控制循环是否继续的标志：
    - True: 继续执行下一轮
    - False: 结束执行，返回结果
    """
    
    next_action: Literal["reasoning", "tool_call", "respond", "error"]
    """
    下一步动作
    
    指定下一个节点应该执行的动作：
    - "reasoning": 思考规划
    - "tool_call": 调用工具
    - "respond": 生成响应
    - "error": 处理错误
    """
    
    # ==================== 错误处理 ====================
    
    errors: List[Dict[str, Any]]
    """
    错误信息列表
    
    记录执行过程中发生的所有错误：
    
    示例：
        [
            {
                "node": "tool_executor",
                "error": "Connection timeout",
                "timestamp": "2026-08-06T10:00:00",
                "retry_count": 1
            }
        ]
    """
    
    retry_count: int
    """
    当前重试次数
    
    记录当前操作的重试次数，用于错误恢复。
    """
    
    max_retries: int
    """
    最大重试次数
    
    错误重试的最大次数限制，默认 3。
    """
    
    # ==================== 元数据 ====================
    
    session_id: str
    """
    会话 ID
    
    唯一标识当前会话，用于记忆存储和日志追踪。
    """
    
    user_id: Optional[str]
    """
    用户 ID
    
    标识用户身份，用于个性化记忆和权限控制。
    """
    
    knowledge_base_id: Optional[str]
    """
    知识库 ID
    
    指定要检索的知识库，用于 RAG 检索。
    """
    
    document_ids: Optional[List[str]]
    """
    文档 ID 列表
    
    指定要检索的具体文档，用于精确检索。
    如果为空，则检索整个知识库。
    """
    
    metadata: Dict[str, Any]
    """
    其他元数据
    
    存储额外的上下文信息：
    - 请求来源
    - 时间戳
    - 自定义参数
    
    示例：
        {
            "source": "web",
            "timestamp": "2026-08-06T10:00:00",
            "custom_params": {"key": "value"}
        }
    """


def create_initial_state(
    session_id: str,
    user_input: str,
    user_id: Optional[str] = None,
    knowledge_base_id: Optional[str] = None,
    document_ids: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> AgentState:
    """
    创建初始状态
    
    初始化 Agent 状态，设置默认值和必要字段。
    从数据库加载历史消息，实现会话记忆。
    
    Args:
        session_id: 会话 ID
        user_input: 用户输入文本
        user_id: 用户 ID（可选）
        knowledge_base_id: 知识库 ID（可选）
        document_ids: 文档ID列表（可选）
        metadata: 其他元数据（可选）
    
    Returns:
        AgentState: 初始化后的状态对象
    
    使用示例：
        >>> state = create_initial_state(
        ...     session_id="session_123",
        ...     user_input="你好，请帮我分析这个问题",
        ...     user_id="user_456"
        ... )
        >>> print(state["current_input"])
        '你好，请帮我分析这个问题'
    """
    # 从数据库加载历史消息
    from app.models.database import SessionLocal
    from app.models.tables import Message, MessageRole
    from langchain_core.messages import HumanMessage, AIMessage
    import logging
    
    logger = logging.getLogger(__name__)
    
    messages = []
    
    try:
        db = SessionLocal()
        # 查询该会话的历史消息，按时间升序排列，限制最近20条
        history_messages = db.query(Message).filter(
            Message.session_id == session_id
        ).order_by(Message.created_at.asc()).limit(20).all()
        
        # 转换为 LangChain 消息格式
        for msg in history_messages:
            if msg.role == MessageRole.USER:
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == MessageRole.ASSISTANT:
                messages.append(AIMessage(content=msg.content))
        
        logger.info(f"Loaded {len(messages)} historical messages for session {session_id}")
        
    except Exception as e:
        logger.error(f"Failed to load historical messages: {e}")
    finally:
        db.close()
    
    return AgentState(
        # 对话相关
        messages=messages,
        current_input=user_input,
        current_output=None,
        
        # 工具相关
        tool_calls=[],
        tool_results=[],
        available_tools=["calculator", "web_search", "python_executor"],
        
        # 记忆相关
        working_memory={},
        short_term_memory={},
        long_term_structured={},
        long_term_semantic=[],
        
        # 执行控制
        iteration_count=0,
        max_iterations=10,
        should_continue=True,
        next_action="reasoning",
        
        # 错误处理
        errors=[],
        retry_count=0,
        max_retries=3,
        
        # 元数据
        session_id=session_id,
        user_id=user_id,
        knowledge_base_id=knowledge_base_id,
        document_ids=document_ids,
        metadata=metadata or {}
    )