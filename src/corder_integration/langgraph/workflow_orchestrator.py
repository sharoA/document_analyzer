#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangGraph工作流编排器 - 基于核心功能生成.md的完整实现
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, List, Dict, Any, Optional
import asyncio
import logging
import time
import os

# 🔧 修改：使用异步SQLite检查点替代PostgreSQL
try:
    # 🔧 修复：使用正确的langgraph-checkpoint-sqlite包导入路径
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
    SQLITE_CHECKPOINTER_AVAILABLE = True
except ImportError:
    logging.warning("异步SQLite检查点不可用，将仅使用内存检查点")
    AsyncSqliteSaver = None
    SQLITE_CHECKPOINTER_AVAILABLE = False

from .nodes.task_splitting_node import task_splitting_node
from .nodes.git_management_node import git_management_node
from .nodes.intelligent_coding_node import intelligent_coding_node
from .nodes.code_review_node import code_review_node
from .nodes.unit_testing_node import unit_testing_node
from .nodes.git_commit_node import git_commit_node

logger = logging.getLogger(__name__)

# 📊 状态定义（与核心功能生成.md保持一致）
class CodingAgentState(TypedDict):
    """编码智能体完整状态定义"""
    
    # 🔄 输入状态
    design_doc: str                         # 设计文档内容
    project_name: str                       # 项目名称
    
    # 🧠 任务拆分结果
    identified_services: List[str]          # 识别的微服务列表
    service_dependencies: Dict[str, List[str]]  # 服务依赖关系图
    task_execution_plan: Dict[str, Any]     # 任务执行计划
    parallel_tasks: List[Dict[str, Any]]    # 可并行执行的任务
    
    # 🔧 Git管理状态
    git_repo_url: Optional[str]             # Git地址
    target_branch: str                      # 目标分支名称
    project_paths: Dict[str, str]           # 各微服务的项目路径
    repo_initialized: bool                  # 仓库初始化状态
    
    # 💻 代码生成状态
    generated_services: Dict[str, Dict[str, Any]]  # 已生成的服务代码
    generated_apis: Dict[str, List[str]]    # 生成的API接口
    generated_sql: Dict[str, List[str]]     # 生成的SQL语句
    service_interconnections: Dict[str, Dict[str, Any]]  # 服务间调用关系
    
    # 🧪 测试状态
    unit_test_results: Dict[str, Dict[str, Any]]    # 单元测试结果
    test_coverage: Dict[str, float]         # 测试覆盖率
    interface_compatibility: Dict[str, bool] # 接口兼容性检查结果
    
    # 🔍 质量检查状态
    code_review_results: Dict[str, Dict[str, Any]]  # 代码审查结果
    static_analysis_results: Dict[str, Any]         # 静态分析结果
    security_scan_results: Dict[str, Any]           # 安全扫描结果
    
    # 📤 Git提交状态
    commit_hashes: Dict[str, str]           # 各服务的提交哈希
    push_results: Dict[str, bool]           # 推送结果
    pr_urls: Dict[str, str]                 # PR地址
    
    # 🔄 执行控制状态
    current_phase: str                      # 当前执行阶段
    completed_services: List[str]           # 已完成的服务
    failed_services: List[str]              # 失败的服务
    retry_count: int                        # 重试次数
    execution_errors: List[str]             # 执行错误列表

