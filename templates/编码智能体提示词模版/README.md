# 🚀 LangGraph编码智能体Jinja2模版系统

## 📋 项目概述

基于Jinja2模版系统的LangGraph编码智能体生成器，可以通过配置文件快速生成不同类型的编码智能体实现。

## 🏗️ 文件结构

```
templates/编码智能体提示词模版/
├── LangGraph_Jinja2_Template.md          # 🎨 Jinja2模版文件
├── project_config.yaml                   # ⚙️ 项目配置文件
├── template_generator.py                 # 🔧 模版生成器脚本
├── README.md                             # 📖 使用说明文档
├── requirements.txt                      # 📦 依赖包清单
└── LLM提示词目录/                        # 🧠 LLM提示词目录
    ├── task_splitting_prompts.md
    ├── git_management_prompts.md
    └── ...
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 生成默认项目

```bash
python template_generator.py generate \
    --config project_config.yaml \
    --template LangGraph_Jinja2_Template.md \
    --output generated_langgraph_agent.md
```

### 3. 查看生成结果

```bash
cat generated_langgraph_agent.md
```

## 📚 详细使用指南

### 🎯 核心功能

#### 1. 单个项目生成

```bash
python template_generator.py generate \
    --config my_project_config.yaml \
    --template LangGraph_Jinja2_Template.md \
    --output my_implementation.md
```

#### 2. 批量项目生成

```bash
python template_generator.py batch \
    --configs config1.yaml config2.yaml config3.yaml \
    --template LangGraph_Jinja2_Template.md \
    --output-dir ./generated_projects/
```

#### 3. 列出可用模版

```bash
python template_generator.py list
```

#### 4. 创建示例配置

```bash
python template_generator.py sample --output my_sample_config.yaml
```

### ⚙️ 配置文件详解

#### 基本配置

```yaml
# 项目基本信息
name: "MyProject"                    # 项目名称
agent_name: "我的编码智能体"         # 智能体名称
base_framework: "核心功能生成.md"   # 基础框架
service_type: "微服务"              # 服务类型
tech_stack: "Spring Boot"           # 技术栈
```

#### 架构配置

```yaml
# 类名配置
state_class_name: "MyAgentState"                    # 状态类名
orchestrator_class_name: "MyWorkflowOrchestrator"   # 编排器类名

# 项目结构
src_path: "src/my_project"                          # 源码路径
integration_module: "my_integration"                # 集成模块
workspace_path: "./workspace"                       # 工作空间路径
```

#### 工作流配置

```yaml
# 工作流节点
workflow_nodes:
  - name: "task_splitting"
    function_name: "task_splitting_node"
    description: "任务拆分节点"
  - name: "git_management"
    function_name: "git_management_node"
    description: "Git管理节点"

# 工作流边
workflow_edges:
  - type: "simple"
    from: "task_splitting"
    to: "git_management"
  - type: "conditional"
    from: "git_management"
    condition_function: "check_git_setup_success"
    conditions:
      success: "intelligent_coding"
      retry: "git_management"
      fail: "END"
```

#### 条件函数配置

```yaml
condition_functions:
  - name: "check_git_setup_success"
    description: "检查Git环境设置是否成功"
    logic: |
      if state["repo_initialized"]:
          return "success"
      elif state["retry_count"] < 3:
          return "retry"
      else:
          return "fail"
```

#### 数据库配置

```yaml
database:
  type: "postgresql"  # postgresql | mysql | memory
  connection_string: "postgresql://user:pass@localhost/db"
```

#### 大模型配置

```yaml
# 大模型配置
llm_client_import: "openai"
llm_client_class: "AsyncOpenAI"
llm_method: "chat.completions"
llm_model: "gpt-4"

# 温度配置
temperature:
  analysis: 0.3
  identification: 0.2
  generation: 0.2
