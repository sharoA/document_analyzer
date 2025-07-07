# 🚀 {{ project_config.name }}编码智能体可执行实现

## 📋 基于{{ project_config.base_framework }}的完整实现

基于现有的架构设计，实现支持多服务协调、任务拆分调度、并行处理的LangGraph工作流。

---

## 🏗️ 核心实现架构

### 1. 工作流编排器 - workflow_orchestrator.py

```python
# {{ project_config.src_path }}/{{ project_config.integration_module }}/langgraph/workflow_orchestrator.py
"""
LangGraph工作流编排器 - 基于{{ project_config.base_framework }}的完整实现
"""

from langgraph.graph import StateGraph, END
{% if project_config.database.type == 'postgresql' %}
from langgraph.checkpoint.postgres import PostgresCheckpointer
{% elif project_config.database.type == 'mysql' %}
from langgraph.checkpoint.mysql import MySQLCheckpointer
{% else %}
from langgraph.checkpoint.memory import MemoryCheckpointer
{% endif %}
from typing import TypedDict, List, Dict, Any, Optional
import asyncio
import logging
import time

from .nodes.task_splitting_node import task_splitting_node
from .nodes.git_management_node import git_management_node
from .nodes.intelligent_coding_node import intelligent_coding_node
from .nodes.code_review_node import code_review_node
from .nodes.unit_testing_node import unit_testing_node
from .nodes.git_commit_node import git_commit_node

# 📊 状态定义
class {{ project_config.state_class_name }}(TypedDict):
    """{{ project_config.agent_name }}完整状态定义"""
    
    # 🔄 输入状态
    requirements_doc: str
    design_doc: str
    project_name: str
    
    # 🧠 任务拆分结果
    identified_services: List[str]
    service_dependencies: Dict[str, List[str]]
    task_execution_plan: Dict[str, Any]
    parallel_tasks: List[Dict[str, Any]]
    
    # 🔧 Git管理状态
    git_repo_url: Optional[str]
    target_branch: str
    project_paths: Dict[str, str]
    repo_initialized: bool
    
    # 💻 代码生成状态
    generated_services: Dict[str, Dict[str, Any]]
    generated_apis: Dict[str, List[str]]
    generated_sql: Dict[str, List[str]]
    service_interconnections: Dict[str, Dict[str, Any]]
    
    # 🧪 测试状态
    unit_test_results: Dict[str, Dict[str, Any]]
    test_coverage: Dict[str, float]
    interface_compatibility: Dict[str, bool]
    
    # 🔍 质量检查状态
    code_review_results: Dict[str, Dict[str, Any]]
    static_analysis_results: Dict[str, Any]
    security_scan_results: Dict[str, Any]
    
    # 📤 Git提交状态
    commit_hashes: Dict[str, str]
    push_results: Dict[str, bool]
    pr_urls: Dict[str, str]
    
    # 🔄 执行控制状态
    current_phase: str
    completed_services: List[str]
    failed_services: List[str]
    retry_count: int
    execution_errors: List[str]

class {{ project_config.orchestrator_class_name }}:
    """LangGraph工作流编排器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.graph = self._build_workflow_graph()
        self.checkpointer = self._setup_checkpointer()
        self.compiled_graph = self.graph.compile(checkpointer=self.checkpointer)
    
    def _setup_checkpointer(self):
        """设置检查点管理器"""
        {% if project_config.database.type == 'postgresql' %}
        return PostgresCheckpointer.from_conn_string(
            conn_string="{{ project_config.database.connection_string }}",
            serde=None
        )
        {% elif project_config.database.type == 'mysql' %}
        return MySQLCheckpointer.from_conn_string(
            conn_string="{{ project_config.database.connection_string }}",
            serde=None
        )
        {% else %}
        return MemoryCheckpointer()
        {% endif %}
    
    def _build_workflow_graph(self) -> StateGraph:
        """构建LangGraph工作流图"""
        workflow = StateGraph({{ project_config.state_class_name }})
        
        # 🧠 添加工作流节点
        {% for node in project_config.workflow_nodes %}
        workflow.add_node("{{ node.name }}", {{ node.function_name }})
        {% endfor %}
        
        # 🚀 设置工作流入口
        workflow.set_entry_point("{{ project_config.entry_node }}")
        
        # 🔄 定义节点流转逻辑
        {% for edge in project_config.workflow_edges %}
        {% if edge.type == 'simple' %}
        workflow.add_edge("{{ edge.from }}", "{{ edge.to }}")
        {% elif edge.type == 'conditional' %}
        workflow.add_conditional_edges(
            "{{ edge.from }}",
            self.{{ edge.condition_function }},
            {
                {% for condition, target in edge.conditions.items() %}
                "{{ condition }}": "{{ target }}"{% if not loop.last %},{% endif %}
                {% endfor %}
            }
        )
        {% endif %}
        {% endfor %}
        
        return workflow
    
    # 🔄 条件检查函数
    {% for condition_func in project_config.condition_functions %}
    def {{ condition_func.name }}(self, state: {{ project_config.state_class_name }}) -> str:
        """{{ condition_func.description }}"""
        {{ condition_func.logic | indent(8) }}
    {% endfor %}
    
    # 🚀 主执行函数
    async def execute_coding_workflow(
        self, 
        requirements_doc: str, 
        design_doc: str, 
        project_name: str
    ) -> Dict[str, Any]:
        """执行完整的编码工作流"""
        
        # 🔄 初始化状态
        initial_state: {{ project_config.state_class_name }} = {
            "requirements_doc": requirements_doc,
            "design_doc": design_doc,
            "project_name": project_name,
            "identified_services": [],
            "service_dependencies": {},
            "task_execution_plan": {},
            "parallel_tasks": [],
            "git_repo_url": None,
            "target_branch": f"{{ project_config.branch_prefix }}/{project_name}",
            "project_paths": {},
            "repo_initialized": False,
            "generated_services": {},
            "generated_apis": {},
            "generated_sql": {},
            "service_interconnections": {},
            "unit_test_results": {},
            "test_coverage": {},
            "interface_compatibility": {},
            "code_review_results": {},
            "static_analysis_results": {},
            "security_scan_results": {},
            "commit_hashes": {},
            "push_results": {},
            "pr_urls": {},
            "current_phase": "{{ project_config.initial_phase }}",
            "completed_services": [],
            "failed_services": [],
            "retry_count": 0,
            "execution_errors": []
        }
        
        # 🎯 执行工作流
        config = {
            "configurable": {
                "thread_id": f"{{ project_config.thread_id_prefix }}_{project_name}_{int(time.time())}"
            }
        }
        
        try:
            # 🔄 运行编译后的图
            final_state = await self.compiled_graph.ainvoke(initial_state, config=config)
            
            # 📊 返回执行结果
            return {
                "status": "success",
                "project_name": project_name,
                "generated_services": final_state["generated_services"],
                "commit_hashes": final_state["commit_hashes"], 
                "pr_urls": final_state["pr_urls"],
                "execution_summary": self._generate_summary(final_state)
            }
            
        except Exception as e:
            self.logger.error(f"工作流执行失败: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "project_name": project_name
            }
```

