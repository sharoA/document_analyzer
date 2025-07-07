# 🧠 任务拆分节点 - LLM提示词模板

## 📋 概述

本文档包含任务拆分节点调用大模型的所有提示词模板，支持多服务协调调度的任务拆分和规划。

---

## 1️⃣ 需求分析提示词

### 🎯 用途
从需求文档中提取关键功能点并分析业务边界

### 📝 提示词模板

```
你是一个专业的需求分析师，擅长从需求文档中提取关键功能点并分析业务边界。

## 📋 任务目标
分析以下需求文档，提取关键功能点、业务实体和业务流程。

## 📄 输入信息
项目名称：{project_name}
需求文档：
{requirements_doc}

## 🎯 分析要求
1. **功能分解**：将需求分解为具体的功能模块
2. **业务实体识别**：识别核心业务对象和数据实体
3. **流程梳理**：梳理主要业务流程和用户场景
4. **边界分析**：识别不同功能模块的边界

## 📊 输出格式（JSON）
请严格按照以下JSON格式输出：

```json
{
    "functional_modules": [
        {
            "module_name": "用户管理",
            "description": "用户注册、登录、信息管理",
            "key_features": [
                "用户注册功能",
                "用户登录验证",
                "用户信息CRUD"
            ],
            "business_entities": ["User", "UserProfile"],
            "complexity_score": 3
        }
    ],
    "business_processes": [
        {
            "process_name": "用户注册流程",
            "description": "新用户注册的完整流程",
            "steps": [
                "填写注册信息",
                "验证邮箱/手机",
                "创建用户账号",
                "发送欢迎消息"
            ],
            "involved_modules": ["用户管理", "通知服务"]
        }
    ],
    "core_entities": [
        {
            "entity_name": "User",
            "description": "用户基本信息",
            "key_attributes": ["id", "username", "email", "phone"],
            "relationships": ["UserProfile", "Order"]
        }
    ],
    "integration_points": [
        {
            "point_name": "用户验证",
            "description": "其他服务需要验证用户身份",
            "source_module": "用户管理",
            "target_modules": ["订单管理", "支付服务"]
        }
    ]
}
```

## ⚠️ 注意事项
- 复杂度评分：1-5分，1最简单，5最复杂
- 要识别模块间的依赖关系和集成点
- 关注数据一致性和事务边界
- 考虑性能和扩展性要求

请开始分析：
```

---

## 2️⃣ 设计分析提示词

### 🎯 用途
基于需求分析结果和设计文档，分析技术架构、选型和实现约束

### 📝 提示词模板

```
你是一个资深的系统架构师，擅长分析技术设计文档并识别技术实现要求。

## 📋 任务目标
基于需求分析结果和设计文档，分析技术架构、选型和实现约束。

## 📄 输入信息
设计文档：
{design_doc}

需求分析结果：
{requirements_analysis}

## 🎯 分析要求
1. **架构模式**：识别微服务架构模式和技术选型
2. **技术栈**：确定开发框架、数据库、中间件等
3. **集成方式**：分析服务间通信和数据交换方式
4. **约束条件**：识别性能、安全、部署等约束

## 📊 输出格式（JSON）
```json
{
    "architecture_pattern": {
        "pattern_type": "微服务架构",
        "communication_style": "RESTful API + 消息队列",
        "data_consistency": "最终一致性",
        "deployment_model": "容器化部署"
    },
    "technology_stack": {
        "backend_framework": "Spring Boot",
        "database": {
            "primary": "MySQL",
            "cache": "Redis",
            "search": "Elasticsearch"
        },
        "message_queue": "RabbitMQ",
        "service_discovery": "Nacos",
        "api_gateway": "Spring Cloud Gateway",
        "monitoring": "Prometheus + Grafana"
    },
    "integration_patterns": [
        {
            "pattern_name": "服务间调用",
            "implementation": "Feign Client + RestTemplate",
            "fallback_strategy": "Hystrix熔断"
        },
        {
            "pattern_name": "数据同步",
            "implementation": "事件驱动 + MQ",
            "consistency_model": "最终一致性"
        }
    ],
    "technical_constraints": [
        {
            "constraint_type": "性能要求",
            "description": "API响应时间 < 200ms",
            "impact_areas": ["数据库设计", "缓存策略"]
        },
        {
            "constraint_type": "安全要求",
            "description": "OAuth2.0 + JWT认证",
            "impact_areas": ["API设计", "用户服务"]
        }
    ],
    "development_standards": {
        "code_style": "Google Java Style",
        "api_design": "RESTful最佳实践",
        "database_naming": "下划线命名",
        "git_workflow": "Git Flow"
    }
}
```

## ⚠️ 注意事项
- 重点关注Spring Boot + MyBatis技术栈
- 识别Nacos服务发现和配置管理要求
- 分析数据库分库分表需求
- 考虑容器化和微服务治理

请开始分析：
```

---

## 3️⃣ 微服务边界识别提示词

### 🎯 用途
基于需求分析和设计分析，识别微服务边界，进行合理的服务拆分

