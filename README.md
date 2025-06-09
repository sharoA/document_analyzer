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

### 5. 智能知识库系统
- 🗄️ **向量数据库**: 基于Weaviate的语义搜索知识库
- 📚 **多格式支持**: 自动处理DOCX、XLSX、Java、XML等文件
- 🔍 **智能检索**: 支持自然语言查询，快速定位相关文档
- 💾 **缓存优化**: Redis缓存机制，提升查询性能
- 🔄 **增量更新**: 支持知识库内容的增量更新和维护

### 6. 统一配置管理
- ⚙️ **YAML配置**: 统一的config.yaml配置文件
- 🔧 **模块化配置**: 支持LLM、数据库、缓存等模块独立配置
- 🔐 **安全管理**: API密钥和敏感信息的安全存储
- 📊 **配置验证**: 自动验证配置项的有效性

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
- **向量数据库**: Weaviate + sentence-transformers，语义搜索和知识检索
- **缓存系统**: Redis，高性能缓存和会话管理
- **配置管理**: YAML + Pydantic，统一配置验证和管理
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

编辑 `config.yaml` 文件，配置以下参数：

```yaml
# LLM配置
volcengine:
  api_key: "your_volcengine_api_key_here"
  base_url: "https://ark.cn-beijing.volces.com/api/v3"
  model: "ep-20241205140139-5vqkz"

# 向量数据库配置
weaviate:
  host: "localhost"
  port: 8080
  api_key: "root-user-key"

# Redis缓存配置
redis:
  host: "localhost"
  port: 6379
  db: 0

# 业务数据库配置（可选）
database:
  url: "mysql://username:password@localhost:3306/business_db"
```

### 3. 启动系统

#### 后端启动
```bash
# 启动后端服务（推荐）
双击 start_back.bat

# 或使用Python直接启动
python run.py
```

#### 前端启动
```bash
# 启动前端服务
双击 启动前端.bat

# 或手动启动
cd frontend
npm install
npm run dev
```

#### 服务检查
```bash
# 检查服务状态
双击 检查服务状态.bat
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

### 步骤5：知识库查询（可选）
1. 使用知识库查询工具：`python query_knowledge_base.py`
2. 输入自然语言查询，如"数据库表结构"、"用户管理代码"等
3. 获取相关的历史文档和代码片段
4. 结合查询结果优化需求分析

## 📁 项目结构

```
analyDesign/
├── 🚀 启动脚本
│   ├── start_back.bat               # 后端启动脚本
│   ├── 启动前端.bat                 # 前端启动脚本
│   ├── 检查服务状态.bat             # 服务状态检查
│   ├── 重新安装环境.bat             # 环境重装脚本
│   ├── run.py                       # 主启动脚本
│   └── query_knowledge_base.py      # 知识库查询工具
│
├── 🐍 后端核心
│   ├── src/
│   │   ├── apis/                    # API接口层
│   │   │   ├── analysis_api.py      # 分析API
│   │   │   ├── file_api.py          # 文件处理API
│   │   │   ├── task_api.py          # 任务管理API
│   │   │   └── websocket_api.py     # WebSocket API
│   │   │
│   │   ├── analysis_services/       # 分析服务层
│   │   │   ├── enhanced_analyzer.py # 智能分析引擎
│   │   │   ├── database_analyzer.py # 数据库分析器
│   │   │   └── document_processor.py # 文档处理器
│   │   │
│   │   ├── utils/                   # 工具模块
│   │   │   ├── volcengine_client.py # 火山引擎AI客户端
│   │   │   ├── openai_client.py     # OpenAI客户端
│   │   │   ├── analysis_utils.py    # 分析工具
│   │   │   ├── task_storage.py      # 任务存储
│   │   │   ├── llm_logger.py        # LLM日志记录
│   │   │   ├── weaviate_helper.py   # Weaviate向量数据库
│   │   │   ├── redis_util.py        # Redis缓存工具
│   │   │   ├── knowledge_init_weaviate.py # 知识库初始化
│   │   │   ├── weaviate_usage_example.py  # Weaviate使用示例
│   │   │   └── redis_usage_example.py     # Redis使用示例
│   │   │
│   │   ├── resource/                # 资源配置
│   │   │   └── config.py            # 统一配置管理
│   │   │
│   │   ├── websockets/              # WebSocket服务
│   │   │   └── socket_handlers.py   # Socket处理器
│   │   │
│   │   └── tasks.db                 # SQLite任务数据库
│   │
│   ├── config.yaml                  # 主配置文件
│   ├── requirements.txt             # Python依赖包
│   └── tasks.db                     # 任务数据库
│
├── 🎨 前端应用
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── components/
│   │   │   │   └── ChatInterface.vue    # 主聊天界面
│   │   │   ├── stores/              # Pinia状态管理
│   │   │   ├── router/              # Vue路由
│   │   │   ├── assets/              # 静态资源
│   │   │   ├── utils/               # 工具函数
│   │   │   ├── App.vue              # 根组件
│   │   │   └── main.js              # 入口文件
│   │   ├── package.json             # 前端依赖
│   │   ├── vite.config.js           # Vite配置
│   │   └── index.html               # HTML模板
│   
├── 📄 数据和模板
│   ├── templates/                   # 设计文档模板
│   │   └── knowledge_init_weaviate.md # 知识库初始化需求
│   ├── uploads/                     # 文件上传目录
│   ├── outputs/                     # 生成文档输出
│   └── logs/                        # 系统日志
│
├── 🔧 环境和配置
│   ├── analyDesign_env/             # Python虚拟环境
│   ├── setup_env.ps1                # 环境设置脚本
│   └── .gitignore                   # Git忽略文件
│
├── 🧪 测试和工具
│   └── tests/                       # 测试文件
│
├── 🗄️ 向量数据库与缓存
│   ├── 知识库使用说明.md            # 知识库使用文档
│   └── query_knowledge_base.py      # 知识库查询工具
│
└── 📚 文档说明
    ├── README.md                    # 项目主文档
    ├── 当前接口结构说明.md          # 接口结构说明
    ├── 文件分析模块接口设计说明.md  # 文件分析模块说明
    ├── 环境配置说明.md              # 环境配置
    └── 快速安装指南.md              # 安装指南
