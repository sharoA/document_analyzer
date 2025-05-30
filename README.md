# 🤖 智能需求分析与设计文档生成系统

这是一个基于人工智能的企业级需求分析和设计文档生成系统，能够结合公司现有的产品需求文档库、数据库结构和设计文档模板来进行深度分析。

## ✨ 核心功能

### 1. 智能需求分析
- 📄 支持多种文档格式（PDF、Word、图片等）
- 🔍 结合历史需求文档库进行语义相似性分析
- 🗄️ 自动分析现有数据库结构和字段
- 🔑 提取业务关键词和技术关键词
- ⚠️ 智能检查需求文档中的问题和缺陷

### 2. API接口设计分析
- 🔌 自动分析需要开发的API接口数量
- 📊 识别每个接口需要的数据字段
- 🗃️ 检查数据库中字段的可用性
- 📋 生成详细的接口设计文档

### 3. 设计文档生成
- 📝 基于企业模板生成后端详细设计文档
- 🎨 结合前端截图生成前端详细设计文档
- 📐 包含系统架构、数据库设计、API设计等完整内容
- 💾 支持设计文档的保存和下载

### 4. 前端截图分析
- 📷 支持上传前端界面截图
- 🔤 自动OCR识别截图中的文字内容
- 🎯 结合截图内容生成前端设计文档

## 🛠️ 技术架构

- **LangChain**: 构建智能体和连接组件
- **DeepSeek**: 大语言模型，提供强大的文本理解和生成能力
- **Weaviate**: 向量数据库，存储和检索文档语义信息
- **SQLAlchemy**: 关系型数据库连接，分析现有业务数据库
- **PyPDF2/pdfplumber/docx/unstructured**: 多格式文档处理
- **Tesseract/EasyOCR**: OCR工具，处理前端截图中的文本
- **Streamlit**: 现代化Web界面，提供友好的用户交互

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone [项目地址]
cd analyDesign

# 配置pip使用阿里云镜像（推荐，加速下载）
python setup_pip_mirror.py

# 或者手动配置pip镜像源
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
pip config set global.trusted-host mirrors.aliyun.com

# 安装Python依赖
pip install -r requirements.txt

# 或者使用阿里云镜像直接安装
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

# 安装Tesseract OCR（Windows）
# 下载并安装：https://github.com/UB-Mannheim/tesseract/wiki

# 安装Docker（用于Weaviate）
# 下载并安装：https://www.docker.com/products/docker-desktop
```

### 2. 配置环境

```bash
# 复制环境配置文件
cp .env.example .env

# 编辑 .env 文件，配置以下参数：
```

```env
# DeepSeek API配置
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# 业务数据库配置（连接现有业务数据库）
BUSINESS_DATABASE_URL=mysql://username:password@localhost:3306/business_db

# 公司信息配置
COMPANY_NAME=您的公司名称
PRODUCT_LINE=您的产品线名称
```

### 3. 启动系统

```bash
# 使用启动脚本（推荐）
python run.py

# 或者手动启动
# 1. 启动Weaviate
docker run -d -p 8080:8080 semitechnologies/weaviate:1.19.6

# 2. 启动Web应用
streamlit run src/enhanced_app.py
```

### 4. 访问系统

打开浏览器访问：`http://localhost:8501`

## 📖 使用指南

### 步骤1：文档上传
1. 在"文档上传"标签页上传需求文档（PDF、Word等）
2. 可选：上传前端界面截图
3. 点击"开始处理文档"

### 步骤2：智能分析
1. 切换到"需求分析"标签页
2. 点击"开始智能分析"
3. 系统将自动：
   - 提取业务关键词
   - 搜索相关数据库表
   - 检查数据字段可用性
   - 识别潜在问题

### 步骤3：生成设计文档
1. 切换到"设计文档"标签页
2. 点击"生成后端设计文档"或"生成前端设计文档"
3. 查看生成的详细设计文档
4. 保存或下载设计文档

### 步骤4：查看分析结果
1. 在"分析结果"标签页查看：
   - API接口设计详情
   - 相似历史文档
   - 完整的分析报告

## 📁 项目结构

```
analyDesign/
├── src/                          # 源代码目录
│   ├── config.py                 # 配置管理
│   ├── document_processor.py     # 文档处理模块
│   ├── vector_store.py          # 向量数据库管理
│   ├── database_analyzer.py     # 数据库分析模块
│   ├── enhanced_analyzer.py     # 增强智能分析器
│   └── enhanced_app.py          # Web应用界面
├── templates/                    # 设计文档模板
│   ├── backend_design_template.md
│   └── frontend_design_template.md
├── uploads/                      # 上传文件存储
├── outputs/                      # 生成文档输出
├── requirements.txt              # Python依赖
├── .env.example                 # 环境配置示例
├── setup_pip_mirror.py          # pip镜像配置工具
├── run.py                       # 启动脚本
├── test_setup.py                # 配置测试脚本
└── README.md                    # 项目说明
```

## 🔧 高级配置

### pip镜像源配置

为了加速包的下载，建议使用国内镜像源：

```bash
# 使用配置工具（推荐）
python setup_pip_mirror.py

# 手动配置常用镜像源
# 阿里云
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

# 清华大学
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple/

# 中科大
pip config set global.index-url https://pypi.mirrors.ustc.edu.cn/simple/
```

### 数据库连接

系统支持连接现有的业务数据库来分析表结构：

```env
# MySQL
BUSINESS_DATABASE_URL=mysql://username:password@localhost:3306/database_name

# PostgreSQL
BUSINESS_DATABASE_URL=postgresql://username:password@localhost:5432/database_name

# SQL Server
BUSINESS_DATABASE_URL=mssql+pyodbc://username:password@server/database?driver=ODBC+Driver+17+for+SQL+Server
```

### 自定义模板

您可以在 `templates/` 目录下自定义设计文档模板：

- `backend_design_template.md`: 后端设计文档模板
- `frontend_design_template.md`: 前端设计文档模板

### 向量数据库配置

支持本地和云端Weaviate部署：

```env
# 本地部署
WEAVIATE_URL=http://localhost:8080

# 云端部署
WEAVIATE_URL=https://your-cluster.weaviate.network
WEAVIATE_API_KEY=your_api_key
```

## 🎯 应用场景

1. **产品需求分析**: 快速分析产品需求文档，识别关键业务点
2. **技术方案设计**: 基于需求自动生成技术实现方案
3. **API接口设计**: 自动分析并设计所需的API接口
4. **数据库设计**: 结合现有数据库结构进行设计优化
5. **文档标准化**: 基于企业模板生成标准化设计文档

## 🔒 安全性

- 支持本地部署，数据不出企业内网
- 敏感信息加密存储
- 支持用户权限管理
- 完整的操作日志记录

## 🤝 贡献指南

欢迎提交Issue和Pull Request来帮助改进这个项目。

## 📄 许可证

MIT License

## 📞 技术支持

如有问题，请提交Issue或联系开发团队。 