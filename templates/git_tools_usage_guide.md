# Git 工具使用指南

## 概述

本文档介绍如何通过大模型的 Function Calling 或 MCP 协议直接调用 Git 操作。我们基于现有的 `git_manager.py` 创建了适配层，让大模型能够安全、智能地执行 Git 操作。

## Git Manager 实现原理

### 核心实现方式

Git Manager 使用 `subprocess.run()` 执行系统级 Git 命令：

```python
def _run_git_command(self, command: List[str], cwd: str) -> str:
    """执行Git命令"""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8'
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Git命令执行失败: {' '.join(command)}")
        logger.error(f"错误输出: {e.stderr}")
        raise
```

### 主要特点

1. **统一接口**：所有 Git 操作都通过 `_run_git_command()` 执行
2. **完善的错误处理**：捕获和记录命令执行错误
3. **结构化返回**：返回标准化的结果数据格式
4. **路径安全**：自动处理工作目录和文件路径
5. **日志记录**：完整的操作日志跟踪

## 大模型调用方式

### 1. Function Calling 方式

#### 可用工具函数

| 函数名 | 描述 | 主要参数 |
|--------|------|----------|
| `git_check_repository_status` | 检查仓库状态 | `project_path` (可选) |
| `git_analyze_project_structure` | 分析项目结构 | `project_path` (可选) |
| `git_setup_project_environment` | 设置项目环境 | `project_name`, `branch_name`, `remote_url` |
| `git_commit_and_push` | 提交并推送代码 | `commit_message`, `project_path`, `push_to_remote` |
| `git_create_commit_message` | 创建规范提交信息 | `commit_type`, `description` |

#### 使用示例

```python
from src.corder_integration.git_function_calling import GitFunctionCalling

# 初始化工具
git_tools = GitFunctionCalling()

# 获取工具 Schema（用于大模型工具注册）
schemas = git_tools.get_function_schemas()

# 执行工具调用
result = git_tools.execute_function("git_check_repository_status", {})
print(result)

# 结果格式：
{
    "success": True,
    "data": {
        "is_git_repo": True,
        "current_branch": "main",
        "has_uncommitted_changes": False,
        ...
    },
    "message": "仓库状态检查完成"
}
```

### 2. MCP (Model Context Protocol) 方式

#### MCP 服务器

```python
from src.corder_integration.git_mcp_server import GitMCPServer

# 创建 MCP 服务器
server = GitMCPServer()

# 处理 MCP 请求
request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "git_check_repository_status",
        "arguments": {}
    }
}

response = await server.handle_request(request)
```

#### MCP 响应格式

```json
{
    "jsonrpc": "2.0",
    "id": 1,
    "result": {
        "content": [
            {
                "type": "text",
                "text": "{\"success\": true, \"data\": {...}, \"message\": \"操作完成\"}"
            }
        ]
    }
}
```

### 3. Anthropic Claude 格式

专门为 Anthropic Claude 优化的 Function Calling 格式：

```python
from src.corder_integration.git_mcp_server import GitClaudeFunctionCalling

claude_tools = GitClaudeFunctionCalling()

# 获取 Claude 格式的工具定义
tools = claude_tools.get_claude_tools()

# 执行工具
result = claude_tools.execute_tool("git_check_repository_status", {})
```

## 工具详细说明

### 1. git_check_repository_status

**功能**：检查 Git 仓库的当前状态

**参数**：
- `project_path` (可选): 项目路径

**返回信息**：
- 是否为 Git 仓库
- 当前分支
- 是否有未提交更改
- 远程仓库信息
- 最后提交信息
- 与远程的同步状态

### 2. git_analyze_project_structure

**功能**：分析现有项目的目录结构和技术栈

**参数**：
- `project_path` (可选): 项目路径

**返回信息**：
- 项目是否存在
- 后端技术栈 (Maven/Gradle)
- 前端技术栈 (Vue.js/React)
- 现有文件列表
- Git 仓库信息

### 3. git_setup_project_environment

**功能**：设置新项目的开发环境

