#!/bin/bash
# 停止前后端服务
# 使用方法: ./stop.sh

echo "=========================================="
echo "  ETF量化交易计算器 - 停止服务"
echo "=========================================="

# 停止后端服务
echo "正在停止后端服务..."
pkill -f "uvicorn backend.main:app" 2>/dev/null && echo "后端服务已停止" || echo "后端服务未运行"

# 停止前端服务
echo "正在停止前端服务..."
pkill -f "vite.*5173" 2>/dev/null && echo "前端服务已停止" || echo "前端服务未运行"

# 清理端口
lsof -ti :8000 2>/dev/null | xargs kill -9 2>/dev/null || true
lsof -ti :5173 2>/dev/null | xargs kill -9 2>/dev/null || true

echo ""
echo "所有服务已停止"
