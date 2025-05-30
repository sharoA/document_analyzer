#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
analyDesign API服务器
集成火山引擎实时交互功能
"""

import json
import time
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from flask import Flask, request, jsonify, make_response
from flask_cors import CORS

# 导入现有的模块
try:
    from .simple_config import settings
    from .volcengine_client import VolcengineClient, VolcengineConfig
except ImportError:
    # 如果相对导入失败，尝试绝对导入
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

app = Flask(__name__)
# 配置CORS，允许所有来源和方法
CORS(app, 
     origins=["http://localhost:3000", "http://127.0.0.1:3000"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"],
     supports_credentials=True)

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

# 会话存储（生产环境建议使用Redis等持久化存储）
sessions = {}

@app.route('/', methods=['GET'])
def index():
    """首页"""
    return jsonify({
        "service": "analyDesign API Server",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "chat": "/api/chat",
            "health": "/api/health",
            "sessions": "/api/sessions"
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
            "volcano_engine": volcano_status
        }
    })

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
                "model": volcano_config.model_id
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

@app.route('/api/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """删除会话"""
    if session_id in sessions:
        del sessions[session_id]
        return jsonify({
            "success": True,
            "message": "会话已删除",
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
    print("🚀 analyDesign API服务器启动中...")
    print("=" * 60)
    print(f"📡 服务地址: http://localhost:8080")
    print(f"🔗 API文档: http://localhost:8080")
    print(f"💬 聊天接口: http://localhost:8080/api/chat")
    print(f"❤️  健康检查: http://localhost:8080/api/health")
    print("=" * 60)
    print("⚠️  请确保已配置火山引擎API密钥")
    print("📝 在src/config.py中设置您的火山引擎配置")
    print("=" * 60)
    
    app.run(
        host='0.0.0.0',
        port=8080,
        debug=True,
        threaded=True
    ) 