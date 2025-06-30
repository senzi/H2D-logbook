#!/bin/bash

# H2D Logbook Local Manager 启动脚本

echo "=== H2D Logbook Local Manager ==="
echo "正在启动本地管理系统..."

# 检查 Python 版本
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3，请先安装 Python 3.7 或更高版本"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "检查并安装依赖..."
pip install -r requirements.txt

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p logs
mkdir -p ../../data/{record,plan,consumable_purchase,consumable_retirement,maintenance}

# 启动应用
echo ""
echo "启动 Flask 应用..."
echo "访问地址: http://127.0.0.1:5000"
echo "管理界面: http://127.0.0.1:5000/"
echo "预览界面: http://127.0.0.1:5000/view"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

python app.py