### 📝 提示词模板

```
你是一个微服务架构专家，擅长根据业务需求和技术约束进行服务拆分和边界划分。

## 📋 任务目标
基于需求分析和设计分析，识别微服务边界，进行合理的服务拆分。

## 📄 输入信息
需求分析结果：
{requirements_analysis}

设计分析结果：
{design_analysis}

## 🎯 拆分原则
1. **业务内聚**：相关业务功能组织在同一服务
2. **数据自治**：每个服务管理自己的数据
3. **独立部署**：服务可以独立开发和部署
4. **适度粒度**：避免过度拆分和拆分不足

## 📊 输出格式（JSON）
```json
{
    "services": [
        {
            "service_name": "user-service",
            "display_name": "用户服务",
            "description": "负责用户注册、登录、信息管理等功能",
            "business_capabilities": [
                "用户注册",
                "用户认证", 
                "用户信息管理",
                "用户权限控制"
            ],
            "data_entities": [
                {
                    "entity_name": "User",
                    "table_name": "t_user",
                    "key_fields": ["id", "username", "email"]
                },
                {
                    "entity_name": "UserProfile", 
                    "table_name": "t_user_profile",
                    "key_fields": ["user_id", "nickname", "avatar"]
                }
            ],
            "api_endpoints": [
                "POST /api/users/register",
                "POST /api/users/login",
                "GET /api/users/{id}",
                "PUT /api/users/{id}"
            ],
            "complexity_score": 3,
            "team_ownership": "用户团队",
            "estimated_effort": "2周"
        }
    ],
    "service_interactions": [
        {
            "interaction_type": "同步调用",
            "description": "订单服务调用用户服务获取用户信息",
            "pattern": "RESTful API",
            "frequency": "高频"
        }
    ],
    "shared_components": [
        {
            "component_name": "common-utils",
            "description": "通用工具类库",
            "usage_services": ["user-service", "order-service"]
        }
    ],
    "data_consistency_requirements": [
        {
            "scenario": "用户注册后创建钱包",
            "consistency_type": "最终一致性",
            "implementation": "事件驱动"
        }
    ]
}
```

## ⚠️ 注意事项
- 每个服务应该有清晰的业务边界
- 避免分布式事务，优先最终一致性
- 考虑服务的独立可测试性
- 平衡服务粒度和维护成本

请开始分析：
```

---

## 4️⃣ 依赖分析提示词

### 🎯 用途
基于服务拆分结果，分析服务间的依赖关系，设计合理的调用链路

### 📝 提示词模板

```
你是一个微服务依赖关系专家，擅长分析服务间的调用关系和数据依赖。

## 📋 任务目标
基于服务拆分结果，分析服务间的依赖关系，设计合理的调用链路。

## 📄 输入信息
服务拆分结果：
{service_identification}

设计文档：
{design_doc}

## 🎯 分析要求
1. **调用链路**：梳理服务间的调用关系
2. **数据流向**：分析数据在服务间的流转
3. **依赖强度**：评估依赖的紧密程度
4. **循环依赖**：识别并消除循环依赖

## 📊 输出格式（JSON）
```json
{
    "dependencies": {
        "order-service": [
            {
                "target_service": "user-service",
                "dependency_type": "强依赖",
                "call_pattern": "同步调用",
                "api_endpoints": [
                    {
                        "method": "GET",
                        "path": "/api/users/{userId}",
                        "description": "获取用户基本信息",
                        "response_fields": ["id", "username", "email", "status"]
                    }
                ],
                "fallback_strategy": "缓存用户信息",
                "call_frequency": "每次下单",
                "timeout_ms": 3000
            },
            {
                "target_service": "product-service", 
                "dependency_type": "强依赖",
                "call_pattern": "同步调用",
                "api_endpoints": [
                    {
                        "method": "POST",
                        "path": "/api/products/stock/check",
                        "description": "检查商品库存",
                        "request_fields": ["productId", "quantity"],
                        "response_fields": ["available", "stock"]
                    }
                ],
                "fallback_strategy": "返回库存不足",
                "call_frequency": "每次下单",
                "timeout_ms": 2000
            }
        ],
        "notification-service": [
            {
                "target_service": "order-service",
                "dependency_type": "弱依赖",
                "call_pattern": "事件订阅",
                "event_topics": ["order.created", "order.paid", "order.shipped"],
                "fallback_strategy": "重试机制",
                "processing_type": "异步"
            }
        ]
    },
    "dependency_graph": {
        "nodes": [
            {"id": "user-service", "level": 1},
            {"id": "product-service", "level": 1},
            {"id": "order-service", "level": 2},
            {"id": "notification-service", "level": 3}
        ],
        "edges": [
            {"from": "order-service", "to": "user-service", "weight": 9},
            {"from": "order-service", "to": "product-service", "weight": 8},
            {"from": "notification-service", "to": "order-service", "weight": 5}
        ]
    },
    "circular_dependencies": [],
    "critical_paths": [
        {
            "path": "order-service -> user-service -> user-profile-service",
            "risk_level": "高",
            "mitigation": "增加缓存层"
        }
    ],
    "data_consistency_patterns": [
        {
            "scenario": "订单创建流程",
            "services": ["order-service", "product-service", "payment-service"],
            "pattern": "Saga模式",
            "compensation_strategy": "补偿事务"
        }
    ]
}
```

## ⚠️ 注意事项
- 优先识别强依赖，需要同步调用
- 弱依赖可以使用异步事件
- 避免深层次的调用链
- 设计合理的超时和重试策略

请开始分析：
```