class LangGraphWorkflowOrchestrator:
    """LangGraph工作流编排器"""
    
    def __init__(self, use_sqlite: bool = True, db_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.use_sqlite = use_sqlite and SQLITE_CHECKPOINTER_AVAILABLE
        self.db_path = db_path or "coding_agent_workflow.db"  # 默认SQLite数据库路径
        self.graph = self._build_workflow_graph()
        self.checkpointer = self._setup_checkpointer()
        self.compiled_graph = self.graph.compile(checkpointer=self.checkpointer)
    
    def _setup_checkpointer(self):
        """设置检查点管理器"""
        if self.use_sqlite and SQLITE_CHECKPOINTER_AVAILABLE:
            # 异步SQLite检查点（生产/开发环境）
            try:
                # 🔧 修复：正确使用AsyncSqliteSaver
                # 对于内存数据库，使用 ":memory:"
                # 对于文件数据库，直接使用文件路径
                if self.db_path == ":memory:":
                    checkpointer = AsyncSqliteSaver.from_conn_string(":memory:")
                else:
                    checkpointer = AsyncSqliteSaver.from_conn_string(self.db_path)
                self.logger.info(f"使用异步SQLite检查点: {self.db_path}")
                return checkpointer
            except Exception as e:
                self.logger.warning(f"异步SQLite检查点初始化失败，降级到内存检查点: {e}")
                return MemorySaver()
        else:
            # 内存检查点（SQLite不可用时）
            self.logger.info("使用内存检查点")
            return MemorySaver()
    
    def _build_workflow_graph(self) -> StateGraph:
        """构建LangGraph工作流图"""
        workflow = StateGraph(CodingAgentState)
        
        # 🧠 添加工作流节点
        workflow.add_node("task_splitting", task_splitting_node)
        workflow.add_node("git_management", git_management_node)
        workflow.add_node("intelligent_coding", intelligent_coding_node)
        workflow.add_node("code_review", code_review_node)
        workflow.add_node("unit_testing", unit_testing_node)
        workflow.add_node("git_commit", git_commit_node)
        
        # 🚀 设置工作流入口
        workflow.set_entry_point("task_splitting")
        
        # 🔄 定义节点流转逻辑
        workflow.add_edge("task_splitting", "git_management")
        
        # Git管理 → 智能编码（支持条件分支）
        workflow.add_conditional_edges(
            "git_management",
            self.check_git_setup_success,
            {
                "success": "intelligent_coding",
                "retry": "git_management",
                "fail": END
            }
        )
        
        # 智能编码 → 代码审查（支持重试逻辑）
        workflow.add_conditional_edges(
            "intelligent_coding", 
            self.check_coding_completion,
            {
                "all_completed": "code_review",
                "partial_completed": "intelligent_coding",
                "dependencies_waiting": "intelligent_coding",
                "critical_error": END
            }
        )
        
        # 代码审查 → 单元测试
        workflow.add_conditional_edges(
            "code_review",
            self.check_review_quality,
            {
                "quality_passed": "unit_testing", 
                "quality_failed": "intelligent_coding",
                "security_risk": END
            }
        )
        
        # 单元测试 → Git提交
        workflow.add_conditional_edges(
            "unit_testing",
            self.check_test_results,
            {
                "tests_passed": "git_commit",
                "tests_failed": "intelligent_coding",
                "coverage_insufficient": "unit_testing"
            }
        )
        
        # Git提交 → 结束
        workflow.add_edge("git_commit", END)
        
        return workflow
    
    # 🔄 条件检查函数
    def check_git_setup_success(self, state: CodingAgentState) -> str:
        """检查Git环境设置是否成功"""
        if state["repo_initialized"]:
            return "success"
        elif state["retry_count"] < 3:
            return "retry"
        else:
            return "fail"
    
    def check_coding_completion(self, state: CodingAgentState) -> str:
        """检查编码完成状态"""
        total_services = len(state["identified_services"])
        completed_services = len(state["completed_services"])
        
        if completed_services == total_services:
            return "all_completed"
        elif len(state["failed_services"]) > 0:
            return "critical_error"
        else:
            # 检查是否有依赖等待
            for service in state["identified_services"]:
                if service not in state["completed_services"]:
                    dependencies = state["service_dependencies"].get(service, [])
                    if any(dep not in state["completed_services"] for dep in dependencies):
                        return "dependencies_waiting"
            return "partial_completed"
    
    def check_review_quality(self, state: CodingAgentState) -> str:
        """检查代码审查质量"""
        review_results = state.get("code_review_results", {})
        if any(result.get("has_critical_issues", False) for result in review_results.values()):
            return "quality_failed"
        elif any(result.get("security_risk", False) for result in review_results.values()):
            return "security_risk"
        else:
            return "quality_passed"
    
    def check_test_results(self, state: CodingAgentState) -> str:
        """检查测试结果"""
        test_results = state.get("unit_test_results", {})
        coverage_results = state.get("test_coverage", {})
        
        # 检查测试是否通过
        if any(not result.get("all_passed", True) for result in test_results.values()):
            return "tests_failed"
        
        # 检查覆盖率
        avg_coverage = sum(coverage_results.values()) / len(coverage_results) if coverage_results else 0
        if avg_coverage < 0.8:  # 80%覆盖率要求
            return "coverage_insufficient"
        
        return "tests_passed"
    
    def _generate_summary(self, final_state: CodingAgentState) -> Dict[str, Any]:
        """生成执行摘要"""
        return {
            "total_services": len(final_state["identified_services"]),
            "completed_services": len(final_state["completed_services"]),
            "failed_services": len(final_state["failed_services"]),
            "test_coverage": final_state.get("test_coverage", {}),
            "execution_phase": final_state["current_phase"],
            "generated_services": final_state.get("generated_services", {}),
            "commit_hashes": final_state.get("commit_hashes", {}),
            "pr_urls": final_state.get("pr_urls", {})
        }
    
    # 🚀 主执行函数
    async def execute_coding_workflow(
        self, 
        design_doc: str, 
        project_name: str,
        output_path: str = None  # 🎯 新增：输出路径参数
    ) -> Dict[str, Any]:
        """执行完整的编码工作流"""
        
        # 🎯 设置默认输出路径
        if output_path is None:
            output_path = r"D:\gitlab"
        
        # 🔄 初始化状态
        initial_state: CodingAgentState = {
            "design_doc": design_doc,
            "project_name": project_name,
            "identified_services": [],
            "service_dependencies": {},
            "task_execution_plan": {},
            "parallel_tasks": [],
            "git_repo_url": None,
            "target_branch": f"feature/{project_name}",
            "project_paths": {},  # 🎯 稍后根据识别的服务动态设置
            "output_path": output_path,  # 🎯 新增：保存输出路径
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
            "current_phase": "task_splitting",
            "completed_services": [],
            "failed_services": [],
            "retry_count": 0,
            "execution_errors": []
        }
        
        # 🎯 执行工作流
        config = {
            "configurable": {
                "thread_id": f"coding_session_{project_name}_{int(time.time())}"
            },
            "recursion_limit": 50  # 🔧 增加递归限制，防止无限循环
        }
        
        try:
            self.logger.info(f"开始执行编码工作流: {project_name} -> {output_path}")
            
            # 🔄 运行编译后的图
            final_state = await self.compiled_graph.ainvoke(initial_state, config=config)
            
            # 📊 返回执行结果
            summary = self._generate_summary(final_state)
            
            self.logger.info(f"工作流执行成功: {project_name}, 完成服务数: {summary['completed_services']}")
            
            return {
                "status": "success",
                "project_name": project_name,
                "output_path": output_path,  # 🎯 新增：返回输出路径
                "execution_summary": summary,
                "final_state": final_state
            }
            
        except Exception as e:
            self.logger.error(f"工作流执行失败: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "project_name": project_name,
                "output_path": output_path  # 🎯 新增：返回输出路径
            }

    # 🎯 新增：便捷的文档处理方法
    async def execute_workflow(
        self,
        document_content: str,
        project_name: str,
        output_path: str = None
    ) -> Dict[str, Any]:
        """便捷方法：直接使用设计文档进行处理"""
        
        # 直接将文档内容作为设计文档
        design_doc = document_content.strip()
        
        return await self.execute_coding_workflow(
            design_doc=design_doc,
            project_name=project_name,
            output_path=output_path
        ) 