**参数**：
- `project_name` (必需): 项目名称
- `branch_name` (必需): 分支名称  
- `remote_url` (可选): 远程仓库 URL

**执行操作**：
- 创建项目目录
- 初始化 Git 仓库
- 创建/切换分支
- 添加远程仓库
- 创建基础目录结构

### 4. git_commit_and_push

**功能**：提交代码并推送到远程仓库

**参数**：
- `commit_message` (必需): 提交信息
- `project_path` (可选): 项目路径
- `push_to_remote` (可选): 是否推送到远程

**执行操作**：
- 添加所有更改文件
- 提交代码
- 推送到远程分支
- 返回提交 ID

### 5. git_create_commit_message

**功能**：创建规范的 Git 提交信息

**参数**：
- `commit_type` (必需): 提交类型 (feat/fix/docs/test/chore等)
- `description` (必需): 提交描述

**格式**：`[提交类型] 描述 - 时间戳`

## 安全性考虑

### 1. 权限控制

- **只读操作**：`git_check_repository_status`, `git_analyze_project_structure`
- **安全操作**：`git_create_commit_message`
- **写入操作**：`git_setup_project_environment`, `git_commit_and_push`

### 2. 路径安全

- 自动规范化项目名称，移除危险字符
- 限制操作范围在配置的项目目录内
- 防止路径遍历攻击

### 3. 命令安全

- 使用参数化命令执行，防止命令注入
- 完整的错误处理和日志记录
- 超时保护机制

## 大模型集成最佳实践

### 1. 渐进式权限

```
第一阶段：只允许只读操作
├── git_check_repository_status
└── git_analyze_project_structure

第二阶段：添加安全操作
├── git_create_commit_message
└── 项目信息查询

第三阶段：启用写入操作
├── git_setup_project_environment  
└── git_commit_and_push
```

### 2. 智能决策流程

```
1. 检查项目状态 → git_check_repository_status
2. 分析项目结构 → git_analyze_project_structure  
3. 根据需要设置环境 → git_setup_project_environment
4. 生成代码后提交 → git_commit_and_push
```

### 3. 错误处理策略

- **自动重试**：网络相关的 Git 操作
- **降级处理**：Git 失败时继续代码生成
- **用户确认**：危险操作前请求确认

## 运行和测试

### 1. Function Calling 测试

```bash
cd src/corder_integration
python -c "
from git_function_calling import demo_function_calling
demo_function_calling()
"
```

### 2. MCP 服务器测试

```bash
cd src/corder_integration  
python git_mcp_server.py --demo
```

### 3. 工具列表查看

```bash
python git_mcp_server.py --list-tools
```

### 4. 单个工具测试

```bash
python git_mcp_server.py --call-tool git_check_repository_status
```

## 性能优化

### 1. 缓存机制

- 项目结构信息缓存
- Git 状态信息缓存
- 减少重复的 Git 命令调用

### 2. 异步操作

- MCP 服务器使用异步处理
- 支持并发的 Git 操作
- 避免阻塞主线程

### 3. 批量操作

- 合并多个 Git 命令
- 减少 subprocess 调用开销
- 优化大文件处理

## 扩展性

### 1. 添加新的 Git 操作

1. 在 `GitManager` 中添加新方法
2. 在 `GitFunctionCalling` 中添加 Schema 定义
3. 实现对应的包装方法
4. 更新工具文档

### 2. 支持其他版本控制系统

- 抽象 VCS 接口
- 实现 SVN/Mercurial 适配器
- 统一的工具调用接口

### 3. 集成 CI/CD

- Git Hook 支持
- 自动化测试触发
- 部署流水线集成

## 总结

通过将 `git_manager.py` 的底层 Git 操作封装为标准的 Function Calling 和 MCP 接口，我们实现了：

1. **安全性**：完善的权限控制和错误处理
2. **易用性**：标准化的接口和清晰的文档
3. **可扩展性**：模块化设计，易于添加新功能
4. **兼容性**：支持多种大模型调用方式

大模型现在可以智能地执行 Git 操作，提升代码生成和项目管理的自动化水平。 