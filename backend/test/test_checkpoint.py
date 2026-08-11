"""
测试 PostgreSQL Checkpoint 功能

验证：
1. Checkpoint 库是否正确安装
2. PostgreSQL 连接是否正常
3. Checkpoint 表是否正确创建
4. Agent 执行器是否正确初始化
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] [%(process)d] [%(threadName)s] - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_checkpoint_import():
    """测试 checkpoint 库导入"""
    print("\n" + "="*60)
    print("测试 1: 检查 checkpoint 库导入")
    print("="*60)
    
    try:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        print("✅ langgraph-checkpoint-postgres 导入成功")
        return True
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("请运行: pip install langgraph-checkpoint-postgres")
        return False


async def test_postgres_connection():
    """测试 PostgreSQL 连接"""
    print("\n" + "="*60)
    print("测试 2: 检查 PostgreSQL 连接")
    print("="*60)
    
    try:
        from app.config import get_settings
        from sqlalchemy import create_engine, text
        
        settings = get_settings()
        connection_string = (
            f"postgresql://{settings.PG_USER}:{settings.PG_PASSWORD}"
            f"@{settings.PG_HOST}:{settings.PG_PORT}/{settings.PG_DB}"
        )
        
        engine = create_engine(connection_string)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ PostgreSQL 连接成功")
            print(f"   版本: {version}")
            return True
            
    except Exception as e:
        print(f"❌ PostgreSQL 连接失败: {e}")
        return False


async def test_checkpoint_setup():
    """测试 checkpoint 表创建"""
    print("\n" + "="*60)
    print("测试 3: 检查 Checkpoint 表创建")
    print("="*60)
    
    try:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        from app.config import get_settings
        
        settings = get_settings()
        connection_string = (
            f"postgresql://{settings.PG_USER}:{settings.PG_PASSWORD}"
            f"@{settings.PG_HOST}:{settings.PG_PORT}/{settings.PG_DB}"
        )
        
        # 创建 checkpointer
        checkpointer = AsyncPostgresSaver.from_conn_string(connection_string)
        
        # 初始化表
        await checkpointer.setup()
        
        print("✅ Checkpoint 表创建成功")
        
        # 验证表是否存在
        from sqlalchemy import create_engine, text
        engine = create_engine(connection_string)
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE '%checkpoint%'
            """))
            tables = [row[0] for row in result]
            if tables:
                print(f"   创建的表: {', '.join(tables)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Checkpoint 表创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_executor_init():
    """测试 Agent 执行器初始化"""
    print("\n" + "="*60)
    print("测试 4: 检查 Agent 执行器初始化")
    print("="*60)
    
    try:
        from app.agent.core.agent_executor import AgentExecutor, CHECKPOINT_AVAILABLE
        
        print(f"Checkpoint 库可用: {CHECKPOINT_AVAILABLE}")
        
        # 使用异步工厂方法创建
        executor = await AgentExecutor.create()
        
        print(f"✅ Agent 执行器初始化成功")
        print(f"   Checkpointer 类型: {type(executor.checkpointer).__name__ if executor.checkpointer else 'None'}")
        print(f"   Checkpoint 已初始化: {executor._checkpoint_initialized}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent 执行器初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("开始测试 PostgreSQL Checkpoint 功能")
    print("="*60)
    
    results = []
    
    # 测试 1: 导入检查
    results.append(await test_checkpoint_import())
    
    # 测试 2: PostgreSQL 连接
    results.append(await test_postgres_connection())
    
    # 测试 3: Checkpoint 表创建
    results.append(await test_checkpoint_setup())
    
    # 测试 4: Agent 执行器初始化
    results.append(await test_agent_executor_init())
    
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
        print("\n✅ 所有测试通过！Checkpoint 功能已正确配置")
    else:
        print("\n❌ 部分测试失败，请检查配置")
    
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())