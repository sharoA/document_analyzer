#!/bin/bash

echo "🚀 智能需求分析系统 - 依赖安装脚本"
echo "支持阿里云、清华大学、腾讯云镜像"
echo "=========================================="
echo

echo "📦 使用国内镜像安装Python依赖包..."
echo

# 定义镜像源
ALIYUN_MIRROR="https://mirrors.aliyun.com/pypi/simple/"
TSINGHUA_MIRROR="https://pypi.tuna.tsinghua.edu.cn/simple/"
TENCENT_MIRROR="https://mirrors.cloud.tencent.com/pypi/simple/"

# 升级pip
echo "🔄 升级pip..."
python3 -m pip install --upgrade pip -i $ALIYUN_MIRROR --trusted-host mirrors.aliyun.com
if [ $? -ne 0 ]; then
    echo "⚠️ 阿里云镜像失败，尝试清华镜像..."
    python3 -m pip install --upgrade pip -i $TSINGHUA_MIRROR --trusted-host pypi.tuna.tsinghua.edu.cn
    if [ $? -ne 0 ]; then
        echo "⚠️ 清华镜像失败，尝试腾讯云镜像..."
        python3 -m pip install --upgrade pip -i $TENCENT_MIRROR --trusted-host mirrors.cloud.tencent.com
    fi
fi

echo
echo "📋 安装项目依赖..."

# 尝试使用阿里云镜像安装
echo "🌟 尝试使用阿里云镜像..."
python3 -m pip install -r requirements.txt -i $ALIYUN_MIRROR --trusted-host mirrors.aliyun.com

if [ $? -ne 0 ]; then
    echo "⚠️ 阿里云镜像安装失败，尝试清华大学镜像..."
    python3 -m pip install -r requirements.txt -i $TSINGHUA_MIRROR --trusted-host pypi.tuna.tsinghua.edu.cn
    
    if [ $? -ne 0 ]; then
        echo "⚠️ 清华镜像安装失败，尝试腾讯云镜像..."
        python3 -m pip install -r requirements.txt -i $TENCENT_MIRROR --trusted-host mirrors.cloud.tencent.com
        
        if [ $? -ne 0 ]; then
            echo "❌ 所有镜像源都安装失败，请检查网络连接"
            echo
            echo "💡 手动安装建议："
            echo "1. 检查网络连接"
            echo "2. 运行 python3 setup_pip_mirror.py 配置镜像源"
            echo "3. 手动执行: pip3 install -r requirements.txt"
            exit 1
        else
            echo "✅ 腾讯云镜像安装成功！"
        fi
    else
        echo "✅ 清华大学镜像安装成功！"
    fi
else
    echo "✅ 阿里云镜像安装成功！"
fi

echo
echo "✅ 依赖安装完成！"
echo
echo "💡 接下来的步骤："
echo "1. 复制 .env.example 为 .env 并配置参数"
echo "2. 运行 python3 test_setup.py 测试配置"
echo "3. 运行 python3 run.py 启动系统"
echo
echo "🌟 支持的镜像源："
echo "  - 阿里云: $ALIYUN_MIRROR"
echo "  - 清华大学: $TSINGHUA_MIRROR"
echo "  - 腾讯云: $TENCENT_MIRROR"

echo 