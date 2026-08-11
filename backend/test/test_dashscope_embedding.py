#!/usr/bin/env python3
"""
测试 DashScope Embedding API
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
env_file = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_file)

# 获取配置
api_key = os.getenv('DASHSCOPE_API_KEY')
base_url = os.getenv('DASHSCOPE_BASE_URL')
model = os.getenv('DASHSCOPE_MODEL', 'qwen3.7-text-embedding')

print(f"API Key: {api_key[:20]}...")
print(f"Base URL: {base_url}")
print(f"Model: {model}")

# 测试 OpenAI SDK 方式
print("\n=== 测试 OpenAI SDK 方式 ===")
try:
    from openai import OpenAI
    
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    
    # 测试单个文本
    print("\n测试单个文本:")
    response = client.embeddings.create(
        model=model,
        input="这是一个测试文本"
    )
    
    print(f"✓ 成功！向量维度: {len(response.data[0].embedding)}")
    print(f"  向量前10位: {response.data[0].embedding[:10]}")
    
    # 测试批量文本
    print("\n测试批量文本:")
    response = client.embeddings.create(
        model=model,
        input=["文本1", "文本2", "文本3"]
    )
    
    print(f"✓ 成功！返回 {len(response.data)} 个向量")
    
except Exception as e:
    print(f"✗ 失败: {e}")

# 测试 LangChain 方式
print("\n=== 测试 LangChain 方式 ===")
try:
    from langchain_openai import OpenAIEmbeddings
    
    embeddings = OpenAIEmbeddings(
        model=model,
        openai_api_key=api_key,
        openai_api_base=base_url
    )
    
    # 测试单个文本
    print("\n测试单个文本:")
    embedding = embeddings.embed_query("这是一个测试文本")
    
    print(f"✓ 成功！向量维度: {len(embedding)}")
    print(f"  向量前10位: {embedding[:10]}")
    
    # 测试批量文本
    print("\n测试批量文本:")
    embeddings_batch = embeddings.embed_documents(["文本1", "文本2", "文本3"])
    
    print(f"✓ 成功！返回 {len(embeddings_batch)} 个向量")
    
except Exception as e:
    print(f"✗ 失败: {e}")

print("\n=== 测试完成 ===")