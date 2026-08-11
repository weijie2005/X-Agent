#!/usr/bin/env python3
"""
直接测试 Agent 执行器

绕过 FastAPI，直接测试 Agent 执行器是否正常工作。
"""
import asyncio
import sys
import os
from pathlib import Path

# 获取当前脚本的绝对路径
script_path = os.path.abspath(__file__)
current_directory = os.path.dirname(script_path)
backend_dir = Path(current_directory).parent

# 添加项目路径到 Python 路径
sys.path.insert(0, str(backend_dir))

# 本地测试时覆盖环境变量
os.environ['REDIS_HOST'] = 'localhost'
os.environ['QDRANT_HOST'] = 'localhost'
os.environ['MINIO_HOST'] = 'localhost:9000'

from app.agent.core.agent_executor import AgentExecutor


async def test_agent_executor():
    """测试 Agent 执行器"""
    print("\n" + "="*60)
    print("直接测试 Agent 执行器")
    print("="*60)
    
    try:
        # 初始化 Agent 执行器
        print("\n1. 初始化 Agent 执行器...")
        executor = AgentExecutor()
        print("   ✓ Agent 执行器初始化成功")
        
        # 测试简单对话
        print("\n2. 发送测试消息...")
        print("   消息: 你好，请用一句话介绍你自己。")
        
        result = await executor.run(
            session_id="test-session-001",
            user_input="你好，请用一句话介绍你自己。"
        )
        
        print("\n3. Agent 执行结果:")
        print(f"   输出: {result.get('output', '无输出')}")
        print(f"   迭代次数: {result.get('metadata', {}).get('iterations', 0)}")
        print(f"   工具调用次数: {result.get('metadata', {}).get('tool_calls', 0)}")
        
        print("\n✓ 测试成功！Agent 执行器工作正常")
        return True
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    success = await test_agent_executor()
    
    print("\n" + "="*60)
    if success:
        print("✓ Agent 执行器测试通过")
    else:
        print("✗ Agent 执行器测试失败")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())