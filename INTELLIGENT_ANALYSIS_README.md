# 智能文档分析系统

基于Redis存储和HTTP轮询的智能文档分析系统，支持三阶段分析流程：文档解析 → 内容分析 → AI智能分析。

## 🚀 功能特性

- **三阶段分析流程**：文档解析、内容分析、AI智能分析
- **Redis数据存储**：每个节点数据存储到Redis，支持节点间数据传递
- **HTTP轮询通信**：稳定可靠的前后端实时进度交互
- **多格式支持**：PDF、Word、Excel、PowerPoint、Markdown、TXT等
- **Markdown报告**：JSON结果自动转换为Markdown格式展示
- **完整API接口**：简化的RESTful API设计

## 📁 项目结构

```
analyDesign/
├── src/
│   ├── apis/
│   │   └── analysis_api.py          # 智能分析API服务
│   ├── analysis_services/           # 分析服务模块
│   │   ├── document_parser.py       # 文档解析服务
│   │   ├── content_analyzer.py      # 内容分析服务
│   │   └── ai_analyzer.py          # AI智能分析服务
│   └── utils/
│       └── redis_util.py           # Redis工具类
├── frontend/src/components/
│   └── DocumentAnalysis.vue        # 前端分析组件
├── uploads/                        # 文件上传目录
│   ├── temp/                       # 临时文件
│   ├── cache/                      # 缓存文件
│   └── analysis_results/           # 分析结果
├── logs/                           # 日志目录
├── run_analysis_api.py             # API启动脚本
├── test_analysis_api.py            # API测试脚本
└── config.yaml                     # 系统配置文件
```

## 🛠️ 环境要求

### 后端依赖
- Python 3.8+
- Redis 服务器
- Flask
- 火山引擎API密钥

### 前端依赖
- Node.js 16+
- Vue 2
- Element Plus

## ⚙️ 配置说明

### 1. 配置文件 (config.yaml)

```yaml
# Redis配置
redis:
  host: localhost
  port: 6379
  db: 0
  password: ''

# 火山引擎配置
volcengine:
  api_key: 'your_api_key_here'
  endpoint: https://ark.cn-beijing.volces.com/api/v3
  model: ep-20241211150018-nh8rw

# 文件上传配置
file_upload:
  max_size: 52428800  # 50MB
  allowed_extensions: ['.txt', '.md', '.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt']

# 目录配置
directories:
  uploads: uploads
  temp: uploads/temp
```

## 🚀 快速开始

### 1. 启动Redis服务

```bash
# 使用Docker启动Redis（推荐）
docker run -d --name redis -p 6379:6379 redis:latest

# 或者使用本地Redis服务
redis-server
```

### 2. 配置环境

```bash
# 安装Python依赖
pip install -r requirements.txt

# 安装前端依赖
cd frontend
npm install
```

### 3. 启动后端API服务

```bash
# 方式1：使用启动脚本
python run_analysis_api.py

# 方式2：直接运行
python -m src.apis.analysis_api
```

### 4. 启动前端服务

```bash
cd frontend
npm run dev
```

### 5. 访问系统

- 前端界面：http://localhost:3000
- 后端API：http://localhost:8082

## 🔧 API接口说明

### 核心接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/analysis` | 上传文件并启动分析 |
| GET | `/api/analysis/{task_id}` | 获取分析进度 |
| GET | `/api/analysis/{task_id}/result` | 获取分析结果（Markdown） |
| DELETE | `/api/analysis/{task_id}` | 取消分析任务 |
| GET | `/api/health` | 健康检查 |

### 接口详情

#### 1. 启动分析
```http
POST /api/analysis
Content-Type: multipart/form-data

file: [文件内容]
```

**响应示例：**
```json
{
  "status": "started",
  "task_id": "uuid-string",
  "message": "分析已启动",
  "basic_info": {
    "filename": "document.pdf",
    "filesize": "2.5MB",
    "file_type": "pdf"
  }
}
```

#### 2. 获取进度
```http
GET /api/analysis/{task_id}
```

