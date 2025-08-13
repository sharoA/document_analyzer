#!/bin/bash

# Ubuntu系统包离线下载脚本
echo "下载Ubuntu系统依赖包..."

# 创建系统包目录
mkdir -p system_packages

# Ubuntu 22.04 LTS 系统包下载链接
echo "下载python3-venv..."
wget -P system_packages/ http://archive.ubuntu.com/ubuntu/pool/main/p/python3-stdlib-extensions/python3-venv_3.11.0-1ubuntu1_amd64.deb

echo "下载python3-pip..."  
wget -P system_packages/ http://archive.ubuntu.com/ubuntu/pool/main/p/python3-pip/python3-pip_24.0+dfsg-1ubuntu1_all.deb

echo "下载python3-setuptools..."
wget -P system_packages/ http://archive.ubuntu.com/ubuntu/pool/main/p/python3-setuptools/python3-setuptools_68.1.2-2ubuntu1.1_all.deb

echo "下载python3-wheel..."
wget -P system_packages/ http://archive.ubuntu.com/ubuntu/pool/main/p/python3-wheel/python3-wheel_0.40.0-1ubuntu1_all.deb

echo "下载python3-dev（可选）..."
wget -P system_packages/ http://archive.ubuntu.com/ubuntu/pool/main/p/python3-defaults/python3-dev_3.11.4-5ubuntu1_amd64.deb

echo "系统包下载完成！"
echo "文件保存在 system_packages/ 目录"
ls -la system_packages/