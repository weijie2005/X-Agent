#!/usr/bin/env python3
"""
后端服务启动脚本

从 .env 文件读取配置，启动 FastAPI 服务
"""
import os
import sys
import uvicorn
from pathlib import Path

# 添加项目路径到 Python 路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.config import get_settings


def main():
    """启动后端服务"""
    # 获取配置
    settings = get_settings()
    
    # 打印启动信息
    print("=" * 80)
    print(f"🚀 启动 {settings.APP_NAME} v{settings.APP_VERSION}")
    print("=" * 80)
    print(f"📡 监听地址: http://{settings.BACKEND_HOST}:{settings.BACKEND_PORT}")
    print(f"📚 API 文档: http://localhost:{settings.BACKEND_PORT}/docs")
    print(f"🔍 健康检查: http://localhost:{settings.BACKEND_PORT}/health")
    print("=" * 80)
    
    # 启动服务
    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG,
        log_level="info"
    )


if __name__ == "__main__":
    main()