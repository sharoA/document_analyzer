# 🔍 条件检查器 & 🤖 LLM调用完整指南

## 📋 工作流概览

```
📄 输入文档 → 🧠 TaskSplittingNode → 🔍 DependencyChecker → 🔧 GitManagementNode → 
🏗️ ServiceChecker → 💻 IntelligentCodingNode → 🔍 CodeReviewNode → ✅ QualityChecker → 
🧪 UnitTestingNode → 🧪 TestChecker → 📤 GitCommitNode → ✅ 完成
```

## 🔍 条件检查器详细说明

### 1. DependencyChecker (任务依赖检查)
**位置**: `TaskSplittingNode` ➡️ `GitManagementNode`
**文件**: `src/corder_integration/langgraph/conditions/dependency_checker.py`

**检查内容**:
```python
✅ 微服务识别完整性
✅ 服务依赖关系明确性  
✅ 数据库结构清晰度
✅ API接口契约完整性
✅ 实现计划可执行性
```

**失败时行为**: 返回 `"task_splitting"` (重新拆分任务)
**成功时行为**: 返回 `"git_management"` (进入Git管理)

---

### 2. ServiceChecker (服务兼容性检查)
**位置**: `GitManagementNode` ➡️ `IntelligentCodingNode`
**文件**: `src/corder_integration/langgraph/conditions/service_checker.py`

**检查内容**:
```python
✅ Git仓库结构适配性
✅ 现有代码兼容性
✅ Nacos配置中心连通性
✅ Maven依赖版本兼容性
✅ 技术栈环境就绪性
```

**失败时行为**: 返回 `"git_management"` (调整Git配置)
**成功时行为**: 返回 `"intelligent_coding"` (开始编码)

---

### 3. QualityChecker (质量门禁检查)
**位置**: `CodeReviewNode` ➡️ `UnitTestingNode`
**文件**: `src/corder_integration/langgraph/conditions/quality_checker.py`

**检查内容**:
```python
✅ 代码规范符合性 (阿里巴巴Java规范)
✅ 安全漏洞扫描结果
✅ 架构设计原则遵守
✅ 代码复杂度控制
✅ 技术债务评估
```

**失败时行为**: 返回 `"intelligent_coding"` (重新生成代码)
**成功时行为**: 返回 `"unit_testing"` (开始测试)

---

### 4. TestChecker (测试结果检查)
**位置**: `UnitTestingNode` ➡️ `GitCommitNode`
**文件**: `src/corder_integration/langgraph/conditions/test_checker.py`

**检查内容**:
```python
✅ 单元测试覆盖率 (目标 >80%)
✅ 所有测试用例通过
✅ 集成测试结果
✅ 性能基准测试
✅ API接口测试
```

**失败时行为**: 返回 `"intelligent_coding"` (修复代码)
**成功时行为**: 返回 `"git_commit"` (提交代码)

---

## 🤖 LLM调用点详细说明

### 🧠 TaskSplittingNode (5个LLM调用)

| LLM调用 | Prompt文件 | 作用描述 | 输入 | 输出 |
|---------|------------|----------|------|------|
| **LLM调用1** | `requirement_analysis_prompt.py` | 需求文档分析 | 需求文档内容 | 功能需求、业务流程、数据实体 |
| **LLM调用2** | `design_analysis_prompt.py` | 设计文档分析 | 设计文档内容 | 系统架构、技术栈、部署要求 |
| **LLM调用3** | `service_boundary_prompt.py` | 微服务边界识别 | 需求+设计分析结果 | 微服务列表、边界定义、职责分工 |
| **LLM调用4** | `dependency_analysis_prompt.py` | 服务依赖分析 | 微服务列表、设计文档 | 依赖关系图、调用链路 |
| **LLM调用5** | `task_scheduling_prompt.py` | 执行计划制定 | 服务+依赖+复杂度 | 并行执行计划、优先级排序 |

---

### 🔧 GitManagementNode (1个LLM调用)

