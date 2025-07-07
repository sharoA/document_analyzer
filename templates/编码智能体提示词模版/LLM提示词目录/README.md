# 🧠 LLM提示词目录

## 📋 目录说明

本目录包含编码智能体各个节点调用大模型的提示词模板，按功能模块组织。

## 📂 目录结构

```
LLM提示词目录/
├── README.md                          # 本说明文件
├── task_splitting_prompts.py          # 任务拆分节点提示词
├── git_management_prompts.py          # Git管理节点提示词
├── intelligent_coding_prompts.py      # 智能编码节点提示词
├── code_review_prompts.py             # 代码审查节点提示词
├── unit_testing_prompts.py            # 单元测试节点提示词
├── git_commit_prompts.py              # Git提交节点提示词
└── common_prompts.py                  # 通用提示词
```

## 🎯 提示词设计原则

### 1. **明确性** - 指令清晰明确
- 明确输入格式和输出格式
- 详细说明期望的行为
- 提供具体的示例

### 2. **一致性** - 保持风格统一
- 统一的JSON输出格式
- 一致的错误处理方式
- 标准化的输入参数

### 3. **可扩展性** - 支持功能扩展
- 模块化的提示词设计
- 参数化的模板系统
- 灵活的上下文注入

### 4. **专业性** - 体现领域专业知识
- Spring Boot微服务最佳实践
- 代码质量和安全标准
- Git工作流程规范

## 🔧 使用方式

### 基本使用
```python
from LLM提示词目录.task_splitting_prompts import REQUIREMENTS_ANALYSIS_PROMPT

prompt = REQUIREMENTS_ANALYSIS_PROMPT.format(
    requirements_doc=requirements_doc,
    project_name=project_name
)
```

### 高级使用
```python
from LLM提示词目录.intelligent_coding_prompts import PromptBuilder

builder = PromptBuilder()
prompt = builder.build_service_analysis_prompt(
    service_name="user-service",
    requirements_doc=requirements_doc,
    design_doc=design_doc,
    context=additional_context
)
```

## 📊 提示词质量指标

- **准确性**: 生成结果的正确性
- **完整性**: 输出信息的完整度  
- **一致性**: 多次调用的稳定性
- **效率性**: Token使用的优化程度

## 🚀 维护指南

1. **版本控制**: 重要修改需要版本标记
2. **测试验证**: 新提示词需要测试验证
3. **性能监控**: 跟踪提示词的效果
4. **持续优化**: 根据反馈持续改进 