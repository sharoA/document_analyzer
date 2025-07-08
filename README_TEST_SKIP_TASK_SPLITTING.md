# 跳过任务拆解阶段的测试脚本使用指南

## 概述

`test_skip_task_splitting.py` 是一个专门用于跳过任务拆解阶段，直接使用现有数据库数据测试后续节点的脚本。

## 功能特性

### 🎯 核心功能
- **跳过任务拆解**: 直接从 `git_management` 节点开始执行工作流程
- **使用现有数据**: 直接读取 `coding_agent_workflow.db` 中的 `task_001` 到 `task_012` 任务数据
- **完整测试流程**: 测试 Git管理、智能编码、代码审查、单元测试、Git提交等后续节点
- **详细报告**: 生成完整的测试执行报告

### 📊 支持的任务类型
- `git_extraction` - Git仓库地址提取
- `git_clone` - Git仓库克隆
- `code_analysis` - 代码结构分析
- `database` - 数据库设计
- `api` - API接口实现
- `config` - 配置管理
- `integration_test` - 集成测试
- `deployment` - 代码部署

## 使用方法

### 1. 环境准备

确保以下文件存在：
```
coding_agent_workflow.db        # 工作流程数据库（包含task_001到task_012任务）
workflow_checkpoints.db         # LangGraph检查点数据库
```

**注意**: 数据库中必须已存在 `task_001` 到 `task_012` 的任务数据。

### 2. 数据验证

运行测试前，可以检查数据库中是否有所需的任务数据：

```bash
# 检查数据库内容
python check_sqlite_db.py
```

确保 `execution_tasks` 表中包含 `task_001` 到 `task_012` 的记录。

### 3. 运行测试

```bash
# 直接运行测试脚本
python test_skip_task_splitting.py
```

### 4. 测试流程

脚本将按以下步骤执行：

1. **🔧 设置测试环境**
   - 初始化工作流程管理器
   - 连接到现有数据库

2. **📋 加载任务数据**
   - 从 `coding_agent_workflow.db` 中读取 `task_001` 到 `task_012`
   - 自动重置任务状态为 `pending`
   - 验证数据完整性

3. **🔄 重置任务状态**
   - 将所有加载的任务状态重置为 `pending`
   - 确保测试从干净状态开始

4. **🏗️ 创建初始状态**
   - 模拟任务拆解完成的状态
   - 提取服务信息（用户服务、确权开立服务）
   - 构建服务依赖关系

5. **🚀 执行工作流程**
   - 从 `git_management` 节点开始
   - 依次执行各个节点
   - 记录执行结果

6. **📄 生成报告**
   - 创建详细的测试报告
   - 保存到 JSON 文件

## 输出结果

### 控制台输出
```
🎉 测试完成！
============================================================
最终阶段: git_commit
完成的服务: ['用户服务', '确权开立服务']
失败的服务: []
执行错误: 0
============================================================
```

### 报告文件
生成的 JSON 报告包含：
- **测试摘要**: 执行阶段、完成/失败服务、错误信息
- **Git管理结果**: 仓库初始化状态、项目路径
- **编码结果**: 生成的服务、API、SQL数量
- **测试结果**: 单元测试结果、测试覆盖率

## 数据库操作

### 任务数据结构
```sql
CREATE TABLE execution_tasks (
    task_id TEXT PRIMARY KEY,           -- 任务ID (task_001, task_002, ...)
    service_name TEXT NOT NULL,         -- 服务名称 (用户服务, 确权开立服务, 系统)
    task_type TEXT NOT NULL,            -- 任务类型 (git_extraction, code_analysis, api, ...)
    priority INTEGER DEFAULT 1,         -- 优先级 (1-10)
    status TEXT DEFAULT 'pending',      -- 状态 (pending, running, completed, failed)
    dependencies TEXT,                  -- 依赖任务ID列表 (JSON数组)
    estimated_duration TEXT,            -- 预估时长
    description TEXT,                   -- 任务描述
    deliverables TEXT,                  -- 交付物列表 (JSON数组)
    implementation_details TEXT,        -- 实现细节
    completion_criteria TEXT,           -- 完成标准
    parameters TEXT,                    -- 任务参数 (JSON对象)
    created_at TIMESTAMP,               -- 创建时间
    updated_at TIMESTAMP                -- 更新时间
)
```

### 任务依赖关系
基于数据库中存储的任务数据：
- task_001 (git_extraction) → 无依赖
- task_002 (git_clone) → 依赖 task_001
- task_003 (git_clone) → 依赖 task_001
- task_004 (code_analysis) → 依赖 task_002
- ... 以此类推

## 节点执行逻辑

### Git管理节点
- 领取 `git_extraction` 和 `git_clone` 类型任务
- 提取Git仓库地址
- 克隆仓库到本地

### 智能编码节点
- 领取 `code_analysis`, `database`, `api`, `config` 类型任务
- 分析代码结构
- 设计数据库
- 实现API接口

### 其他节点
- **代码审查节点**: 质量检查、安全扫描
- **单元测试节点**: 生成和执行测试用例
- **Git提交节点**: 提交代码到仓库

## 故障排除

### 常见错误

1. **任务数据不存在**
   ```
   ❌ 数据库中没有找到task_001到task_012的任务数据
   ```
   **解决**: 确保数据库中包含所需的任务数据，可运行其他脚本先生成任务数据

2. **数据库锁定**
   ```
   ❌ 数据库锁定，第1次重试...
   ```
   **解决**: 关闭其他使用数据库的进程，脚本会自动重试

3. **任务状态重置失败**
   ```
   ❌ 任务状态重置失败
   ```
   **解决**: 检查数据库文件权限和连接状态

### 调试模式

修改日志级别以获取更详细的信息：
```python
logging.basicConfig(level=logging.DEBUG)
```

## 扩展功能

### 自定义任务数据

可以修改 `TestWorkflowManager.load_tasks_from_database()` 方法来支持自定义的任务ID范围或筛选条件。

### 添加新的任务类型

在各个节点的 `supported_task_types` 列表中添加新的任务类型，并实现对应的执行逻辑。

### 状态持久化

测试过程中的状态变化会保存到 `workflow_checkpoints.db` 中，可以用于断点续传。

## 注意事项

1. **数据库分离**: 
   - `coding_agent_workflow.db` 用于任务存储
   - `workflow_checkpoints.db` 用于LangGraph检查点

2. **任务状态管理**: 
   - 脚本会自动处理任务的领取、执行、完成状态更新

3. **并发安全**: 
   - 使用SQLite WAL模式和重试机制确保并发安全

4. **测试隔离**: 
   - 每次运行都会重置任务状态为pending，确保测试从干净状态开始 