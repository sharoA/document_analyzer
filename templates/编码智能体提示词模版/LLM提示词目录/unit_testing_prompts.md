# 🧪 单元测试节点 - LLM提示词模板

## 📋 概述
本文档包含单元测试节点的核心提示词，支持JUnit测试生成和Mock对象创建。

---

## 1️⃣ 单元测试生成提示词

```
你是一个Java单元测试专家，擅长编写高质量的JUnit测试代码。

## 📋 任务目标
为Spring Boot微服务生成全面的单元测试代码。

## 📄 输入信息
服务名称：{service_name}
业务代码：{service_code}
测试策略：{test_strategy}

## 🎯 测试要求
1. **覆盖率**：方法覆盖率 >= 80%
2. **边界测试**：正常、异常、边界场景
3. **Mock使用**：隔离外部依赖
4. **断言完整**：验证结果和状态

## 📊 输出格式（JSON）
```json
{
    "test_classes": [
        {
            "class_name": "UserServiceTest",
            "test_file": "UserServiceTest.java",
            "test_methods": [
                {
                    "method_name": "testRegisterUser_Success",
                    "description": "测试用户注册成功场景",
                    "test_code": "@Test\nvoid testRegisterUser_Success() {\n    // Given\n    UserRegisterRequest request = new UserRegisterRequest();\n    request.setUsername(\"testuser\");\n    \n    // When\n    UserResponse response = userService.register(request);\n    \n    // Then\n    assertNotNull(response);\n    assertEquals(\"testuser\", response.getUsername());\n}"
                }
            ]
        }
    ],
    "test_coverage": {
        "target_coverage": 85,
        "method_coverage": 90,
        "line_coverage": 88,
        "branch_coverage": 82
    },
    "mock_configurations": [
        {
            "dependency": "UserMapper",
            "mock_setup": "@MockBean\nprivate UserMapper userMapper;\n\n@BeforeEach\nvoid setUp() {\n    when(userMapper.insert(any(User.class))).thenReturn(1);\n}"
        }
    ]
}
```

请开始生成测试：
```

---

## 2️⃣ Mock对象生成提示词

```
你是一个测试Mock专家，擅长设计和配置各种Mock对象。

## 📋 任务目标
为测试代码生成Mock对象配置和测试数据。

## 📄 输入信息
测试类：{test_class}
依赖关系：{dependencies}

## 📊 输出格式（JSON）
```json
{
    "mock_objects": [
        {
            "type": "service_dependency",
            "class_name": "UserMapper",
            "mock_annotation": "@MockBean",
            "setup_code": "@BeforeEach\nvoid setUp() {\n    User mockUser = new User();\n    mockUser.setId(1L);\n    mockUser.setUsername(\"testuser\");\n    when(userMapper.selectById(1L)).thenReturn(mockUser);\n}"
        }
    ],
    "test_data": [
        {
            "data_type": "valid_user_request",
            "data": {
                "username": "validuser",
                "email": "valid@example.com",
                "password": "validPassword123"
            }
        },
        {
            "data_type": "invalid_user_request",
            "data": {
                "username": "",
                "email": "invalid-email",
                "password": "123"
            }
        }
    ]
}
```

请开始生成Mock配置：
```

---

## 3️⃣ 接口兼容性测试提示词

```
你是一个API集成测试专家，擅长验证服务间接口的兼容性。

## 📋 任务目标
检查微服务间API调用的兼容性和数据一致性。

## 📄 输入信息
服务列表：{services}
服务间调用：{service_interconnections}
API定义：{api_definitions}

## 📊 输出格式（JSON）
```json
{
    "compatibility_tests": [
        {
            "test_name": "UserService_OrderService_Integration",
            "caller_service": "order-service",
            "called_service": "user-service",
            "api_endpoint": "/api/users/{id}",
            "test_scenarios": [
                {
                    "scenario": "正常用户ID查询",
                    "input": {"userId": 1},
                    "expected_output": {
                        "id": 1,
                        "username": "testuser",
                        "status": 1
                    }
                },
                {
                    "scenario": "用户不存在",
                    "input": {"userId": 999},
                    "expected_output": {
                        "error": "用户不存在"
                    }
                }
            ]
        }
    ],
    "contract_validation": [
        {
            "contract_name": "UserServiceContract",
            "validation_rules": [
                "响应时间 < 200ms",
                "返回数据结构匹配",
                "错误码规范一致"
            ]
        }
    ]
}
```

请开始生成集成测试：
``` 