---

## 🎯 使用示例

```python
# {{ project_config.src_path }}/main.py
"""
{{ project_config.name }}编码智能体使用示例
"""

import asyncio
from {{ project_config.integration_module }}.langgraph.workflow_orchestrator import {{ project_config.orchestrator_class_name }}

async def main():
    """主执行函数"""
    
    # 📄 输入文档
    requirements_doc = """
    {{ project_config.sample_requirements }}
    """
    
    design_doc = """
    {{ project_config.sample_design }}
    """
    
    # 🚀 执行工作流
    orchestrator = {{ project_config.orchestrator_class_name }}()
    
    result = await orchestrator.execute_coding_workflow(
        requirements_doc=requirements_doc,
        design_doc=design_doc,
        project_name="{{ project_config.sample_project_name }}"
    )
    
    print(f"执行结果: {result}")
    
    if result["status"] == "success":
        print(f"✅ 成功生成 {len(result['generated_services'])} 个{{ project_config.service_type }}")
        print(f"📝 提交哈希: {result['commit_hashes']}")
        print(f"🔗 PR地址: {result['pr_urls']}")
    else:
        print(f"❌ 执行失败: {result['error']}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📊 核心特性

### ✨ 基于LangGraph的强大工作流
1. **状态管理**：完整的状态跟踪和持久化
2. **条件分支**：智能的流程控制和重试机制
3. **并行处理**：支持多服务并行生成
4. **错误恢复**：完善的错误处理和重试

### 🎯 符合{{ project_config.base_framework }}的设计
1. **任务拆分调度**：智能识别{{ project_config.service_type }}和依赖关系
2. **Git管理**：完整的版本控制支持
3. **代码生成**：{{ project_config.tech_stack }}技术栈
4. **质量保证**：代码审查 + 单元测试
5. **自动提交**：Git提交和PR创建

### 🔧 提示词分离
所有大模型调用的提示词都提取到了单独的目录中，便于维护和优化。

这个实现完全基于{{ project_config.base_framework }}的设计，提供了可执行的LangGraph工作流！ 