# 📤 Git提交节点 - LLM提示词模板

## 📋 概述
本文档包含Git提交节点的核心提示词，支持提交信息生成和PR创建。

---

## 1️⃣ 提交信息生成提示词

```
你是一个Git提交规范专家，擅长生成符合Conventional Commits规范的提交信息。

## 📋 任务目标
基于代码变更内容，生成规范化的Git提交信息。

## 📄 输入信息
服务名称：{service_name}
变更摘要：{changes_summary}
测试结果：{test_results}

## 🎯 提交规范
1. **格式**：type(scope): description
2. **类型**：feat, fix, docs, style, refactor, test, chore
3. **范围**：服务名称或模块名称
4. **描述**：简洁明了的变更说明

## 📊 输出格式（JSON）
```json
{
    "commit_message": {
        "type": "feat",
        "scope": "user-service",
        "description": "add user registration and authentication APIs",
        "body": "- Implement user registration endpoint with email validation\n- Add JWT-based authentication system\n- Create user profile management APIs\n- Add comprehensive unit tests with 90% coverage",
        "footer": "Closes #123",
        "full_message": "feat(user-service): add user registration and authentication APIs\n\n- Implement user registration endpoint with email validation\n- Add JWT-based authentication system\n- Create user profile management APIs\n- Add comprehensive unit tests with 90% coverage\n\nCloses #123"
    },
    "file_changes": [
        {
            "action": "added",
            "file_path": "services/user-service/src/main/java/com/company/user/controller/UserController.java",
            "description": "用户API控制器"
        },
        {
            "action": "added",
            "file_path": "services/user-service/src/main/java/com/company/user/service/UserService.java",
            "description": "用户业务逻辑服务"
        }
    ],
    "quality_metrics": {
        "test_coverage": 90,
        "code_quality_score": 85,
        "security_issues": 0
    }
}
```

请开始生成提交信息：
```

---

## 2️⃣ PR描述生成提示词

```
你是一个代码协作专家，擅长编写清晰详细的Pull Request描述。

## 📋 任务目标
为代码变更生成详细的PR描述，便于代码审查和项目管理。

## 📄 输入信息
项目状态：{project_state}
变更内容：{changes}

## 📊 输出格式（JSON）
```json
{
    "pr_description": {
        "title": "feat: 完成用户服务和订单服务开发",
        "summary": "本PR实现了电商系统的用户管理和订单处理微服务，包含完整的API接口、业务逻辑、数据库设计和单元测试。",
        "changes": [
            "✅ 用户服务：注册、登录、信息管理",
            "✅ 订单服务：订单创建、查询、状态管理",
            "✅ 服务间调用：Feign Client集成",
            "✅ 数据库：MySQL表结构和MyBatis映射",
            "✅ 单元测试：90%以上覆盖率"
        ],
        "testing": "- 所有单元测试通过\n- 集成测试验证服务间调用\n- API接口测试完成\n- 测试覆盖率：用户服务92%，订单服务88%",
        "deployment": "需要执行SQL脚本创建数据库表，配置Nacos服务注册中心",
        "breaking_changes": [],
        "notes": "建议在staging环境充分测试后再部署到生产环境"
    },
    "review_checklist": [
        "代码符合团队规范",
        "单元测试覆盖率达标",
        "API文档已更新",
        "数据库变更已记录",
        "安全检查通过"
    ]
}
```

请开始生成PR描述：
```

---

## 3️⃣ 发布说明生成提示词

```
你是一个项目发布专家，擅长编写用户友好的发布说明。

## 📋 任务目标
基于代码变更和功能完成情况，生成发布说明文档。

## 📄 输入信息
版本信息：{version_info}
功能列表：{features}
修复列表：{fixes}

## 📊 输出格式（JSON）
```json
{
    "release_notes": {
        "version": "v1.0.0",
        "release_date": "2024-01-15",
        "title": "电商微服务系统首个版本发布",
        "highlights": [
            "完整的用户管理系统",
            "订单处理核心功能",
            "微服务架构基础设施"
        ],
        "new_features": [
            {
                "feature": "用户注册和认证",
                "description": "支持邮箱注册、JWT认证、用户信息管理"
            },
            {
                "feature": "订单管理",
                "description": "订单创建、查询、状态跟踪功能"
            }
        ],
        "improvements": [
            "优化API响应时间",
            "增强数据验证逻辑",
            "改进错误处理机制"
        ],
        "technical_details": {
            "architecture": "Spring Boot微服务",
            "database": "MySQL 8.0",
            "deployment": "Docker容器化",
            "monitoring": "集成日志和监控"
        }
    }
}
```

请开始生成发布说明：
``` 