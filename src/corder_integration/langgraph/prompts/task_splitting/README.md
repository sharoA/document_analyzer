# 任务拆分提示词库

本目录包含任务拆分节点使用的所有 Jinja2 提示词模板文件，用于生成细粒度、可执行的开发任务。

## 📁 文件结构

```
task_splitting/
├── README.md                           # 本说明文档
├── design_analysis_prompts.jinja2      # 设计分析提示词
├── service_boundary_prompts.jinja2     # 服务边界识别提示词
├── dependency_analysis_prompts.jinja2  # 依赖分析提示词
├── task_scheduling_prompts.jinja2      # 任务调度提示词
└── generate_sqlite_tasks_prompts.jinja2 # 细粒度任务生成提示词
```

## 🎯 提示词说明

### 1. 设计分析提示词 (`design_analysis_prompts.jinja2`)

**功能**：分析系统设计文档，提取架构信息和技术栈

**输入参数**：
- `design_doc`: 设计文档内容
- `project_name`: 项目名称
- `context_window`: 上下文信息（可选）

**输出格式**：
```json
{
  "architecture_style": "微服务",
  "technology_stack": ["Spring Boot", "MySQL", "Redis"],
  "functional_modules": [
    {
      "name": "用户管理模块",
      "description": "负责用户注册、登录、权限管理",
      "responsibilities": ["用户认证", "权限控制"]
    }
  ],
  "system_components": ["API网关", "配置中心"],
  "data_flow": ["用户请求 -> API网关 -> 微服务"],
  "integration_points": ["第三方支付", "短信服务"],
  "summary": "设计分析概要"
}
```

### 2. 服务边界识别提示词 (`service_boundary_prompts.jinja2`)

**功能**：将系统拆分成具体的微服务，包含详细的数据模型、API接口和业务逻辑

**输入参数**：
- `design_summary`: 设计概要
- `architecture_summary`: 架构概要
- `context_window`: 上下文信息（可选）

**输出格式**：
```json
{
  "identified_services": [
    {
      "name": "用户服务",
      "description": "负责用户管理相关功能",
      "responsibilities": ["用户注册", "用户认证", "用户信息管理"],
      "data_models": [
        {
          "table_name": "user",
          "fields": ["id", "username", "password", "email"],
          "description": "用户基础信息表",
          "primary_key": "id",
          "indexes": ["username", "email"]
        }
      ],
      "api_endpoints": [
        {
          "method": "POST",
          "path": "/api/users/register",
          "description": "用户注册接口",
          "request_params": ["username", "password", "email"],
          "response_fields": ["user_id", "token"],
          "business_logic": "验证输入 -> 检查重复 -> 密码加密 -> 保存用户"
        }
      ],
      "business_logic": [
        {
          "function_name": "registerUser",
          "description": "用户注册业务逻辑",
          "input": "RegisterRequest",
          "output": "RegisterResponse",
          "logic_steps": ["验证参数", "检查重复", "加密密码", "保存数据"]
        }
      ],
      "external_dependencies": ["redis-cache", "email-service"],
      "config_requirements": ["数据库配置", "Redis配置"]
    }
  ],
  "service_relationships": {
    "data_sharing": ["共享用户会话"],
    "api_calls": ["用户服务 -> 权限服务"],
    "event_flows": ["用户注册事件"]
  },
  "summary": "识别了X个微服务"
}
```

### 3. 依赖分析提示词 (`dependency_analysis_prompts.jinja2`)

**功能**：分析服务间的依赖关系，包括API调用、数据依赖、配置依赖和基础设施依赖

**输入参数**：
- `services_summary`: 服务概要
- `architecture_summary`: 架构概要
- `context_window`: 上下文信息（可选）

**输出格式**：
```json
{
  "service_dependencies": {
    "用户服务": {
      "api_dependencies": [
        {
          "service": "权限服务",
          "endpoints": ["/api/permissions/check"],
          "call_type": "同步调用",
          "description": "用户登录时验证权限"
        }
      ],
      "data_dependencies": [
        {
          "type": "database",
          "resource": "user_db",
          "shared_with": [],
          "description": "用户服务独享用户数据库"
        }
      ],
      "config_dependencies": ["配置中心", "服务注册中心"],
      "infrastructure_dependencies": ["MySQL", "Redis", "Nginx"]
    }
  },
  "dependency_graph": {
    "levels": [
      {
        "level": 1,
        "services": ["用户服务", "权限服务"],
        "description": "基础服务层"
      }
    ],
    "circular_dependencies": [],
    "independent_services": ["日志服务"]
  },
  "deployment_order": [
    {
      "phase": 1,
      "services": ["配置中心", "服务注册中心"],
      "reason": "基础设施服务"
    }
  ],
  "risk_analysis": {
    "single_points_of_failure": [
      {
        "service": "用户服务",
        "impact": "高",
        "reason": "多个服务依赖用户验证"
      }
    ]
  }
}
```

### 4. 任务调度提示词 (`task_scheduling_prompts.jinja2`)

