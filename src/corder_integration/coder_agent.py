#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编码智能体核心控制器
协调各个子模块的工作，管理整个开发流程
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

from .config import get_coder_config, get_config_manager
from .task_planner import TaskPlanner, ExecutionPlan
from .workflow_engine import WorkflowEngine, WorkflowState
from .git_manager import GitManager
from ..utils.task_storage import get_task_storage

logger = logging.getLogger(__name__)

class CoderAgent:
    """编码智能体核心控制器"""
    
    def __init__(self):
        self.config = get_coder_config()
        self.config_manager = get_config_manager()
        self.task_planner = TaskPlanner()
        self.workflow_engine = WorkflowEngine()
        self.git_manager = GitManager()
        self.task_storage = get_task_storage()
        
        # 设置工作流回调
        self.workflow_engine.set_callbacks(
            on_state_change=self._on_workflow_state_change,
            on_task_complete=self._on_task_complete,
            on_error=self._on_workflow_error
        )
    
    async def process_design_document(
        self, 
        document_content: str, 
        project_name: Optional[str] = None,
        execute_immediately: bool = True
    ) -> Dict[str, Any]:
        """
        处理设计文档并生成代码
        
        Args:
            document_content: markdown设计文档内容
            project_name: 项目名称（可选）
            execute_immediately: 是否立即执行（默认True）
            
        Returns:
            处理结果
        """
        logger.info("开始处理设计文档")
        
        try:
            # 创建任务记录
            task_id = self.task_storage.create_task(
                filename=f"{project_name or 'UnknownProject'}.md",
                file_size=len(document_content.encode('utf-8')),
                file_type="design_document"
            )
            
            # 更新任务状态
            self.task_storage.update_task_status(
                task_id, "processing", 0, None
            )
            
            result = {
                "task_id": task_id,
                "project_name": project_name,
                "status": "success",
                "execution_plan": None,
                "workflow_result": None,
                "created_at": datetime.now().isoformat()
            }
            
            if execute_immediately:
                # 执行完整工作流
                workflow_result = await self.workflow_engine.execute_workflow(
                    document_content, project_name
                )
                result["workflow_result"] = workflow_result
                
                # 更新任务状态
                if workflow_result.get("status") == "completed":
                    self.task_storage.update_task_status(
                        task_id, "completed", 100, None
                    )
                else:
                    self.task_storage.update_task_status(
                        task_id, "failed", 50, workflow_result.get("error")
                    )
            else:
                # 仅创建执行计划
                execution_plan = self.task_planner.create_execution_plan(
                    document_content, project_name
                )
                result["execution_plan"] = execution_plan.to_dict()
                
                # 保存执行计划
                self.task_planner.save_execution_plan(execution_plan)
                
                # 更新任务状态
                self.task_storage.update_task_status(
                    task_id, "planned", 10, None
                )
            
            logger.info(f"设计文档处理完成，任务ID: {task_id}")
            return result
            
        except Exception as e:
            logger.error(f"处理设计文档失败: {e}")
            
            # 更新任务状态为失败
            if 'task_id' in locals():
                self.task_storage.update_task_status(
                    task_id, "failed", 0, str(e)
                )
            
            return {
                "status": "failed",
                "error": str(e),
                "created_at": datetime.now().isoformat()
            }
    
    async def execute_plan(self, plan_id: str) -> Dict[str, Any]:
        """
        执行已保存的执行计划
        
        Args:
            plan_id: 执行计划ID
            
        Returns:
            执行结果
        """
        logger.info(f"执行计划: {plan_id}")
        
        try:
            # 加载执行计划
            execution_plan = self.task_planner.load_execution_plan(plan_id)
            if not execution_plan:
                raise Exception(f"执行计划不存在: {plan_id}")
            
            # 设置工作流上下文
            self.workflow_engine.context.execution_plan = execution_plan
            
            # 执行工作流（从环境准备开始）
            workflow_result = await self.workflow_engine.execute_workflow(
                "", execution_plan.project_name
            )
            
            return {
                "status": "success",
                "plan_id": plan_id,
                "workflow_result": workflow_result,
                "executed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"执行计划失败: {e}")
            return {
                "status": "failed",
                "plan_id": plan_id,
                "error": str(e),
                "executed_at": datetime.now().isoformat()
            }
    
    def get_project_status(self, project_path: Optional[str] = None) -> Dict[str, Any]:
        """
        获取项目状态信息
        
        Args:
            project_path: 项目路径（可选）
            
        Returns:
            项目状态信息
        """
        try:
            # 获取Git仓库状态
            git_status = self.git_manager.get_repository_status(project_path)
            
            # 获取工作流状态
            workflow_status = self.workflow_engine.get_workflow_status()
            
            # 分析项目结构
            structure_analysis = self.git_manager.analyze_existing_structure(project_path)
            
            return {
                "git_status": git_status,
                "workflow_status": workflow_status,
                "structure_analysis": structure_analysis,
                "config": {
                    "project_root": self.config.project_root,
                    "backend_framework": self.config.backend_framework,
                    "frontend_framework": self.config.frontend_framework
                },
                "updated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取项目状态失败: {e}")
            return {
                "error": str(e),
                "updated_at": datetime.now().isoformat()
            }
    
    def list_recent_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取最近的任务列表
        
        Args:
            limit: 返回的任务数量限制
            
        Returns:
            任务列表
        """
        try:
            tasks = self.task_storage.get_all_tasks(limit)
            return tasks
        except Exception as e:
            logger.error(f"获取任务列表失败: {e}")
            return []
    
    def get_task_details(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务详情
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务详情或None
        """
        try:
            return self.task_storage.get_task(task_id)
        except Exception as e:
            logger.error(f"获取任务详情失败: {e}")
            return None
    
    async def _on_workflow_state_change(
        self, 
        old_state: WorkflowState, 
        new_state: WorkflowState, 
        context
    ):
        """工作流状态变更回调"""
        logger.info(f"工作流状态变更: {old_state.value} -> {new_state.value}")
        
        # 这里可以添加状态变更的处理逻辑
        # 比如更新数据库、发送通知等
    
    async def _on_task_complete(self, task, result):
        """任务完成回调"""
        logger.info(f"任务完成: {task}")
        
        # 这里可以添加任务完成的处理逻辑
    
    async def _on_workflow_error(self, error, context):
        """工作流错误回调"""
        logger.error(f"工作流错误: {error}")
        
        # 这里可以添加错误处理逻辑
        # 比如发送警报、保存错误日志等
    
    def generate_project_summary(self, project_path: Optional[str] = None) -> Dict[str, Any]:
        """
        生成项目摘要报告
        
        Args:
            project_path: 项目路径
            
        Returns:
            项目摘要
        """
        try:
            status = self.get_project_status(project_path)
            
            summary = {
                "project_overview": {
                    "path": project_path or self.config.project_root,
                    "git_initialized": status.get("git_status", {}).get("is_git_repo", False),
                    "current_branch": status.get("git_status", {}).get("current_branch", ""),
                    "has_backend": status.get("structure_analysis", {}).get("has_backend", False),
                    "has_frontend": status.get("structure_analysis", {}).get("has_frontend", False)
                },
                "development_progress": {
                    "workflow_state": status.get("workflow_status", {}).get("current_state", ""),
                    "completed_phases": len(status.get("workflow_status", {}).get("completed_phases", [])),
                    "total_errors": status.get("workflow_status", {}).get("total_errors", 0)
                },
                "files_overview": {
                    "total_files": len(status.get("structure_analysis", {}).get("existing_files", [])),
                    "backend_structure": status.get("structure_analysis", {}).get("backend_structure", {}),
                    "frontend_structure": status.get("structure_analysis", {}).get("frontend_structure", {})
                },
                "generated_at": datetime.now().isoformat()
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"生成项目摘要失败: {e}")
            return {
                "error": str(e),
                "generated_at": datetime.now().isoformat()
            } 