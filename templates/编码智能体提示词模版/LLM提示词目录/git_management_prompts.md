# 🔧 Git管理节点 - LLM提示词模板

## 📋 概述

本文档包含Git管理节点调用大模型的所有提示词模板，支持Git仓库信息提取、环境配置和分支管理。

---

## 1️⃣ Git信息提取提示词

### 🎯 用途
从设计文档中提取Git仓库地址、分支策略等Git相关信息

### 📝 提示词模板

```
你是一个Git专家，擅长从技术文档中提取Git仓库信息和版本控制相关配置。

## 📋 任务目标
分析设计文档，提取Git仓库信息、分支策略、工作流程等配置信息。

## 📄 输入信息
设计文档：
{design_doc}

项目名称：{project_name}

## 🎯 提取要求
1. **仓库信息**：Git仓库地址、访问凭证要求
2. **分支策略**：分支命名规范、工作流程
3. **提交规范**：提交信息格式、代码审查流程
4. **部署配置**：CI/CD管道、环境分支映射

## 📊 输出格式（JSON）
请严格按照以下JSON格式输出：

```json
{
    "repository": {
        "repo_url": "https://github.com/company/ecommerce-system.git",
        "repo_type": "remote", 
        "access_method": "https",
        "authentication_required": true,
        "default_branch": "main"
    },
    "branch_strategy": {
        "workflow": "Git Flow",
        "feature_branch_prefix": "feature/",
        "hotfix_branch_prefix": "hotfix/",
        "release_branch_prefix": "release/",
        "protected_branches": ["main", "develop"],
        "merge_strategy": "squash merge"
    },
    "commit_conventions": {
        "format": "conventional commits",
        "types": ["feat", "fix", "docs", "style", "refactor", "test", "chore"],
        "scope_required": true,
        "max_length": 72,
        "examples": [
            "feat(user): add user registration API",
            "fix(order): resolve payment timeout issue"
        ]
    },
    "ci_cd_config": {
        "pipeline_tool": "GitHub Actions",
        "trigger_events": ["push", "pull_request"],
        "environments": [
            {
                "name": "development",
                "branch": "develop",
                "auto_deploy": true
            },
            {
                "name": "staging", 
                "branch": "release/*",
                "auto_deploy": false
            },
            {
                "name": "production",
                "branch": "main",
                "auto_deploy": false
            }
        ]
    },
    "code_review": {
        "required": true,
        "min_reviewers": 2,
        "auto_merge_conditions": [
            "所有检查通过",
            "至少2个审批",
            "无冲突"
        ],
        "quality_gates": [
            "单元测试覆盖率 >= 80%",
            "代码扫描无高危漏洞",
            "构建成功"
        ]
    },
    "project_structure": {
        "monorepo": false,
        "microservice_repos": [
            {
                "service_name": "user-service",
                "repo_path": "services/user-service"
            },
            {
                "service_name": "order-service", 
                "repo_path": "services/order-service"
            }
        ],
        "shared_components": [
            {
                "component_name": "common-utils",
                "repo_path": "shared/common-utils"
            }
        ]
    }
}
```

## ⚠️ 注意事项
- 如果文档中没有明确的Git信息，使用合理的默认值
- 考虑项目规模选择合适的分支策略
- 确保分支命名符合团队规范
- 优先考虑代码安全和质量控制

请开始分析：
```

---

## 2️⃣ 仓库初始化提示词

### 🎯 用途
生成Git仓库初始化和配置的具体操作指令

### 📝 提示词模板

