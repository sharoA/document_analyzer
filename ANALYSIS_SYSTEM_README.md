# 智能文档分析系统

一个基于Vue 3 + Flask的智能文档分析系统，支持三阶段分析流程：文档解析、内容分析、AI智能分析。

## 系统架构

- **前端**: Vue 3 + Element Plus (端口 3000)
- **后端API**: Flask (端口 8082)
- **数据存储**: Redis (用于进度和结果存储)
- **分析引擎**: 三阶段分析服务

## 功能特性

### 三阶段分析流程

1. **文档解析阶段**
   - 文件格式识别
   - 结构解析
   - 内容提取
   - 质量分析

2. **内容分析阶段**
   - 功能变更识别
   - 新增/修改/删除功能提取
   - 关键变更分析

3. **AI智能分析阶段**
   - 需求提取
   - 技术设计建议
   - 实现方案推荐

### 执行模式

- **自动模式**: 一键执行完整分析流程
- **手动模式**: 逐步执行各个分析阶段

### 进度监控

- 实时进度条显示
- 独立阶段进度跟踪
- 自动轮询更新

## 快速开始

### 1. 环境准备

确保已安装以下软件：
- Python 3.8+
- Node.js 16+
- Redis 6+

### 2. 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt

# 安装前端依赖
cd frontend
npm install
cd ..
```

### 3. 启动Redis

```bash
# Windows
redis-server

# Linux/Mac
sudo systemctl start redis
# 或
redis-server
```

### 4. 启动系统

```bash
# 使用一键启动脚本
python start_analysis_system.py

# 或者分别启动
# 启动API服务器
python -m src.apis.enhanced_api

# 启动前端服务器
cd frontend && npm run dev
```

### 5. 访问系统

- 前端界面: http://localhost:3000
- API文档: http://localhost:8082/api/v2/health

## 使用指南

### 上传文档

1. 在主界面选择文件上传
2. 支持格式：txt, doc, docx, pdf
3. 选择执行模式（自动/手动）
4. 点击上传开始分析

### 监控进度

- 自动模式：系统自动执行所有阶段，实时显示进度
- 手动模式：手动点击各阶段的"开始"按钮
- 进度条显示每个阶段的完成百分比（0-100%）

### 查看结果

1. 等待所有阶段完成
2. 点击"查看结果"按钮
3. 在标签页中查看各阶段的分析结果
4. 可导出完整分析报告

## API接口

### 主要接口

- `POST /api/v2/analysis/start` - 开始分析
- `POST /api/v2/analysis/stage` - 执行单个阶段
- `GET /api/v2/analysis/progress/{task_id}` - 查询进度
- `GET /api/v2/analysis/result/{task_id}` - 获取结果
- `GET /api/v2/analysis/export/{task_id}` - 导出结果

### 接口示例

```bash
# 健康检查
curl http://localhost:8082/api/v2/health

# 开始分析
curl -X POST http://localhost:8082/api/v2/analysis/start \
  -H "Content-Type: application/json" \
  -d '{
    "execution_mode": "automatic",
    "file_name": "test.txt",
    "file_content": "这是测试文档内容..."
  }'

# 查询进度
curl http://localhost:8082/api/v2/analysis/progress/{task_id}
```

## 技术细节

### 前端技术栈

- Vue 3 Composition API
- Element Plus UI组件库
- Axios HTTP客户端
- Vite构建工具

### 后端技术栈

- Flask Web框架
- Redis数据存储
- ThreadPoolExecutor后台任务
- 同步API设计

### 数据流程

1. 前端上传文件 → API接收请求
2. API启动后台分析任务 → 返回任务ID
3. 后台执行三阶段分析 → 更新Redis进度
4. 前端轮询进度接口 → 实时显示进度
5. 分析完成 → 前端获取结果

## 故障排除

### 常见问题

1. **Redis连接失败**
   - 确保Redis服务正在运行
   - 检查端口6379是否被占用

2. **前端无法访问API**
   - 检查API服务器是否在8082端口运行
   - 确认CORS配置正确

3. **分析任务卡住**
   - 检查Redis中的任务状态
   - 重启API服务器

### 日志查看

- API服务器日志：控制台输出
- 前端日志：浏览器开发者工具
- Redis数据：使用Redis客户端查看

## 开发说明

### 项目结构

```
├── frontend/                 # Vue 3前端
│   ├── src/
│   │   ├── components/      # 组件
│   │   ├── router/          # 路由
│   │   └── stores/          # 状态管理
├── src/                     # Python后端
│   ├── apis/                # API接口
│   ├── analysis_services/   # 分析服务
│   └── utils/               # 工具类
├── start_analysis_system.py # 启动脚本
└── requirements.txt         # Python依赖
```

### 扩展开发

1. **添加新的分析阶段**
   - 在`sync_service_manager.py`中添加新阶段
   - 更新前端组件显示

2. **集成真实AI服务**
   - 替换mock方法为真实AI调用
   - 配置API密钥和端点

3. **支持更多文件格式**
   - 扩展文档解析器
   - 更新前端文件类型限制

## 许可证

MIT License 