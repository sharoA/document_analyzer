#!/bin/bash

# 增强版Linux环境部署脚本（支持系统包安装）
echo "=========================================="
echo "   文档分析系统 - 增强版离线部署脚本"
echo "=========================================="

# 检查Python3是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装 Python3"
    exit 1
fi

echo "✅ Python版本: $(python3 --version)"

# 检查并安装系统依赖包
echo "🔍 检查系统依赖包..."
if [ -d "system_packages" ]; then
    echo "📦 发现系统包，正在安装..."
    sudo dpkg -i system_packages/python3-*.deb 2>/dev/null || true
    sudo apt-get install -f -y 2>/dev/null || true
    echo "✅ 系统包安装完成"
fi

# 检查python3-venv是否可用
if ! python3 -m venv --help &> /dev/null; then
    echo "⚠️  python3-venv不可用，尝试使用系统Python..."
    USE_SYSTEM_PYTHON=true
else
    echo "✅ python3-venv可用"
    USE_SYSTEM_PYTHON=false
fi

if [ "$USE_SYSTEM_PYTHON" = "false" ]; then
    # 创建虚拟环境
    echo "🔧 创建Python虚拟环境..."
    rm -rf venv
    python3 -m venv venv
    
    # 激活虚拟环境
    echo "🔧 激活虚拟环境..."
    source venv/bin/activate
    
    # 升级pip
    echo "🔧 升级pip..."
    python -m pip install --upgrade pip 2>/dev/null || true
    
    PYTHON_CMD="python"
else
    echo "🔧 使用系统Python（跳过虚拟环境）..."
    PYTHON_CMD="python3"
fi

# 从离线包安装依赖
echo "📦 从离线包安装Python依赖..."
if [ -d "offline_packages" ]; then
    $PYTHON_CMD -m pip install --no-index --find-links offline_packages/ -r requirements.txt
    echo "✅ 主要依赖安装完成"
    
    # 如果存在langgraph依赖文件
    if [ -f "requirements_langgraph.txt" ]; then
        $PYTHON_CMD -m pip install --no-index --find-links offline_packages/ -r requirements_langgraph.txt 2>/dev/null || true
        echo "✅ LangGraph依赖安装完成"
    fi
else
    echo "❌ 找不到 offline_packages 目录"
    echo "尝试安装基础包..."
    $PYTHON_CMD -m pip install flask requests pyyaml 2>/dev/null || true
fi

# 检查安装是否成功
echo "🔍 验证Python包安装..."
$PYTHON_CMD -c "import flask, requests; print('✅ 核心包导入成功')" 2>/dev/null || {
    echo "⚠️  部分包导入失败，但可以尝试启动"
}

# 设置权限
echo "🔧 设置文件权限..."
chmod +x run.py 2>/dev/null || true
chmod +x src/apis/api_server.py 2>/dev/null || true

# 创建必要目录
mkdir -p uploads/temp uploads/analysis_results uploads/cache logs outputs

echo "=========================================="
echo "✅ 部署完成！"
echo ""
if [ "$USE_SYSTEM_PYTHON" = "false" ]; then
    echo "启动方式："
    echo "1. source venv/bin/activate"
    echo "2. python run.py"
else
    echo "启动方式："
    echo "python3 run.py"
fi
echo "   或者 python3 src/apis/api_server.py"
echo "=========================================="