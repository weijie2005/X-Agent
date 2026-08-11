"""
测试 DeepSeek API 连接
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

# 本地测试时覆盖 Redis 主机名
os.environ['REDIS_HOST'] = 'localhost'
os.environ['QDRANT_HOST'] = 'localhost'
os.environ['MINIO_HOST'] = 'localhost:9000'

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from app.config import get_settings


async def test_deepseek_api():
    """测试 DeepSeek API"""
    print("\n=== 测试 DeepSeek API 连接 ===")
    
    settings = get_settings()
    
    print(f"\n配置信息:")
    print(f"  API Key: {settings.LLM_API_KEY[:20]}...")
    print(f"  Base URL: {settings.LLM_BASE_URL}")
    print(f"  Model: {settings.LLM_MODEL_NAME}")
    
    try:
        # 初始化 LLM
        llm = ChatOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            model=settings.LLM_MODEL_NAME,
            temperature=0.7,
            max_tokens=100
        )
        
        print("\n✓ LLM 初始化成功")
        
        # 测试简单对话
        messages = [
            SystemMessage(content="你是一个友好的AI助手。"),
            HumanMessage(content="你好，请用一句话介绍你自己。")
        ]
        
        print("\n发送测试消息...")
        response = await llm.ainvoke(messages)
        
        print(f"\n✓ API 调用成功!")
        print(f"\n响应内容:")
        print(f"  {response.content}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ API 调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("DeepSeek API 连接测试")
    print("="*60)
    
    success = await test_deepseek_api()
    
    print("\n" + "="*60)
    if success:
        print("✓ 测试成功！DeepSeek API 可用")
    else:
        print("✗ 测试失败！请检查配置")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())