# 📝 提示词模板目录

这个目录包含了LangGraph编码智能体项目的所有提示词模板文件。

## 🏗️ 文件结构

### 主要提示词模板（详细版）
- `requirements_analysis_prompts.jinja2` - 需求分析专家提示词
- `design_analysis_prompts.jinja2` - 系统架构分析专家提示词
- `service_boundary_prompts.jinja2` - 微服务边界划分专家提示词
- `dependency_analysis_prompts.jinja2` - 服务依赖关系分析专家提示词
- `task_scheduling_prompts.jinja2` - 任务执行计划制定专家提示词
- `service_analysis_prompts.jinja2` - 微服务需求分析专家提示词
- `code_generation_prompts.jinja2` - Spring Boot代码生成专家提示词
- `api_design_prompts.jinja2` - RESTful API设计专家提示词

### 默认提示词模板目录（简化版）
`default/` 目录包含所有功能对应的简化版默认提示词：

#### 任务拆分节点默认提示词
- `default/requirements_analysis_default_prompts.jinja2` - 需求分析默认提示词
- `default/design_analysis_default_prompts.jinja2` - 设计分析默认提示词
- `default/service_boundary_default_prompts.jinja2` - 服务边界识别默认提示词
- `default/dependency_analysis_default_prompts.jinja2` - 依赖分析默认提示词
- `default/task_scheduling_default_prompts.jinja2` - 任务调度默认提示词

#### 智能编码节点默认提示词
- `default/service_analysis_default_prompts.jinja2` - 服务分析默认提示词
- `default/code_generation_default_prompts.jinja2` - 代码生成默认提示词
- `default/api_design_default_prompts.jinja2` - API设计默认提示词

## 🔧 设计原则

### 1. 单一职责原则
每个模板文件只负责一个特定的功能，便于维护和复用。

### 2. 模块化设计
- **高内聚**：相关的提示词放在同一个文件中
- **低耦合**：不同功能的提示词分离到独立文件
- **易扩展**：可以方便地添加新的提示词类型

### 3. 三级加载机制
```
优先级：专门模板 > 对应默认模板 > 内置模板
1. 专门提示词模板（详细版，独立功能文件）
2. 对应默认提示词模板（简化版，default/目录中的独立文件）
3. 内置提示词模板（最后备选，代码中硬编码）
```

### 4. 目录层次分离
- **主目录**：存放详细的专门功能模板
- **default/ 子目录**：存放简化的默认模板
- **代码中的内置模板**：最后的备选方案

## 📚 模板使用说明

### Jinja2宏定义规范
```jinja2
{# 文件描述注释 #}

{% macro prompt_name(param1, param2) %}
# 专家角色

具体的提示词内容...

### 参数1
{{ param1 }}

### 参数2
{{ param2 }}

## 输出要求
具体的输出格式要求...
{% endmacro %}
```

### 代码中的调用方式
```python
# 获取渲染后的提示词
prompt = prompt_manager.get_prompt("prompt_type", 
                                 param1="value1", 
                                 param2="value2")
```

## 🎯 模板内容规范

### 1. 专家角色定义
每个提示词都应该明确定义AI的专家角色和专业能力。

### 2. 任务描述清晰
详细说明要完成的具体任务和分析要点。

### 3. 输入参数明确
通过Jinja2变量明确标识所有输入参数。

### 4. 输出格式规范
使用JSON Schema或明确的格式要求定义输出结构。

### 5. 示例完整
提供足够的示例帮助AI理解期望的输出格式。

## 🚀 扩展指南

### 添加新的提示词类型
1. 创建新的`功能_prompts.jinja2`文件（主模板）
2. 创建对应的`default/功能_default_prompts.jinja2`文件（默认模板）
3. 在对应的节点类中添加模板文件映射
4. 实现`宏名_prompt`宏函数
5. 更新内置模板（可选）

### 修改现有提示词
1. 优先编辑主模板文件（详细版）
2. 可选择性更新默认模板文件（简化版）
3. 保持宏函数名和参数接口不变
4. 测试修改后的效果

## 🧪 测试验证

可以使用测试脚本验证模板加载和渲染功能：

```bash
python test_modular_prompts_simple.py
```

该脚本会测试：
- 主模板文件是否正常加载
- 默认模板文件是否正确分离
- 宏函数是否正确调用
- 优先级机制是否工作
- 错误处理机制是否生效

## 📁 完整目录结构

```
src/corder_integration/langgraph/prompts/
├── README.md                                    # 本文档
├── __init__.py                                  # 包初始化文件
├── requirements_analysis_prompts.jinja2        # 需求分析专家提示词
├── design_analysis_prompts.jinja2              # 设计分析专家提示词
├── service_boundary_prompts.jinja2             # 服务边界划分专家提示词
├── dependency_analysis_prompts.jinja2          # 依赖分析专家提示词
├── task_scheduling_prompts.jinja2              # 任务调度专家提示词
├── service_analysis_prompts.jinja2             # 服务分析专家提示词
├── code_generation_prompts.jinja2              # 代码生成专家提示词
├── api_design_prompts.jinja2                   # API设计专家提示词
└── default/                                     # 默认提示词目录
    ├── requirements_analysis_default_prompts.jinja2
    ├── design_analysis_default_prompts.jinja2
    ├── service_boundary_default_prompts.jinja2
    ├── dependency_analysis_default_prompts.jinja2
    ├── task_scheduling_default_prompts.jinja2
    ├── service_analysis_default_prompts.jinja2
    ├── code_generation_default_prompts.jinja2
    └── api_design_default_prompts.jinja2
``` 