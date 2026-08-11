"""
Agent 核心执行器

本模块使用 LangGraph StateGraph 实现 Agent 核心执行链路：
用户输入 → 预处理 → 思考规划 → 工具调用 → 结果汇总 → 记忆写入

设计原则：
- 状态机模式：使用 StateGraph 管理状态流转
- 节点化设计：每个处理步骤是一个独立节点
- 可中断恢复：支持 checkpoint 断点续跑
- 可观测性：集成 LangSmith 追踪

使用方式：
    from app.agent.core.agent_executor import AgentExecutor
    
    executor = AgentExecutor()
    result = await executor.run(
        session_id="session_123",
        user_input="你好"
    )
"""
from typing import Dict, Any, Optional, AsyncIterator
import logging
import json
from urllib.parse import quote_plus
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

try:
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from psycopg_pool import AsyncConnectionPool
    CHECKPOINT_AVAILABLE = True
except ImportError:
    CHECKPOINT_AVAILABLE = False
    logger.warning("langgraph-checkpoint-postgres not installed, checkpoint disabled")

from app.agent.core.state import AgentState, create_initial_state
from app.agent.memory.memory_system import MemorySystem
from app.agent.prompts.prompt_engine import PromptEngine
from app.agent.tools.registry import get_tool_registry, register_all_tools
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AgentExecutor:
    """
    Agent 核心执行器
    
    基于 LangGraph StateGraph 实现完整的 Agent 执行流程。
    
    使用方式：
        # 方式1：同步初始化（checkpoint可能未完全初始化）
        executor = AgentExecutor()
        
        # 方式2：异步初始化（推荐，确保checkpoint完全初始化）
        executor = await AgentExecutor.create()
    """
    
    def __init__(self):
        """初始化 Agent 执行器"""
        self.settings = get_settings()
        self.prompt_engine = PromptEngine()
        
        # 初始化工具注册中心
        register_all_tools()
        self.tool_registry = get_tool_registry()
        
        # 初始化 LLM
        self.llm = ChatOpenAI(
            api_key=self.settings.LLM_API_KEY,
            base_url=self.settings.LLM_BASE_URL,
            model=self.settings.LLM_MODEL_NAME,
            temperature=self.settings.LLM_TEMPERATURE,
            max_tokens=self.settings.LLM_MAX_TOKENS,
            timeout=self.settings.LLM_TIMEOUT
        )
        
        # 配置 checkpoint（PostgreSQL）- 必须在构建图之前
        self.checkpointer = None
        self._connection_pool = None
        
        # 图将在 create() 方法中构建
        self.graph = None
        
        # 标记checkpoint是否已初始化
        self._checkpoint_initialized = False
    
    @classmethod
    async def create(cls) -> 'AgentExecutor':
        """
        异步工厂方法：创建并初始化 Agent 执行器
        
        推荐使用此方法，确保 checkpoint 完全初始化。
        
        Returns:
            初始化完成的 AgentExecutor 实例
        
        使用示例：
            executor = await AgentExecutor.create()
        """
        executor = cls()
        
        # 初始化 checkpoint（使用连接池）
        if CHECKPOINT_AVAILABLE:
            try:
                # 构建连接字符串
                encoded_password = quote_plus(executor.settings.PG_PASSWORD)
                connection_string = (
                    f"postgresql://{executor.settings.PG_USER}:{encoded_password}"
                    f"@{executor.settings.PG_HOST}:{executor.settings.PG_PORT}/{executor.settings.PG_DB}"
                )
                
                # 创建连接池（自动管理连接）
                executor._connection_pool = AsyncConnectionPool(
                    connection_string,
                    min_size=1,
                    max_size=10,
                    open=False
                )
                
                # 打开连接池
                await executor._connection_pool.open()
                
                # 创建 checkpointer（使用连接池）
                executor.checkpointer = AsyncPostgresSaver(executor._connection_pool)
                
                # 初始化 checkpoint 表
                await executor.checkpointer.setup()
                
                executor._checkpoint_initialized = True
                logger.info("Checkpoint tables initialized successfully with connection pool")
                
            except Exception as e:
                logger.error(f"Failed to initialize checkpoint: {e}", exc_info=True)
                logger.warning("Continuing without checkpoint (no persistence)")
                executor.checkpointer = None
                executor._connection_pool = None
        
        # 构建 StateGraph（在 checkpoint 初始化之后）
        executor.graph = executor._build_graph()
        
        return executor
    
    def _build_graph(self) -> StateGraph:
        """
        构建状态图
        
        定义 Agent 执行的完整流程：
        
        1. preprocess_node: 预处理用户输入
        2. reasoning_node: 思考规划
        3. tool_executor_node: 工具调用
        4. respond_node: 生成响应
        5. memory_writer_node: 写入记忆
        6. reflection_node: 反思检查
        
        Returns:
            StateGraph 实例
        """
        # 创建状态图
        workflow = StateGraph(AgentState)
        
        # 添加节点
        workflow.add_node("preprocess", self._preprocess_node)
        workflow.add_node("reasoning", self._reasoning_node)
        workflow.add_node("tool_executor", self._tool_executor_node)
        workflow.add_node("respond", self._respond_node)
        workflow.add_node("memory_writer", self._memory_writer_node)
        workflow.add_node("reflection", self._reflection_node)
        
        # 设置入口点
        workflow.set_entry_point("preprocess")
        
        # 添加边（定义流程）
        workflow.add_edge("preprocess", "reasoning")
        
        # 条件分支：根据 next_action 决定下一步
        workflow.add_conditional_edges(
            "reasoning",
            self._should_continue,
            {
                "tool_call": "tool_executor",
                "respond": "respond",
                "error": END
            }
        )
        
        workflow.add_edge("tool_executor", "reasoning")
        workflow.add_edge("respond", "reflection")
        
        # 条件分支：反思是否通过
        workflow.add_conditional_edges(
            "reflection",
            self._check_reflection,
            {
                "pass": "memory_writer",
                "retry": "reasoning"
            }
        )
        
        workflow.add_edge("memory_writer", END)
        
        # 编译图
        if self.checkpointer:
            app = workflow.compile(checkpointer=self.checkpointer)
        else:
            app = workflow.compile()
        
        logger.info("Agent graph built successfully")
        return app
    
    async def _preprocess_node(self, state: AgentState) -> Dict[str, Any]:
        """
        预处理节点
        
        处理步骤：
        1. 初始化记忆系统
        2. 加载历史记忆
        3. 构建初始上下文
        
        Args:
            state: 当前状态
        
        Returns:
            状态更新字典
        """
        logger.info(f"Preprocessing for session: {state['session_id']}")
        
        # 初始化记忆系统
        memory = MemorySystem(
            session_id=state['session_id'],
            user_id=state.get('user_id')
        )
        
        # 加载短期记忆
        session_summary = await memory.retrieve_short_term_memory("summary")
        
        # 加载长期结构化记忆
        user_profile = await memory.long_term_structured.get_user_profile()
        
        # 更新状态
        updates = {
            "working_memory": {
                "session_summary": session_summary,
                "user_profile": user_profile
            },
            "iteration_count": state['iteration_count'] + 1
        }
        
        await memory.close()
        
        return updates
    
    async def _reasoning_node(self, state: AgentState) -> Dict[str, Any]:
        """
        思考规划节点
        
        处理步骤：
        1. 构建系统提示词
        2. 调用 LLM 进行推理
        3. 判断是否需要工具调用
        4. 更新状态
        
        Args:
            state: 当前状态
        
        Returns:
            状态更新字典
        """
        logger.info(f"Reasoning for iteration: {state['iteration_count']}")
        
        # 初始化推理步骤列表
        reasoning_steps = state.get('reasoning_steps', [])
        
        # 记录推理步骤1：分析用户输入
        reasoning_steps.append({
            "step": len(reasoning_steps) + 1,
            "action": "分析用户输入",
            "content": f"用户提问：{state['current_input']}"
        })
        
        # 构建系统提示词
        system_prompt = self.prompt_engine.build_system_prompt(
            role="assistant",
            context={
                "user_name": state.get('user_id', '用户'),
                "conversation_topic": state['working_memory'].get('current_topic', '未知'),
                "user_intent": state['working_memory'].get('user_intent', '未知')
            },
            available_tools=state['available_tools'],
            memory_hints=str(state['working_memory'].get('session_summary', ''))
        )
        
        # 检查是否需要从知识库检索
        rag_context = await self._retrieve_from_knowledge_base(
            state['current_input'], 
            state.get('knowledge_base_id'),
            state.get('document_ids')
        )
        if rag_context:
            system_prompt += f"\n\n相关知识库内容：\n{rag_context}"
            reasoning_steps.append({
                "step": len(reasoning_steps) + 1,
                "action": "检索知识库",
                "content": f"已从知识库检索到相关信息并添加到上下文中。请基于知识库内容回答用户问题，不要尝试访问本地文件或使用document_parser工具。"
            })
        
        # 构建消息列表
        messages = [SystemMessage(content=system_prompt)]
        
        # 添加历史消息
        messages.extend(state['messages'])
        
        # 添加当前用户输入
        messages.append(HumanMessage(content=state['current_input']))
        
        # 记录推理步骤2：调用LLM进行推理
        reasoning_steps.append({
            "step": len(reasoning_steps) + 1,
            "action": "调用大模型进行推理",
            "content": "正在分析问题并生成回答..."
        })
        
        # 调用 LLM
        response = await self.llm.ainvoke(messages)
        
        # 检查是否需要工具调用
        tool_call = self.prompt_engine.extract_tool_call(response.content)
        
        # 记录推理步骤3：判断是否需要工具
        if tool_call:
            reasoning_steps.append({
                "step": len(reasoning_steps) + 1,
                "action": "决定调用工具",
                "content": f"需要调用工具：{tool_call.get('tool_name')}，参数：{tool_call.get('tool_args')}"
            })
        else:
            reasoning_steps.append({
                "step": len(reasoning_steps) + 1,
                "action": "直接生成回答",
                "content": "不需要调用工具，直接生成回答"
            })
        
        updates = {
            "messages": [response],
            "reasoning_steps": reasoning_steps
        }
        
        if tool_call:
            updates["tool_calls"] = [tool_call]
            updates["next_action"] = "tool_call"
        else:
            updates["current_output"] = response.content
            updates["next_action"] = "respond"
        
        return updates
    
    async def _retrieve_from_knowledge_base(
        self, 
        query: str, 
        knowledge_base_id: Optional[str] = None,
        document_ids: Optional[list] = None
    ) -> Optional[str]:
        """
        从知识库检索相关信息
        
        Args:
            query: 用户查询
            knowledge_base_id: 知识库ID（可选）
            document_ids: 文档ID列表（可选）
        
        Returns:
            检索到的上下文，如果没有则返回None
        """
        try:
            from app.agent.rag.agentic_rag import AgenticRAG
            from app.models.database import SessionLocal
            from app.models.tables import KnowledgeBase
            
            db = SessionLocal()
            try:
                # 根据knowledge_base_id获取知识库
                if knowledge_base_id:
                    kb = db.query(KnowledgeBase).filter(
                        KnowledgeBase.id == knowledge_base_id,
                        KnowledgeBase.is_active == True
                    ).first()
                else:
                    # 如果没有指定，获取默认知识库
                    kb = db.query(KnowledgeBase).filter(
                        KnowledgeBase.is_active == True
                    ).first()
                
                if not kb:
                    logger.info(f"Knowledge base not found: {knowledge_base_id}")
                    return None
                
                # 使用Agentic RAG检索
                rag = AgenticRAG(collection_name=kb.collection_name)
                
                # 判断是否需要检索
                if not rag.should_retrieve(query):
                    return None
                
                # 执行检索（如果有document_ids，传递过滤条件）
                retrieval_result = rag.retrieve(
                    query,
                    filter_conditions={"document_id": {"$in": document_ids}} if document_ids else None
                )
                
                if not retrieval_result.get('results'):
                    return None
                
                # 格式化检索结果
                context = rag.format_context(retrieval_result['results'], max_length=1000)
                
                logger.info(f"Retrieved {len(retrieval_result['results'])} chunks from knowledge base {kb.name}")
                
                return context
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to retrieve from knowledge base: {e}")
            return None
    
    async def _tool_executor_node(self, state: AgentState) -> Dict[str, Any]:
        """
        工具执行节点
        
        处理步骤：
        1. 执行工具调用
        2. 收集结果
        3. 处理错误
        4. 更新状态
        
        Args:
            state: 当前状态
        
        Returns:
            状态更新字典
        """
        logger.info(f"Executing tools: {len(state['tool_calls'])} calls")
        
        # 获取推理步骤列表
        reasoning_steps = state.get('reasoning_steps', [])
        
        tool_results = []
        
        for tool_call in state['tool_calls']:
            tool_name = tool_call.get('tool_name')
            tool_args = tool_call.get('tool_args', {})
            
            # 记录推理步骤：开始执行工具
            reasoning_steps.append({
                "step": len(reasoning_steps) + 1,
                "action": f"执行工具：{tool_name}",
                "content": f"正在调用 {tool_name} 工具，参数：{json.dumps(tool_args, ensure_ascii=False)}"
            })
            
            try:
                # 使用工具注册中心执行工具
                result = await self.tool_registry.execute(tool_name, **tool_args)
                
                # 记录工具调用结果
                tool_results.append({
                    "tool_call_id": tool_call.get('id'),
                    "name": tool_name,
                    "result": result.output if result.success else None,
                    "error": result.error,
                    "success": result.success,
                    "metadata": result.metadata
                })
                
                # 记录推理步骤：工具执行结果
                if result.success:
                    reasoning_steps.append({
                        "step": len(reasoning_steps) + 1,
                        "action": f"工具执行成功",
                        "content": f"{tool_name} 工具返回结果：\n{str(result.output)[:500]}..."  # 限制长度
                    })
                    logger.info(f"Tool {tool_name} executed successfully")
                else:
                    reasoning_steps.append({
                        "step": len(reasoning_steps) + 1,
                        "action": f"工具执行失败",
                        "content": f"{tool_name} 工具执行失败：{result.error}"
                    })
                    logger.error(f"Tool {tool_name} failed: {result.error}")
                
            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                
                tool_results.append({
                    "tool_call_id": tool_call.get('id'),
                    "name": tool_name,
                    "result": None,
                    "error": str(e),
                    "success": False
                })
                
                # 记录推理步骤：工具执行异常
                reasoning_steps.append({
                    "step": len(reasoning_steps) + 1,
                    "action": f"工具执行异常",
                    "content": f"{tool_name} 工具执行异常：{str(e)}"
                })
        
        return {
            "tool_results": tool_results,
            "tool_calls": [],
            "reasoning_steps": reasoning_steps,
            "next_action": "reasoning"
        }
    
    async def _respond_node(self, state: AgentState) -> Dict[str, Any]:
        """
        响应生成节点
        
        处理步骤：
        1. 整合所有信息
        2. 生成最终响应
        3. 格式化输出
        
        Args:
            state: 当前状态
        
        Returns:
            状态更新字典
        """
        logger.info("Generating final response")
        
        # 如果已经有输出，直接返回
        if state.get('current_output'):
            return {}
        
        # 否则从最后的 AI 消息中提取
        last_message = state['messages'][-1] if state['messages'] else None
        
        if last_message and hasattr(last_message, 'content'):
            return {"current_output": last_message.content}
        
        return {"current_output": "抱歉，我无法生成有效的响应。"}
    
    async def _memory_writer_node(self, state: AgentState) -> Dict[str, Any]:
        """
        记忆写入节点
        
        处理步骤：
        1. 提取关键信息
        2. 写入四级记忆
        3. 更新会话摘要
        
        Args:
            state: 当前状态
        
        Returns:
            状态更新字典
        """
        logger.info(f"Writing memory for session: {state['session_id']}")
        
        memory = MemorySystem(
            session_id=state['session_id'],
            user_id=state.get('user_id')
        )
        
        # 存储到短期记忆
        await memory.store_short_term_memory(
            "last_interaction",
            {
                "input": state['current_input'],
                "output": state['current_output'],
                "timestamp": state['metadata'].get('timestamp')
            },
            ttl=7200
        )
        
        # 更新会话摘要（简化版）
        summary = f"用户询问：{state['current_input'][:100]}"
        await memory.store_short_term_memory(
            "summary",
            {"text": summary},
            ttl=7200
        )
        
        await memory.close()
        
        return {}
    
    async def _reflection_node(self, state: AgentState) -> Dict[str, Any]:
        """
        反思节点
        
        处理步骤：
        1. 检查响应质量
        2. 识别错误和幻觉
        3. 决定是否需要重试
        
        Args:
            state: 当前状态
        
        Returns:
            状态更新字典
        """
        logger.info("Reflecting on response quality")
        
        # 简化版反思：检查是否有明显错误
        output = state.get('current_output', '')
        
        # 检查是否包含错误标记
        has_error = any([
            "错误" in output,
            "失败" in output,
            "抱歉" in output and "无法" in output
        ])
        
        # 检查重试次数
        retry_count = state.get('retry_count', 0)
        max_retries = state.get('max_retries', 3)
        
        if has_error and retry_count < max_retries:
            return {
                "retry_count": retry_count + 1,
                "next_action": "reasoning"
            }
        
        return {"next_action": "memory_writer"}
    
    def _should_continue(self, state: AgentState) -> str:
        """
        判断是否继续执行
        
        Args:
            state: 当前状态
        
        Returns:
            下一个节点名称
        """
        # 检查迭代次数
        if state['iteration_count'] >= state['max_iterations']:
            logger.warning("Max iterations reached")
            return "respond"
        
        # 检查下一步动作
        return state.get('next_action', 'respond')
    
    def _check_reflection(self, state: AgentState) -> str:
        """
        检查反思结果
        
        Args:
            state: 当前状态
        
        Returns:
            下一个节点名称
        """
        next_action = state.get('next_action', 'memory_writer')
        
        if next_action == 'reasoning':
            return 'retry'
        
        return 'pass'
    
    async def run(
        self,
        session_id: str,
        user_input: str,
        user_id: Optional[str] = None,
        knowledge_base_id: Optional[str] = None,
        document_ids: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        运行 Agent
        
        Args:
            session_id: 会话 ID
            user_input: 用户输入
            user_id: 用户 ID（可选）
            knowledge_base_id: 知识库 ID（可选）
            metadata: 其他元数据（可选）
        
        Returns:
            执行结果字典
        """
        logger.info(f"Running agent for session: {session_id}")
        
        # 确保 graph 已构建（如果未使用 create() 方法）
        if self.graph is None:
            logger.warning("Graph not initialized, building without checkpoint")
            self.graph = self._build_graph()
        
        # 创建初始状态
        initial_state = create_initial_state(
            session_id=session_id,
            user_input=user_input,
            user_id=user_id,
            knowledge_base_id=knowledge_base_id,
            document_ids=document_ids,
            metadata=metadata
        )
        
        # 配置执行参数
        config = {
            "configurable": {
                "thread_id": session_id
            }
        }
        
        try:
            # 执行图
            result = await self.graph.ainvoke(initial_state, config=config)
            
            return {
                "success": True,
                "output": result.get('current_output', ''),
                "messages": result.get('messages', []),
                "metadata": {
                    "iterations": result.get('iteration_count', 0),
                    "tool_calls": len(result.get('tool_results', []))
                }
            }
        
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "output": "抱歉，处理您的请求时出现错误。"
            }
    
    async def stream(
        self,
        session_id: str,
        user_input: str,
        user_id: Optional[str] = None,
        knowledge_base_id: Optional[str] = None,
        document_ids: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        流式运行 Agent
        
        支持 SSE 流式输出。
        
        Args:
            session_id: 会话 ID
            user_input: 用户输入
            user_id: 用户 ID（可选）
            knowledge_base_id: 知识库 ID（可选）
            metadata: 其他元数据（可选）
        
        Yields:
            状态更新字典
        """
        logger.info(f"Streaming agent for session: {session_id}")
        
        # 确保 graph 已构建（如果未使用 create() 方法）
        if self.graph is None:
            logger.warning("Graph not initialized, building without checkpoint")
            self.graph = self._build_graph()
        
        # 创建初始状态
        initial_state = create_initial_state(
            session_id=session_id,
            user_input=user_input,
            user_id=user_id,
            knowledge_base_id=knowledge_base_id,
            document_ids=document_ids,
            metadata=metadata
        )
        
        # 配置执行参数
        config = {
            "configurable": {
                "thread_id": session_id
            }
        }
        
        try:
            # 流式执行图
            async for event in self.graph.astream(initial_state, config=config):
                # 确保事件包含 reasoning_steps
                if isinstance(event, dict):
                    # 如果事件中有状态更新，提取 reasoning_steps
                    for node_name, state_update in event.items():
                        if isinstance(state_update, dict):
                            # 确保 reasoning_steps 在状态中
                            if 'reasoning_steps' not in state_update and 'reasoning_steps' in initial_state:
                                state_update['reasoning_steps'] = initial_state.get('reasoning_steps', [])
                
                yield {
                    "event": "update",
                    "data": event
                }
            
            # 返回最终结果
            yield {
                "event": "done",
                "data": {"message": "Agent execution completed"}
            }
        
        except Exception as e:
            logger.error(f"Agent streaming failed: {e}")
            
            yield {
                "event": "error",
                "data": {"error": str(e)}
            }
    
    async def close(self):
        """
        清理资源
        
        关闭连接池和其他资源
        """
        if self._connection_pool:
            try:
                await self._connection_pool.close()
                logger.info("Checkpoint connection pool closed")
            except Exception as e:
                logger.error(f"Failed to close connection pool: {e}")