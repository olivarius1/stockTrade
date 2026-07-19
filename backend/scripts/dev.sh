#!/bin/bash
# 开发环境快速启动脚本 (在 WSL 中运行)
# 用法: bash scripts/dev.sh

set -e

echo "=== 启动 Docker 基础设施 (PostgreSQL + Redis) ==="
cd "$(dirname "$0")/../.."
docker-compose up -d

echo ""
echo "=== 等待 PostgreSQL 就绪 ==="
sleep 3

echo ""
echo "=== 初始化开发数据库表结构 ==="
cd backend
python init_db.py

echo ""
echo "=== 启动本地后端服务 ==="
echo "访问地址: http://localhost:8000/docs"
echo ""
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
