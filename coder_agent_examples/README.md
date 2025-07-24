# 编码智能体使用指南

## 概述

编码智能体是一个AI驱动的代码生成工具，能够根据markdown格式的详细设计文档自动生成高质量的前后端代码，并完成完整的开发流程。

## 核心功能

- 📖 **智能文档解析**: 解析markdown格式的详细设计文档
- 🗂️ **任务自动分解**: 将开发需求分解为可执行的任务单元
- 🔧 **环境自动准备**: Git分支管理和项目环境设置
- 💻 **代码自动生成**: 支持Java8+Spring Boot后端和Vue2前端
- 🧪 **单元测试生成**: 自动生成高质量的单元测试代码
- 📦 **版本控制集成**: 自动提交和推送到Git仓库

## 技术栈支持

### 后端 (Java8 + Spring Boot)
- Spring Boot 2.7.x
- DDD架构设计
- MyBatis ORM框架
- Swagger/OpenAPI 3.0
- JUnit5 + Mockito测试
- Maven构建工具

### 前端 (Vue2)
- Vue2 + TypeScript(可选)
- Vue Router路由
- Pinia状态管理
- Axios HTTP客户端
- Element Plus/Ant Design Vue UI框架
- Jest测试框架

## 快速开始

### 1. 环境准备

确保您的系统已安装以下工具：
- Python 3.8+
- Node.js 16+
- Java 8+
- Maven 3.6+
- Git

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置文件

在 `config.yaml` 中配置编码智能体参数：

```yaml
coder_agent:
  project_root: "/Users/renyu/Documents/create_project"
  backend_framework: "spring_boot"
  frontend_framework: "vue2"
  # ... 其他配置
```

## 使用方法

### 方法1: 命令行接口

#### 生成代码（完整流程）
```bash
python coder_agent_main.py generate --file design_document.md --project my-project
```

#### 仅创建执行计划
```bash
python coder_agent_main.py generate --file design_document.md --project my-project --plan-only
```

#### 执行已保存的计划
```bash
python coder_agent_main.py execute --plan-id PLAN_ID
```

#### 查看项目状态
```bash
python coder_agent_main.py status --path /path/to/project
```

#### 列出近期任务
```bash
python coder_agent_main.py list --limit 20
```

#### Git操作
```bash
# 设置Git环境
python coder_agent_main.py git setup --project-name my-project --branch feature/new-module

# 提交代码
python coder_agent_main.py git commit --message "feat: 添加用户管理模块"
```

### 方法2: Python API

```python
import asyncio
from src.corder_integration.coder_agent import CoderAgent

async def main():
    # 创建智能体实例
    agent = CoderAgent()
    
    # 读取设计文档
    with open('design_document.md', 'r', encoding='utf-8') as f:
        document_content = f.read()
    
    # 处理文档并生成代码
    result = await agent.process_design_document(
        document_content=document_content,
        project_name="my-project",
        execute_immediately=True
    )
    
    if result['status'] == 'success':
        print("✅ 代码生成成功!")
        print(f"任务ID: {result['task_id']}")
    else:
        print(f"❌ 生成失败: {result['error']}")

# 运行
asyncio.run(main())
```

### 方法3: REST API

启动API服务器：
```bash
python run.py
```

#### 处理设计文档
```bash
curl -X POST http://localhost:8000/api/coder-agent/process-document \
  -H "Content-Type: application/json" \
  -d '{
    "document_content": "# 项目设计文档...",
    "project_name": "my-project",
    "execute_immediately": true
  }'
```

#### 执行计划
```bash
curl -X POST http://localhost:8000/api/coder-agent/execute-plan/PLAN_ID
```

#### 获取任务状态
```bash
curl http://localhost:8000/api/coder-agent/tasks
```

## 设计文档格式

编码智能体支持标准的markdown格式设计文档，建议包含以下章节：

```markdown
# 项目名称

## 1. 项目概述
- 项目描述
- 业务背景
- 技术要求

## 2. 架构设计
- 系统架构图
- 技术栈选择
- 部署结构

## 3. 数据库设计
- ER图
- 表结构定义
- 数据关系

## 4. API设计
- RESTful接口规范
- 请求/响应格式
- 错误码定义

## 5. 前端设计
- 页面结构
- 组件设计
- 交互流程

## 6. 开发规范
- 代码规范
- 目录结构
- 版本控制规范
```

## 输出结构

生成的项目结构如下：

