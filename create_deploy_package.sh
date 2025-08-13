#!/bin/bash

# 创建完整部署包的脚本
echo "=========================================="
echo "      创建Linux离线部署包"
echo "=========================================="

# 设置包名和日期
PACKAGE_NAME="document_analyzer_linux_$(date +%Y%m%d_%H%M%S)"
echo "包名: $PACKAGE_NAME.zip"

# 1. 先创建离线依赖包
echo "🔧 步骤1: 创建离线依赖包..."
chmod +x create_offline_package.sh
./create_offline_package.sh

if [ $? -ne 0 ]; then
    echo "❌ 离线包创建失败"
    exit 1
fi

# 2. 创建临时部署目录
echo "🔧 步骤2: 准备部署文件..."
rm -rf deploy_temp
mkdir deploy_temp

# 3. 复制项目文件（排除不需要的文件）
echo "📦 复制项目文件..."
rsync -av --progress . deploy_temp/ \
    --exclude 'venv/' \
    --exclude '.git/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude '.DS_Store' \
    --exclude 'node_modules/' \
    --exclude 'deploy_temp/' \
    --exclude '*.log' \
    --exclude 'logs/' \
    --exclude 'backup/' \
    --exclude 'uploads/temp/' \
    --exclude 'uploads/cache/' \
    --exclude '*.db-shm' \
    --exclude '*.db-wal'

# 4. 设置脚本权限
chmod +x deploy_temp/deploy_linux.sh
chmod +x deploy_temp/create_offline_package.sh

# 5. 创建README
cat > deploy_temp/DEPLOY_README.md << EOF
# 文档分析系统 - Linux离线部署指南

## 系统要求
- Linux系统 (Ubuntu/CentOS/RedHat)
- Python 3.8+ 
- 至少2GB内存
- 至少1GB磁盘空间

## 部署步骤

### 1. 解压部署包
\`\`\`bash
unzip ${PACKAGE_NAME}.zip
cd ${PACKAGE_NAME}
\`\`\`

### 2. 运行部署脚本
\`\`\`bash
chmod +x deploy_linux.sh
./deploy_linux.sh
\`\`\`

### 3. 启动系统
\`\`\`bash
source venv/bin/activate
python run.py
\`\`\`

或者启动API服务器：
\`\`\`bash
source venv/bin/activate
python src/apis/api_server.py
\`\`\`

## 常见问题

### 1. Python版本不符
如果系统Python版本低于3.8，请升级Python或安装Python3.8+

### 2. 权限问题
如果遇到权限问题，使用sudo运行：
\`\`\`bash
sudo chmod +x deploy_linux.sh
sudo ./deploy_linux.sh
\`\`\`

### 3. 依赖安装失败
检查offline_packages目录是否完整，重新解压部署包

## 目录结构
- src/: 源代码
- offline_packages/: Python依赖包
- requirements.txt: 依赖列表
- deploy_linux.sh: 部署脚本
- run.py: 主程序入口

## 技术支持
如有问题请联系开发团队
EOF

# 6. 打包
echo "📦 创建ZIP部署包..."
cd deploy_temp
zip -r "../${PACKAGE_NAME}.zip" . -x "*.pyc" "__pycache__/*"
cd ..

# 7. 清理临时文件
rm -rf deploy_temp

# 8. 显示结果
echo "=========================================="
echo "✅ 部署包创建完成！"
echo ""
echo "📦 包名: ${PACKAGE_NAME}.zip"
echo "📏 大小: $(du -h ${PACKAGE_NAME}.zip | cut -f1)"
echo "📂 位置: $(pwd)/${PACKAGE_NAME}.zip"
echo ""
echo "🚀 Linux部署步骤:"
echo "1. 上传 ${PACKAGE_NAME}.zip 到Linux服务器"
echo "2. unzip ${PACKAGE_NAME}.zip"
echo "3. cd ${PACKAGE_NAME}"
echo "4. chmod +x deploy_linux.sh && ./deploy_linux.sh"
echo "5. source venv/bin/activate && python run.py"
echo "=========================================="