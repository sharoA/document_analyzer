#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
analyDesign WebSocket服务器
专门处理实时通信功能
"""

import json
import time
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from flask import Flask, request
from flask_socketio import SocketIO, emit, disconnect
from flask_cors import CORS

# 导入现有的模块
try:
    from ..resource.config import get_config
    from ..utils.volcengine_client import VolcengineClient, VolcengineConfig
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from src.resource.config import get_config
    from src.utils.volcengine_client import VolcengineClient, VolcengineConfig

# 获取配置
config = get_config()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'analyDesign_websocket_secret_key'

# 配置CORS
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"])

# 创建SocketIO实例
socketio = SocketIO(
    app,
    cors_allowed_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    async_mode='threading',
    logger=True,
    engineio_logger=True
)

# 初始化火山引擎客户端
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
    volcano_client = None

# 存储连接的客户端
connected_clients = {}

@socketio.on('connect')
def handle_connect():
    """处理客户端连接"""
    client_id = request.sid
    connected_clients[client_id] = {
        'connected_at': datetime.now(),
        'last_activity': datetime.now()
    }
    
    logger.info(f"客户端连接: {client_id}")
    
    emit('connected', {
        'status': 'success',
        'client_id': client_id,
        'message': '连接成功',
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('disconnect')
def handle_disconnect():
    """处理客户端断开连接"""
    client_id = request.sid
    
    if client_id in connected_clients:
        del connected_clients[client_id]
    
    logger.info(f"客户端断开连接: {client_id}")

@socketio.on('ping')
def handle_ping(data):
    """处理心跳"""
    client_id = request.sid
    
    if client_id in connected_clients:
        connected_clients[client_id]['last_activity'] = datetime.now()
    
    emit('pong', {
        'timestamp': datetime.now().isoformat(),
        'client_id': client_id
    })

@socketio.on('chat')
def handle_chat(data):
    """处理聊天消息"""
    try:
        client_id = request.sid
        message = data.get('message', '').strip()
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        if not message:
            emit('error', {
                'error': '消息内容不能为空',
                'timestamp': datetime.now().isoformat()
            })
            return
        
        logger.info(f"收到聊天消息 - Client: {client_id}, Session: {session_id}, Message: {message}")
        
        # 发送处理中状态
        emit('chat_processing', {
            'session_id': session_id,
            'message': '正在处理您的消息...',
            'timestamp': datetime.now().isoformat()
        })
        
        # 检查火山引擎客户端是否可用
        if not volcano_client:
            emit('chat_response', {
                'success': False,
                'error': '火山引擎客户端未初始化，请检查配置',
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            })
            return
        
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
            
            # 发送AI回复
            emit('chat_response', {
                'success': True,
                'response': ai_response,
                'session_id': session_id,
                'timestamp': datetime.now().isoformat(),
                'confidence': 0.9,
                'intent': '需求分析',
                'model': volcano_config.model_id
            })
            
            logger.info(f"成功处理聊天请求 - Client: {client_id}, Session: {session_id}")
            
        except Exception as volcano_error:
            logger.error(f"火山引擎调用失败: {volcano_error}")
            emit('chat_response', {
                'success': False,
                'error': f'火山引擎调用失败: {str(volcano_error)}',
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"处理聊天消息时出错: {e}")
        emit('error', {
            'error': f'服务器内部错误: {str(e)}',
            'timestamp': datetime.now().isoformat()
        })

@socketio.on('file_upload_progress')
def handle_file_upload_progress(data):
    """处理文件上传进度更新"""
    try:
        client_id = request.sid
        task_id = data.get('task_id')
        progress = data.get('progress', 0)
        status = data.get('status', 'uploading')
        
        logger.info(f"文件上传进度更新 - Client: {client_id}, Task: {task_id}, Progress: {progress}%")
        
        # 广播进度更新（可以选择只发送给特定客户端）
        emit('file_progress_update', {
            'task_id': task_id,
            'progress': progress,
            'status': status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"处理文件上传进度时出错: {e}")
        emit('error', {
            'error': f'处理文件上传进度失败: {str(e)}',
            'timestamp': datetime.now().isoformat()
        })

@socketio.on('get_status')
def handle_get_status():
    """获取服务器状态"""
    try:
        status_info = {
            'server_status': 'running',
            'connected_clients': len(connected_clients),
            'volcano_engine_status': 'connected' if volcano_client else 'disconnected',
            'timestamp': datetime.now().isoformat()
        }
        
        emit('status_response', status_info)
        
    except Exception as e:
        logger.error(f"获取状态时出错: {e}")
        emit('error', {
            'error': f'获取状态失败: {str(e)}',
            'timestamp': datetime.now().isoformat()
        })

def create_app():
    """应用工厂函数"""
    return app

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 analyDesign WebSocket服务器启动中...")
    print("=" * 60)
    print(f"🔌 WebSocket地址: ws://localhost:8081/socket.io/")
    print(f"📡 服务地址: http://localhost:8081")
    print("=" * 60)
    print("✨ 功能特性:")
    print("  📨 实时聊天对话")
    print("  📁 文件上传进度跟踪")
    print("  💓 心跳检测")
    print("  📊 服务器状态监控")
    print("=" * 60)
    
    try:
        socketio.run(
            app,
            host='0.0.0.0',
            port=8081,
            debug=True,
            allow_unsafe_werkzeug=True
        )
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}") 