| LLM调用 | Prompt文件 | 作用描述 | 输入 | 输出 |
|---------|------------|----------|------|------|
| **LLM调用6** | `git_extraction_prompt.py` | Git信息提取 | 设计文档、服务列表 | 仓库结构、分支策略、Git配置 |

---

### 💻 IntelligentCodingNode (4个LLM调用)

| LLM调用 | Prompt文件 | 作用描述 | 输入 | 输出 |
|---------|------------|----------|------|------|
| **LLM调用7** | `service_analysis_prompt.py` | 服务需求分析 | 单个服务的需求 | 详细功能设计、数据模型 |
| **LLM调用8** | `code_generation_prompt.py` | 代码生成 (核心) | 功能设计、技术栈 | SpringBoot项目代码 |
| **LLM调用9** | `api_design_prompt.py` | API设计 | 服务功能、数据模型 | RESTful API定义 |
| **LLM调用10** | `service_interconnect_prompt.py` | 服务互联代码 | 服务依赖关系 | 服务间调用代码 |

---

### 🔍 CodeReviewNode (2个LLM调用)

| LLM调用 | Prompt文件 | 作用描述 | 输入 | 输出 |
|---------|------------|----------|------|------|
| **LLM调用11** | `code_review_prompt.py` | 代码质量审查 | 生成的源代码 | 代码评审报告、改进建议 |
| **LLM调用12** | `security_check_prompt.py` | 安全检查 | 源代码、依赖 | 安全漏洞报告、修复建议 |

---

### 🧪 UnitTestingNode (2个LLM调用)

| LLM调用 | Prompt文件 | 作用描述 | 输入 | 输出 |
|---------|------------|----------|------|------|
| **LLM调用13** | `test_generation_prompt.py` | 测试用例生成 | 源代码、API定义 | JUnit测试代码 |
| **LLM调用14** | `mock_generation_prompt.py` | Mock对象生成 | 服务依赖关系 | Mockito测试代码 |

---

### 📤 GitCommitNode (2个LLM调用)

| LLM调用 | Prompt文件 | 作用描述 | 输入 | 输出 |
|---------|------------|----------|------|------|
| **LLM调用15** | `commit_message_prompt.py` | 提交信息生成 | 代码变更内容 | 规范的Git提交信息 |
| **LLM调用16** | `pr_description_prompt.py` | PR描述生成 | 功能变更摘要 | Pull Request描述 |

---

## 🔄 条件检查器在工作流中的作用机制

```python
# 条件检查器的工作原理
def dependency_check_condition(state: CodingAgentState) -> str:
    """
    检查任务拆分结果是否满足依赖要求
    """
    if 所有依赖检查通过:
        return "git_management"    # 进入下一节点
    else:
        return "task_splitting"    # 返回重新处理

# 在LangGraph中的使用
workflow.add_conditional_edges(
    "task_splitting",                    # 源节点
    dependency_check_condition,          # 条件函数
    {
        "git_management": "git_management",   # 成功路径
        "task_splitting": "task_splitting"    # 失败路径(重试)
    }
)
```

## 📊 整体数据流

```
📄 需求+设计文档
    ↓ (5个LLM调用)
🧠 任务拆分结果 (services, dependencies, plan)
    ↓ (DependencyChecker)
🔧 Git配置结果 (repository, branches)  
    ↓ (ServiceChecker)
💻 代码生成结果 (source code, APIs)
    ↓ (QualityChecker)
🧪 测试执行结果 (test code, coverage)
    ↓ (TestChecker)  
📤 Git提交结果 (commits, PRs)
    ↓
✅ 完整的微服务项目
```

## 💡 关键设计原则

1. **🔄 智能重试**: 条件检查失败时自动返回上级节点重新处理
2. **📊 状态驱动**: 所有检查基于CodingAgentState状态进行
3. **🤖 LLM专用化**: 每个LLM调用都有专门的prompt模板
4. **🛡️ 质量保证**: 多层质量检查确保最终代码质量
5. **⚡ 并行优化**: 支持微服务并行生成和测试 