```
你是一个Git仓库管理专家，擅长设计和配置Git仓库的初始化方案。

## 📋 任务目标
基于项目信息和Git配置要求，生成仓库初始化的详细操作步骤。

## 📄 输入信息
项目名称：{project_name}
Git配置信息：{git_config}
服务列表：{service_list}

## 🎯 初始化要求
1. **仓库结构**：设计合理的目录结构
2. **初始文件**：创建必要的配置文件
3. **分支设置**：配置分支保护规则
4. **Hook配置**：设置Git钩子

## 📊 输出格式（JSON）
```json
{
    "initialization_steps": [
        {
            "step": 1,
            "action": "clone_repository",
            "command": "git clone https://github.com/company/ecommerce-system.git",
            "description": "克隆远程仓库到本地",
            "error_handling": "如果仓库不存在，初始化新仓库"
        },
        {
            "step": 2,
            "action": "create_feature_branch",
            "command": "git checkout -b feature/ecommerce-system",
            "description": "创建功能分支",
            "error_handling": "如果分支已存在，切换到该分支"
        },
        {
            "step": 3,
            "action": "setup_directory_structure",
            "commands": [
                "mkdir -p services/user-service/src/main/java",
                "mkdir -p services/order-service/src/main/java",
                "mkdir -p shared/common-utils/src/main/java"
            ],
            "description": "创建项目目录结构"
        }
    ],
    "directory_structure": {
        "root": "ecommerce-system/",
        "structure": [
            {
                "path": "services/",
                "type": "directory",
                "description": "微服务目录"
            },
            {
                "path": "services/user-service/",
                "type": "directory", 
                "description": "用户服务"
            },
            {
                "path": "services/order-service/",
                "type": "directory",
                "description": "订单服务"
            },
            {
                "path": "shared/",
                "type": "directory",
                "description": "共享组件"
            },
            {
                "path": "docker/",
                "type": "directory",
                "description": "Docker配置"
            },
            {
                "path": "docs/",
                "type": "directory",
                "description": "项目文档"
            }
        ]
    },
    "initial_files": [
        {
            "file_path": "README.md",
            "content": "# {project_name}\n\n微服务电商系统\n\n## 项目结构\n\n- services/: 微服务目录\n- shared/: 共享组件\n- docker/: 容器配置\n- docs/: 项目文档",
            "description": "项目说明文件"
        },
        {
            "file_path": ".gitignore",
            "content": "target/\n*.jar\n*.war\n*.class\n.idea/\n*.iml\n.DS_Store\nnode_modules/\n.env",
            "description": "Git忽略规则"
        },
        {
            "file_path": "docker-compose.yml",
            "content": "version: '3.8'\nservices:\n  mysql:\n    image: mysql:8.0\n    environment:\n      MYSQL_ROOT_PASSWORD: root\n    ports:\n      - \"3306:3306\"",
            "description": "开发环境Docker配置"
        }
    ],
    "git_configuration": [
        {
            "config_type": "branch_protection",
            "branch": "main",
            "rules": [
                "require_pull_request_reviews",
                "require_status_checks",
                "enforce_admins"
            ]
        },
        {
            "config_type": "hook_setup",
            "hook_type": "pre-commit",
            "script": "#!/bin/sh\n# 运行代码格式检查\nmvn checkstyle:check"
        }
    ]
}
```

## ⚠️ 注意事项
- 确保目录结构符合Spring Boot项目规范
- 考虑团队开发和CI/CD需求
- 设置合理的文件权限和访问控制
- 准备回滚和错误恢复方案

请开始生成初始化方案：
```

---

## 3️⃣ 分支管理提示词

### 🎯 用途
生成分支创建、切换、合并等分支管理操作

### 📝 提示词模板

```
你是一个Git分支管理专家，擅长设计和执行Git分支操作策略。

## 📋 任务目标
基于项目需求和分支策略，生成分支管理的具体操作方案。

## 📄 输入信息
项目名称：{project_name}
当前分支状态：{current_branch_status}
目标分支：{target_branch}
操作类型：{operation_type}

## 🎯 分支管理要求
1. **分支创建**：按规范创建功能分支
2. **分支同步**：保持与主分支同步
3. **冲突解决**：处理分支冲突
4. **合并策略**：选择合适的合并方式

## 📊 输出格式（JSON）
```json
{
    "branch_operations": [
        {
            "operation": "fetch_latest",
            "commands": [
                "git fetch origin",
                "git pull origin main"
            ],
            "description": "获取最新代码",
            "prerequisites": ["网络连接正常", "有仓库访问权限"]
        },
        {
            "operation": "create_feature_branch",
            "commands": [
                "git checkout main",
                "git checkout -b feature/ecommerce-system-$(date +%Y%m%d)"
            ],
            "description": "创建功能分支",
            "naming_convention": "feature/项目名称-日期"
        },
        {
            "operation": "setup_upstream",
            "commands": [
                "git push -u origin feature/ecommerce-system-$(date +%Y%m%d)"
            ],
            "description": "设置上游分支",
            "purpose": "建立本地分支与远程分支的跟踪关系"
        }
    ],
    "branch_protection": {
        "protected_branches": ["main", "develop"],
        "protection_rules": [
            {
                "rule": "require_pull_request_reviews",
                "min_reviewers": 2,
                "dismiss_stale_reviews": true
            },
            {
                "rule": "require_status_checks",
                "strict": true,
                "contexts": ["continuous-integration", "code-quality"]
            },
            {
                "rule": "restrict_pushes",
                "push_allowlist": ["admin", "maintainer"]
            }
        ]
    },
    "merge_strategy": {
        "preferred_method": "squash_merge",
        "conditions": [
            {
                "condition": "all_checks_passed",
                "description": "所有CI检查通过"
            },
            {
                "condition": "conflicts_resolved", 
                "description": "所有冲突已解决"
            },
            {
                "condition": "reviews_approved",
                "description": "代码审查已通过"
            }
        ],
        "post_merge_actions": [
            "delete_feature_branch",
            "update_changelog",
            "tag_release"
        ]
    },
    "conflict_resolution": {
        "detection_commands": [
            "git status",
            "git diff --name-only --diff-filter=U"
        ],
        "resolution_steps": [
            {
                "step": "identify_conflicts",
                "command": "git status",
                "description": "识别冲突文件"
            },
            {
                "step": "resolve_conflicts",
                "manual_action": "编辑冲突文件，选择保留的代码",
                "tools": ["VSCode", "IntelliJ IDEA", "merge tool"]
            },
            {
                "step": "mark_resolved",
                "command": "git add <conflicted_files>",
                "description": "标记冲突已解决"
            },
            {
                "step": "complete_merge",
                "command": "git commit",
                "description": "完成合并"
            }
        ]
    }
}
```

## ⚠️ 注意事项
- 确保分支命名符合团队规范
- 定期同步主分支避免大量冲突
- 保护重要分支防止意外修改
- 建立清晰的分支生命周期管理

请开始生成分支管理方案：
```