```

### 🎨 模版自定义

#### 自定义过滤器

模版系统内置了以下过滤器：

```jinja2
{{ project_config.name | snake_case }}      # 转换为snake_case
{{ project_config.name | camel_case }}      # 转换为camelCase  
{{ project_config.name | pascal_case }}     # 转换为PascalCase
{{ logic_code | indent(4) }}                # 缩进4个空格
```

#### 条件模版

```jinja2
{% if project_config.database.type == 'postgresql' %}
from langgraph.checkpoint.postgres import PostgresCheckpointer
{% elif project_config.database.type == 'mysql' %}
from langgraph.checkpoint.mysql import MySQLCheckpointer
{% else %}
from langgraph.checkpoint.memory import MemoryCheckpointer
{% endif %}
```

#### 循环模版

```jinja2
{% for node in project_config.workflow_nodes %}
workflow.add_node("{{ node.name }}", {{ node.function_name }})
{% endfor %}
```

## 🔧 高级功能

### 1. 自定义模版

创建自己的模版文件：

```jinja2
# my_custom_template.md
# 🚀 {{ project_config.name }}项目

## 配置信息
- 项目名称: {{ project_config.name }}
- 技术栈: {{ project_config.tech_stack }}
- 服务类型: {{ project_config.service_type }}
```

### 2. 多环境配置

```yaml
# development.yaml
name: "MyProject-Dev"
database:
  type: "memory"
llm_model: "gpt-3.5-turbo"

# production.yaml  
name: "MyProject-Prod"
database:
  type: "postgresql"
  connection_string: "postgresql://prod_user:prod_pass@prod_host/prod_db"
llm_model: "gpt-4"
```

### 3. 配置继承

```yaml
# base_config.yaml
name: "BaseProject"
tech_stack: "Spring Boot"
service_type: "微服务"

# extended_config.yaml
extends: "base_config.yaml"
name: "ExtendedProject"
additional_feature: "特殊功能"
```

## 🧪 测试和验证

### 1. 配置文件验证

```bash
python template_generator.py validate --config my_config.yaml
```

### 2. 模版语法检查

```bash
python template_generator.py check --template my_template.md
```

### 3. 生成预览

```bash
python template_generator.py preview \
    --config my_config.yaml \
    --template my_template.md
```

## 📚 最佳实践

### 1. 配置文件管理

- 使用版本控制管理配置文件
- 为不同环境创建不同的配置文件
- 使用有意义的文件名（如：`ecommerce_dev.yaml`）

### 2. 模版设计

- 保持模版的可读性和可维护性
- 使用注释说明复杂的模版逻辑
- 模块化设计，避免过长的模版文件

### 3. 错误处理

- 验证配置文件的完整性
- 提供清晰的错误信息
- 使用日志记录生成过程

## 🔍 故障排除

### 常见问题

#### 1. 模版渲染失败

**错误信息**: `TemplateError: 'xxx' is undefined`

**解决方案**: 检查配置文件中是否缺少必要的字段

#### 2. 配置文件格式错误

**错误信息**: `yaml.scanner.ScannerError`

**解决方案**: 检查YAML文件的语法格式

#### 3. 依赖缺失

**错误信息**: `ModuleNotFoundError: No module named 'jinja2'`

**解决方案**: 
```bash
pip install jinja2 pyyaml
```

### 调试技巧

1. **启用详细日志**:
   ```bash
   python template_generator.py --verbose generate ...
   ```

2. **使用预览模式**:
   ```bash
   python template_generator.py preview --config config.yaml --template template.md
   ```

3. **检查生成的文件**:
   ```bash
   python -m py_compile generated_file.py
   ```

## 🚀 进阶用法

### 1. 自定义过滤器

```python
# custom_filters.py
def custom_filter(value):
    return value.upper()

# 在template_generator.py中注册
self.jinja_env.filters['custom'] = custom_filter
```

### 2. 插件系统

```python
# 创建插件目录
mkdir plugins/

# 创建插件文件
# plugins/my_plugin.py
def process_config(config):
    # 自定义配置处理逻辑
    return config
```

### 3. 集成CI/CD

```yaml
# .github/workflows/generate.yml
name: Generate Project
on: [push]
jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Generate Implementation
        run: |
          python template_generator.py generate \
            --config project_config.yaml \
            --template LangGraph_Jinja2_Template.md \
            --output generated_implementation.md
```

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持

如果您有任何问题或建议，请：

1. 查看 [FAQ](FAQ.md)
2. 提交 [Issue](https://github.com/your-repo/issues)
3. 联系维护者

---

**享受使用LangGraph编码智能体模版系统！** 🎉 