```

### 🎯 核心文件说明

#### 后端服务
- **`run.py`**: 主要后端服务启动入口，集成HTTP API和WebSocket
- **`src/analysis_services/enhanced_analyzer.py`**: AI智能分析核心引擎
- **`src/utils/volcengine_client.py`**: 火山引擎大模型接口
- **`src/resource/config.py`**: 统一配置管理系统
- **`config.yaml`**: 主配置文件，包含所有服务配置

#### 向量数据库与缓存
- **`src/utils/weaviate_helper.py`**: Weaviate向量数据库连接管理
- **`src/utils/redis_util.py`**: Redis缓存工具和连接管理
- **`src/utils/knowledge_init_weaviate.py`**: 知识库初始化脚本
- **`query_knowledge_base.py`**: 知识库查询工具
- **`知识库使用说明.md`**: 知识库使用文档

#### API接口层
- **`src/apis/analysis_api.py`**: 分析相关API接口
- **`src/apis/file_api.py`**: 文件处理API接口
- **`src/apis/task_api.py`**: 任务管理API接口
- **`src/apis/websocket_api.py`**: WebSocket API接口

#### 工具模块
- **`src/utils/analysis_utils.py`**: 分析工具函数
- **`src/utils/task_storage.py`**: 任务存储管理
- **`src/utils/llm_logger.py`**: LLM调用日志记录
- **`src/utils/openai_client.py`**: OpenAI客户端

#### 前端应用
- **`frontend/src/components/ChatInterface.vue`**: 主聊天交互界面
- **`frontend/src/stores/`**: Pinia状态管理，包含WebSocket连接
- **`frontend/package.json`**: 前端依赖和脚本配置

#### 启动脚本
- **`start_back.bat`**: 后端服务启动脚本
- **`启动前端.bat`**: 前端服务启动脚本
- **`检查服务状态.bat`**: 服务状态检查工具
- **`重新安装环境.bat`**: 环境重装脚本

#### 配置和环境
- **`analyDesign_env/`**: Python虚拟环境目录
- **`setup_env.ps1`**: 自动创建和配置虚拟环境
- **`requirements.txt`**: Python依赖包列表

## 🔧 高级配置

### 数据库连接

系统支持连接现有的业务数据库来分析表结构：

```python
# MySQL
BUSINESS_DATABASE_URL = "mysql://username:password@localhost:3306/database_name"

# PostgreSQL
BUSINESS_DATABASE_URL = "postgresql://username:password@localhost:5432/database_name"
```

### 知识库配置

系统支持向量数据库和缓存系统的配置：

```yaml
# Weaviate向量数据库
weaviate:
  host: "localhost"
  port: 8080
  api_key: "root-user-key"
  collection_name: "KnowledgeDocument"

# Redis缓存
redis:
  host: "localhost"
  port: 6379
  db: 0
  connection_pool:
    max_connections: 20
```

### 知识库初始化

首次使用需要初始化知识库：

```bash
# 初始化知识库（将D:\knowledge_base内容导入）
python src/utils/knowledge_init_weaviate.py

# 查询知识库
python query_knowledge_base.py
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



## 📞 技术支持
任玉