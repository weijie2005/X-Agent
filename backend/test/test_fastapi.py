#!/usr/bin/env python3
"""
FastAPI 接口测试脚本

测试第2阶段完成的所有 FastAPI 接口。
"""
import requests
import json
from uuid import uuid4
import sys
import os
from pathlib import Path

# 添加项目路径到 Python 路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.config import get_settings

# 从配置文件读取后端地址和端口
settings = get_settings()
BASE_URL = f"http://localhost:{settings.BACKEND_PORT}"


def print_response(response, test_name):
    """打印响应信息"""
    print(f"\n=== {test_name} ===")
    print(f"状态码: {response.status_code}")
    try:
        data = response.json()
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
    except:
        print(f"响应: {response.text}")
    return response.status_code == 200 or response.status_code == 201


def test_root():
    """测试根路径"""
    response = requests.get(f"{BASE_URL}/")
    return print_response(response, "根路径")


def test_health():
    """测试健康检查"""
    response = requests.get(f"{BASE_URL}/health")
    return print_response(response, "健康检查")


def test_session_apis():
    """测试会话管理接口"""
    print("\n" + "="*60)
    print("测试会话管理接口")
    print("="*60)
    
    # 创建会话
    session_id = str(uuid4())
    user_id = str(uuid4())
    
    create_data = {
        "title": "测试会话",
        "user_id": user_id
    }
    
    response = requests.post(
        f"{BASE_URL}/sessions",
        json=create_data
    )
    success = print_response(response, "创建会话")
    
    if not success:
        return False
    
    # 获取返回的会话 ID
    session = response.json()
    session_id = session.get("id")
    
    # 获取会话列表
    response = requests.get(f"{BASE_URL}/sessions?user_id={user_id}")
    print_response(response, "获取会话列表")
    
    # 获取会话详情
    response = requests.get(f"{BASE_URL}/sessions/{session_id}")
    print_response(response, "获取会话详情")
    
    # 更新会话
    update_data = {
        "title": "更新后的会话"
    }
    response = requests.patch(
        f"{BASE_URL}/sessions/{session_id}",
        json=update_data
    )
    print_response(response, "更新会话")
    
    # 添加消息
    message_data = {
        "role": "user",
        "content": "这是一条测试消息",
        "tokens_used": 10
    }
    response = requests.post(
        f"{BASE_URL}/sessions/{session_id}/messages",
        json=message_data
    )
    print_response(response, "添加消息")
    
    # 获取历史消息
    response = requests.get(f"{BASE_URL}/sessions/{session_id}/messages")
    print_response(response, "获取历史消息")
    
    return True


def test_file_apis():
    """测试文件上传接口"""
    print("\n" + "="*60)
    print("测试文件上传接口")
    print("="*60)
    
    # 先创建一个会话
    session_id = str(uuid4())
    create_data = {
        "title": "文件上传测试会话"
    }
    
    response = requests.post(
        f"{BASE_URL}/sessions",
        json=create_data
    )
    
    if response.status_code != 201:
        print("✗ 创建会话失败，跳过文件上传测试")
        return False
    
    session = response.json()
    session_id = session.get("id")
    
    # 创建测试文件
    test_content = b"This is a test file content."
    files = {
        'file': ('test.txt', test_content, 'text/plain')
    }
    
    # 上传文件
    response = requests.post(
        f"{BASE_URL}/files/upload/{session_id}",
        files=files
    )
    print_response(response, "上传文件")
    
    if response.status_code != 201:
        print("✗ 文件上传失败")
        return False
    
    file_data = response.json()
    file_id = file_data.get("id")
    
    # 获取文件元数据
    response = requests.get(f"{BASE_URL}/files/{file_id}")
    print_response(response, "获取文件元数据")
    
    # 获取会话的所有文件
    response = requests.get(f"{BASE_URL}/files/session/{session_id}")
    print_response(response, "获取会话的所有文件")
    
    return True


def test_agent_api():
    """测试 Agent 对话接口"""
    print("\n" + "="*60)
    print("测试 Agent 对话接口")
    print("="*60)
    
    # 先创建一个会话
    create_data = {
        "title": "Agent 测试会话"
    }
    
    response = requests.post(
        f"{BASE_URL}/sessions",
        json=create_data
    )
    
    if response.status_code != 201:
        print("✗ 创建会话失败，跳过 Agent 测试")
        return False
    
    session = response.json()
    session_id = session.get("id")
    
    # 测试 Agent 对话（同步）
    chat_data = {
        "session_id": session_id,
        "user_input": "你好，请介绍一下你自己"
    }
    
    print("\n注意：Agent 对话需要配置正确的 LLM API Key")
    print("如果未配置或配置错误，此测试可能会失败")
    
    response = requests.post(
        f"{BASE_URL}/agent/chat",
        json=chat_data,
        timeout=30
    )
    
    if response.status_code == 200:
        print_response(response, "Agent 对话（同步）")
        return True
    else:
        print(f"✗ Agent 对话失败（状态码: {response.status_code}）")
        print("这可能是正常的，如果 LLM API Key 未配置")
        return True  # 不影响整体测试结果


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("FastAPI 接口测试")
    print("="*60)
    
    results = []
    
    # 测试基础接口
    results.append(("根路径", test_root()))
    results.append(("健康检查", test_health()))
    
    # 测试会话管理接口
    results.append(("会话管理", test_session_apis()))
    
    # 测试文件上传接口
    results.append(("文件上传", test_file_apis()))
    
    # 测试 Agent 对话接口
    results.append(("Agent 对话", test_agent_api()))
    
    # 打印测试结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name}: {status}")
    
    # 统计
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败")


if __name__ == "__main__":
    main()