#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
analyDesign 集成服务器
同时支持HTTP API和WebSocket连接
"""

import json
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, disconnect

# 导入现有的模块
try:
    from .simple_config import settings
    from .volcengine_client import VolcengineClient, VolcengineConfig
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.simple_config import settings
    from src.volcengine_client import VolcengineClient, VolcengineConfig

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'analydesign_secret_key_2025'

# 配置CORS
CORS(app, 
     origins=["http://localhost:3000", "http://127.0.0.1:3000"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"],
     supports_credentials=True)

# 创建SocketIO实例
socketio = SocketIO(app, 
                   cors_allowed_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
                   async_mode='threading')

# 初始化火山引擎客户端
try:
    volcano_config = VolcengineConfig(
        api_key=settings.VOLCENGINE_API_KEY,
        model_id=settings.VOLCENGINE_MODEL_ID,
        base_url=settings.VOLCENGINE_BASE_URL,
        temperature=settings.DEFAULT_TEMPERATURE,
        max_tokens=settings.DEFAULT_MAX_TOKENS
    )
    volcano_client = VolcengineClient(volcano_config)
    logger.info("火山引擎客户端初始化成功")
except Exception as e:
    logger.error(f"火山引擎客户端初始化失败: {e}")
    volcano_client = None

# 会话存储
sessions = {}
connected_clients = {}

# ==================== HTTP API 路由 ====================

@app.route('/', methods=['GET'])
def index():
    """首页"""
    return jsonify({
        "service": "analyDesign 集成服务器",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "features": {
            "http_api": True,
            "websocket": True,
            "volcano_engine": volcano_client is not None
        },
        "endpoints": {
            "chat": "/api/chat",
            "health": "/api/health",
            "sessions": "/api/sessions",
            "websocket": "/socket.io/"
        }
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    volcano_status = "connected" if volcano_client else "disconnected"
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api_server": "running",
            "websocket_server": "running",
            "volcano_engine": volcano_status
        },
        "connections": {
            "websocket_clients": len(connected_clients),
            "active_sessions": len(sessions)
        }
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """HTTP聊天接口"""
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
        
        logger.info(f"收到HTTP聊天请求 - Session: {session_id}, Message: {message}")
        
        # 处理聊天消息
        response_data = process_chat_message(message, session_id, "http")
        
        if response_data["success"]:
            logger.info(f"成功处理HTTP聊天请求 - Session: {session_id}")
            return jsonify(response_data)
        else:
            return jsonify(response_data), 500
            
    except Exception as e:
        logger.error(f"处理HTTP聊天请求时出错: {e}")
        return jsonify({
            "success": False,
            "error": f"服务器内部错误: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """获取所有会话"""
    return jsonify({
        "success": True,
        "sessions": sessions,
        "count": len(sessions),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """获取特定会话"""
    if session_id in sessions:
        return jsonify({
            "success": True,
            "session": sessions[session_id],
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })
    else:
        return jsonify({
            "success": False,
            "error": "会话不存在",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }), 404

# ==================== WebSocket 事件处理 ====================

@socketio.on('connect')
def handle_connect():
    """客户端连接事件"""
    client_id = request.sid
    connected_clients[client_id] = {
        "connected_at": datetime.now().isoformat(),
        "session_id": None
    }
    
    logger.info(f"WebSocket客户端 {client_id} 已连接，当前连接数: {len(connected_clients)}")
    
    # 发送欢迎消息
    emit('message', {
        "type": "system",
        "message": "欢迎使用 analyDesign 智能需求分析系统！现在使用WebSocket实时通信。",
        "timestamp": datetime.now().isoformat(),
        "message_id": str(uuid.uuid4())
    })

@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开事件"""
    client_id = request.sid
    if client_id in connected_clients:
        del connected_clients[client_id]
    
    logger.info(f"WebSocket客户端 {client_id} 已断开，当前连接数: {len(connected_clients)}")