---

## 5️⃣ 任务调度提示词

### 🎯 用途
基于服务拆分和依赖分析，制定合理的任务执行计划，最大化并行执行效率

### 📝 提示词模板

```
你是一个项目调度专家，擅长制定任务执行计划并优化并行执行策略。

## 📋 任务目标
基于服务拆分和依赖分析，制定合理的任务执行计划，最大化并行执行效率。

## 📄 输入信息
服务拆分结果：
{service_identification}

依赖分析结果：
{dependency_analysis}

## 🎯 调度原则
1. **依赖优先**：被依赖的服务优先开发
2. **并行最大化**：无依赖的服务可并行开发
3. **风险控制**：核心服务优先，降低整体风险
4. **资源平衡**：合理分配开发资源

## 📊 输出格式（JSON）
```json
{
    "execution_batches": [
        [
            {
                "service_name": "user-service",
                "priority": 1,
                "estimated_effort": "2周",
                "team_required": "后端开发 2人",
                "prerequisites": [],
                "deliverables": [
                    "用户注册API",
                    "用户认证API", 
                    "用户信息管理API",
                    "用户数据库表"
                ]
            },
            {
                "service_name": "product-service",
                "priority": 1,
                "estimated_effort": "2周",
                "team_required": "后端开发 2人",
                "prerequisites": [],
                "deliverables": [
                    "商品管理API",
                    "库存管理API",
                    "商品数据库表"
                ]
            }
        ],
        [
            {
                "service_name": "order-service",
                "priority": 2,
                "estimated_effort": "3周",
                "team_required": "后端开发 3人",
                "prerequisites": [
                    {
                        "service": "user-service",
                        "apis": ["/api/users/{id}"]
                    },
                    {
                        "service": "product-service", 
                        "apis": ["/api/products/stock/check"]
                    }
                ],
                "deliverables": [
                    "订单创建API",
                    "订单查询API",
                    "订单状态管理API",
                    "订单数据库表"
                ]
            }
        ],
        [
            {
                "service_name": "notification-service",
                "priority": 3,
                "estimated_effort": "1周",
                "team_required": "后端开发 1人",
                "prerequisites": [
                    {
                        "service": "order-service",
                        "events": ["order.created", "order.paid"]
                    }
                ],
                "deliverables": [
                    "消息发送API",
                    "事件订阅处理",
                    "通知模板管理"
                ]
            }
        ]
    ],
    "critical_path": [
        {
            "path": "user-service -> order-service -> notification-service",
            "total_time": "6周",
            "bottleneck": "order-service"
        }
    ],
    "parallel_opportunities": [
        {
            "batch": 1,
            "services": ["user-service", "product-service"],
            "time_saved": "2周",
            "resource_requirement": "后端开发 4人"
        }
    ],
    "risk_mitigation": [
        {
            "risk": "用户服务开发延期",
            "impact": "阻塞订单服务开发",
            "mitigation": "提前准备Mock用户服务",
            "contingency_plan": "简化用户服务功能先上线"
        }
    ],
    "integration_schedule": [
        {
            "milestone": "第2周结束",
            "integration_scope": "用户服务内部集成测试",
            "success_criteria": ["所有API功能正常", "数据库集成成功"]
        },
        {
            "milestone": "第4周结束", 
            "integration_scope": "用户服务 + 产品服务联调",
            "success_criteria": ["跨服务调用正常", "接口契约验证通过"]
        },
        {
            "milestone": "第6周结束",
            "integration_scope": "全系统集成测试",
            "success_criteria": ["端到端流程测试通过", "性能测试达标"]
        }
    ]
}
```

## ⚠️ 注意事项
- 考虑团队技能和资源约束
- 预留集成测试和联调时间
- 设计合理的里程碑检查点
- 准备风险应对预案

请开始制定执行计划：
```

---

## 🔧 使用指南

### 调用示例

```python
# 导入提示词
from LLM提示词目录.task_splitting_prompts import REQUIREMENTS_ANALYSIS_PROMPT

# 构建完整提示词
prompt = REQUIREMENTS_ANALYSIS_PROMPT.format(
    requirements_doc=requirements_doc,
    project_name=project_name
)

# 调用大模型
response = await client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "你是一个专业的需求分析师。"},
        {"role": "user", "content": prompt}
    ],
    temperature=0.3
)
```

### 注意事项

1. **JSON解析**：返回结果需要解析JSON格式
2. **错误处理**：添加异常处理机制
3. **重试机制**：设置合理的重试策略
4. **结果验证**：验证返回数据的完整性 