#!/bin/bash
# 启动前后端服务
# 使用方法: ./start.sh

set -e

echo "=========================================="
echo "  ETF量化交易计算器 - 启动服务"
echo "=========================================="

# 检查虚拟环境是否存在
if [ ! -d ".venv" ]; then
    echo "错误: 虚拟环境不存在，请先运行 ./setup.sh"
    exit 1
fi

# 检查前端依赖是否存在
if [ ! -d "frontend/node_modules" ]; then
    echo "错误: 前端依赖不存在，请先运行 ./setup.sh"
    exit 1
fi

# 激活虚拟环境
source .venv/bin/activate

# 创建日志目录
mkdir -p logs

# 启动后端服务
echo "正在启动后端服务 (端口 8000)..."
nohup uvicorn backend.main:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "后端服务已启动 (PID: $BACKEND_PID)"

# 等待后端启动
sleep 2

# 检查后端是否启动成功
if curl -s http://localhost:8000/health > /dev/null; then
    echo "后端服务启动成功"
else
    echo "警告: 后端服务可能未正常启动，请检查 logs/backend.log"
fi

# 启动前端服务
echo "正在启动前端服务 (端口 5173)..."
cd frontend
nohup npm run dev -- --port 5173 > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "前端服务已启动 (PID: $FRONTEND_PID)"

# 等待前端启动
sleep 3

echo ""
echo "=========================================="
echo "  服务启动完成!"
echo "=========================================="
echo ""
echo "  前端地址: http://localhost:5173"
echo "  后端地址: http://localhost:8000"
echo "  API文档:  http://localhost:8000/docs"
echo ""
echo "  后端日志: logs/backend.log"
echo "  前端日志: logs/frontend.log"
echo ""
echo "  停止服务: ./stop.sh 或 kill $BACKEND_PID $FRONTEND_PID"
echo ""
