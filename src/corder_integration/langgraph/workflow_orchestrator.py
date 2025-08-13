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
from datetime import datetime

# 导入LangGraph核心组件
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# from .nodes.task_splitting_node import task_splitting_node  # 任务拆分节点
from .nodes.task_simple_splitting_node import task_simple_splitting_node  # 🆕 简化版任务拆分节点
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
    project_task_id: str                    # 🆕 项目唯一标识，用于任务拆解和编码智能体操作
    
    # 🧠 任务拆分结果
    identified_services: List[str]          # 识别的微服务列表
    service_dependencies: Dict[str, List[str]]  # 服务依赖关系图
    task_execution_plan: Dict[str, Any]     # 任务执行计划
    parallel_tasks: List[Dict[str, Any]]    # 可并行执行的任务
    
    # 🔧 Git管理状态
    git_repo_url: Optional[str]             # Git地址
    target_branch: str                      # 目标分支名称
    project_paths: Dict[str, str]           # 各微服务的项目路径
    output_path: Optional[str]              # 输出路径
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
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.graph = self._build_workflow_graph()
        # 使用内存检查点
        self.checkpointer = MemorySaver()
    
    def _build_workflow_graph(self) -> StateGraph:
        """构建LangGraph工作流图"""
        workflow = StateGraph(CodingAgentState)
        
        # 🧠 添加工作流节点
        # workflow.add_node("task_splitting", task_splitting_node) #原复杂版本，已注释
        workflow.add_node("task_splitting", task_simple_splitting_node) # 🆕 使用简化版任务拆分节点
        workflow.add_node("git_management", git_management_node)
        workflow.add_node("intelligent_coding", intelligent_coding_node)
        workflow.add_node("code_review", code_review_node)
        workflow.add_node("unit_testing", unit_testing_node)
        workflow.add_node("git_commit", git_commit_node)
        
        # 🚀 设置工作流入口
        workflow.set_entry_point("task_splitting") #先注释，调试完成后面节点后再放开
        # workflow.set_entry_point("git_management")
        
        # 🔄 定义节点流转逻辑
        workflow.add_edge("task_splitting", "git_management") #先注释，调试完成后面节点后再放开
        # workflow.add_edge("git_management", "intelligent_coding")



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
        # 🔧 修复：检查是否有识别的服务，如果没有则直接失败
        if len(state["identified_services"]) == 0:
            self.logger.warning("没有识别到任何服务，Git设置阶段结束")
            return "fail"
            
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
        
        # 🔧 修复：如果没有识别到任何服务，直接结束流程
        if total_services == 0:
            self.logger.warning("没有识别到任何服务，结束编码流程")
            return "critical_error"
        
        # 🆕 新增：无进展检测机制
        retry_count = state.get("retry_count", 0)
        
        # 如果已经重试多次但没有进展，强制结束
        if retry_count >= 5:
            self.logger.warning(f"编码流程重试次数过多({retry_count})，强制结束")
            return "critical_error"
        
        # 🔧 修复：检查数据库中是否还有编码相关任务，而不是只看 coding_operations
        project_task_id = state.get("project_task_id")
        if project_task_id and retry_count >= 2:
            try:
                from .task_manager import NodeTaskManager
                task_manager = NodeTaskManager()
                # 检查是否还有编码相关任务（intelligent_coding_node 支持的任务类型）
                coding_task_types = ["code_analysis", "database", "api", "config"]
                remaining_coding_tasks = task_manager.get_node_tasks(coding_task_types, project_task_id)
                
                if len(remaining_coding_tasks) == 0:
                    self.logger.info("✅ 所有编码相关任务已完成，进入下一阶段")
                    return "all_completed"
                else:
                    self.logger.info(f"🔄 还有 {len(remaining_coding_tasks)} 个编码任务待执行，继续等待")
                    
            except Exception as e:
                self.logger.warning(f"⚠️ 检查剩余任务时出错: {e}")
        
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
        # 🔧 修复：如果没有识别到任何服务，直接通过
        if len(state["identified_services"]) == 0:
            self.logger.warning("没有识别到任何服务，代码审查直接通过")
            return "quality_passed"
            
        review_results = state.get("code_review_results", {})
        if any(result.get("has_critical_issues", False) for result in review_results.values()):
            return "quality_failed"
        elif any(result.get("security_risk", False) for result in review_results.values()):
            return "security_risk"
        else:
            return "quality_passed"
    
    def check_test_results(self, state: CodingAgentState) -> str:
        """检查测试结果"""
        # 🔧 修复：如果没有识别到任何服务，直接通过
        if len(state["identified_services"]) == 0:
            self.logger.warning("没有识别到任何服务，测试检查直接通过")
            return "tests_passed"
            
        test_results = state.get("unit_test_results", {})
        coverage_results = state.get("test_coverage", {})
        
        # 🆕 如果没有任何测试结果，说明没有测试任务，直接通过
        if not test_results and not coverage_results:
            self.logger.info("没有测试任务，测试检查直接通过")
            return "tests_passed"
        
        # 检查测试是否通过
        if any(not result.get("all_passed", True) for result in test_results.values()):
            return "tests_failed"
        
        # 检查覆盖率 - 🆕 修复：如果没有覆盖率数据，认为通过
        if coverage_results:
            avg_coverage = sum(coverage_results.values()) / len(coverage_results)
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
        project_task_id: str,  # 🆕 添加project_task_id参数
        output_path: str = None  # 🎯 新增：输出路径参数
    ) -> Dict[str, Any]:
        """执行完整的编码工作流"""
        
        # 🎯 设置默认输出路径
        if output_path is None:
            from src.resource.config import ConfigManager
            config_manager = ConfigManager()
            coder_config = config_manager.get_coder_agent_config()
            output_path = coder_config.get("project_root", "/Users/renyu/Documents/create_project")
        
        # 编译图形
        compiled_graph = self.graph.compile(checkpointer=self.checkpointer)
        
        # 🔧 生成新的分支名称格式
        target_branch = self._generate_target_branch(project_name)
        
        # 🔄 初始化状态
        initial_state: CodingAgentState = {
            "design_doc": design_doc,
            "project_name": project_name,
            "project_task_id": project_task_id,  # 🆕 添加项目唯一标识
            "identified_services": [],
            "service_dependencies": {},
            "task_execution_plan": {},
            "parallel_tasks": [],
            "git_repo_url": None,
            "target_branch": target_branch,
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
            "current_phase": "task_splitting", #先注释，调试完成后面节点后再放开
            # "current_phase": "git_management",
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
            "recursion_limit": 100  # 🔧 增加递归限制，防止复杂工作流被误判
        }
        
        try:
            self.logger.info(f"开始执行编码工作流: {project_name} -> {output_path}")
            
            # 🔄 运行编译后的图
            final_state = await compiled_graph.ainvoke(initial_state, config=config)
            
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
    
    def _generate_target_branch(self, project_name: str) -> str:
        """生成目标分支名称 - 格式: D_日期_项目名称"""
        # 获取当前日期 (YYYYMMDD格式)
        current_date = datetime.now().strftime("%Y%m%d")
        
        # 清理项目名称，去除特殊字符
        import re
        clean_project_name = re.sub(r'[^\w\-_]', '_', project_name)
        clean_project_name = re.sub(r'_+', '_', clean_project_name)  # 合并多个下划线
        clean_project_name = clean_project_name.strip('_')  # 去除首尾下划线
        
        target_branch = f"D_{current_date}_{clean_project_name}"
        
        self.logger.info(f"生成目标分支名称: {project_name} -> {target_branch}")
        return target_branch

    # 🎯 新增：便捷的文档处理方法
    async def execute_workflow(
        self,
        document_content: str,
        project_name: str,
        project_task_id: str,  # 🆕 添加project_task_id参数
        output_path: str = None
    ) -> Dict[str, Any]:
        """便捷方法：直接使用设计文档进行处理"""
        
        # 直接将文档内容作为设计文档
        design_doc = document_content.strip()
        
        return await self.execute_coding_workflow(
            design_doc=design_doc,
            project_name=project_name,
            project_task_id=project_task_id,  # 🆕 传递project_task_id
            output_path=output_path
        ) 