@socketio.on('chat')
def handle_chat(data):
    """处理聊天消息"""
    try:
        client_id = request.sid
        message = data.get('message', '').strip()
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        if not message:
            emit('error', {
                "error": "消息内容不能为空",
                "timestamp": datetime.now().isoformat()
            })
            return
        
        logger.info(f"收到WebSocket聊天请求 - Client: {client_id}, Session: {session_id}, Message: {message}")
        
        # 更新客户端会话信息
        if client_id in connected_clients:
            connected_clients[client_id]["session_id"] = session_id
        
        # 发送处理中消息
        emit('message', {
            "type": "processing",
            "message": "正在分析您的需求，请稍候...",
            "timestamp": datetime.now().isoformat(),
            "message_id": str(uuid.uuid4())
        })
        
        # 处理聊天消息
        response_data = process_chat_message(message, session_id, "websocket")
        
        if response_data["success"]:
            # 发送AI回复
            emit('message', {
                "type": "chat_response",
                "message": response_data["response"],
                "timestamp": datetime.now().isoformat(),
                "message_id": str(uuid.uuid4()),
                "analysis": {
                    "confidence": response_data.get("confidence", 0.9),
                    "intent": response_data.get("intent", "需求分析"),
                    "model": response_data.get("model")
                }
            })
            
            logger.info(f"成功处理WebSocket聊天请求 - Client: {client_id}, Session: {session_id}")
        else:
            # 发送错误消息
            emit('error', {
                "error": response_data["error"],
                "timestamp": datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"处理WebSocket聊天请求时出错: {e}")
        emit('error', {
            "error": f"服务器内部错误: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })

@socketio.on('ping')
def handle_ping():
    """处理心跳"""
    emit('pong', {
        "timestamp": datetime.now().isoformat()
    })

# ==================== 共享业务逻辑 ====================

def process_chat_message(message: str, session_id: str, source: str = "unknown") -> Dict[str, Any]:
    """
    处理聊天消息的共享逻辑
    
    Args:
        message: 用户消息
        session_id: 会话ID
        source: 消息来源 (http/websocket)
    
    Returns:
        处理结果
    """
    try:
        # 更新会话信息
        if session_id not in sessions:
            sessions[session_id] = {
                "created_at": datetime.now().isoformat(),
                "messages": [],
                "source": source
            }
        
        sessions[session_id]["messages"].append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat(),
            "source": source
        })
        
        # 检查火山引擎客户端是否可用
        if not volcano_client:
            return {
                "success": False,
                "error": "火山引擎客户端未初始化，请检查配置",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
        
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
        ai_response = volcano_client.chat(messages=messages)
        
        # 保存AI回复到会话
        sessions[session_id]["messages"].append({
            "role": "assistant",
            "content": ai_response,
            "timestamp": datetime.now().isoformat(),
            "source": source
        })
        
        return {
            "success": True,
            "response": ai_response,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "confidence": 0.9,
            "intent": "需求分析",
            "model": volcano_config.model_id,
            "source": source
        }
        
    except Exception as e:
        logger.error(f"处理聊天消息时出错: {e}")
        return {
            "success": False,
            "error": f"处理消息失败: {str(e)}",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }

# ==================== 错误处理 ====================

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
    """应用工厂函数"""
    return app

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 analyDesign 集成服务器启动中...")
    print("=" * 60)
    print(f"📡 服务地址: http://localhost:8081")
    print(f"🔗 API文档: http://localhost:8081")
    print(f"💬 HTTP聊天: http://localhost:8081/api/chat")
    print(f"🔌 WebSocket: ws://localhost:8081/socket.io/")
    print(f"❤️  健康检查: http://localhost:8081/api/health")
    print("=" * 60)
    print("✨ 功能特性:")
    print("   • HTTP RESTful API")
    print("   • WebSocket 实时通信")
    print("   • 火山引擎 AI 集成")
    print("   • 会话管理")
    print("   • CORS 跨域支持")
    print("=" * 60)
    print("⚠️  请确保已配置火山引擎API密钥")
    print("📝 在src/simple_config.py中设置您的火山引擎配置")
    print("=" * 60)
    
    # 使用SocketIO运行应用
    socketio.run(
        app,
        host='0.0.0.0',
        port=8081,
        debug=True,
        allow_unsafe_werkzeug=True
    ) 