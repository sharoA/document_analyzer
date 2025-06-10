#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
analyDesign 增强API服务器
支持新的三阶段分析架构：文档解析、内容分析、AI智能分析
"""

import json
import uuid
import logging
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional

from flask import Flask, request, jsonify, make_response
from flask_cors import CORS

# 导入核心模块
try:
    from ..resource.config import get_config
    from ..utils.volcengine_client import VolcengineClient, VolcengineConfig
    from ..analysis_services.sync_service_manager import initialize_service_manager, get_service_manager
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from src.resource.config import get_config
    from src.utils.volcengine_client import VolcengineClient, VolcengineConfig
    from src.analysis_services.sync_service_manager import initialize_service_manager, get_service_manager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 获取配置
config = get_config()

# 创建Flask应用
app = Flask(__name__)

# 配置CORS
CORS(app, 
     origins=["http://localhost:3000", "http://127.0.0.1:3000"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"],
     supports_credentials=True)

# 初始化火山引擎客户端
volcano_client = None
try:
    volcengine_config = config.get_volcengine_config()
    volcano_config = VolcengineConfig(
        api_key=volcengine_config.get('api_key', ''),
        model_id=volcengine_config.get('model', 'doubao-pro-4k'),
        base_url=volcengine_config.get('endpoint', 'https://ark.cn-beijing.volces.com/api/v3'),
        temperature=volcengine_config.get('temperature', 0.7),
        max_tokens=volcengine_config.get('max_tokens', 4000)
    )
    volcano_client = VolcengineClient(volcano_config)
    logger.info("火山引擎客户端初始化成功")
except Exception as e:
    logger.error(f"火山引擎客户端初始化失败: {e}")

# 初始化服务管理器
service_manager = None
try:
    redis_config = {
        'host': 'localhost',
        'port': 6379,
        'db': 0
    }
    
    service_manager = initialize_service_manager(
        llm_client=volcano_client,
        vector_db_type="mock",
        redis_config=redis_config
    )
    logger.info("服务管理器初始化成功")
except Exception as e:
    logger.error(f"服务管理器初始化失败: {e}")

@app.route('/api/v2/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    try:
        status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "api_server": "running",
                "service_manager": "connected" if service_manager else "disconnected",
                "llm_client": "connected" if volcano_client else "disconnected"
            }
        }
        
        if service_manager:
            service_status = service_manager.get_service_status()
            status["services"]["analysis_services"] = service_status
        
        return jsonify(status), 200
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

# 会话存储
sessions = {}

@app.route('/api/chat', methods=['POST'])
def chat():
    """聊天接口"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "请求数据为空"
            }), 400
        
        message = data.get('message', '').strip()
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        if not message:
            return jsonify({
                "success": False,
                "error": "消息内容不能为空"
            }), 400
        
        logger.info(f"收到聊天请求 - Session: {session_id}, Message: {message}")
        
        # 更新会话信息
        if session_id not in sessions:
            sessions[session_id] = {
                "created_at": datetime.now().isoformat(),
                "messages": []
            }
        
        sessions[session_id]["messages"].append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # 检查火山引擎客户端是否可用
        if not volcano_client:
            return jsonify({
                "success": False,
                "error": "火山引擎客户端未初始化，请检查配置",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }), 500
        
        # 构建消息列表
        messages = [
            {
                "role": "system",
                "content": "你是analyDesign智能需求分析助手，专门帮助用户进行需求分析、访谈提纲生成和问卷设计。请用专业、友好的语气回答用户问题。"
            },
            {
                "role": "user",
                "content": message
            }
        ]
        
        # 调用火山引擎API
        try:
            ai_response = volcano_client.chat(messages=messages)
            
            # 保存AI回复到会话
            sessions[session_id]["messages"].append({
                "role": "assistant",
                "content": ai_response,
                "timestamp": datetime.now().isoformat()
            })
            
            response_data = {
                "success": True,
                "response": ai_response,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "confidence": 0.9,  # 可以根据实际情况调整
                "intent": "需求分析",  # 可以通过NLP分析得出
                "model": volcano_client.config.model_id if hasattr(volcano_client, 'config') else "unknown"
            }
            
            logger.info(f"成功处理聊天请求 - Session: {session_id}")
            return jsonify(response_data)
            
        except Exception as volcano_error:
            logger.error(f"火山引擎调用失败: {volcano_error}")
            return jsonify({
                "success": False,
                "error": f"火山引擎调用失败: {str(volcano_error)}",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        logger.error(f"处理聊天请求时出错: {e}")
        return jsonify({
            "success": False,
            "error": f"服务器内部错误: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """获取所有会话列表"""
    try:
        session_list = []
        for session_id, session_data in sessions.items():
            session_list.append({
                "session_id": session_id,
                "created_at": session_data.get("created_at"),
                "message_count": len(session_data.get("messages", [])),
                "last_activity": session_data.get("messages", [])[-1].get("timestamp") if session_data.get("messages") else None
            })
        
        # 按最后活动时间排序
        session_list.sort(key=lambda x: x.get("last_activity", ""), reverse=True)
        
        return jsonify({
            "success": True,
            "sessions": session_list,
            "total": len(session_list)
        })
        
    except Exception as e:
        logger.error(f"获取会话列表失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/sessions/<session_id>', methods=['GET'])
def get_session(session_id: str):
    """获取特定会话详情"""
    try:
        if session_id not in sessions:
            return jsonify({
                "success": False,
                "error": "会话不存在"
            }), 404
        
        return jsonify({
            "success": True,
            "session": sessions[session_id]
        })
        
    except Exception as e:
        logger.error(f"获取会话详情失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id: str):
    """删除特定会话"""
    try:
        if session_id not in sessions:
            return jsonify({
                "success": False,
                "error": "会话不存在"
            }), 404
        
        del sessions[session_id]
        
        return jsonify({
            "success": True,
            "message": f"会话 {session_id} 已删除"
        })
        
    except Exception as e:
        logger.error(f"删除会话失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/file/upload', methods=['POST'])
def upload_file():
    """文件上传接口 - 支持JSON和multipart/form-data两种格式，兼容原有接口"""
    try:
        # 检查请求类型
        if request.content_type and 'application/json' in request.content_type:
            # JSON格式上传（前端使用）
            data = request.get_json()
            if not data or 'file_info' not in data:
                return jsonify({
                    "success": False,
                    "error": "请求数据格式错误，缺少file_info"
                }), 400
            
            file_info = data['file_info']
            
            # 验证必要字段
            if not all(key in file_info for key in ['name', 'content']):
                return jsonify({
                    "success": False,
                    "error": "文件信息不完整，缺少name或content字段"
                }), 400
            
            # 解码base64文件内容
            try:
                import base64
                file_content = base64.b64decode(file_info['content'])
            except Exception as e:
                return jsonify({
                    "success": False,
                    "error": f"文件内容解码失败: {str(e)}"
                }), 400
            
            # 更新文件信息
            file_name = file_info['name']
            file_size = len(file_content)
            
        else:
            # multipart/form-data格式上传（传统方式）
            if 'file' not in request.files:
                return jsonify({
                    "success": False,
                    "error": "没有上传文件"
                }), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({
                    "success": False,
                    "error": "文件名为空"
                }), 400
            
            # 读取文件内容
            try:
                file_content = file.read()
                file_name = file.filename
                file_size = len(file_content)
            except Exception as e:
                return jsonify({
                    "success": False,
                    "error": f"读取文件失败: {str(e)}"
                }), 400
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 保存文件到临时目录
        try:
            import os
            uploads_dir = "uploads/temp"
            os.makedirs(uploads_dir, exist_ok=True)
            file_path = os.path.join(uploads_dir, f"{task_id}_{file_name}")
            
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            logger.info(f"文件保存成功: {file_path}")
        except Exception as e:
            logger.error(f"文件保存失败: {e}")
            return jsonify({
                "success": False,
                "error": f"文件保存失败: {str(e)}"
            }), 500
        
        # 保存文件信息到Redis，供WebSocket服务器使用
        try:
            if service_manager and service_manager.redis_client:
                file_info = {
                    'task_id': task_id,
                    'file_path': file_path,
                    'file_name': file_name,
                    'file_size': file_size,
                    'upload_time': datetime.now().isoformat()
                }
                
                # 如果是文本文件，也保存解码后的内容
                file_ext = file_name.lower().split('.')[-1] if '.' in file_name else ''
                text_extensions = ['txt', 'md', 'csv', 'log', 'json', 'xml', 'html']
                
                if file_ext in text_extensions:
                    try:
                        file_info['file_content'] = file_content.decode('utf-8') if isinstance(file_content, bytes) else str(file_content)
                    except UnicodeDecodeError:
                        file_info['file_content'] = ""
                else:
                    file_info['file_content'] = ""
                
                import json
                file_info_key = f"file_upload:{task_id}"
                service_manager.redis_client.setex(file_info_key, 3600, json.dumps(file_info, ensure_ascii=False))
                logger.info(f"文件信息已保存到Redis - Task: {task_id}")
        except Exception as e:
            logger.warning(f"保存文件信息到Redis失败: {e}")  # 不影响主流程
        
        # 启动分析流程 (使用service_manager)
        if service_manager:
            try:
                # 判断文件类型并准备相应的内容
                file_ext = file_name.lower().split('.')[-1] if '.' in file_name else ''
                
                # 文本文件类型尝试解码为文本
                text_extensions = ['txt', 'md', 'csv', 'log', 'json', 'xml', 'html']
                
                if file_ext in text_extensions:
                    try:
                        file_text = file_content.decode('utf-8') if isinstance(file_content, bytes) else str(file_content)
                        logger.info(f"文本文件解码成功: {file_name}")
                    except UnicodeDecodeError:
                        # 即使是文本文件，如果解码失败，也使用文件路径
                        file_text = ""
                        logger.info(f"文本文件解码失败，使用文件路径处理: {file_name}")
                else:
                    # 对于Word、PDF等二进制文件，不尝试解码，直接使用文件路径
                    file_text = ""
                    logger.info(f"二进制文件 {file_name}，使用文档解析服务处理")
                
                # 启动完整的分析流水线（而不是只启动单个阶段）
                result = service_manager.full_analysis_pipeline(
                    task_id=task_id,
                    file_path=file_path,
                    file_content=file_text,  # 文本内容或空字符串
                    file_name=file_name
                )
                
                if result.get("success"):
                    logger.info(f"完整分析流水线已启动 - 任务ID: {task_id}")
                else:
                    logger.error(f"启动分析流水线失败: {result.get('error')}")
                
            except Exception as e:
                logger.error(f"启动分析流程失败: {e}")
        
        logger.info(f"文件上传成功 - 任务ID: {task_id}, 文件名: {file_name}, 大小: {file_size} bytes")
        
        # 返回上传成功信息
        return jsonify({
            "success": True,
            "task_id": task_id,
            "file_name": file_name,
            "file_size": file_size,
            "file_path": file_path,
            "status": "uploaded",
            "message": "文件上传成功，开始解析",
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        return jsonify({
            "success": False,
            "error": f"上传失败: {str(e)}"
        }), 500

@app.route('/api/file/parsing/<task_id>', methods=['GET'])
def get_parsing_status(task_id: str):
    """获取文件解析状态 - 兼容原有接口"""
    try:
        if not service_manager:
            return jsonify({
                "success": False,
                "error": "服务管理器未初始化"
            }), 500
        
        # 检查进度信息
        result = service_manager.get_analysis_progress(task_id)
        
        if not result.get("success"):
            # 如果Redis中没有进度信息，返回初始状态
            return jsonify({
                "success": True,
                "task_id": task_id,
                "data": {
                    "progress": {
                        "document_parsing": 0,
                        "content_analysis": 0,
                        "ai_analysis": 0
                    },
                    "current_stage": "document_parsing",
                    "timestamp": datetime.now().isoformat()
                }
            }), 200
        
        # 直接返回后端格式，前端期望的格式
        data = result.get("data", {})
        
        return jsonify({
            "success": True,
            "task_id": task_id,
            "data": data
        }), 200
        
    except Exception as e:
        logger.error(f"获取解析状态失败: {e}")
        return jsonify({
            "success": False,
            "error": f"获取状态失败: {str(e)}",
            "task_id": task_id
        }), 500

@app.route('/api/file/analyze/<task_id>', methods=['POST'])
def start_content_analysis(task_id: str):
    """开始内容分析 - 兼容原有接口"""
    try:
        if not service_manager:
            return jsonify({
                "success": False,
                "error": "服务管理器未初始化"
            }), 500
        
        logger.info(f"开始内容分析 - 任务ID: {task_id}")
        
        # 执行内容分析阶段
        result = service_manager.execute_single_stage(
            task_id=task_id,
            stage="content_analysis",
            input_data={"task_id": task_id}
        )
        
        return jsonify(result), 200 if result.get("success") else 500
        
    except Exception as e:
        logger.error(f"开始内容分析失败: {e}")
        return jsonify({
            "success": False,
            "error": f"内容分析启动失败: {str(e)}",
            "task_id": task_id
        }), 500

@app.route('/api/file/ai-analyze/<task_id>', methods=['POST'])
def start_ai_analysis(task_id: str):
    """开始AI分析 - 兼容原有接口"""
    try:
        if not service_manager:
            return jsonify({
                "success": False,
                "error": "服务管理器未初始化"
            }), 500
        
        logger.info(f"开始AI分析 - 任务ID: {task_id}")
        
        # 获取分析类型参数
        data = request.get_json() or {}
        analysis_type = data.get("analysis_type", "comprehensive")
        
        # 执行AI分析阶段
        result = service_manager.execute_single_stage(
            task_id=task_id,
            stage="ai_analysis",
            input_data={
                "task_id": task_id,
                "analysis_type": analysis_type
            }
        )
        
        return jsonify(result), 200 if result.get("success") else 500
        
    except Exception as e:
        logger.error(f"开始AI分析失败: {e}")
        return jsonify({
            "success": False,
            "error": f"AI分析启动失败: {str(e)}",
            "task_id": task_id
        }), 500

@app.route('/api/file/result/<task_id>', methods=['GET'])
def get_file_analysis_result(task_id: str):
    """获取文件分析结果 - 兼容原有接口"""
    try:
        if not service_manager:
            return jsonify({
                "success": False,
                "error": "服务管理器未初始化"
            }), 500
        
        logger.info(f"获取文件分析结果 - 任务ID: {task_id}")
        
        # 获取分析结果
        result = service_manager.get_analysis_result(task_id, include_stages=True)
        
        if not result.get("success"):
            return jsonify(result), 404
        
        # 转换格式以兼容前端
        data = result.get("data", {})
        
        return jsonify({
            "success": True,
            "task_id": task_id,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"获取文件分析结果失败: {e}")
        return jsonify({
            "success": False,
            "error": f"获取结果失败: {str(e)}",
            "task_id": task_id
        }), 500

@app.route('/api/v2/analysis/start', methods=['POST'])
def start_analysis():
    """开始分析接口 - 支持完整流水线或单阶段分析"""
    try:
        if not service_manager:
            return jsonify({
                "success": False,
                "error": "服务管理器未初始化"
            }), 500
        
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "请求数据不能为空"
            }), 400
        
        # 提取必要参数
        execution_mode = data.get('execution_mode', 'automatic')  # automatic | manual
        task_id = data.get('task_id', str(uuid.uuid4()))
        file_path = data.get('file_path', '')
        file_content = data.get('file_content', '')
        file_name = data.get('file_name', '')
        
        # 验证输入
        if not file_content and not file_path:
            return jsonify({
                "success": False,
                "error": "必须提供文件内容或文件路径"
            }), 400
        
        if not file_name:
            return jsonify({
                "success": False,
                "error": "必须提供文件名"
            }), 400
        
        # 读取文件内容（如果提供的是文件路径）
        if file_path and not file_content:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
            except Exception as e:
                return jsonify({
                    "success": False,
                    "error": f"读取文件失败: {str(e)}"
                }), 400
        
        logger.info(f"开始分析 - 任务ID: {task_id}, 模式: {execution_mode}")
        
        if execution_mode == 'automatic':
            # 自动模式：执行完整流水线
            result = service_manager.full_analysis_pipeline(
                task_id=task_id,
                file_path=file_path,
                file_content=file_content,
                file_name=file_name
            )
            
            return jsonify(result), 200 if result.get("success") else 500
            
        else:
            # 手动模式：仅准备任务，等待手动触发
            return jsonify({
                "success": True,
                "task_id": task_id,
                "execution_mode": "manual",
                "message": "任务已创建，等待手动执行各阶段",
                "available_stages": ["document_parsing", "content_analysis", "ai_analysis"],
                "input_data": {
                    "file_path": file_path,
                    "file_name": file_name,
                    "content_length": len(file_content)
                }
            }), 200
            
    except Exception as e:
        logger.error(f"开始分析失败: {e}")
        return jsonify({
            "success": False,
            "error": f"开始分析失败: {str(e)}"
        }), 500

@app.route('/api/v2/analysis/stage', methods=['POST'])
def execute_stage():
    """执行单个分析阶段"""
    try:
        if not service_manager:
            return jsonify({
                "success": False,
                "error": "服务管理器未初始化"
            }), 500
        
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "请求数据不能为空"
            }), 400
        
        task_id = data.get('task_id')
        stage = data.get('stage')
        input_data = data.get('input_data', {})
        
        if not task_id or not stage:
            return jsonify({
                "success": False,
                "error": "必须提供task_id和stage参数"
            }), 400
        
        # 验证阶段名称
        valid_stages = ["document_parsing", "content_analysis", "ai_analysis"]
        if stage not in valid_stages:
            return jsonify({
                "success": False,
                "error": f"无效的阶段名称，支持的阶段: {valid_stages}"
            }), 400
        
        logger.info(f"执行单阶段分析 - 任务ID: {task_id}, 阶段: {stage}")
        
        # 执行指定阶段
        result = service_manager.execute_single_stage(
            task_id=task_id,
            stage=stage,
            input_data=input_data
        )
        
        return jsonify(result), 200 if result.get("success") else 500
        
    except Exception as e:
        logger.error(f"执行阶段分析失败: {e}")
        return jsonify({
            "success": False,
            "error": f"执行阶段失败: {str(e)}"
        }), 500

@app.route('/api/v2/analysis/progress/<task_id>', methods=['GET'])
def get_progress(task_id: str):
    """获取分析进度 - 查询所有阶段的进度"""
    try:
        if not service_manager:
            return jsonify({
                "success": False,
                "error": "服务管理器未初始化"
            }), 500
        
        logger.info(f"获取分析进度 - 任务ID: {task_id}")
        
        # 从service_manager获取进度
        result = service_manager.get_analysis_progress(task_id)
        
        return jsonify(result), 200 if result.get("success") else 404
        
    except Exception as e:
        logger.error(f"获取分析进度失败: {e}")
        return jsonify({
            "success": False,
            "error": f"获取进度失败: {str(e)}",
            "task_id": task_id
        }), 500

@app.route('/api/v2/analysis/progress/<task_id>/stage/<stage>', methods=['GET'])
def get_stage_progress(task_id: str, stage: str):
    """获取特定阶段的进度"""
    try:
        if not service_manager:
            return jsonify({
                "success": False,
                "error": "服务管理器未初始化"
            }), 500
        
        # 验证阶段名称
        valid_stages = ["document_parsing", "content_analysis", "ai_analysis"]
        if stage not in valid_stages:
            return jsonify({
                "success": False,
                "error": f"无效的阶段名称，支持的阶段: {valid_stages}"
            }), 400
        
        logger.info(f"获取阶段进度 - 任务ID: {task_id}, 阶段: {stage}")
        
        # 获取完整进度信息
        result = service_manager.get_analysis_progress(task_id)
        
        if not result.get("success"):
            return jsonify(result), 404
        
        # 提取特定阶段的进度
        data = result.get("data", {})
        progress = data.get("progress", {})
        
        if stage not in progress:
            return jsonify({
                "success": False,
                "error": f"阶段 {stage} 的进度信息不存在",
                "task_id": task_id,
                "stage": stage
            }), 404
        
        stage_progress = {
            "success": True,
            "task_id": task_id,
            "stage": stage,
            "progress": progress[stage],
            "current_stage": data.get("current_stage"),
            "timestamp": data.get("timestamp")
        }
        
        return jsonify(stage_progress), 200
        
    except Exception as e:
        logger.error(f"获取阶段进度失败: {e}")
        return jsonify({
            "success": False,
            "error": f"获取阶段进度失败: {str(e)}",
            "task_id": task_id,
            "stage": stage
        }), 500

@app.route('/api/v2/analysis/result/<task_id>', methods=['GET'])
def get_analysis_result(task_id: str):
    """获取分析结果接口 - 支持完整结果和摘要"""
    try:
        if not service_manager:
            return jsonify({
                "success": False,
                "error": "服务管理器未初始化"
            }), 500
        
        # 获取查询参数
        include_stages = request.args.get('include_stages', 'true').lower() == 'true'
        format_type = request.args.get('format', 'detailed')  # detailed | summary
        
        logger.info(f"获取分析结果 - 任务ID: {task_id}, 包含阶段: {include_stages}, 格式: {format_type}")
        
        # 从Redis获取结果
        result = service_manager.get_analysis_result(task_id, include_stages)
        
        if not result.get("success"):
            return jsonify(result), 404
        
        # 根据format_type调整返回格式
        if format_type == 'summary':
            # 只返回摘要信息
            data = result.get("data", {})
            summary_result = {
                "success": True,
                "task_id": task_id,
                "timestamp": data.get("timestamp"),
                "status": data.get("status"),
                "summary": data.get("summary", {}),
                "quick_access": data.get("quick_access", {})
            }
            return jsonify(summary_result), 200
        
        # 返回完整结果
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"获取分析结果失败: {e}")
        return jsonify({
            "success": False,
            "error": f"获取结果失败: {str(e)}",
            "task_id": task_id
        }), 500

@app.route('/api/v2/analysis/result/<task_id>/stage/<stage>', methods=['GET'])
def get_stage_result(task_id: str, stage: str):
    """获取特定阶段的分析结果"""
    try:
        if not service_manager:
            return jsonify({
                "success": False,
                "error": "服务管理器未初始化"
            }), 500
        
        # 验证阶段名称
        valid_stages = ["document_parsing", "content_analysis", "ai_analysis"]
        if stage not in valid_stages:
            return jsonify({
                "success": False,
                "error": f"无效的阶段名称，支持的阶段: {valid_stages}"
            }), 400
        
        logger.info(f"获取阶段结果 - 任务ID: {task_id}, 阶段: {stage}")
        
        # 获取完整结果
        result = service_manager.get_analysis_result(task_id, include_stages=True)
        
        if not result.get("success"):
            return jsonify(result), 404
        
        # 提取特定阶段的结果
        data = result.get("data", {})
        stages = data.get("stages", {})
        
        if stage not in stages:
            return jsonify({
                "success": False,
                "error": f"阶段 {stage} 的结果不存在",
                "task_id": task_id,
                "stage": stage
            }), 404
        
        stage_result = {
            "success": True,
            "task_id": task_id,
            "stage": stage,
            "data": stages[stage],
            "timestamp": data.get("timestamp")
        }
        
        return jsonify(stage_result), 200
        
    except Exception as e:
        logger.error(f"获取阶段结果失败: {e}")
        return jsonify({
            "success": False,
            "error": f"获取阶段结果失败: {str(e)}",
            "task_id": task_id,
            "stage": stage
        }), 500

@app.route('/api/v2/analysis/tasks', methods=['GET'])
def list_analysis_tasks():
    """列出所有分析任务"""
    try:
        if not service_manager:
            return jsonify({
                "success": False,
                "error": "服务管理器未初始化"
            }), 500
        
        # 获取查询参数
        limit = int(request.args.get('limit', 50))
        
        logger.info(f"列出分析任务 - 限制数量: {limit}")
        
        # 从service_manager获取任务列表
        result = service_manager.list_analysis_tasks(limit)
        
        return jsonify(result), 200 if result.get("success") else 500
        
    except Exception as e:
        logger.error(f"列出分析任务失败: {e}")
        return jsonify({
            "success": False,
            "error": f"列出任务失败: {str(e)}"
        }), 500

@app.route('/api/v2/analysis/result/<task_id>', methods=['DELETE'])
def delete_analysis_result(task_id: str):
    """删除分析结果"""
    try:
        if not service_manager:
            return jsonify({
                "success": False,
                "error": "服务管理器未初始化"
            }), 500
        
        logger.info(f"删除分析结果 - 任务ID: {task_id}")
        
        # 删除分析结果
        result = service_manager.delete_analysis_result(task_id)
        
        return jsonify(result), 200 if result.get("success") else 500
        
    except Exception as e:
        logger.error(f"删除分析结果失败: {e}")
        return jsonify({
            "success": False,
            "error": f"删除失败: {str(e)}",
            "task_id": task_id
        }), 500

@app.route('/api/v2/analysis/export/<task_id>', methods=['GET'])
def export_analysis_result(task_id: str):
    """导出分析结果"""
    try:
        if not service_manager:
            return jsonify({
                "success": False,
                "error": "服务管理器未初始化"
            }), 500
        
        # 获取导出格式
        export_format = request.args.get('format', 'json')  # json | markdown | pdf
        
        logger.info(f"导出分析结果 - 任务ID: {task_id}, 格式: {export_format}")
        
        # 获取分析结果
        result = service_manager.get_analysis_result(task_id, include_stages=True)
        
        if not result.get("success"):
            return jsonify(result), 404
        
        data = result.get("data", {})
        
        if export_format == 'json':
            # JSON格式导出
            response = make_response(json.dumps(data, ensure_ascii=False, indent=2))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            response.headers['Content-Disposition'] = f'attachment; filename=analysis_{task_id}.json'
            return response
            
        elif export_format == 'markdown':
            # Markdown格式导出
            markdown_content = _generate_markdown_report(data)
            response = make_response(markdown_content)
            response.headers['Content-Type'] = 'text/markdown; charset=utf-8'
            response.headers['Content-Disposition'] = f'attachment; filename=analysis_{task_id}.md'
            return response
            
        else:
            return jsonify({
                "success": False,
                "error": f"不支持的导出格式: {export_format}",
                "supported_formats": ["json", "markdown"]
            }), 400
            
    except Exception as e:
        logger.error(f"导出分析结果失败: {e}")
        return jsonify({
            "success": False,
            "error": f"导出失败: {str(e)}",
            "task_id": task_id
        }), 500

@app.route('/api/v2/analysis/stages', methods=['GET'])
def get_analysis_stages():
    """获取分析阶段信息"""
    try:
        stages_info = [
            {
                "stage": "document_parsing",
                "name": "文档解析",
                "description": "文件格式识别、结构解析、内容提取、质量分析、版本信息提取",
                "outputs": ["file_info", "structure", "content_elements", "quality_info", "version_info", "metadata"]
            },
            {
                "stage": "content_analysis",
                "name": "内容分析",
                "description": "功能变更识别：新增功能、修改功能、删除功能、关键变更提取",
                "outputs": ["new_features", "modified_features", "deleted_features", "key_changes", "analysis_summary"]
            },
            {
                "stage": "ai_analysis",
                "name": "AI智能分析",
                "description": "需求提取、技术设计、实现建议、综合总结",
                "outputs": ["requirements", "technical_design", "implementation_suggestions", "analysis_summary"]
            }
        ]
        
        return jsonify({
            "success": True,
            "stages": stages_info,
            "total_stages": len(stages_info)
        }), 200
        
    except Exception as e:
        logger.error(f"获取分析阶段信息失败: {e}")
        return jsonify({
            "success": False,
            "error": f"获取阶段信息失败: {str(e)}"
        }), 500

def _generate_markdown_report(data: Dict[str, Any]) -> str:
    """生成Markdown格式的分析报告"""
    try:
        summary = data.get("summary", {})
        stages = data.get("stages", {})
        quick_access = data.get("quick_access", {})
        
        markdown = f"""# 文档分析报告

## 基本信息
- **任务ID**: {data.get("task_id", "N/A")}
- **分析时间**: {data.get("timestamp", "N/A")}
- **分析状态**: {data.get("status", "N/A")}

## 文档概况
- **文件类型**: {summary.get("document_info", {}).get("file_type", "N/A")}
- **文件大小**: {summary.get("document_info", {}).get("file_size", 0)} bytes
- **质量评分**: {summary.get("document_info", {}).get("quality_score", "N/A")}/100
- **结构质量**: {summary.get("document_info", {}).get("structure_quality", "N/A")}

## 分析摘要
- **总变更数**: {summary.get("analysis_summary", {}).get("total_changes", 0)}
- **新增功能**: {summary.get("analysis_summary", {}).get("new_features_count", 0)}
- **修改功能**: {summary.get("analysis_summary", {}).get("modified_features_count", 0)}
- **关键变更**: {summary.get("analysis_summary", {}).get("key_changes_count", 0)}
- **变更复杂度**: {summary.get("analysis_summary", {}).get("change_complexity", "N/A")}

## 需求信息
- **总需求数**: {summary.get("requirements_info", {}).get("total_requirements", 0)}
- **高优先级需求**: {summary.get("requirements_info", {}).get("high_priority_requirements", 0)}
- **预估工作量**: {summary.get("requirements_info", {}).get("estimated_effort", "N/A")}

"""

        # 添加新增功能详情
        new_features = quick_access.get("new_features", [])
        if new_features:
            markdown += "\n## 新增功能详情\n\n"
            for i, feature in enumerate(new_features[:5], 1):  # 只显示前5个
                markdown += f"### {i}. {feature.get('feature_name', 'N/A')}\n"
                markdown += f"- **描述**: {feature.get('description', 'N/A')}\n"
                markdown += f"- **优先级**: {feature.get('priority', 'N/A')}\n"
                markdown += f"- **复杂度**: {feature.get('complexity', 'N/A')}\n\n"

        # 添加技术设计摘要
        technical_design = quick_access.get("technical_design", "")
        if technical_design:
            markdown += "\n## 技术设计\n\n"
            markdown += technical_design[:1000] + "...\n\n"  # 截取前1000字符

        # 添加实施建议摘要
        implementation_suggestions = quick_access.get("implementation_suggestions", "")
        if implementation_suggestions:
            markdown += "\n## 实施建议\n\n"
            markdown += implementation_suggestions[:1000] + "...\n\n"  # 截取前1000字符

        markdown += "\n---\n*本报告由analyDesign智能分析系统生成*\n"
        
        return markdown
        
    except Exception as e:
        logger.error(f"生成Markdown报告失败: {e}")
        return f"# 分析报告生成失败\n\n错误信息: {str(e)}\n"

@app.route('/api/v2/analysis/markdown/<task_id>', methods=['GET'])
def get_analysis_markdown(task_id: str):
    """获取分析结果的完整markdown格式"""
    try:
        if not service_manager:
            return jsonify({
                "success": False,
                "error": "服务管理器未初始化"
            }), 500
        
        logger.info(f"获取markdown分析报告 - 任务ID: {task_id}")
        
        # 获取完整分析结果
        result = service_manager.get_analysis_result(task_id, include_stages=True)
        
        if not result.get("success"):
            return jsonify(result), 404
        
        data = result.get("data", {})
        
        # 生成完整的markdown报告
        markdown_content = _generate_full_markdown_report(data)
        
        return jsonify({
            "success": True,
            "task_id": task_id,
            "markdown": markdown_content,
            "timestamp": data.get("timestamp")
        }), 200
        
    except Exception as e:
        logger.error(f"获取markdown报告失败: {e}")
        return jsonify({
            "success": False,
            "error": f"获取markdown失败: {str(e)}",
            "task_id": task_id
        }), 500

def _generate_full_markdown_report(data: Dict[str, Any]) -> str:
    """生成完整的Markdown格式分析报告"""
    try:
        stages = data.get("stages", {})
        summary = data.get("summary", {})
        
        # 获取各阶段数据
        document_parsing = stages.get("document_parsing", {})
        content_analysis = stages.get("content_analysis", {})
        ai_analysis = stages.get("ai_analysis", {})
        
        markdown = f"""# 需求文档智能分析报告

> **任务ID**: `{data.get("task_id", "N/A")}`  
> **生成时间**: {data.get("timestamp", "N/A")}  
> **分析状态**: {data.get("status", "N/A")}

---

"""

        # 1. 文档基本信息
        if document_parsing:
            file_info = document_parsing.get("file_info", {})
            structure = document_parsing.get("structure", {})
            quality_info = document_parsing.get("quality_info", {})
            
            markdown += f"""## 📄 文档基本信息

### 文件信息
- **文件名**: {file_info.get("file_name", "N/A")}
- **文件类型**: {file_info.get("file_type", "N/A")}
- **文件大小**: {file_info.get("file_size_mb", 0):.2f} MB
- **创建时间**: {file_info.get("creation_date", "N/A")}
- **修改时间**: {file_info.get("modification_date", "N/A")}

### 文档结构
- **文档标题**: {structure.get("title", "未找到文档标题")}
- **章节数量**: {structure.get("total_sections", 0)}
- **最大层级**: {structure.get("max_depth", 1)}
- **结构质量**: {structure.get("structure_quality", "N/A")}

### 质量评估
- **总体评分**: {quality_info.get("overall_score", 0)}/100
- **可读性**: {quality_info.get("readability", {}).get("level", "N/A")} ({quality_info.get("readability", {}).get("score", 0)}/100)
- **完整性**: {quality_info.get("completeness", {}).get("score", 0)}/100
- **格式化**: {quality_info.get("formatting", {}).get("score", 0)}/100
- **一致性**: {quality_info.get("consistency", {}).get("score", 0)}/100

"""

        # 2. 内容分析结果
        if content_analysis:
            new_features = content_analysis.get("new_features", [])
            modified_features = content_analysis.get("modified_features", [])
            deleted_features = content_analysis.get("deleted_features", [])
            key_changes = content_analysis.get("key_changes", [])
            analysis_summary = content_analysis.get("analysis_summary", {})
            
            markdown += f"""## 🔍 内容分析结果

### 变更统计
- **新增功能**: {len(new_features)} 项
- **修改功能**: {len(modified_features)} 项  
- **删除功能**: {len(deleted_features)} 项
- **关键变更**: {len(key_changes)} 项
- **变更复杂度**: {analysis_summary.get("change_complexity", "N/A")}
- **预估工作量**: {analysis_summary.get("estimated_total_effort", "N/A")}

"""

            # 新增功能详情
            if new_features:
                markdown += "### ✨ 新增功能详情\n\n"
                for i, feature in enumerate(new_features, 1):
                    markdown += f"""#### {i}. {feature.get('feature_name', 'N/A')}
- **描述**: {feature.get('description', 'N/A')}
- **优先级**: {feature.get('priority', 'N/A')}
- **复杂度**: {feature.get('complexity', 'N/A')}
- **预估工作量**: {feature.get('estimated_effort', 'N/A')}

"""

            # 修改功能详情
            if modified_features:
                markdown += "### 🔧 修改功能详情\n\n"
                for i, feature in enumerate(modified_features, 1):
                    markdown += f"""#### {i}. {feature.get('feature_name', 'N/A')}
- **变更类型**: {feature.get('change_type', 'N/A')}
- **变更描述**: {feature.get('change_description', 'N/A')}
- **影响范围**: {feature.get('impact_scope', 'N/A')}
- **优先级**: {feature.get('priority', 'N/A')}

"""

            # 关键变更
            if key_changes:
                markdown += "### 🚨 关键变更\n\n"
                for i, change in enumerate(key_changes, 1):
                    markdown += f"""#### {i}. {change.get('change_title', 'N/A')}
- **变更类型**: {change.get('change_type', 'N/A')}
- **重要程度**: {change.get('importance', 'N/A')}
- **影响评估**: {change.get('impact_assessment', 'N/A')}
- **建议措施**: {change.get('recommendations', 'N/A')}

"""

        # 3. AI智能分析结果
        if ai_analysis:
            requirements = ai_analysis.get("requirements", [])
            technical_design = ai_analysis.get("technical_design", "")
            implementation_suggestions = ai_analysis.get("implementation_suggestions", "")
            analysis_summary = ai_analysis.get("analysis_summary", "")
            
            # 需求提取
            if requirements:
                markdown += f"""## 📋 需求提取结果

共提取到 **{len(requirements)}** 项需求：

"""
                for i, req in enumerate(requirements, 1):
                    markdown += f"""### {i}. {req.get('requirement_title', 'N/A')}
- **需求类型**: {req.get('requirement_type', 'N/A')}
- **优先级**: {req.get('priority', 'N/A')}
- **描述**: {req.get('description', 'N/A')}
- **验收条件**: {req.get('acceptance_criteria', 'N/A')}

"""

            # 技术设计
            if technical_design:
                markdown += f"""## 🏗️ 技术架构设计

{technical_design}

"""

            # 实施建议
            if implementation_suggestions:
                markdown += f"""## 💡 实施建议

{implementation_suggestions}

"""

            # 综合分析总结
            if analysis_summary:
                markdown += f"""## 📊 综合分析总结

{analysis_summary}

"""

        markdown += """
---

## 📝 使用说明

本报告由 **analyDesign 智能需求分析系统** 基于AI技术自动生成，包含以下分析阶段：

1. **文档解析**: 识别文件格式、提取文档结构和内容
2. **内容分析**: 分析功能变更、识别新增/修改/删除的功能点
3. **AI智能分析**: 提取需求、生成技术设计方案和实施建议

> ⚠️ **注意**: AI分析结果仅供参考，实际实施时请结合项目具体情况进行调整。

---

*报告生成时间: {data.get("timestamp", "N/A")}*
"""

        return markdown
        
    except Exception as e:
        logger.error(f"生成完整Markdown报告失败: {e}")
        return f"""# ❌ 分析报告生成失败

**错误信息**: {str(e)}

**任务ID**: {data.get("task_id", "N/A")}  
**时间**: {data.get("timestamp", "N/A")}

请检查系统状态或联系管理员。
"""

# 错误处理
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "接口不存在",
        "timestamp": datetime.now().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "服务器内部错误",
        "timestamp": datetime.now().isoformat()
    }), 500

def create_app():
    """创建应用实例"""
    return app

if __name__ == '__main__':
    logger.info("启动增强API服务器...")
    app.run(host='0.0.0.0', port=8082, debug=True) 