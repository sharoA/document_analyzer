#!/bin/bash

# 创建离线部署包脚本
echo "开始创建离线部署包..."

# 创建离线包目录
mkdir -p offline_packages

# 激活虚拟环境（如果存在）
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "已激活虚拟环境"
fi

# 下载所有依赖包到离线目录
echo "正在下载依赖包到 offline_packages/ ..."
pip download -r requirements.txt -d offline_packages/

# 如果有额外的依赖文件，也下载
if [ -f "requirements_langgraph.txt" ]; then
    echo "正在下载 langgraph 依赖包..."
    pip download -r requirements_langgraph.txt -d offline_packages/
fi

echo "依赖包下载完成！"
echo "离线包位置: ./offline_packages/"
echo "文件数量: $(ls offline_packages/ | wc -l)"