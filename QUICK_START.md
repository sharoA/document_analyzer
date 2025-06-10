# 智能文档分析系统 - 快速启动指南

## 🚀 一分钟快速启动

### 1. 环境检查
确保已安装：
- Python 3.8+
- Node.js 16+
- Redis 6+

### 2. 启动Redis
```bash
# Windows
redis-server

# Linux/Mac
redis-server
```

### 3. 安装依赖
```bash
# Python依赖
pip install flask flask-cors redis

# 前端依赖
cd frontend && npm install && cd ..
```

### 4. 启动系统
```bash
# 一键启动（推荐）
python start_analysis_system.py

# 或分别启动
python -m src.apis.enhanced_api  # API服务器
cd frontend && npm run dev       # 前端服务器
```

### 5. 访问系统
- 🌐 前端界面: http://localhost:3000
- 📡 API服务: http://localhost:8082
- ❤️ 健康检查: http://localhost:8082/api/v2/health

## 🧪 快速测试

```bash
# 运行系统测试
python test_system.py
```

## 📋 使用步骤

1. **上传文档**
   - 访问 http://localhost:3000
   - 拖拽或点击上传文档文件
   - 选择执行模式（自动/手动）

2. **监控进度**
   - 自动模式：系统自动执行所有阶段
   - 手动模式：手动点击各阶段"开始"按钮
   - 实时查看进度条更新

3. **查看结果**
   - 等待所有阶段完成（进度条100%）
   - 点击"查看结果"按钮
   - 在标签页中查看各阶段分析结果
   - 可导出完整分析报告

## 🔧 故障排除

### Redis连接失败
```bash
# 检查Redis是否运行
redis-cli ping
# 应该返回 PONG

# 如果没有安装Redis
# Windows: 下载Redis for Windows
# Linux: sudo apt install redis-server
# Mac: brew install redis
```

### 端口被占用
```bash
# 检查端口占用
netstat -an | grep :3000  # 前端端口
netstat -an | grep :8082  # API端口
netstat -an | grep :6379  # Redis端口
```

### 前端无法访问API
- 确认API服务器在8082端口运行
- 检查防火墙设置
- 确认CORS配置正确

## 📊 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Vue 3 前端    │    │   Flask API     │    │     Redis       │
│   (端口 3000)   │◄──►│   (端口 8082)   │◄──►│   (端口 6379)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
    用户界面交互              API接口处理              数据存储
    进度监控                  后台任务管理              进度/结果缓存
    结果展示                  三阶段分析                任务状态管理
```

## 🎯 核心功能

### 三阶段分析
1. **文档解析** - 文件格式识别、结构解析、内容提取
2. **内容分析** - 功能变更识别、关键信息提取
3. **AI智能分析** - 需求提取、技术设计、实现建议

### 执行模式
- **自动模式** - 一键执行完整流程
- **手动模式** - 逐步控制各阶段执行

### 实时监控
- 独立进度条显示各阶段完成度
- 自动轮询更新（每2秒）
- 当前执行阶段高亮显示

## 📝 API接口示例

```bash
# 健康检查
curl http://localhost:8082/api/v2/health

# 开始分析
curl -X POST http://localhost:8082/api/v2/analysis/start \
  -H "Content-Type: application/json" \
  -d '{
    "execution_mode": "automatic",
    "file_name": "test.txt",
    "file_content": "测试文档内容..."
  }'

# 查询进度
curl http://localhost:8082/api/v2/analysis/progress/{task_id}

# 获取结果
curl http://localhost:8082/api/v2/analysis/result/{task_id}
```

## 🎉 完成！

现在你可以开始使用智能文档分析系统了！

如有问题，请查看详细文档：`ANALYSIS_SYSTEM_README.md` 