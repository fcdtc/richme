#!/bin/bash
# 初始化虚拟环境并安装所有依赖
# 使用方法: ./setup.sh

set -e

echo "=========================================="
echo "  ETF量化交易计算器 - 环境初始化"
echo "=========================================="

# 检查 Python 版本
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "检测到 Python 版本: $PYTHON_VERSION"

# 创建虚拟环境
if [ -d ".venv" ]; then
    echo "虚拟环境已存在，跳过创建"
else
    echo "正在创建虚拟环境..."
    python3 -m venv .venv
    echo "虚拟环境创建完成"
fi

# 激活虚拟环境并安装后端依赖
echo "正在安装后端依赖..."
source .venv/bin/activate
pip install --upgrade pip --quiet
pip install -r backend/requirements.txt --quiet
echo "后端依赖安装完成"

# 安装前端依赖
echo "正在安装前端依赖..."
cd frontend
if [ -d "node_modules" ]; then
    echo "前端依赖已存在，跳过安装"
else
    npm install --silent
fi
cd ..
echo "前端依赖安装完成"

echo ""
echo "=========================================="
echo "  环境初始化完成!"
echo "=========================================="
echo ""
echo "使用 ./start.sh 启动项目"
