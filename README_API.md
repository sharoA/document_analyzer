# analyDesign API服务器配置说明

## 🚀 快速开始

### 1. 后端API服务器已启动
- **地址**: http://localhost:8080
- **状态**: ✅ 运行中
- **端口**: 8080

### 2. 前端应用
- **地址**: http://localhost:3000
- **状态**: ✅ 运行中
- **模式**: API模式（已连接后端）

## 🔧 火山引擎配置

### 配置步骤：

1. **获取火山引擎API密钥**
   - 登录火山引擎控制台
   - 创建或选择您的模型
   - 获取API Key和模型ID

2. **修改配置文件**
   
   编辑 `api_server.py` 文件中的配置：
   ```python
   VOLCANO_ENGINE_CONFIG = {
       "api_key": "your_volcano_engine_api_key",  # 替换为您的API密钥
       "endpoint": "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
       "model": "ep-20241230140956-8xqvs",  # 替换为您的模型ID
       "timeout": 30
   }
   ```

3. **重启后端服务器**
   ```bash
   # 停止当前服务器 (Ctrl+C)
   # 重新启动
   python api_server.py
   ```

## 📡 API接口说明

### 聊天接口
- **URL**: `POST /api/chat`
- **功能**: 与火山引擎AI进行对话
- **请求格式**:
  ```json
  {
    "message": "用户输入的消息",
    "session_id": "会话ID（可选）"
  }
  ```
- **响应格式**:
  ```json
  {
    "success": true,
    "response": "AI回复内容",
    "session_id": "会话ID",
    "confidence": 0.9,
    "timestamp": "2024-01-01T12:00:00"
  }
  ```

### 健康检查
- **URL**: `GET /api/health`
- **功能**: 检查服务器状态

### 会话管理
- **获取所有会话**: `GET /api/sessions`
- **获取特定会话**: `GET /api/sessions/{session_id}`
- **删除会话**: `DELETE /api/sessions/{session_id}`

## 🔄 当前状态

### ✅ 已完成
- [x] 后端API服务器搭建
- [x] 前端API集成
- [x] 跨域配置
- [x] 错误处理
- [x] 会话管理
- [x] 实时交互界面

### ⚠️ 需要配置
- [ ] 火山引擎API密钥
- [ ] 火山引擎模型ID

## 🧪 测试功能

1. **打开前端应用**: http://localhost:3000
2. **查看连接状态**: 应显示"已连接"
3. **发送测试消息**: 在输入框中输入任何问题
4. **查看响应**: 
   - 如果配置了火山引擎：将显示AI回复
   - 如果未配置：将显示错误提示

## 🛠️ 故障排除

### 前端显示连接错误
- 检查后端服务器是否运行在8080端口
- 检查防火墙设置

### 火山引擎调用失败
- 验证API密钥是否正确
- 检查模型ID是否有效
- 确认网络连接正常

### 服务器启动失败
- 检查端口8080是否被占用
- 确认Python依赖已安装：`pip install flask flask-cors requests`

## 📞 支持

如需帮助，请检查：
1. 浏览器控制台错误信息
2. 后端服务器日志
3. 网络连接状态

---

**🎉 恭喜！您的analyDesign智能需求分析系统已经可以与火山引擎进行实时交互了！** 