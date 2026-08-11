"""
Agent 功能测试脚本

测试 Agent 核心功能是否正常工作。
"""
import asyncio
import sys
import os
from pathlib import Path

# 获取当前脚本的绝对路径
script_path = os.path.abspath(__file__)
# 获取脚本所在的目录
current_directory = os.path.dirname(script_path)
# 获取 backend 目录
backend_dir = Path(current_directory).parent

# 添加项目路径到 Python 路径
sys.path.insert(0, str(backend_dir))

# 本地测试时覆盖 Redis 主机名（Docker 容器名 -> localhost）
os.environ['REDIS_HOST'] = 'localhost'
os.environ['QDRANT_HOST'] = 'localhost'
os.environ['MINIO_HOST'] = 'localhost:9000'

from app.agent.core.agent_executor import AgentExecutor
from app.agent.memory.memory_system import MemorySystem
from app.agent.prompts.prompt_engine import PromptEngine


async def test_agent_executor():
    """测试 Agent 执行器"""
    print("\n=== 测试 Agent 执行器 ===")
    
    try:
        executor = AgentExecutor()
        print("✓ Agent 执行器初始化成功")
        
        # 测试简单对话
        result = await executor.run(
            session_id="test_session_001",
            user_input="你好，请介绍一下你自己",
            user_id="test_user_001"
        )
        
        if result.get("success"):
            print("✓ Agent 执行成功")
            print(f"输出: {result.get('output', '')[:100]}...")
        else:
            print(f"✗ Agent 执行失败: {result.get('error')}")
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def test_memory_system():
    """测试记忆系统"""
    print("\n=== 测试记忆系统 ===")
    
    try:
        memory = MemorySystem(
            session_id="test_session_002",
            user_id="test_user_002"
        )
        print("✓ 记忆系统初始化成功")
        
        # 测试工作记忆
        await memory.store_working_memory("test_key", "test_value")
        value = await memory.retrieve_working_memory("test_key")
        if value == "test_value":
            print("✓ 工作记忆存储和检索成功")
        else:
            print("✗ 工作记忆检索失败")
        
        # 测试短期记忆
        await memory.store_short_term_memory("test_key", {"data": "test"}, ttl=60)
        value = await memory.retrieve_short_term_memory("test_key")
        if value and value.get("data") == "test":
            print("✓ 短期记忆存储和检索成功")
        else:
            print("✗ 短期记忆检索失败")
        
        await memory.close()
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_prompt_engine():
    """测试提示词引擎"""
    print("\n=== 测试提示词引擎 ===")
    
    try:
        engine = PromptEngine()
        print("✓ 提示词引擎初始化成功")
        
        # 测试系统提示词生成
        system_prompt = engine.build_system_prompt(
            role="assistant",
            context={
                "user_name": "测试用户",
                "conversation_topic": "测试对话",
                "user_intent": "功能测试"
            },
            available_tools=["calculator", "web_search"]
        )
        
        if system_prompt and len(system_prompt) > 100:
            print("✓ 系统提示词生成成功")
            print(f"提示词长度: {len(system_prompt)} 字符")
        else:
            print("✗ 系统提示词生成失败")
        
        # 测试工具调用提示词
        tool_prompt = engine.build_tool_call_prompt(["calculator", "web_search"])
        if tool_prompt and "calculator" in tool_prompt:
            print("✓ 工具调用提示词生成成功")
        else:
            print("✗ 工具调用提示词生成失败")
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("Agent 核心功能测试")
    print("="*60)
    
    # 测试提示词引擎（不依赖外部服务）
    test_prompt_engine()
    
    # 测试记忆系统（依赖 Redis）
    await test_memory_system()
    
    # 测试 Agent 执行器（依赖所有服务）
    # 注意：需要配置正确的 LLM API Key
    # await test_agent_executor()
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())