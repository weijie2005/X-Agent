#!/bin/bash
# 前端服务启动脚本

# 进入前端目录
cd "$(dirname "$0")"

# 加载 .env 文件
if [ -f .env ]; then
    echo "📋 加载配置文件: .env"
    export $(cat .env | grep -v '^#' | xargs)
    echo "📡 前端地址: http://${FRONTEND_HOST}:${FRONTEND_PORT}"
    echo "🔗 后端代理: http://${BACKEND_HOST}:${BACKEND_PORT}"
    echo "="
fi

# 启动前端服务
echo "🚀 启动前端服务..."
/usr/bin/npm run dev