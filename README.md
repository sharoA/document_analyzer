# 智能文档分析系统 (Intelligent Document Analysis System)

## 简介

本项目是一个功能强大的文档分析系统，旨在利用AI技术自动处理和分析用户上传的文档。系统能够解析多种格式的文档，提取关键信息，进行深度内容分析，并将结果存储在向量数据库中以供查询。此外，系统还具备根据分析结果生成代码的能力，并提供一个现代化的Web界面进行交互。

## 主要功能

*   **文档上传与解析**: 支持用户上传文档，并能解析多种常见的文档格式。
*   **AI内容分析**: 利用大型语言模型 (LLM) 和 LangChain 框架对文档内容进行深入分析、摘要和信息提取。
*   **向量化与知识库**: 将文档内容向量化并存储在 Weaviate 向量数据库中，构建可供检索的知识库。
*   **代码生成**: 基于对需求的分析，能够自动化生成前端和后端代码的初步框架。
*   **Web用户界面**: 提供一个基于 Vue.js 的现代化、用户友好的界面，用于上传文档、查看分析结果和管理项目。
*   **任务状态管理**: 异步处理分析任务，并允许用户查询任务进度。

## 技术栈

*   **后端**:
    *   **框架**: Python, FastAPI
    *   **AI/LLM**: LangChain
    *   **数据库**: Weaviate (向量数据库), SQLite (任务和元数据存储)
    *   **依赖管理**: pip

*   **前端**:
    *   **框架**: Vue.js 3
    *   **构建工具**: Vite
    *   **UI 库**: Element Plus
    *   **依赖管理**: npm

## 项目结构

```
.
├── frontend/         # 前端 Vue.js 应用
│   ├── src/
│   └── package.json
├── src/              # 后端 Python 应用
│   ├── apis/         # FastAPI 接口定义
│   ├── analysis_services/ # 核心分析服务
│   ├── corder_integration/ # 代码生成器集成
│   └── utils/        # 工具函数
├── uploads/          # 用户上传的原始文件
├── outputs/          # 分析后生成的报告
├── templates/        # Prompt 和报告模板
├── config.yaml       # 项目配置文件
├── requirements.txt  # Python 依赖
├── run.py            # 后端应用启动脚本
└── README.md         # 项目说明文档
```

## 安装与运行

### 1. 环境准备

*   安装 Python 3.8+
*   安装 Node.js 16+
*   (可选) 推荐使用虚拟环境 (e.g., venv)

### 2. 后端设置

```bash
# 1. 克隆项目
git clone <repository_url>
cd document_analyzer

# 2. (可选) 创建并激活虚拟环境
python -m venv venv
source venv/bin/activate  # on Windows use `venv\Scripts\activate`

# 3. 安装 Python 依赖
pip install -r requirements.txt

# 4. 配置
#    根据需要修改 `config.yaml` 文件，例如配置API密钥、数据库地址等。
```

### 3. 前端设置

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装 Node.js 依赖
npm install

# 3. (可选) 配置
#    如果前端需要连接到不同的后端地址，请修改 `vite.config.js` 中的代理设置。
```

### 4. 运行项目

*   **启动后端服务**:
    在项目根目录下运行：
    ```bash
    python run.py
    ```
    API 服务默认会在 `http://127.0.0.1:8765` 启动。

*   **启动前端服务**:
    在 `frontend` 目录下运行：
    ```bash
    npm run dev
    ```
    前端开发服务器通常会运行在 `http://localhost:5173`。

## 使用说明

1.  启动后端和前端服务。
2.  通过浏览器访问前端地址。
3.  在Web界面上传您需要分析的文档。
4.  发起分析任务，并等待系统处理。
5.  在界面上查看分析结果、生成的报告或代码。

## 主要API端点

项目通过 FastAPI 提供了一系列 RESTful API。

*   `POST /api/analysis/upload`: 上传文档进行分析。
*   `GET /api/analysis/tasks/{task_id}`: 查询分析任务的状态和进度。
*   `GET /api/analysis/results/{task_id}`: 获取特定任务的分析结果。
*   `POST /api/coder/generate`: 请求代码生成。

更详细的API定义请参考 `src/apis/` 目录下的代码。