```
/Users/renyu/Documents/create_project/zqyl-ls
├── backend/                    # 后端项目
│   ├── src/main/java/
│   │   └── com/example/
│   │       ├── entity/         # 实体类
│   │       ├── repository/     # 数据访问层
│   │       ├── service/        # 业务逻辑层
│   │       └── controller/     # 控制器层
│   ├── src/test/java/          # 测试代码
│   └── pom.xml                 # Maven配置
├── frontend/                   # 前端项目
│   ├── src/
│   │   ├── components/         # Vue组件
│   │   ├── views/              # 页面视图
│   │   ├── router/             # 路由配置
│   │   └── store/              # 状态管理
│   ├── tests/                  # 测试代码
│   └── package.json            # npm配置
├── tasks/                      # 任务管理
│   ├── task_breakdown.json     # 任务分解
│   ├── execution_plan.md       # 执行计划
│   └── progress_tracker.json   # 进度跟踪
├── test-project/               # 测试项目
│   ├── backend-tests/          # 后端测试
│   ├── frontend-tests/         # 前端测试
│   └── test-reports/           # 测试报告
└── docs/                       # 技术文档
    └── tech-stack/             # 技术栈文档
```

## 工作流程

编码智能体按照以下流程工作：

1. **文档解析阶段**
   - 解析markdown设计文档
   - 提取关键信息和技术要求
   - 识别业务逻辑和数据结构

2. **任务规划阶段**
   - 分解开发任务
   - 确定依赖关系和执行顺序
   - 生成详细执行计划

3. **环境准备阶段**
   - Git分支管理
   - 项目结构分析
   - 环境配置准备

4. **代码生成阶段**
   - 后端代码生成（Entity、Repository、Service、Controller）
   - 前端代码生成（Vue组件、路由、状态管理）
   - 配置文件生成

5. **测试阶段**
   - 单元测试代码生成
   - 测试用例执行
   - 测试报告生成

6. **版本控制阶段**
   - 代码提交
   - 远程推送
   - 分支管理

## 配置说明

### 主要配置项

```yaml
coder_agent:
  # 项目路径配置
  project_root: "/Users/renyu/Documents/create_project"        # 项目根目录
  tasks_dir: "tasks"                    # 任务目录
  test_project_dir: "test-project"      # 测试项目目录
  
  # Git配置
  default_branch_pattern: "D_{timestamp}_aigc"  # 默认分支模式
  
  # 技术栈配置
  backend_framework: "spring_boot"      # 后端框架
  frontend_framework: "vue2"           # 前端框架
  
  # 测试配置
  test_coverage_target: 0.8            # 测试覆盖率目标
  
  # AI配置
  code_generation_model: ""       # 代码生成模型
  max_tokens: 4000                     # 最大token数
```

## 错误处理

### 常见问题及解决方案

1. **文档解析失败**
   - 检查markdown格式是否正确
   - 确保文档包含必要的章节信息

2. **Git操作失败**
   - 检查Git配置和权限
   - 确认远程仓库地址正确

3. **代码生成错误**
   - 检查AI模型配置
   - 验证网络连接状态

4. **测试执行失败**
   - 检查Java和Node.js环境
   - 确认依赖包安装正确

## 性能优化

### 推荐配置

- **大型项目**: 建议分阶段执行，先创建计划再执行
- **并发处理**: 使用异步模式提高处理效率
- **缓存策略**: 启用Redis缓存加速重复操作
- **资源管理**: 合理设置AI模型的token限制

## 扩展开发

### 自定义模板

可以在 `coder_agent_templates/` 目录下添加自定义代码模板：

```python
# 自定义后端模板
CUSTOM_ENTITY_TEMPLATE = """
@Entity
@Table(name = "{table_name}")
public class {class_name} {{
    // 自定义实体代码
}}
"""
```

### 插件开发

通过实现 `WorkflowStep` 接口可以添加自定义工作流步骤：

```python
from src.corder_integration.workflow_engine import WorkflowStep

class CustomStep(WorkflowStep):
    async def execute(self, context):
        # 自定义逻辑
        pass
```

## 技术支持

- 📖 详细文档: [项目Wiki](链接)
- 🐛 问题反馈: [GitHub Issues](链接)
- 💬 技术交流: [讨论区](链接)

## 版本历史

- v1.0.0: 初始版本，支持基础代码生成
- v1.1.0: 增加测试自动化功能
- v1.2.0: 优化工作流引擎，支持异步处理

---

**注意**: 使用前请确保理解生成代码的质量和安全性要求，建议在生产环境使用前进行充分测试。 