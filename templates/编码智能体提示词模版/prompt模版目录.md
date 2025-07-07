# 🎯 Prompt模板目录结构

## 📂 目录组织原则
- 按智能体功能域组织
- 每个LLM调用点对应一个专门的prompt文件
- 支持prompt版本化和A/B测试
- 包含示例输入输出和参数说明

## 📋 完整目录结构

```
src/corder_integration/prompts/
├── __init__.py
├── base/                                    # 🔧 基础prompt模板
│   ├── __init__.py
│   ├── base_prompts.py                      # 基础prompt结构
│   ├── system_context.py                    # 系统上下文prompt
│   └── response_format.py                   # 响应格式约束
│
├── task_splitting/                          # 🧠 任务拆分LLM调用 (5个)
│   ├── __init__.py
│   ├── requirement_analysis_prompt.py       # 📋 LLM调用1：需求文档分析
│   ├── design_analysis_prompt.py            # 🏗️ LLM调用2：设计文档分析
│   ├── service_boundary_prompt.py           # 🔍 LLM调用3：微服务边界识别
│   ├── dependency_analysis_prompt.py        # 🌐 LLM调用4：服务依赖分析
│   └── task_scheduling_prompt.py            # 📅 LLM调用5：执行计划制定
│
├── git_management/                          # 🔧 Git管理LLM调用 (1个)
│   ├── __init__.py
│   └── git_extraction_prompt.py             # 📂 LLM调用6：Git信息提取
│
├── intelligent_coding/                      # 💻 智能编码LLM调用 (4个)
│   ├── __init__.py
│   ├── service_analysis_prompt.py           # 🔍 LLM调用7：服务需求分析
│   ├── code_generation_prompt.py            # 🏗️ LLM调用8：代码生成 (核心)
│   ├── api_design_prompt.py                 # 🌐 LLM调用9：API设计
│   └── service_interconnect_prompt.py       # 🔗 LLM调用10：服务互联代码
│
├── code_review/                             # 🔍 代码审查LLM调用 (2个)
│   ├── __init__.py
│   ├── code_review_prompt.py                # 📝 LLM调用11：代码质量审查
│   └── security_check_prompt.py             # 🔒 LLM调用12：安全检查
│
├── unit_testing/                            # 🧪 单元测试LLM调用 (2个)
│   ├── __init__.py
│   ├── test_generation_prompt.py            # 📝 LLM调用13：测试用例生成
│   └── mock_generation_prompt.py            # 🎭 LLM调用14：Mock对象生成
│
└── git_commit/                              # 📤 Git提交LLM调用 (2个)
    ├── __init__.py
    ├── commit_message_prompt.py              # 📝 LLM调用15：提交信息生成
    └── pr_description_prompt.py              # 📋 LLM调用16：PR描述生成
```

## 🎯 LLM调用点统计
- **TaskSplittingNode**: 5个LLM调用
- **GitManagementNode**: 1个LLM调用
- **IntelligentCodingNode**: 4个LLM调用 (核心编码逻辑)
- **CodeReviewNode**: 2个LLM调用
- **UnitTestingNode**: 2个LLM调用
- **GitCommitNode**: 2个LLM调用

**总计**: 16个专门的LLM调用点，每个都有对应的prompt模板

## 📝 Prompt模板标准格式

每个prompt文件都包含：
1. **system_prompt**: 系统角色定义
2. **user_prompt**: 用户输入模板
3. **examples**: 输入输出示例
4. **constraints**: 响应格式约束
5. **version**: prompt版本号