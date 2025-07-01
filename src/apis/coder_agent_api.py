#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编码智能体API接口
提供REST API服务用于调用编码智能体功能
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from flask import Blueprint, request, jsonify, current_app
from werkzeug.exceptions import BadRequest

from ..corder_integration.coder_agent import CoderAgent
from ..corder_integration.task_planner import TaskPlanner
from ..corder_integration.git_manager import GitManager
from ..utils.task_storage import get_task_storage

logger = logging.getLogger(__name__)

# 创建蓝图
coder_agent_api = Blueprint('coder_agent_api', __name__, url_prefix='/api/coder-agent')

# 全局智能体实例
_coder_agent = None

def get_coder_agent() -> CoderAgent:
    """获取编码智能体实例"""
    global _coder_agent
    if _coder_agent is None:
        _coder_agent = CoderAgent()
    return _coder_agent

@coder_agent_api.route('/status', methods=['GET'])
def get_agent_status():
    """获取智能体状态"""
    try:
        agent = get_coder_agent()
        
        # 获取项目路径参数
        project_path = request.args.get('project_path')
        
        status = agent.get_project_status(project_path)
        
        return jsonify({
            "status": "success",
            "data": status,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取智能体状态失败: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@coder_agent_api.route('/process-document', methods=['POST'])
def process_design_document():
    """处理设计文档并生成代码"""
    try:
        data = request.get_json()
        
        if not data or 'document_content' not in data:
            raise BadRequest("缺少document_content参数")
        
        document_content = data['document_content']
        project_name = data.get('project_name')
        execute_immediately = data.get('execute_immediately', True)
        
        agent = get_coder_agent()
        
        # 使用异步方法
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                agent.process_design_document(
                    document_content, 
                    project_name, 
                    execute_immediately
                )
            )
        finally:
            loop.close()
        
        return jsonify({
            "status": "success",
            "data": result,
            "timestamp": datetime.now().isoformat()
        })
        
    except BadRequest as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 400
        
    except Exception as e:
        logger.error(f"处理设计文档失败: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@coder_agent_api.route('/execute-plan/<plan_id>', methods=['POST'])
def execute_execution_plan(plan_id: str):
    """执行指定的执行计划"""
    try:
        agent = get_coder_agent()
        
        # 使用异步方法
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(agent.execute_plan(plan_id))
        finally:
            loop.close()
        
        return jsonify({
            "status": "success",
            "data": result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"执行计划失败: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@coder_agent_api.route('/tasks', methods=['GET'])
def get_tasks():
    """获取任务列表"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        agent = get_coder_agent()
        tasks = agent.list_recent_tasks(limit)
        
        return jsonify({
            "status": "success",
            "data": {
                "tasks": tasks,
                "total": len(tasks)
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@coder_agent_api.route('/tasks/<task_id>', methods=['GET'])
def get_task_details(task_id: str):
    """获取任务详情"""
    try:
        agent = get_coder_agent()
        task = agent.get_task_details(task_id)
        
        if not task:
            return jsonify({
                "status": "error",
                "message": "任务不存在",
                "timestamp": datetime.now().isoformat()
            }), 404
        
        return jsonify({
            "status": "success",
            "data": task,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取任务详情失败: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@coder_agent_api.route('/project-summary', methods=['GET'])
def get_project_summary():
    """获取项目摘要"""
    try:
        project_path = request.args.get('project_path')
        
        agent = get_coder_agent()
        summary = agent.generate_project_summary(project_path)
        
        return jsonify({
            "status": "success",
            "data": summary,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取项目摘要失败: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@coder_agent_api.route('/git/status', methods=['GET'])
def get_git_status():
    """获取Git仓库状态"""
    try:
        project_path = request.args.get('project_path')
        
        git_manager = GitManager()
        status = git_manager.get_repository_status(project_path)
        
        return jsonify({
            "status": "success",
            "data": status,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取Git状态失败: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@coder_agent_api.route('/git/setup', methods=['POST'])
def setup_git_environment():
    """设置Git环境"""
    try:
        data = request.get_json()
        
        if not data or 'project_name' not in data or 'branch_name' not in data:
            raise BadRequest("缺少project_name或branch_name参数")
        
        project_name = data['project_name']
        branch_name = data['branch_name']
        remote_url = data.get('remote_url')
        
        git_manager = GitManager()
        result = git_manager.setup_project_environment(
            project_name, branch_name, remote_url
        )
        
        return jsonify({
            "status": "success",
            "data": result,
            "timestamp": datetime.now().isoformat()
        })
        
    except BadRequest as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 400
        
    except Exception as e:
        logger.error(f"设置Git环境失败: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@coder_agent_api.route('/git/commit', methods=['POST'])
def commit_and_push():
    """提交并推送代码"""
    try:
        data = request.get_json()
        
        if not data or 'commit_message' not in data:
            raise BadRequest("缺少commit_message参数")
        
        commit_message = data['commit_message']
        project_path = data.get('project_path')
        push_to_remote = data.get('push_to_remote', True)
        
        git_manager = GitManager()
        result = git_manager.commit_and_push_code(
            commit_message, project_path, push_to_remote
        )
        
        return jsonify({
            "status": "success",
            "data": result,
            "timestamp": datetime.now().isoformat()
        })
        
    except BadRequest as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 400
        
    except Exception as e:
        logger.error(f"提交代码失败: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@coder_agent_api.route('/parse-document', methods=['POST'])
def parse_design_document():
    """解析设计文档（仅规划，不执行）"""
    try:
        data = request.get_json()
        
        if not data or 'document_content' not in data:
            raise BadRequest("缺少document_content参数")
        
        document_content = data['document_content']
        project_name = data.get('project_name')
        
        task_planner = TaskPlanner()
        execution_plan = task_planner.create_execution_plan(
            document_content, project_name
        )
        
        # 保存执行计划
        tasks_dir = task_planner.save_execution_plan(execution_plan)
        
        return jsonify({
            "status": "success",
            "data": {
                "execution_plan": execution_plan.to_dict(),
                "tasks_directory": tasks_dir
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except BadRequest as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 400
        
    except Exception as e:
        logger.error(f"解析设计文档失败: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@coder_agent_api.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    try:
        # 检查各个组件状态
        health_status = {
            "coder_agent": "healthy",
            "task_storage": "healthy",
            "git_manager": "healthy",
            "openai_client": "healthy"
        }
        
        # 尝试初始化各个组件
        try:
            get_coder_agent()
        except Exception as e:
            health_status["coder_agent"] = f"error: {str(e)}"
        
        try:
            get_task_storage()
        except Exception as e:
            health_status["task_storage"] = f"error: {str(e)}"
        
        overall_status = "healthy" if all(
            status == "healthy" for status in health_status.values()
        ) else "degraded"
        
        return jsonify({
            "status": "success",
            "data": {
                "overall_status": overall_status,
                "components": health_status
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

# 错误处理器
@coder_agent_api.errorhandler(400)
def bad_request(error):
    return jsonify({
        "status": "error",
        "message": "请求参数错误",
        "details": str(error),
        "timestamp": datetime.now().isoformat()
    }), 400

@coder_agent_api.errorhandler(404)
def not_found(error):
    return jsonify({
        "status": "error",
        "message": "资源不存在",
        "timestamp": datetime.now().isoformat()
    }), 404

@coder_agent_api.errorhandler(500)
def internal_error(error):
    return jsonify({
        "status": "error",
        "message": "内部服务器错误",
        "timestamp": datetime.now().isoformat()
    }), 500 