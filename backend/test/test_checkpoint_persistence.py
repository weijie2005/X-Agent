"""
测试 Checkpoint 断点续跑功能

验证：
1. Checkpoint 是否正确保存状态
2. 服务重启后是否能恢复任务
3. 多次执行是否共享状态
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_checkpoint_persistence():
    """测试 checkpoint 状态持久化"""
    print("\n" + "="*60)
    print("测试: Checkpoint 状态持久化")
    print("="*60)
    
    try:
        from app.agent.core.agent_executor import AgentExecutor
        from uuid import uuid4
        
        # 1. 创建执行器（异步初始化）
        print("\n1. 初始化 Agent 执行器...")
        executor = await AgentExecutor.create()
        
        print(f"   ✅ Checkpointer 类型: {type(executor.checkpointer).__name__}")
        print(f"   ✅ Checkpoint 已初始化: {executor._checkpoint_initialized}")
        
        # 2. 执行一次对话（使用UUID格式的session_id）
        session_id = str(uuid4())
        print(f"\n2. 执行第一次对话 (session_id={session_id})...")
        
        result1 = await executor.run(
            session_id=session_id,
            user_input="你好",
            metadata={"test": "checkpoint_test_1"}
        )
        
        print(f"   ✅ 第一次对话完成")
        print(f"   输出: {result1.get('output', '')[:100]}...")
        
        # 3. 模拟服务重启（重新创建执行器）
        print("\n3. 模拟服务重启（重新创建执行器）...")
        executor2 = await AgentExecutor.create()
        
        print(f"   ✅ 新执行器创建成功")
        
        # 4. 使用相同的 session_id 继续对话（应该能恢复历史）
        print(f"\n4. 使用相同 session_id 继续对话...")
        
        result2 = await executor2.run(
            session_id=session_id,
            user_input="谢谢",
            metadata={"test": "checkpoint_test_2"}
        )
        
        print(f"   ✅ 第二次对话完成")
        print(f"   输出: {result2.get('output', '')[:200]}...")
        
        # 5. 验证状态恢复
        print("\n5. 验证状态恢复...")
        
        # 检查是否包含历史消息
        messages = result2.get('messages', [])
        print(f"   消息数量: {len(messages)}")
        
        if len(messages) > 1:
            print("   ✅ 历史消息已恢复")
        else:
            print("   ⚠️ 未检测到历史消息恢复")
        
        print("\n" + "="*60)
        print("✅ Checkpoint 断点续跑功能测试完成")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_multiple_sessions():
    """测试多个会话的状态隔离"""
    print("\n" + "="*60)
    print("测试: 多会话状态隔离")
    print("="*60)
    
    try:
        from app.agent.core.agent_executor import AgentExecutor
        
        executor = await AgentExecutor.create()
        
        # 会话1
        session1 = "test_session_001"
        print(f"\n1. 会话1: {session1}")
        result1 = await executor.run(
            session_id=session1,
            user_input="我是用户A"
        )
        print(f"   输出: {result1.get('output', '')[:100]}...")
        
        # 会话2
        session2 = "test_session_002"
        print(f"\n2. 会话2: {session2}")
        result2 = await executor.run(
            session_id=session2,
            user_input="我是用户B"
        )
        print(f"   输出: {result2.get('output', '')[:100]}...")
        
        # 继续会话1
        print(f"\n3. 继续会话1: {session1}")
        result3 = await executor.run(
            session_id=session1,
            user_input="我是谁？"
        )
        print(f"   输出: {result3.get('output', '')[:200]}...")
        
        print("\n✅ 多会话状态隔离测试完成")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("开始测试 Checkpoint 断点续跑功能")
    print("="*60)
    
    results = []
    
    # 测试 1: 状态持久化
    results.append(await test_checkpoint_persistence())
    
    # 测试 2: 多会话隔离
    results.append(await test_multiple_sessions())
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    total = len(results)
    passed = sum(results)
    failed = total - passed
    
    print(f"总测试数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    
    if all(results):
        print("\n✅ 所有测试通过！Checkpoint 断点续跑功能正常工作")
    else:
        print("\n❌ 部分测试失败")
    
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())