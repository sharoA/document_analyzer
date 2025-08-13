#!/bin/bash

# Linux环境部署脚本
echo "=========================================="
echo "       文档分析系统 - 离线部署脚本"
echo "=========================================="

# 检查Python3是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装 Python3"
    exit 1
fi

echo "✅ Python版本: $(python3 --version)"

# 创建虚拟环境
echo "🔧 创建Python虚拟环境..."
rm -rf venv
python3 -m venv venv

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 升级pip
echo "🔧 升级pip..."
python -m pip install --upgrade pip

# 从离线包安装依赖
echo "📦 从离线包安装Python依赖..."
if [ -d "offline_packages" ]; then
    pip install --no-index --find-links offline_packages/ -r requirements.txt
    echo "✅ 主要依赖安装完成"
    
    # 如果存在langgraph依赖文件
    if [ -f "requirements_langgraph.txt" ]; then
        pip install --no-index --find-links offline_packages/ -r requirements_langgraph.txt
        echo "✅ LangGraph依赖安装完成"
    fi
else
    echo "❌ 找不到 offline_packages 目录"
    exit 1
fi

# 检查安装是否成功
echo "🔍 验证Python包安装..."
python -c "import flask, requests, langchain, openai; print('✅ 核心包导入成功')" || {
    echo "❌ 包导入失败"
    exit 1
}

# 设置权限
echo "🔧 设置文件权限..."
chmod +x run.py 2>/dev/null || true
chmod +x src/apis/api_server.py 2>/dev/null || true

echo "=========================================="
echo "✅ 部署完成！"
echo ""
echo "启动方式："
echo "1. source venv/bin/activate"
echo "2. python run.py"
echo "   或者 python src/apis/api_server.py"
echo "=========================================="