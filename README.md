# 🤖 智能需求分析与设计文档生成系统

这是一个基于人工智能的企业级需求分析和设计文档生成系统，采用前后端分离架构，能够结合公司现有的产品需求文档库、数据库结构和设计文档模板来进行深度分析。

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

### 前后端分离架构
```
┌─────────────────┐    WebSocket/HTTP    ┌─────────────────┐
│   Vue 3 前端    │ ←─────────────────→ │  Python 后端    │
│                 │                      │                 │
│ • Element Plus  │                      │ • Flask API     │
│ • WebSocket     │                      │ • SocketIO      │
│ • 实时聊天界面   │                      │ • AI 分析引擎   │
└─────────────────┘                      └─────────────────┘
     端口: 3000                              端口: 8081
```

### 技术栈
- **前端**: Vue 3 + Element Plus + WebSocket + Vite
- **后端**: Python Flask + SocketIO + AI引擎
- **LangChain**: 构建智能体和连接组件
- **DeepSeek/火山引擎**: 大语言模型，提供强大的文本理解和生成能力
- **Weaviate**: 向量数据库，存储和检索文档语义信息
- **SQLAlchemy**: 关系型数据库连接，分析现有业务数据库
- **PyPDF2/pdfplumber/docx/unstructured**: 多格式文档处理
- **Tesseract/EasyOCR**: OCR工具，处理前端截图中的文本

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone [项目地址]
cd analyDesign

# 设置虚拟环境
powershell -ExecutionPolicy Bypass -File setup_env.ps1

# 激活虚拟环境
call analyDesign_env\Scripts\activate.bat

# 安装Python依赖
pip install -r requirements.txt
```

### 2. 配置环境

编辑 `src/simple_config.py` 文件，配置以下参数：

```python
# 火山引擎API配置
VOLCENGINE_API_KEY = "your_volcengine_api_key_here"

# 业务数据库配置（可选）
BUSINESS_DATABASE_URL = "mysql://username:password@localhost:3306/business_db"
```

### 3. 启动系统

#### 后端启动
```bash
# 快速启动（推荐）
双击 start_backend_quick.bat

# 或选择启动模式
双击 start_backend.bat

# 或开发调试模式
双击 start_backend_dev.bat
```

#### 前端启动
```bash
cd frontend
npm install
npm run dev
```

### 4. 访问系统

- **前端界面**: `http://localhost:3000`
- **后端API**: `http://localhost:8081`
- **WebSocket**: `ws://localhost:8081/socket.io/`

## 📖 使用指南

### 步骤1：启动服务
1. 启动后端服务（端口8081）
2. 启动前端服务（端口3000）
3. 在浏览器中访问前端界面

### 步骤2：文档上传与分析
1. 在聊天界面上传需求文档（PDF、Word等）
2. 可选：上传前端界面截图
3. 系统自动进行智能分析

### 步骤3：实时对话
1. 与AI助手进行实时对话
2. 获取需求分析结果
3. 生成设计文档和建议

### 步骤4：查看结果
1. 查看分析报告和设计建议
2. 下载生成的设计文档
3. 获取API接口设计详情

## 📁 项目结构

```
analyDesign/
├── 🐍 后端部分
│   ├── src/
│   │   ├── integrated_server.py     # 集成服务器
│   │   ├── api_server.py           # API服务器
│   │   ├── enhanced_analyzer.py    # 智能分析器
│   │   ├── websocket_server.py     # WebSocket服务
│   │   └── simple_config.py        # 配置文件
│   ├── start_backend_quick.bat     # 快速启动脚本
│   ├── start_backend.bat           # 启动选择脚本
│   └── requirements.txt            # Python依赖
│
├── 🎨 前端部分
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── components/
│   │   │   │   └── ChatInterface.vue    # 主聊天界面
│   │   │   └── stores/
│   │   │       └── websocket.js         # WebSocket状态管理
│   │   └── package.json             # 前端依赖
│   
├── 📄 配置和模板
│   ├── templates/                   # 设计文档模板
│   ├── uploads/                     # 上传文件存储
│   ├── outputs/                     # 生成文档输出
│   └── logs/                        # 日志文件
```

## 🔧 高级配置

### 数据库连接

系统支持连接现有的业务数据库来分析表结构：

```python
# MySQL
BUSINESS_DATABASE_URL = "mysql://username:password@localhost:3306/database_name"

# PostgreSQL
BUSINESS_DATABASE_URL = "postgresql://username:password@localhost:5432/database_name"
```

### 自定义模板

您可以在 `templates/` 目录下自定义设计文档模板：

- `backend_design_template.md`: 后端设计文档模板
- `frontend_design_template.md`: 前端设计文档模板

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