#!/usr/bin/env python3
"""
验证配置文件是否正确加载
"""
import sys
from pathlib import Path

# 添加项目路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.config import get_settings

def main():
    """验证配置"""
    settings = get_settings()
    
    print("=" * 80)
    print("📋 配置验证")
    print("=" * 80)
    
    print(f"\n应用信息:")
    print(f"  应用名称: {settings.APP_NAME}")
    print(f"  应用版本: {settings.APP_VERSION}")
    print(f"  调试模式: {settings.DEBUG}")
    
    print(f"\n服务配置:")
    print(f"  后端地址: {settings.BACKEND_HOST}")
    print(f"  后端端口: {settings.BACKEND_PORT}")
    print(f"  前端地址: {settings.FRONTEND_HOST}")
    print(f"  前端端口: {settings.FRONTEND_PORT}")
    
    print(f"\n数据库配置:")
    print(f"  PostgreSQL: {settings.PG_HOST}:{settings.PG_PORT}")
    print(f"  Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    print(f"  Qdrant: {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
    
    print(f"\nLLM 配置:")
    print(f"  API 地址: {settings.LLM_BASE_URL}")
    print(f"  模型: {settings.LLM_MODEL_NAME}")
    
    print(f"\n✅ 配置加载成功!")
    print("=" * 80)

if __name__ == "__main__":
    main()