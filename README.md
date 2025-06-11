# 🤖 智能需求分析与设计文档生成系统

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![Vue](https://img.shields.io/badge/Vue-3.4%2B-green.svg)](https://vuejs.org)
[![Flask](https://img.shields.io/badge/Flask-2.0%2B-red.svg)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

这是一个基于人工智能的企业级需求分析和设计文档生成系统，采用前后端分离架构，结合大语言模型（LLM）、向量数据库和智能分析引擎，能够自动分析需求文档、生成设计文档、提供API接口建议，并支持实时对话交互。

## ✨ 核心功能

### 🔍 智能文档分析
- **多格式支持**: PDF、Word、图片、Markdown、文本等多种格式
- **智能解析**: 基于AI的文档内容理解和结构化提取
- **语义分析**: 结合向量数据库进行语义相似性分析
- **OCR识别**: 支持图片和扫描文档的文字识别
- **增量处理**: 支持大文档的分块处理和增量分析

### 🤖 AI驱动的需求分析
- **智能提取**: 自动提取业务需求、功能模块、数据字段
- **缺陷检测**: 智能识别需求文档中的问题和缺陷
- **关键词分析**: 提取业务关键词和技术关键词
- **相似性匹配**: 基于历史文档库进行相似需求匹配
- **多轮对话**: 支持与AI助手的实时交互式分析

### 🔌 API接口设计分析
- **接口识别**: 自动分析需要开发的API接口数量和类型
- **数据映射**: 识别每个接口需要的数据字段和结构
- **数据库分析**: 检查现有数据库字段的可用性和完整性
- **CRUD操作**: 自动生成增删改查操作建议
- **接口文档**: 生成详细的API设计文档和规范

### 📝 设计文档生成
- **模板化生成**: 基于企业模板生成标准化设计文档
- **多层次设计**: 包含系统架构、数据库设计、API设计等
- **前端设计**: 结合截图分析生成前端设计文档
- **技术方案**: 提供完整的技术实现方案和建议
- **文档导出**: 支持Markdown、PDF等多种格式导出

### 🗄️ 智能知识库系统
- **向量数据库**: 基于Weaviate/FAISS的高性能语义搜索
- **多源数据**: 支持DOCX、XLSX、Java、XML、PDF等多种文件
- **智能检索**: 自然语言查询，快速定位相关文档和代码
- **缓存优化**: Redis缓存机制，提升查询性能
- **增量更新**: 支持知识库内容的实时更新和维护

### ⚙️ 统一配置管理
- **YAML配置**: 基于config.yaml的统一配置管理
- **模块化配置**: LLM、数据库、缓存等模块独立配置
- **环境隔离**: 支持开发、测试、生产环境配置
- **安全管理**: API密钥和敏感信息的安全存储
- **配置验证**: 自动验证配置项的有效性和完整性

## 🛠️ 技术架构

### 系统架构图
```
┌─────────────────────────────────────────────────────────────────┐
│                         前端层 (Vue 3)                          │
├─────────────────────────────────────────────────────────────────┤
│  • Element Plus UI      • 实时聊天界面    • 文件上传管理        │
│  • WebSocket客户端      • 响应式设计      • 进度监控           │
└─────────────────┬───────────────────────────────────────────────┘
                  │ HTTP/WebSocket
┌─────────────────┴───────────────────────────────────────────────┐
│                         网关层                                   │
├─────────────────────────────────────────────────────────────────┤
│  • API Gateway (Flask)  • CORS处理       • 请求路由           │
│  • WebSocket Handler    • 身份认证       • 负载均衡           │
└─────────────────┬───────────────────────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────────────────────┐
│                      业务服务层                                 │
├─────────────────────────────────────────────────────────────────┤
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐          │
│  │  文档解析服务  │ │  AI分析服务   │ │  知识库服务   │          │
│  │               │ │               │ │               │          │
│  │ • PDF解析     │ │ • LLM调用     │ │ • 向量检索    │          │
│  │ • Word解析    │ │ • 需求分析    │ │ • 语义搜索    │          │
│  │ • OCR识别     │ │ • 设计生成    │ │ • 知识管理    │          │
│  └───────────────┘ └───────────────┘ └───────────────┘          │
└─────────────────┬───────────────────────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────────────────────┐
│                       数据层                                    │
├─────────────────────────────────────────────────────────────────┤
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐          │
│  │   任务存储    │ │   向量数据库   │ │   缓存层      │          │
│  │               │ │               │ │               │          │
│  │ • SQLite/     │ │ • Weaviate/   │ │ • Redis       │          │
│  │   Redis       │ │   FAISS       │ │ • 会话管理    │          │
│  │ • 任务队列    │ │ • 语义向量    │ │ • 结果缓存    │          │
│  └───────────────┘ └───────────────┘ └───────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### 核心技术栈

#### 前端技术栈
- **Vue 3.4+**: 现代响应式前端框架
- **Element Plus 2.4+**: 企业级UI组件库
- **Vite 4.5+**: 高性能构建工具
- **Pinia 2.1+**: 状态管理
- **Vue Router 4.2+**: 路由管理
- **WebSocket**: 实时双向通信
- **Axios**: HTTP客户端
- **Markdown-it**: Markdown渲染
- **PDF.js**: PDF预览支持

#### 后端技术栈
- **Python 3.8+**: 核心编程语言
- **Flask 2.0+**: 轻量级Web框架
- **Flask-SocketIO**: WebSocket支持
- **Flask-CORS**: 跨域资源共享
- **SQLAlchemy**: 数据库ORM
- **Pydantic**: 数据验证和序列化

#### AI与数据处理
- **火山引擎/DeepSeek**: 大语言模型服务
- **LangChain**: AI应用开发框架
- **Sentence-Transformers**: 文本向量化
- **Weaviate/FAISS**: 向量数据库
- **Redis**: 高性能缓存和会话存储
- **PyPDF2/PDFPlumber**: PDF文档处理
- **python-docx**: Word文档处理
- **Tesseract/EasyOCR**: 光学字符识别

#### 开发与部署
- **Poetry/pip**: 依赖管理
- **pytest**: 单元测试
- **Black/isort**: 代码格式化
- **Docker**: 容器化部署
- **Nginx**: 反向代理（可选）

## 🚀 快速开始

### 1. 环境要求

- **Python**: 3.8 或更高版本
- **Node.js**: 16.0 或更高版本
- **npm**: 7.0 或更高版本
- **内存**: 建议4GB或以上
- **存储**: 建议2GB可用空间

### 2. 获取代码

```bash
# 克隆项目
git clone [项目地址]
cd analyDesign
```

### 3. 后端环境配置

#### 自动化安装（推荐）
```powershell
# Windows PowerShell
powershell -ExecutionPolicy Bypass -File setup_env.ps1
```

#### 手动安装
```bash
# 创建虚拟环境
python -m venv analyDesign_env

# 激活虚拟环境
# Windows
call analyDesign_env\Scripts\activate.bat
# Linux/macOS
source analyDesign_env/bin/activate

# 安装Python依赖
pip install -r requirements.txt
```

### 4. 配置系统

编辑 `config.yaml` 文件，配置必要参数：

```yaml
# LLM配置 - 必须配置
volcengine:
  api_key: "你的火山引擎API密钥"
  endpoint: "https://ark.cn-beijing.volces.com/api/v3"
  model: "ep-20250605091804-wmw6w"  # 或其他可用模型
  temperature: 0.7
  max_tokens: 4000

# 向量数据库配置 - 可选
vector_database:
  type: weaviate  # 或 faiss
  weaviate:
    host: localhost
    port: 8080
    api_key: "root-user-key"
    default_collection:
      name: "AnalyDesignDocuments"

# Redis缓存配置 - 可选
redis:
  host: localhost
  port: 6379
  db: 0
  password: ""

# 应用配置
app:
  debug: false
  host: 0.0.0.0
  port: 8000
  name: AnalyDesign
```

### 5. 前端环境配置

```bash
cd frontend

# 安装依赖
npm install

# 或使用yarn
yarn install
```

### 6. 启动系统

#### 方式一：使用启动脚本（推荐）

```bash
# 启动后端服务
双击 start_back.bat
# 或
python run.py

# 启动前端服务
双击 启动前端.bat
# 或
cd frontend && npm run dev
```

#### 方式二：手动启动

```bash
# 终端1 - 启动后端
python run.py --mode full

# 终端2 - 启动前端
cd frontend
npm run dev
```

#### 方式三：检查服务状态

```bash
# 检查所有服务状态
双击 检查服务状态.bat
```

### 7. 访问系统

- **前端界面**: http://localhost:3000
- **后端API**: http://localhost:8082
- **WebSocket**: ws://localhost:8081/socket.io/
- **健康检查**: http://localhost:8082/api/health

## 📖 详细使用指南

### 步骤1：系统初始化
1. 确保所有服务正常启动
2. 检查配置文件中的API密钥设置
3. 验证向量数据库连接（如果使用）
4. 确认Redis缓存服务（如果使用）

### 步骤2：文档上传与处理
1. **选择文档**: 支持PDF、Word、图片、文本等格式
2. **上传文件**: 通过前端界面拖拽或选择文件上传
3. **实时监控**: 查看文件解析和处理进度
4. **错误处理**: 自动处理和反馈文件格式错误

### 步骤3：智能分析配置
1. **分析类型选择**:
   - 基础内容分析
   - 智能需求分析  
   - 全面深度分析
2. **参数配置**:
   - 分析深度级别
   - 输出格式偏好
   - 特定关注点

### 步骤4：实时对话交互
1. **AI助手对话**: 与智能分析助手实时交流
2. **问题澄清**: 针对需求不明确的地方进行深入询问
3. **补充信息**: 提供额外的上下文和业务背景
4. **迭代优化**: 基于反馈持续优化分析结果

### 步骤5：结果查看与导出
1. **分析报告**: 查看详细的需求分析报告
2. **设计文档**: 获取生成的技术设计文档
3. **API规范**: 查看推荐的API接口设计
4. **文档导出**: 支持Markdown、PDF等格式导出

### 步骤6：知识库管理（高级功能）
1. **知识库查询**:
   ```bash
   python query_knowledge_base.py
   ```
2. **自然语言查询**: 输入业务相关问题获取历史文档
3. **相似案例**: 查找类似的历史需求和解决方案
4. **知识更新**: 将新的分析结果加入知识库

## 📁 项目目录结构

```
analyDesign/
├── 🚀 启动与配置
│   ├── run.py                           # 主启动脚本
│   ├── config.yaml                      # 统一配置文件
│   ├── start_back.bat                   # 后端启动脚本
│   ├── 启动前端.bat                      # 前端启动脚本
│   ├── setup_env.ps1                    # 环境安装脚本
│   ├── activate_env.bat                 # 环境激活脚本
│   └── requirements.txt                 # Python依赖列表
│
├── 🐍 后端核心 (src/)
│   ├── apis/                            # API接口层
│   │   ├── api_server.py                # 主API服务器
│   │   ├── analysis_api.py              # 分析相关API
│   │   ├── file_api.py                  # 文件处理API
│   │   ├── task_api.py                  # 任务管理API
│   │   └── websocket_api.py             # WebSocket接口
│   │
│   ├── analysis_services/               # 分析服务层
│   │   ├── __init__.py                  # 服务管理器入口
│   │   ├── service_manager.py           # 服务管理器
│   │   ├── document_parser.py           # 文档解析服务
│   │   ├── content_analyzer.py          # 内容分析服务
│   │   ├── ai_analyzer.py               # AI分析服务
│   │   ├── vector_database.py           # 向量数据库服务
│   │   ├── base_service.py              # 基础服务类
│   │   └── test_services.py             # 服务测试
│   │
│   ├── utils/                           # 工具类库
│   │   ├── logger_config.py             # 日志配置
│   │   ├── volcengine_client.py         # 火山引擎客户端
│   │   ├── task_storage.py              # 任务存储
│   │   ├── redis_task_storage.py        # Redis任务存储
│   │   └── llm_logger.py                # LLM调用日志
│   │
│   ├── websockets/                      # WebSocket服务
│   │   └── websocket_server.py          # WebSocket服务器
│   │
│   └── resource/                        # 资源配置
│       └── config.py                    # 配置管理类
│
├── 🎨 前端界面 (frontend/)
│   ├── src/                             # 源代码目录
│   │   ├── components/                  # Vue组件
│   │   ├── views/                       # 页面视图
│   │   ├── router/                      # 路由配置
│   │   ├── store/                       # 状态管理
│   │   ├── utils/                       # 工具函数
│   │   ├── assets/                      # 静态资源
│   │   └── main.js                      # 入口文件
│   │
│   ├── package.json                     # 前端依赖配置
│   ├── vite.config.js                   # Vite构建配置
│   └── index.html                       # HTML模板
│
├── 📊 数据存储
│   ├── uploads/                         # 文件上传目录
│   │   ├── temp/                        # 临时文件
│   │   ├── cache/                       # 缓存文件
│   │   └── analysis_results/            # 分析结果
│   │
│   ├── outputs/                         # 输出文件目录
│   ├── logs/                            # 日志文件目录
│   ├── templates/                       # 文档模板目录
│   └── tasks.db                         # 任务数据库
│
├── 🧪 测试与工具
│   ├── tests/                           # 测试用例
│   ├── query_knowledge_base.py          # 知识库查询工具
│   └── 检查服务状态.bat                  # 服务状态检查
│
├── 📚 文档说明
│   ├── README.md                        # 项目说明（本文档）
│   ├── 快速安装指南.md                   # 安装指南
│   ├── 接口快速参考表.md                 # API参考
│   ├── 接口梳理总结.md                   # 接口文档
│   ├── 文件分析模块接口设计说明.md        # 模块设计说明
│   ├── 知识库使用说明.md                 # 知识库说明
│   ├── 环境配置说明.md                   # 环境配置
│   └── INTELLIGENT_ANALYSIS_README.md   # 智能分析说明
│
└── 🔧 环境与配置
    ├── .gitignore                       # Git忽略配置
    ├── .git/                            # Git版本控制
    └── analyDesign_env/                 # Python虚拟环境
```

## 🔧 高级配置

### LLM模型配置

支持多种大语言模型：

```yaml
# 火山引擎（推荐）
volcengine:
  api_key: "your_api_key"
  model: "ep-20250605091804-wmw6w"
  temperature: 0.7

# OpenAI GPT
openai:
  api_key: "your_openai_key"
  model: "gpt-3.5-turbo"
  base_url: "https://api.openai.com/v1"
```

### 向量数据库配置

#### Weaviate配置（推荐）
```yaml
vector_database:
  type: weaviate
  weaviate:
    host: localhost
    port: 8080
    scheme: http
    api_key: "root-user-key"
    default_collection:
      name: "AnalyDesignDocuments"
      vectorizer: none
      vector_dimension: 768
```

#### FAISS配置（轻量级）
```yaml
vector_database:
  type: faiss
  faiss:
    index_file: "uploads/cache/vector_index.faiss"
    metadata_file: "uploads/cache/vector_metadata.json"
```

### Redis缓存配置

```yaml
redis:
  host: localhost
  port: 6379
  db: 0
  password: ""
  connection_pool:
    max_connections: 50
  cache:
    default_ttl: 3600
    key_prefix: "analydesign:"
```

### 文件处理配置

```yaml
file_upload:
  max_size: 52428800  # 50MB
  allowed_extensions:
    - .txt
    - .md
    - .pdf
    - .docx
    - .doc
    - .pptx
    - .ppt
  temp_dir: uploads/temp

analysis:
  chunk_size: 1000
  overlap_size: 200
  max_content_length: 100000
  enable_ai_analysis: true
  enable_content_analysis: true
```

## 🔍 API接口文档

### 核心接口概览

| 接口路径 | 方法 | 功能 | 状态 |
|---------|------|------|------|
| `/api/health` | GET | 健康检查 | ✅ |
| `/api/chat` | POST | AI对话交互 | ✅ |
| `/api/file/upload` | POST | 文件上传 | ✅ |
| `/api/file/parsing/<task_id>` | GET | 解析状态查询 | ✅ |
| `/api/file/analyze/<task_id>` | POST | 内容分析 | ✅ |
| `/api/file/ai-analyze/<task_id>` | POST | AI深度分析 | ✅ |
| `/api/file/result/<task_id>` | GET | 分析结果获取 | ✅ |
| `/api/v2/analysis/start` | POST | 新版分析启动 | ✅ |
| `/api/v2/analysis/progress/<task_id>` | GET | 分析进度查询 | ✅ |

### WebSocket事件

| 事件名称 | 方向 | 描述 |
|---------|------|------|
| `connect` | Client → Server | 建立连接 |
| `disconnect` | Client → Server | 断开连接 |
| `message` | Client ↔ Server | 消息传递 |
| `progress_update` | Server → Client | 进度更新 |
| `analysis_complete` | Server → Client | 分析完成 |
| `error` | Server → Client | 错误通知 |

详细的API文档请参考：[接口快速参考表.md](接口快速参考表.md)

## 🧪 测试与验证

### 运行测试
```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试
python -m pytest tests/test_analysis_services.py

# 运行服务测试
python src/analysis_services/test_services.py
```

### 健康检查
```bash
# 检查后端API健康状态
curl http://localhost:8082/api/health

# 检查WebSocket连接
curl http://localhost:8081/api/health
```

### 功能验证
```bash
# 测试知识库查询
python query_knowledge_base.py

# 检查服务状态
双击 检查服务状态.bat
```

## 🔧 故障排除

### 常见问题

#### 1. 环境安装问题
```bash
# 重新安装环境
双击 重新安装环境.bat

# 手动清理环境
rmdir /s analyDesign_env
powershell -ExecutionPolicy Bypass -File setup_env.ps1
```

#### 2. 依赖安装失败
```bash
# 更新pip
python -m pip install --upgrade pip

# 使用清华源安装
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 3. 端口冲突
编辑 `config.yaml` 修改端口配置：
```yaml
app:
  port: 8000  # 修改为其他可用端口
```

#### 4. API密钥问题
确保在 `config.yaml` 中正确配置API密钥：
```yaml
volcengine:
  api_key: "your_valid_api_key_here"
```

#### 5. 前端启动失败
```bash
cd frontend
# 清理node_modules
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### 日志查看
- **应用日志**: `logs/app.log`
- **错误日志**: `logs/error.log`
- **分析日志**: `logs/analysis.log`

## 🤝 贡献指南

### 开发环境设置
1. Fork项目到个人仓库
2. 克隆个人仓库到本地
3. 创建开发分支
4. 安装开发依赖

### 代码规范
- **Python**: 遵循PEP 8规范
- **JavaScript**: 使用ESLint配置
- **Vue**: 遵循Vue 3最佳实践
- **提交信息**: 使用Conventional Commits格式

### 提交流程
1. 编写代码和测试
2. 运行测试确保通过
3. 提交代码并推送到个人仓库
4. 创建Pull Request

## 📄 许可证

本项目采用 [MIT License](LICENSE) 许可证。

## 🆘 技术支持

- **问题反馈**: [GitHub Issues](项目地址/issues)
- **功能建议**: [GitHub Discussions](项目地址/discussions)
- **邮箱支持**: [support@analydesign.com](mailto:support@analydesign.com)

## 🔄 版本历史

### v1.0.0 (当前版本)
- ✅ 完整的前后端分离架构
- ✅ 智能文档分析和AI对话功能
- ✅ 向量数据库和知识库支持
- ✅ 多种LLM模型集成
- ✅ 实时WebSocket通信
- ✅ 完善的配置管理系统

### 计划功能
- 📋 用户权限管理系统
- 📊 可视化数据报表
- 🔄 批处理任务支持
- 🌐 多语言国际化支持
- 📱 移动端响应式优化

---

**🌟 如果这个项目对你有帮助，请给我们一个Star！**