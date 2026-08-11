#!/usr/bin/env python3
"""测试会话历史消息加载"""
import requests
import json

session_id = "2d350c1f-6dbd-4f8b-bf77-ee3cce48eb19"

print(f"测试会话历史消息加载: {session_id}")
print("=" * 60)

try:
    response = requests.get(
        f"http://localhost:8080/api/v1/sessions/{session_id}/messages",
        params={"limit": 10}
    )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        messages = response.json()
        print(f"消息数量: {len(messages)}")
        print()
        
        for i, msg in enumerate(messages, 1):
            print(f"--- Message {i} ---")
            print(f"Role: {msg.get('role')}")
            print(f"Content: {msg.get('content', '')[:100]}...")
            print()
    else:
        print(f"错误: {response.text}")
        
except Exception as e:
    print(f"异常: {e}")