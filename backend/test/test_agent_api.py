#!/usr/bin/env python3
"""
Agent 对话接口测试

测试 Agent 对话功能，使用 DeepSeek API。
"""
import requests
import json
from uuid import uuid4
import os
import sys

# 本地测试时覆盖 Redis 主机名（Docker 容器名 -> localhost）
# 必须在导入任何项目模块之前设置
os.environ['REDIS_HOST'] = 'localhost'
os.environ['QDRANT_HOST'] = 'localhost'
os.environ['MINIO_HOST'] = 'localhost:9000'

BASE_URL = "http://localhost:8001"


def create_test_session():
    """创建测试会话"""
    print("\n=== 创建测试会话 ===")
    
    create_data = {
        "title": "Agent 对话测试"
    }
    
    response = requests.post(
        f"{BASE_URL}/sessions",
        json=create_data
    )
    
    if response.status_code == 201:
        session = response.json()
        print(f"✓ 会话创建成功")
        print(f"  会话 ID: {session['id']}")
        return session['id']
    else:
        print(f"✗ 创建会话失败: {response.status_code}")
        return None


def test_agent_chat(session_id):
    """测试 Agent 对话"""
    print("\n=== 测试 Agent 对话（同步）===")
    
    chat_data = {
        "session_id": session_id,
        "user_input": "你好，请用一句话介绍你自己。"
    }
    
    print(f"\n发送消息: {chat_data['user_input']}")
    print("等待 Agent 响应...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/agent/chat",
            json=chat_data,
            timeout=30
        )
        
        print(f"\n状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✓ Agent 响应成功!")
            print(f"\n响应内容:")
            print(f"  {result.get('output', '无内容')}")
            print(f"\n元数据:")
            print(f"  迭代次数: {result.get('metadata', {}).get('iterations', 0)}")
            print(f"  工具调用: {result.get('metadata', {}).get('tool_calls', 0)}")
            return True
        else:
            print(f"\n✗ Agent 响应失败")
            print(f"  错误: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("\n✗ 请求超时（30秒）")
        return False
    except Exception as e:
        print(f"\n✗ 请求失败: {e}")
        return False


def test_agent_stream(session_id):
    """测试 Agent 流式对话"""
    print("\n=== 测试 Agent 对话（流式）===")
    
    chat_data = {
        "session_id": session_id,
        "user_input": "请帮我计算 2 + 2 等于多少？"
    }
    
    print(f"\n发送消息: {chat_data['user_input']}")
    print("等待 Agent 流式响应...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/agent/chat/stream",
            json=chat_data,
            stream=True,
            timeout=30
        )
        
        print(f"\n状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("\n✓ 流式连接成功!")
            print("\n流式响应内容:")
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    
                    # 跳过空行
                    if not line_str.strip():
                        continue
                    
                    # 处理 SSE 格式
                    if line_str.startswith('data: '):
                        data = line_str[6:]  # 移除 'data: ' 前缀
                        
                        # 检查是否是结束标记
                        if data.strip() == '[DONE]':
                            print("\n\n✓ 流式响应完成")
                            break
                        
                        # 尝试解析 JSON
                        try:
                            event = json.loads(data)
                            event_type = event.get('event')
                            
                            if event_type == 'update':
                                # 打印更新信息
                                update_data = event.get('data', {})
                                if 'current_output' in update_data:
                                    print(f"\n输出: {update_data['current_output'][:100]}...")
                            elif event_type == 'done':
                                print("\n✓ Agent 执行完成")
                            elif event_type == 'error':
                                print(f"\n✗ 错误: {event.get('data', {}).get('error')}")
                        except json.JSONDecodeError:
                            # 不是 JSON，直接打印
                            print(f"\n原始数据: {data[:100]}")
            
            return True
        else:
            print(f"\n✗ 流式响应失败")
            print(f"  错误: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("\n✗ 请求超时（30秒）")
        return False
    except Exception as e:
        print(f"\n✗ 请求失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("Agent 对话接口测试")
    print("="*60)
    
    # 创建测试会话
    session_id = create_test_session()
    
    if not session_id:
        print("\n✗ 无法创建测试会话，测试终止")
        return
    
    # 测试同步对话
    success1 = test_agent_chat(session_id)
    
    # 测试流式对话
    success2 = test_agent_stream(session_id)
    
    # 打印测试结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    print(f"同步对话: {'✓ 通过' if success1 else '✗ 失败'}")
    print(f"流式对话: {'✓ 通过' if success2 else '✗ 失败'}")
    
    if success1 and success2:
        print("\n🎉 所有测试通过！Agent 对话功能正常")
    else:
        print("\n⚠️  部分测试失败")


if __name__ == "__main__":
    main()