---

## 4️⃣ 代码提交规范提示词

### 🎯 用途
生成符合团队规范的Git提交信息和提交流程

### 📝 提示词模板

```
你是一个代码提交规范专家，擅长设计和执行Git提交最佳实践。

## 📋 任务目标
基于代码变更内容和提交规范，生成规范的提交信息和提交流程。

## 📄 输入信息
变更内容：{change_summary}
文件列表：{changed_files}
项目类型：{project_type}
提交类型：{commit_type}

## 🎯 提交规范
1. **提交信息格式**：遵循Conventional Commits规范
2. **提交原子性**：每次提交只包含一个逻辑变更
3. **代码质量**：确保提交前代码质量检查通过
4. **关联问题**：关联相关的Issue或任务

## 📊 输出格式（JSON）
```json
{
    "commit_message": {
        "type": "feat",
        "scope": "user-service",
        "description": "add user registration and authentication APIs",
        "body": "- Implement user registration endpoint with email validation\n- Add JWT-based authentication system\n- Create user profile management APIs\n- Add password encryption and validation",
        "footer": "Closes #123, #124",
        "full_message": "feat(user-service): add user registration and authentication APIs\n\n- Implement user registration endpoint with email validation\n- Add JWT-based authentication system\n- Create user profile management APIs\n- Add password encryption and validation\n\nCloses #123, #124"
    },
    "commit_types": {
        "feat": "新功能",
        "fix": "bug修复",
        "docs": "文档更新",
        "style": "代码格式调整",
        "refactor": "代码重构",
        "test": "测试代码",
        "chore": "构建和工具相关",
        "perf": "性能优化",
        "ci": "CI/CD配置"
    },
    "pre_commit_checks": [
        {
            "check_name": "code_formatting",
            "command": "mvn spotless:check",
            "description": "检查代码格式",
            "fix_command": "mvn spotless:apply"
        },
        {
            "check_name": "unit_tests",
            "command": "mvn test",
            "description": "运行单元测试",
            "required": true
        },
        {
            "check_name": "code_coverage",
            "command": "mvn jacoco:check",
            "description": "检查测试覆盖率",
            "threshold": "80%"
        },
        {
            "check_name": "security_scan",
            "command": "mvn dependency-check:check",
            "description": "安全漏洞扫描",
            "required": true
        }
    ],
    "commit_workflow": [
        {
            "step": 1,
            "action": "stage_changes",
            "command": "git add .",
            "description": "暂存所有变更"
        },
        {
            "step": 2,
            "action": "pre_commit_validation",
            "description": "运行预提交检查",
            "automated": true
        },
        {
            "step": 3,
            "action": "commit_changes",
            "command": "git commit -m \"feat(user-service): add user registration and authentication APIs\"",
            "description": "提交代码变更"
        },
        {
            "step": 4,
            "action": "push_changes",
            "command": "git push origin feature/user-auth",
            "description": "推送到远程分支"
        }
    ],
    "quality_gates": [
        {
            "gate": "automated_tests",
            "status": "required",
            "description": "所有自动化测试必须通过"
        },
        {
            "gate": "code_review",
            "status": "required",
            "min_reviewers": 2,
            "description": "至少需要2个人的代码审查"
        },
        {
            "gate": "security_check",
            "status": "required",
            "description": "安全扫描无高危漏洞"
        },
        {
            "gate": "documentation",
            "status": "recommended",
            "description": "API文档和README更新"
        }
    ]
}
```

## ⚠️ 注意事项
- 提交信息要简洁明了，说明变更的目的
- 确保每次提交都是可构建和可测试的
- 关联相关的Issue或需求编号
- 遵循团队约定的提交频率和粒度

请开始生成提交方案：
```

---

## 🔧 使用指南

### 调用示例

```python
# Git信息提取
from LLM提示词目录.git_management_prompts import GIT_EXTRACTION_PROMPT

prompt = GIT_EXTRACTION_PROMPT.format(
    design_doc=design_doc,
    project_name=project_name
)

# 分支管理
from LLM提示词目录.git_management_prompts import BRANCH_MANAGEMENT_PROMPT

prompt = BRANCH_MANAGEMENT_PROMPT.format(
    project_name=project_name,
    current_branch_status=current_status,
    target_branch=target_branch,
    operation_type="create"
)
```

### 最佳实践

1. **信息提取准确性**：仔细解析文档中的Git相关信息
2. **操作安全性**：在执行Git操作前进行验证
3. **错误处理**：为每个Git操作提供错误处理方案
4. **权限验证**：确保有足够的仓库访问权限 