**功能**：制定详细的开发执行计划，包含阶段安排、并行任务组和时间估算

**输入参数**：
- `services_summary`: 服务概要
- `dependencies_summary`: 依赖概要
- `context_window`: 上下文信息（可选）

**输出格式**：
```json
{
  "execution_phases": [
    {
      "phase_name": "基础设施搭建阶段",
      "phase_order": 1,
      "description": "搭建项目基础设施",
      "estimated_duration": "2天",
      "services_involved": ["全部服务"],
      "task_categories": [
        {
          "category": "database",
          "description": "数据库基础设施",
          "tasks": [
            {
              "task_name": "创建数据库实例",
              "service": "基础设施",
              "deliverable": "MySQL数据库实例",
              "estimated_hours": 2,
              "prerequisites": ["环境准备"],
              "assignee_role": "DBA"
            }
          ]
        }
      ],
      "success_criteria": ["数据库正常连接"],
      "parallel_execution": true
    }
  ],
  "parallel_groups": [
    {
      "group_name": "基础服务并行组",
      "services": ["用户服务", "权限服务"],
      "estimated_duration": "5天",
      "coordination_points": ["API接口设计统一"]
    }
  ],
  "resource_allocation": {
    "backend_developers": 3,
    "total_estimated_time": "12天"
  }
}
```

### 5. 细粒度任务生成提示词 (`generate_sqlite_tasks_prompts.jinja2`)

**功能**：将高层次的执行计划拆分成具体的、可执行的开发任务

**输入参数**：
- `execution_plan`: 执行计划（JSON格式）
- `services_summary`: 服务概要
- `context_window`: 上下文信息（可选）

**输出格式**：
```json
{
  "tasks": [
    {
      "task_id": "task_001",
      "service_name": "用户服务",
      "task_type": "database",
      "priority": 1,
      "dependencies": [],
      "estimated_duration": "30分钟",
      "description": "创建用户基础信息表",
      "deliverables": [
        "user.sql - 用户表创建脚本",
        "user_indexes.sql - 用户表索引脚本"
      ],
      "implementation_details": "CREATE TABLE user (id BIGINT PRIMARY KEY AUTO_INCREMENT, ...)",
      "completion_criteria": "用户表创建成功，包含所有必要字段和约束",
      "parameters": {
        "table_name": "user",
        "database_name": "user_service_db",
        "file_path": "src/main/resources/sql/user.sql"
      }
    }
  ],
  "task_summary": {
    "total_tasks": 6,
    "by_type": {
      "database": 1,
      "api": 1,
      "service": 1,
      "config": 1,
      "test": 1,
      "deployment": 1
    },
    "estimated_total_time": "225分钟"
  }
}
```

## 📋 任务类型说明

| 类型 | 说明 | 示例 |
|------|------|------|
| `database` | 数据库相关任务 | 创建表结构、索引、迁移脚本 |
| `api` | API接口开发任务 | REST API实现、Controller层 |
| `service` | 业务逻辑实现任务 | Service类、业务逻辑 |
| `config` | 配置管理任务 | 配置文件、环境变量 |
| `test` | 测试相关任务 | 单元测试、集成测试 |
| `deployment` | 部署相关任务 | Docker配置、CI/CD |

## 🔧 使用方式

### 1. 在代码中调用

```python
# 初始化提示词管理器
prompts = TaskSplittingPrompts()

# 获取渲染后的提示词
prompt = prompts.get_prompt(
    "service_boundary",
    design_summary="微服务架构设计",
    architecture_summary="Spring Boot + MySQL + Redis",
    context_window="上下文信息"
)

# 发送给LLM处理
result = llm_client.chat(messages=[
    {"role": "system", "content": "你是微服务架构专家"},
    {"role": "user", "content": prompt}
])
```

### 2. 模板文件结构

所有Jinja2模板文件都遵循以下结构：

```jinja2
{#- 注释：模板说明 -#}

{% macro template_name(param1, param2, optional_param=None) %}
模板内容，包含：
1. 角色定义
2. 输入参数说明
3. 任务要求
4. 输出格式规范
5. 示例和要点

{% if optional_param %}
可选内容处理
{% endif %}

输出JSON格式：
{
  "field1": "value1",
  "field2": ["array_value"],
  "field3": {
    "nested": "object"
  }
}
{% endmacro %}
```

## 🚀 优化建议

### 1. 提示词优化
- 根据实际使用效果调整提示词内容
- 添加更多示例和边界条件处理
- 优化JSON格式定义

### 2. 参数扩展
- 根据需要添加新的输入参数
- 支持更多的上下文信息
- 增加错误处理和重试机制

### 3. 输出格式
- 标准化所有提示词的输出格式
- 添加数据验证和清洗
- 支持增量更新和版本控制

## 📝 维护说明

1. **修改提示词**：直接编辑对应的 `.jinja2` 文件
2. **新增提示词**：创建新的模板文件并更新代码中的映射
3. **测试提示词**：使用测试数据验证输出格式和质量
4. **版本管理**：重要修改请备份并记录变更日志 