**响应示例：**
```json
{
  "task_id": "uuid-string",
  "basic_info": {...},
  "progress": {
    "status": "running",
    "overall_progress": 66,
    "current_stage": "content_analysis",
    "stages": {
      "document_parsing": {
        "status": "completed",
        "progress": 100,
        "message": "文档解析完成"
      },
      "content_analysis": {
        "status": "running",
        "progress": 50,
        "message": "正在分析内容..."
      },
      "ai_analysis": {
        "status": "pending",
        "progress": 0,
        "message": "等待开始"
      }
    }
  }
}
```

#### 3. 获取结果
```http
GET /api/analysis/{task_id}/result
```

**响应示例：**
```json
{
  "status": "success",
  "task_id": "uuid-string",
  "format": "markdown",
  "content": "# 文档分析报告...",
  "raw_data": {...}
}
```

## 🏗️ 分析流程架构

### 数据流程

```
文件上传 → Redis存储基本信息
    ↓
阶段1：文档解析
    ↓ (结果存储到Redis)
阶段2：内容分析 ← (从Redis读取上一阶段结果)
    ↓ (结果存储到Redis)
阶段3：AI智能分析 ← (从Redis读取前两阶段结果)
    ↓ (最终结果存储到Redis)
组装完整结果 → JSON转Markdown
```

### Redis数据结构

```
analysis:{task_id}:basic_info         # 基本信息
analysis:{task_id}:progress          # 进度信息
analysis:{task_id}:document_parsing  # 文档解析结果
analysis:{task_id}:content_analysis  # 内容分析结果
analysis:{task_id}:ai_analysis       # AI分析结果
analysis:{task_id}:result            # 最终完整结果
```

### 轮询机制

- **前端轮询频率**：每2秒轮询一次进度
- **自动停止**：分析完成或失败时停止轮询
- **错误处理**：网络错误时自动重试
- **状态恢复**：页面刷新后可恢复轮询状态

## 🧪 测试与验证

### 1. 运行API测试

```bash
# 确保API服务正在运行
python test_analysis_api.py
```

### 2. 手动测试步骤

1. **健康检查**：访问 http://localhost:8082/api/health
2. **上传文件**：使用前端界面或Postman上传测试文件
3. **监控进度**：观察三个阶段的进度变化
4. **查看结果**：分析完成后查看Markdown格式报告

### 3. 测试文件示例

支持上传各种格式的文档文件：
- 需求文档（Word/PDF）
- 技术文档（Markdown）
- 数据表格（Excel）
- 演示文稿（PowerPoint）

## 🔍 故障排除

### 常见问题

1. **Redis连接失败**
   - 检查Redis服务是否启动
   - 确认配置文件中的Redis连接信息

2. **火山引擎API错误**
   - 检查API密钥是否正确
   - 确认网络连接和访问权限

3. **文件上传失败**
   - 检查文件格式是否支持
   - 确认文件大小不超过限制

4. **分析进度卡住**
   - 查看后端日志了解具体错误
   - 检查分析服务是否正常运行

### 日志查看

```bash
# 查看API服务日志
tail -f logs/api_server.log

# 查看分析服务日志
tail -f logs/analysis_service.log
```

## 📊 性能优化

### Redis优化
- 设置合理的过期时间（24小时）
- 使用连接池提高并发性能
- 监控内存使用情况

### API优化
- 使用线程池处理后台分析任务
- 实现任务队列机制防止过载
- 添加缓存减少重复计算

### 前端优化
- 智能轮询频率调整
- 组件化分析界面
- 结果缓存机制

## 🔮 扩展功能

### 计划中的功能
- [ ] 支持批量文件分析
- [ ] 分析结果对比功能
- [ ] 自定义分析模板
- [ ] 分析历史管理
- [ ] 导出多种格式报告

### 集成建议
- 集成到现有文档管理系统
- 支持企业级身份认证
- 添加审批流程管理
- 集成通知推送功能

## 📝 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🤝 贡献指南

欢迎提交问题和功能请求！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解贡献指南。

---

**联系方式**：如有问题请提交 Issue 或发送邮件至 [your-email@example.com] 