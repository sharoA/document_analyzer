# 🚀 LangGraph编码智能体

基于 `LangGraph可执行实现.md` 实现的完整编码智能体系统，支持多服务协调、任务拆分调度、并行处理的智能编码工作流。

## ✨ 核心特性

### 🧠 智能工作流
- **任务拆分**：自动识别微服务边界和依赖关系
- **Git管理**：完整的版本控制和分支管理
- **智能编码**：并行生成Spring Boot微服务代码
- **代码审查**：AI驱动的代码质量检查
- **单元测试**：自动生成和执行测试用例
- **自动提交**：智能Git提交和PR创建

### 🔧 技术架构
- **LangGraph框架**：状态管理和工作流编排
- **Jinja2模板**：可配置的提示词系统
- **异步处理**：支持并行微服务生成
- **检查点机制**：支持PostgreSQL/内存检查点
- **错误恢复**：完善的重试和容错机制

## 📁 目录结构

```
src/corder_integration/langgraph/
├── workflow_orchestrator.py      # 🎯 工作流编排器
├── nodes/                         # 🧠 智能体节点
│   ├── task_splitting_node.py    # 任务拆分节点
│   ├── git_management_node.py    # Git管理节点
│   ├── intelligent_coding_node.py # 智能编码节点
│   ├── code_review_node.py       # 代码审查节点
│   ├── unit_testing_node.py      # 单元测试节点
│   └── git_commit_node.py        # Git提交节点
├── prompts/                       # 📝 提示词模板
│   ├── task_splitting_prompts.jinja2
│   └── intelligent_coding_prompts.jinja2
└── README.md                      # 📖 使用说明
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements_langgraph.txt
```

### 2. 配置环境变量

```bash
export OPENAI_API_KEY="your-openai-api-key"
export POSTGRES_CONNECTION_STRING="postgresql://user:pass@localhost/db"  # 可选
```

### 3. API调用示例

```python
import requests

# 调用LangGraph编码智能体
response = requests.post('http://localhost:5000/api/coder-agent/process-document', json={
    "document_content": """
    电商订单系统需求：
    1. 用户服务：用户注册、登录、用户信息管理
    2. 产品服务：产品展示、库存管理、价格管理
    3. 订单服务：订单创建、支付处理、订单状态管理
    4. 通知服务：订单状态变更通知、用户消息推送
    
    设计文档:
    技术设计：
    - 架构：Spring Boot微服务架构
    - 注册中心：Nacos
    - 数据库：MySQL + MyBatis
    - 服务间调用：Feign + RestTemplate
    
    Git仓库：https://github.com/company/ecommerce-system.git
    """,
    "project_name": "ecommerce-system",
    "use_langgraph": true
})

print(response.json())
```

### 4. 响应格式

```json
{
    "status": "success",
    "workflow_type": "langgraph",
    "data": {
        "project_name": "ecommerce-system",
        "execution_summary": {
            "total_services": 4,
            "completed_services": 4,
            "failed_services": 0,
            "test_coverage": {
                "UserService": 0.85,
                "ProductService": 0.88,
                "OrderService": 0.90,
                "NotificationService": 0.82
            },
            "generated_services": {...},
            "commit_hashes": {...},
            "pr_urls": {...}
        }
    }
}
```

## 🔄 工作流详解

### 1. 任务拆分节点
- 📋 需求分析：提取功能模块和业务流程
- 🏗️ 设计分析：识别技术栈和架构模式
- 🔍 服务拆分：确定微服务边界
- 🌐 依赖分析：构建服务依赖图
- 📅 调度规划：制定并行执行计划

### 2. Git管理节点
- 🔍 仓库检测：自动识别Git仓库URL
- 📁 目录创建：为每个服务创建项目目录
- 🌿 分支管理：创建feature分支
- 🔧 环境准备：初始化Git环境

### 3. 智能编码节点
- 📋 需求分析：细化服务技术要求
- 💻 代码生成：生成完整Spring Boot项目
- 🌐 API设计：设计RESTful接口
- 🔗 服务互联：实现服务间调用

### 4. 代码审查节点
- 🔍 质量检查：代码规范和性能分析
- 🛡️ 安全扫描：识别安全风险
- 🏗️ 架构一致性：检查设计模式一致性
- 📊 评分报告：生成质量评估报告

### 5. 单元测试节点
- 🧪 测试生成：自动生成JUnit测试
- ⚡ 测试执行：运行测试套件
- 📈 覆盖率统计：计算测试覆盖率
- 🔗 兼容性检查：验证服务间接口

### 6. Git提交节点
- 📝 提交信息：生成规范的commit message
- 💾 代码提交：提交所有生成的代码
- 🚀 远程推送：推送到远程仓库
- 🔗 PR创建：生成Pull Request

## ⚙️ 配置选项

### 工作流配置

```python
# 使用PostgreSQL检查点（生产环境）
orchestrator = LangGraphWorkflowOrchestrator(use_postgres=True)

# 使用内存检查点（开发环境）
orchestrator = LangGraphWorkflowOrchestrator(use_postgres=False)
```

### 提示词自定义

提示词模板位于 `prompts/` 目录下，使用Jinja2格式，支持：
- 🔧 参数化模板
- 🎯 条件渲染
- 🔄 模板继承
- 📦 模块化设计

## 📊 监控和调试

### 日志系统
```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

### 状态检查
```python
# 获取工作流状态
status = orchestrator.get_workflow_status(thread_id)
```

### 错误处理
- ✅ 自动重试机制
- 🔄 状态回滚支持
- 📊 详细错误报告
- 🚨 异常监控

## 🎯 最佳实践

1. **文档格式**：确保需求文档和设计文档分离清晰
2. **Git配置**：提供完整的Git仓库URL
3. **环境变量**：正确配置OpenAI API密钥
4. **依赖管理**：安装所有必需的依赖包
5. **错误监控**：关注日志输出和错误信息

## 🔧 故障排除

### 常见问题

1. **提示词加载失败**
   ```
   解决：检查prompts目录下的.jinja2文件是否存在
   ```

2. **Git操作失败**
   ```
   解决：确保Git环境正确配置，有权限访问仓库
   ```

3. **OpenAI API错误**
   ```
   解决：检查API密钥配置和网络连接
   ```

4. **依赖导入错误**
   ```
   解决：安装requirements_langgraph.txt中的所有依赖
   ```

## 📈 性能优化

- 🚀 **并行处理**：同时处理多个微服务
- 💾 **检查点机制**：支持工作流中断恢复
- 🔄 **智能重试**：区分不同类型的错误
- 📊 **资源监控**：监控内存和CPU使用

## 🤝 贡献指南

1. Fork本项目
2. 创建feature分支
3. 提交更改
4. 创建Pull Request

欢迎贡献代码、报告问题或提出改进建议！

---

**Built with ❤️ using LangGraph and OpenAI GPT-4** 