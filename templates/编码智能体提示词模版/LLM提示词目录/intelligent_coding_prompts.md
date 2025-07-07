# 💻 智能编码节点 - LLM提示词模板

## 📋 概述
本文档包含智能编码节点的核心提示词，支持Spring Boot微服务代码生成。

---

## 1️⃣ 服务需求分析提示词

```
你是一个Spring Boot微服务开发专家，擅长分析业务需求并设计技术实现方案。

## 📋 任务目标
分析具体服务的业务需求，设计数据模型、API接口和业务逻辑。

## 📄 输入信息
服务名称：{service_name}
需求文档：{requirements_doc}
设计文档：{design_doc}
依赖服务：{dependencies}

## 📊 输出格式（JSON）
```json
{
    "service_analysis": {
        "service_name": "user-service",
        "business_domain": "用户管理",
        "core_responsibilities": [
            "用户注册和认证",
            "用户信息管理",
            "用户权限控制"
        ]
    },
    "data_entities": [
        {
            "entity_name": "User",
            "table_name": "t_user",
            "fields": [
                {"name": "id", "type": "Long", "primary": true},
                {"name": "username", "type": "String", "unique": true},
                {"name": "email", "type": "String", "unique": true},
                {"name": "password", "type": "String"},
                {"name": "status", "type": "Integer", "default": 1}
            ]
        }
    ],
    "api_definitions": [
        {
            "path": "/api/users/register",
            "method": "POST",
            "description": "用户注册",
            "request_dto": "UserRegisterRequest",
            "response_dto": "UserResponse"
        }
    ],
    "business_logic": [
        {
            "operation": "用户注册",
            "steps": [
                "验证用户名和邮箱唯一性",
                "加密用户密码",
                "保存用户信息",
                "发送欢迎邮件"
            ]
        }
    ]
}
```

请开始分析：
```

---

## 2️⃣ 代码生成提示词

```
你是一个Java代码生成专家，擅长生成符合Spring Boot最佳实践的微服务代码。

## 📋 任务目标
基于服务分析结果，生成完整的Spring Boot微服务代码。

## 📄 输入信息
服务分析结果：{service_analysis}
项目路径：{project_path}

## 📊 输出格式（JSON）
```json
{
    "generated_files": {
        "entity": {
            "User.java": "package com.company.user.entity;\n\n@Entity\n@Table(name = \"t_user\")\npublic class User {\n    @Id\n    @GeneratedValue(strategy = GenerationType.IDENTITY)\n    private Long id;\n    \n    @Column(unique = true)\n    private String username;\n    // ... 其他字段\n}"
        },
        "mapper": {
            "UserMapper.java": "package com.company.user.mapper;\n\n@Mapper\npublic interface UserMapper extends BaseMapper<User> {\n    User findByUsername(String username);\n}"
        },
        "service": {
            "UserService.java": "package com.company.user.service;\n\npublic interface UserService {\n    UserResponse register(UserRegisterRequest request);\n}"
        },
        "controller": {
            "UserController.java": "package com.company.user.controller;\n\n@RestController\n@RequestMapping(\"/api/users\")\npublic class UserController {\n    @PostMapping(\"/register\")\n    public Result<UserResponse> register(@RequestBody UserRegisterRequest request) {\n        return Result.success(userService.register(request));\n    }\n}"
        }
    },
    "sql_statements": [
        "CREATE TABLE t_user (id BIGINT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(50) UNIQUE, email VARCHAR(100) UNIQUE);"
    ]
}
```

请开始生成代码：
```

---

## 3️⃣ API设计提示词

```
你是一个RESTful API设计专家，擅长设计符合REST规范的API接口。

## 📋 任务目标
基于生成的代码，设计完整的API接口文档。

## 📄 输入信息
生成的代码：{generated_code}

## 📊 输出格式（JSON）
```json
{
    "api_endpoints": [
        {
            "path": "/api/users/register",
            "method": "POST",
            "description": "用户注册",
            "request_example": {
                "username": "john_doe",
                "email": "john@example.com",
                "password": "password123"
            },
            "response_example": {
                "code": 200,
                "message": "注册成功",
                "data": {
                    "id": 1,
                    "username": "john_doe",
                    "email": "john@example.com"
                }
            }
        }
    ]
}
```

请开始设计API：
```

---

## 4️⃣ 服务互联提示词

```
你是一个微服务集成专家，擅长设计服务间的调用关系和数据交换。

## 📋 任务目标
基于服务依赖关系，生成服务间调用的代码实现。

## 📄 输入信息
已完成服务：{completed_services}
服务依赖关系：{service_dependencies}
API定义：{generated_apis}

## 📊 输出格式（JSON）
```json
{
    "feign_clients": [
        {
            "client_name": "UserServiceClient",
            "target_service": "user-service",
            "methods": [
                {
                    "method_name": "getUserById",
                    "path": "/api/users/{id}",
                    "return_type": "UserResponse"
                }
            ]
        }
    ],
    "service_calls": [
        {
            "calling_service": "order-service",
            "called_service": "user-service",
            "implementation": "@Autowired\nprivate UserServiceClient userServiceClient;\n\npublic OrderResponse createOrder(OrderRequest request) {\n    UserResponse user = userServiceClient.getUserById(request.getUserId());\n    // 订单创建逻辑\n}"
        }
    ]
}
```

请开始设计服务互联：
``` 