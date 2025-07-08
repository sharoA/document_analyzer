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
import time

from flask import Blueprint, request, jsonify, current_app
from werkzeug.exceptions import BadRequest


# 尝试导入LangGraph工作流编排器，如果失败则设为None
try:
    from ..corder_integration.langgraph.workflow_orchestrator import LangGraphWorkflowOrchestrator
    LANGGRAPH_AVAILABLE = True
except ImportError as e:
    logging.warning(f"LangGraph工作流编排器不可用: {e}")
    LangGraphWorkflowOrchestrator = None
    LANGGRAPH_AVAILABLE = False

# 导入统一代码生成器
try:
    from ..corder_integration.code_generator import UnifiedCodeGenerator
    CODE_GENERATOR_AVAILABLE = True
except ImportError as e:
    logging.warning(f"代码生成器不可用: {e}")
    UnifiedCodeGenerator = None
    CODE_GENERATOR_AVAILABLE = False

logger = logging.getLogger(__name__)

# 创建蓝图
coder_agent_api = Blueprint('coder_agent_api', __name__, url_prefix='/api/coder-agent')

# 全局实例
_workflow_orchestrator = None
_code_generator = None


def get_workflow_orchestrator():
    """获取LangGraph工作流编排器实例"""
    global _workflow_orchestrator
    if not LANGGRAPH_AVAILABLE:
        return None
    if _workflow_orchestrator is None:
        _workflow_orchestrator = LangGraphWorkflowOrchestrator(use_sqlite=True)
    return _workflow_orchestrator


def get_code_generator():
    """获取统一代码生成器实例"""
    global _code_generator
    if not CODE_GENERATOR_AVAILABLE:
        return None
    if _code_generator is None:
        _code_generator = UnifiedCodeGenerator()
    return _code_generator


@coder_agent_api.route('/process-document', methods=['POST'])
def process_design_document():
    """处理设计文档并生成代码 - 使用LangGraph工作流"""
    try:
        data = request.get_json()
        
        if not data or 'document_content' not in data:
            raise BadRequest("缺少document_content参数")
        
        document_content = data['document_content']
        project_name = data.get('project_name', f'project_{int(datetime.now().timestamp())}')
        use_langgraph = data.get('use_langgraph', True)  # 默认使用LangGraph
        execute_immediately = data.get('execute_immediately', True)
        output_path = data.get('output_path', r'D:\gitlab')  # 代码输出路径
        
        logger.info(f"开始处理文档: {project_name}")
        logger.info(f"文档长度: {len(document_content)} 字符")
        logger.info(f"使用LangGraph: {use_langgraph}")
        logger.info(f"代码输出路径: {output_path}")
        
        # 检查是否可以使用LangGraph
        if use_langgraph and LANGGRAPH_AVAILABLE:
            # 🚀 使用LangGraph工作流
            logger.info(f"使用LangGraph工作流处理项目: {project_name}")
            
            orchestrator = get_workflow_orchestrator()
            if orchestrator is None:
                raise Exception("LangGraph工作流编排器不可用")
            
            # 使用异步方法执行LangGraph工作流
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    orchestrator.execute_workflow(
                        document_content=document_content,
                        project_name=project_name,
                        output_path=output_path
                    )
                )
            finally:
                loop.close()
            
            return jsonify({
                "status": "success",
                "project_name": project_name,
                "execution_id": f"exec_{int(datetime.now().timestamp())}",
                "message": "文档处理完成（使用LangGraph工作流）",
                "document_length": len(document_content),
                "execute_immediately": execute_immediately,
                "output_path": output_path,
                "timestamp": datetime.now().isoformat(),
                "workflow_result": result,
                "workflow_type": "langgraph"
            })
            
        else:
            # 🔄 使用传统工作流作为降级方案
            if use_langgraph and not LANGGRAPH_AVAILABLE:
                logger.warning("请求使用LangGraph但不可用，降级到传统工作流")
            
            logger.info(f"使用传统工作流处理项目: {project_name}")
            
            # 🎯 调用代码生成服务
            generator = get_code_generator()
            if generator is None:
                raise Exception("代码生成器不可用")
            
            # 异步调用代码生成
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                generation_result = loop.run_until_complete(
                    generator.generate_project_code(
                        document_content=document_content,
                        project_name=project_name,
                        output_path=output_path,
                        use_ai=True  # 🚀 传统工作流也使用AI大模型！
                    )
                )
            finally:
                loop.close()
            
            # 简单的文档分析
            lines = document_content.strip().split('\n')
            non_empty_lines = [line for line in lines if line.strip()]
            
            # 估算任务和工时
            tasks_created = len(generation_result.get("services", []))
            estimated_hours = tasks_created * 1.6  # 每个任务平均1.6小时
            
            workflow_result = {
                "tasks_created": tasks_created,
                "estimated_hours": round(estimated_hours, 1),
                "status": "completed" if generation_result["success"] else "partially_completed",
                "document_sections": len(non_empty_lines),
                "processing_method": generation_result["generation_method"],
                "code_generated": generation_result["success"],
                "services": generation_result["services"],
                "failed_services": generation_result.get("failed_services", []),
                "output_path": generation_result["output_path"]
            }
            
            return jsonify({
                "status": "success",
                "project_name": project_name,
                "execution_id": f"exec_{int(datetime.now().timestamp())}",
                "message": f"文档处理完成（使用传统智能体）{'，代码已生成' if generation_result['success'] else ''}",
                "document_length": len(document_content),
                "execute_immediately": execute_immediately,
                "output_path": generation_result["output_path"],
                "timestamp": datetime.now().isoformat(),
                "workflow_result": workflow_result,
                "workflow_type": "traditional"
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


@coder_agent_api.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    try:
        return jsonify({
            "status": "healthy",
            "service": "coder-agent-api",
            "langgraph_available": LANGGRAPH_AVAILABLE,
            "code_generator_available": CODE_GENERATOR_AVAILABLE,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


@coder_agent_api.route('/status', methods=['GET'])
def get_agent_status():
    """获取智能体状态"""
    try:
        available_workflows = []
        if LANGGRAPH_AVAILABLE:
            available_workflows.append("langgraph")
        if CODE_GENERATOR_AVAILABLE:
            available_workflows.append("traditional")
        
        return jsonify({
            "status": "success",
            "data": {
                "service": "coder-agent-api",
                "langgraph_available": LANGGRAPH_AVAILABLE,
                "code_generator_available": CODE_GENERATOR_AVAILABLE,
                "workflow_orchestrator": _workflow_orchestrator is not None,
                "code_generator": _code_generator is not None,
                "available_workflows": available_workflows
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取智能体状态失败: {e}")
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
        "message": "Bad Request",
        "timestamp": datetime.now().isoformat()
    }), 400

@coder_agent_api.errorhandler(404)
def not_found(error):
    return jsonify({
        "status": "error", 
        "message": "Not Found",
        "timestamp": datetime.now().isoformat()
    }), 404

@coder_agent_api.errorhandler(500)
def internal_error(error):
    return jsonify({
        "status": "error",
        "message": "Internal Server Error", 
        "timestamp": datetime.now().isoformat()
    }), 500 