#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
analyDesign WebSocket服务器
支持三阶段文档分析的实时通信功能
"""

import json
import time
import uuid
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

from flask import Flask, request
from flask_socketio import SocketIO, emit, disconnect
from flask_cors import CORS

# 导入Redis客户端
try:
    import redis
    redis_available = True
except ImportError:
    redis_available = False

# 导入现有的模块
import sys
import os

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from src.resource.config import get_config
    from src.utils.volcengine_client import VolcengineClient, VolcengineConfig
    from src.analysis_services.document_parser import DocumentParserService
    from src.analysis_services.content_analyzer import ContentAnalyzerService
    from src.analysis_services.ai_analyzer import AIAnalyzerService
except ImportError as e:
    logger.error(f"导入模块失败: {e}")
    # 尝试直接从当前目录的相对路径导入
    sys.path.append(os.path.join(current_dir, '..', '..'))
    from src.resource.config import get_config
    from src.utils.volcengine_client import VolcengineClient, VolcengineConfig
    from src.analysis_services.document_parser import DocumentParserService
    from src.analysis_services.content_analyzer import ContentAnalyzerService
    from src.analysis_services.ai_analyzer import AIAnalyzerService

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
    async_mode='eventlet',
    logger=True,
    engineio_logger=True,
    max_http_buffer_size=10 * 1024 * 1024,  # 10MB
    ping_timeout=60,  # 增加超时时间
    ping_interval=25
)

# 初始化Redis客户端
redis_client = None
if redis_available:
    try:
        redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        redis_client.ping()
        logger.info("Redis连接成功")
    except Exception as e:
        logger.warning(f"Redis连接失败: {e}")
        redis_client = None

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

# 初始化分析服务
document_parser = DocumentParserService(llm_client=volcano_client)
content_analyzer = ContentAnalyzerService(llm_client=volcano_client)
ai_analyzer = AIAnalyzerService(llm_client=volcano_client)

# 存储连接的客户端和分析任务
connected_clients = {}
analysis_tasks = {}
task_clients = {}  # task_id -> client_id (用于定向发送事件)

# 分析阶段定义
ANALYSIS_STAGES = [
    {"stage": "document_parsing", "name": "文档解析", "weight": 30},
    {"stage": "content_analysis", "name": "内容分析", "weight": 35},
    {"stage": "ai_analysis", "name": "AI智能分析", "weight": 35}
]

class AnalysisProgress:
    """分析进度管理器"""
    
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.current_stage = 0
        self.stage_progress = {}
        self.overall_progress = 0
        self.status = "waiting"  # waiting, running, completed, error
        self.start_time = None
        self.end_time = None
        self.results = {}
        
    def start_analysis(self):
        """开始分析"""
        self.status = "running"
        self.start_time = time.time()
        
    def update_stage_progress(self, stage: str, progress: int):
        """更新阶段进度"""
        self.stage_progress[stage] = progress
        self._calculate_overall_progress()
        
    def complete_stage(self, stage: str, result: Dict[str, Any]):
        """完成阶段"""
        self.stage_progress[stage] = 100
        self.results[stage] = result
        self._calculate_overall_progress()
        
        # 检查是否所有阶段都完成
        if len(self.results) >= len(ANALYSIS_STAGES):
            self.status = "completed"
            self.end_time = time.time()
            
    def set_error(self, error_message: str):
        """设置错误状态"""
        self.status = "error"
        self.error_message = error_message
        self.end_time = time.time()
        
    def _calculate_overall_progress(self):
        """计算总体进度"""
        total_weight = sum(stage["weight"] for stage in ANALYSIS_STAGES)
        weighted_progress = 0
        
        for stage_info in ANALYSIS_STAGES:
            stage = stage_info["stage"]
            weight = stage_info["weight"]
            progress = self.stage_progress.get(stage, 0)
            weighted_progress += (progress * weight) / 100
            
        self.overall_progress = int((weighted_progress / total_weight) * 100)
        
    def to_dict(self):
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "status": self.status,
            "overall_progress": self.overall_progress,
            "stage_progress": self.stage_progress,
            "current_stage": self.current_stage,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": (self.end_time - self.start_time) if self.start_time and self.end_time else None,
            "results": self.results
        }

@socketio.on('connect')
def handle_connect():
    """处理客户端连接 - 支持TaskID作为SessionID"""
    client_id = request.sid
    
    # 🔧 新架构：检查是否是任务级连接
    task_id = request.args.get('task_id')
    connection_type = 'task' if task_id else 'general'
    
    logger.info(f"📡 收到连接请求:")
    logger.info(f"   - 连接类型: {connection_type}")
    logger.info(f"   - Socket ID: {client_id}")
    logger.info(f"   - 任务ID: {task_id or 'N/A'}")
    
    # 🔧 新架构：如果是任务级连接，尝试使用TaskID作为SessionID
    if task_id:
        logger.info(f"🎯 [任务级连接] 尝试使用TaskID作为SessionID")
        logger.info(f"   - 期望: TaskID({task_id}) = SessionID({client_id})")
        
        # 直接建立TaskID到当前SessionID的映射
        task_clients[task_id] = client_id
        logger.info(f"✅ [任务级连接] 建立映射: Task[{task_id}] -> Client[{client_id}]")
    
    connected_clients[client_id] = {
        'connected_at': datetime.now(),
        'last_activity': datetime.now(),
        'connection_type': connection_type,
        'task_id': task_id
    }
    
    # 显式将客户端加入以其session ID命名的房间
    socketio.server.enter_room(client_id, client_id)
    logger.info(f"客户端连接: {client_id} - 已加入房间: {client_id}")
    
    emit('connected', {
        'status': 'success',
        'client_id': client_id,
        'task_id': task_id,
        'connection_type': connection_type,
        'message': '连接成功',
        'timestamp': datetime.now().isoformat(),
        'available_stages': [stage["name"] for stage in ANALYSIS_STAGES]
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

@socketio.on('start_analysis')
def handle_start_analysis(data):
    """处理开始分析请求"""
    try:
        client_id = request.sid
        task_id = data.get('task_id', str(uuid.uuid4()))
        execution_mode = data.get('execution_mode', 'automatic')  # automatic | manual
        
        logger.info(f"📥 收到start_analysis请求:")
        logger.info(f"   - 当前Session ID: {client_id}")
        logger.info(f"   - 任务ID: {task_id}")
        logger.info(f"   - 请求数据: {data}")
        logger.info(f"   - 当前连接的客户端: {list(connected_clients.keys())}")
        logger.info(f"   - 现有任务映射: {task_clients}")
        
        logger.info(f"开始分析任务 - Client: {client_id}, Task: {task_id}, Mode: {execution_mode}")
        logger.info(f"📋 任务映射: Task[{task_id}] -> Client[{client_id}]")
        
        # 尝试从上传的文件获取文件信息
        file_info = get_uploaded_file_info(task_id)
        if not file_info:
            emit('analysis_error', {
                'task_id': task_id,
                'error': '未找到上传的文件，请先上传文件',
                'timestamp': datetime.now().isoformat()
            })
            return
        
        # 创建分析进度管理器
        progress_manager = AnalysisProgress(task_id)
        analysis_tasks[task_id] = progress_manager
        task_clients[task_id] = client_id  # 记录任务对应的客户端ID
        
        logger.info(f"🎯 已记录任务客户端映射: {task_id} -> {client_id}")
        logger.info(f"📋 更新后的任务映射: {task_clients}")
        
        # 发送分析开始确认
        emit('analysis_started', {
            'task_id': task_id,
            'execution_mode': execution_mode,
            'stages': ANALYSIS_STAGES,
            'timestamp': datetime.now().isoformat()
        })
        
        # 根据执行模式启动分析
        if execution_mode == 'automatic':
            # 自动模式：顺序执行所有阶段
            socketio.start_background_task(run_automatic_analysis, task_id, file_info)
        else:
            # 手动模式：等待用户手动触发每个阶段
            progress_manager.status = "waiting_for_trigger"
            emit('analysis_ready', {
                'task_id': task_id,
                'message': '分析已准备就绪，等待手动触发',
                'next_stage': ANALYSIS_STAGES[0],
                'timestamp': datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"启动分析任务时出错: {e}")
        emit('analysis_error', {
            'task_id': task_id,
            'error': f'启动分析失败: {str(e)}',
            'timestamp': datetime.now().isoformat()
        })

@socketio.on('trigger_stage')
def handle_trigger_stage(data):
    """处理手动触发阶段分析"""
    try:
        client_id = request.sid
        task_id = data.get('task_id')
        stage = data.get('stage')
        
        if task_id not in analysis_tasks:
            emit('analysis_error', {
                'task_id': task_id,
                'error': '分析任务不存在',
                'timestamp': datetime.now().isoformat()
            })
            return
            
        progress_manager = analysis_tasks[task_id]
        
        logger.info(f"手动触发阶段 - Client: {client_id}, Task: {task_id}, Stage: {stage}")
        
        # 启动单个阶段分析
        socketio.start_background_task(run_single_stage_analysis, task_id, stage, data)
        
    except Exception as e:
        logger.error(f"触发阶段分析时出错: {e}")
        emit('analysis_error', {
            'task_id': task_id,
            'error': f'触发阶段失败: {str(e)}',
            'timestamp': datetime.now().isoformat()
        })

@socketio.on('get_analysis_progress')
def handle_get_analysis_progress(data):
    """获取分析进度"""
    try:
        task_id = data.get('task_id')
        
        if task_id in analysis_tasks:
            progress_manager = analysis_tasks[task_id]
            emit('analysis_progress', progress_manager.to_dict())
        else:
            emit('analysis_error', {
                'task_id': task_id,
                'error': '分析任务不存在',
                'timestamp': datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"获取分析进度时出错: {e}")
        emit('error', {
            'error': f'获取进度失败: {str(e)}',
            'timestamp': datetime.now().isoformat()
        })

@socketio.on('establish_task_binding')
def handle_establish_task_binding(data):
    """处理任务强绑定请求 - 简化版本"""
    try:
        client_id = request.sid
        task_id = data.get('task_id')
        provided_session_id = data.get('session_id')
        action = data.get('action', 'strong_binding')
        
        logger.info(f"🎯 [简化方案] 收到任务强绑定请求:")
        logger.info(f"   - 当前客户端ID: {client_id}")
        logger.info(f"   - 任务ID: {task_id}")
        logger.info(f"   - 提供的Session ID: {provided_session_id}")
        logger.info(f"   - 动作: {action}")
        
        if task_id and client_id:
            # 强制建立绑定，使用当前实际的client_id
            task_clients[task_id] = client_id
            logger.info(f"✅ [强绑定] Task[{task_id}] -> Client[{client_id}]")
            logger.info(f"📋 更新后映射: {task_clients}")
            
            # 确保客户端在正确的房间
            socketio.server.enter_room(client_id, client_id)
            
            # 发送绑定确认
            emit('task_binding_confirmed', {
                'task_id': task_id,
                'session_id': client_id,
                'action': action,
                'status': 'success',
                'message': '任务绑定成功',
                'timestamp': datetime.now().isoformat()
            })
            
        else:
            logger.warning(f"⚠️ [强绑定] 缺少必要参数: task_id={task_id}, client_id={client_id}")
            emit('task_binding_error', {
                'error': '缺少task_id或client_id参数',
                'timestamp': datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"处理任务强绑定时出错: {e}")
        emit('task_binding_error', {
            'error': f'强绑定失败: {str(e)}',
            'timestamp': datetime.now().isoformat()
        })

@socketio.on('update_session_mapping')
def handle_update_session_mapping(data):
    """处理Session ID映射更新"""
    try:
        client_id = request.sid
        task_id = data.get('task_id')
        new_session_id = data.get('new_session_id')
        old_session_id = data.get('old_session_id')
        action = data.get('action', 'manual_update')
        
        logger.info(f"📝 收到Session ID更新请求:")
        logger.info(f"   - 当前客户端ID: {client_id}")
        logger.info(f"   - 任务ID: {task_id}")
        logger.info(f"   - 新Session ID: {new_session_id}")
        logger.info(f"   - 旧Session ID: {old_session_id}")
        logger.info(f"   - 操作类型: {action}")
        logger.info(f"   - 更新前映射: {task_clients}")
        
        if task_id and new_session_id:
            # 🔧 增强：处理不同类型的映射更新
            if action == 'initial_mapping':
                # 初始映射：直接设置
                task_clients[task_id] = new_session_id
                logger.info(f"✅ [初始映射] Task[{task_id}] -> Client[{new_session_id}]")
                
            elif action == 'session_changed':
                # Session变更：更新映射并验证
                old_client = task_clients.get(task_id)
                task_clients[task_id] = new_session_id
                logger.info(f"🔄 [Session变更] Task[{task_id}]: {old_client} -> {new_session_id}")
                
            elif action == 'reconnect_sync':
                # 重连同步：强制更新映射
                task_clients[task_id] = new_session_id
                logger.info(f"🔄 [重连同步] Task[{task_id}] -> Client[{new_session_id}]")
                
                # 🔧 新增：重连后立即发送最新进度
                if task_id in analysis_tasks:
                    progress_manager = analysis_tasks[task_id]
                    logger.info(f"📡 [重连同步] 立即发送最新进度到新客户端: {new_session_id}")
                    
                    # 发送当前进度状态
                    socketio.emit('analysis_progress', progress_manager.to_dict(), room=new_session_id)
                    
                    # 如果任务已完成，发送完成消息
                    if progress_manager.status == 'completed':
                        socketio.emit('analysis_completed', {
                            'task_id': task_id,
                            'status': 'completed',
                            'message': '分析已完成',
                            'timestamp': datetime.now().isoformat()
                        }, room=new_session_id)
                        logger.info(f"📡 [重连同步] 已发送完成状态到客户端: {new_session_id}")
                
            elif action == 'consistency_check':
                # 一致性检查：更新映射并重发状态
                task_clients[task_id] = new_session_id
                logger.info(f"🔍 [一致性检查] Task[{task_id}] -> Client[{new_session_id}]")
                
                # 🔧 新增：一致性检查后立即发送最新进度和状态
                if task_id in analysis_tasks:
                    progress_manager = analysis_tasks[task_id]
                    logger.info(f"📡 [一致性检查] 立即发送最新进度到客户端: {new_session_id}")
                    logger.info(f"📊 当前任务状态: {progress_manager.status}")
                    logger.info(f"📊 当前总进度: {progress_manager.overall_progress}%")
                    
                    # 发送当前进度状态
                    socketio.emit('analysis_progress', progress_manager.to_dict(), room=new_session_id)
                    
                    # 如果任务已完成，发送完成消息
                    if progress_manager.status == 'completed':
                        socketio.emit('analysis_completed', {
                            'task_id': task_id,
                            'status': 'completed',
                            'message': '分析已完成',
                            'timestamp': datetime.now().isoformat()
                        }, room=new_session_id)
                        logger.info(f"📡 [一致性检查] 已发送完成状态到客户端: {new_session_id}")
                
            else:
                # 默认更新
                task_clients[task_id] = new_session_id
                logger.info(f"✅ [默认更新] Task[{task_id}] -> Client[{new_session_id}]")
                
                # 🔧 新增：默认更新也重发状态
                if task_id in analysis_tasks:
                    progress_manager = analysis_tasks[task_id]
                    logger.info(f"📡 [默认更新] 立即发送最新进度到客户端: {new_session_id}")
                    
                    # 发送当前进度状态
                    socketio.emit('analysis_progress', progress_manager.to_dict(), room=new_session_id)
                    
                    # 如果任务已完成，发送完成消息
                    if progress_manager.status == 'completed':
                        socketio.emit('analysis_completed', {
                            'task_id': task_id,
                            'status': 'completed',
                            'message': '分析已完成',
                            'timestamp': datetime.now().isoformat()
                        }, room=new_session_id)
                        logger.info(f"📡 [默认更新] 已发送完成状态到客户端: {new_session_id}")
            
            # 确保客户端加入正确的房间
            socketio.server.enter_room(new_session_id, new_session_id)
            
            # 🔧 新增：验证映射更新结果
            actual_mapping = task_clients.get(task_id)
            if actual_mapping == new_session_id:
                logger.info(f"✅ Session ID映射验证成功: Task[{task_id}] -> Client[{new_session_id}]")
            else:
                logger.error(f"❌ Session ID映射验证失败: 期望[{new_session_id}], 实际[{actual_mapping}]")
            
            logger.info(f"📋 更新后映射: {task_clients}")
            
            # 发送确认
            emit('session_mapping_updated', {
                'task_id': task_id,
                'new_session_id': new_session_id,
                'old_session_id': old_session_id,
                'action': action,
                'status': 'success',
                'timestamp': datetime.now().isoformat()
            })
        else:
            logger.warning(f"⚠️ Session ID更新请求缺少必要参数")
            emit('session_mapping_error', {
                'error': '缺少task_id或new_session_id参数',
                'timestamp': datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"更新Session ID映射时出错: {e}")
        emit('session_mapping_error', {
            'error': f'更新失败: {str(e)}',
            'timestamp': datetime.now().isoformat()
        })

# 添加客户端验证和更新函数
def validate_and_update_client_mapping(task_id: str) -> str:
    """验证并更新任务的客户端映射，返回有效的客户端ID"""
    logger.info(f"🔍 开始验证客户端映射 - 任务: {task_id}")
    
    if task_id not in task_clients:
        logger.warning(f"❌ 任务 {task_id} 没有客户端映射")
        return None
    
    stored_client_id = task_clients[task_id]
    logger.info(f"📋 存储的客户端ID: {stored_client_id}")
    logger.info(f"📋 当前连接的客户端: {list(connected_clients.keys())}")
    
    # 检查房间状态
    try:
        rooms = socketio.server.manager.get_rooms(stored_client_id, '/')
        logger.info(f"🏠 客户端 {stored_client_id} 所在房间: {rooms}")
    except Exception as e:
        logger.warning(f"⚠️ 无法获取房间信息: {e}")
    
    # 检查存储的客户端ID是否仍然连接
    if stored_client_id in connected_clients:
        logger.info(f"✅ 客户端 {stored_client_id} 仍然有效")
        return stored_client_id
    else:
        logger.warning(f"⚠️ 存储的客户端 {stored_client_id} 已断开连接")
        
        # 尝试找到最新连接的客户端（如果只有一个连接的话）
        active_clients = list(connected_clients.keys())
        logger.info(f"🔍 当前活跃客户端列表: {active_clients}")
        
        if len(active_clients) == 1:
            new_client_id = active_clients[0]
            logger.info(f"🔄 更新任务 {task_id} 的客户端映射: {stored_client_id} -> {new_client_id}")
            task_clients[task_id] = new_client_id
            logger.info(f"✅ 映射更新完成，新的映射: {task_clients}")
            return new_client_id
        elif len(active_clients) > 1:
            logger.warning(f"⚠️ 发现多个活跃客户端，无法自动选择: {active_clients}")
            # 选择最新的连接（假设键是按连接顺序排列的）
            new_client_id = active_clients[-1]
            logger.info(f"🎯 选择最新连接的客户端: {new_client_id}")
            task_clients[task_id] = new_client_id
            return new_client_id
        else:
            logger.error(f"❌ 没有活跃的客户端连接")
            return None

def run_automatic_analysis(task_id: str, input_data: Dict[str, Any]):
    """运行自动分析（所有阶段）"""
    try:
        progress_manager = analysis_tasks[task_id]
        client_id = validate_and_update_client_mapping(task_id)
        
        logger.info(f"🚀 开始自动分析 - Task: {task_id}")
        logger.info(f"🎯 获取客户端映射: Task[{task_id}] -> Client[{client_id}]")
        
        if not client_id:
            logger.error(f"❌ 未找到任务 {task_id} 对应的客户端ID")
            logger.error(f"📋 当前任务客户端映射: {task_clients}")
            return
            
        progress_manager.start_analysis()
        
        # 发送开始信息到特定客户端
        logger.info(f"📡 发送进度更新到客户端: {client_id} (任务: {task_id})")
        logger.info(f"🔧 [调试] 使用广播方式发送analysis_progress事件")
        socketio.emit('analysis_progress', progress_manager.to_dict())
        
        # 阶段1: 文档解析
        logger.info(f"开始文档解析 - Task: {task_id}")
        progress_manager.update_stage_progress("document_parsing", 10)
        
        # 重新验证客户端ID
        client_id = validate_and_update_client_mapping(task_id)
        if not client_id:
            logger.error(f"❌ 无法获取有效的客户端ID，停止分析")
            return
        logger.info(f"🔧 [调试] 文档解析阶段 - 广播analysis_progress")
        socketio.emit('analysis_progress', progress_manager.to_dict())
        
        stage_result = run_stage_analysis("document_parsing", task_id, input_data)
        if not stage_result["success"]:
            progress_manager.set_error(stage_result["error"])
            client_id = validate_and_update_client_mapping(task_id)
            if client_id:
                socketio.emit('analysis_error', {
                    'task_id': task_id,
                    'stage': 'document_parsing',
                    'error': stage_result["error"],
                    'timestamp': datetime.now().isoformat()
                }, room=client_id)
            return
            
        progress_manager.complete_stage("document_parsing", stage_result["data"])
        input_data["document_parsing"] = stage_result["data"]
        
        # 存储中间结果到Redis
        save_stage_result_to_redis(task_id, "document_parsing", stage_result["data"])
        
        # 发送阶段完成和进度更新
        client_id = validate_and_update_client_mapping(task_id)
        if client_id:
            socketio.emit('stage_completed', {
                'task_id': task_id,
                'stage': 'document_parsing',
                'result': stage_result["data"],
                'timestamp': datetime.now().isoformat()
            }, room=client_id)
            socketio.emit('analysis_progress', progress_manager.to_dict(), room=client_id)
        logger.info(f"文档解析完成 - Task: {task_id}")
        
        # 阶段2: 内容分析
        logger.info(f"开始内容分析 - Task: {task_id}")
        progress_manager.update_stage_progress("content_analysis", 10)
        
        client_id = validate_and_update_client_mapping(task_id)
        if client_id:
            logger.info(f"📡 即将发送analysis_progress到客户端: {client_id}")
            logger.info(f"📊 进度数据: overall_progress={progress_manager.overall_progress}%")
            socketio.emit('analysis_progress', progress_manager.to_dict(), room=client_id)
            logger.info(f"✅ analysis_progress已发送到房间: {client_id}")
        
        stage_result = run_stage_analysis("content_analysis", task_id, input_data)
        if not stage_result["success"]:
            progress_manager.set_error(stage_result["error"])
            client_id = validate_and_update_client_mapping(task_id)
            if client_id:
                socketio.emit('analysis_error', {
                    'task_id': task_id,
                    'stage': 'content_analysis',
                    'error': stage_result["error"],
                    'timestamp': datetime.now().isoformat()
                }, room=client_id)
            return
            
        progress_manager.complete_stage("content_analysis", stage_result["data"])
        input_data["content_analysis"] = stage_result["data"]
        
        # 存储中间结果到Redis
        save_stage_result_to_redis(task_id, "content_analysis", stage_result["data"])
        
        # 发送阶段完成和进度更新
        client_id = validate_and_update_client_mapping(task_id)
        if client_id:
            socketio.emit('stage_completed', {
                'task_id': task_id,
                'stage': 'content_analysis',
                'result': stage_result["data"],
                'timestamp': datetime.now().isoformat()
            }, room=client_id)
            socketio.emit('analysis_progress', progress_manager.to_dict(), room=client_id)
        logger.info(f"内容分析完成 - Task: {task_id}")
        
        # 阶段3: AI智能分析
        logger.info(f"开始AI智能分析 - Task: {task_id}")
        progress_manager.update_stage_progress("ai_analysis", 10)
        
        client_id = validate_and_update_client_mapping(task_id)
        if client_id:
            socketio.emit('analysis_progress', progress_manager.to_dict(), room=client_id)
        
        stage_result = run_stage_analysis("ai_analysis", task_id, input_data)
        if not stage_result["success"]:
            progress_manager.set_error(stage_result["error"])
            client_id = validate_and_update_client_mapping(task_id)
            if client_id:
                socketio.emit('analysis_error', {
                    'task_id': task_id,
                    'stage': 'ai_analysis',
                    'error': stage_result["error"],
                    'timestamp': datetime.now().isoformat()
                }, room=client_id)
            return
            
        progress_manager.complete_stage("ai_analysis", stage_result["data"])
        
        # 存储最终结果到Redis
        save_stage_result_to_redis(task_id, "ai_analysis", stage_result["data"])
        save_final_result_to_redis(task_id, progress_manager.results)
        
        # 发送阶段完成和最终完成
        client_id = validate_and_update_client_mapping(task_id)
        if client_id:
            socketio.emit('stage_completed', {
                'task_id': task_id,
                'stage': 'ai_analysis',
                'result': stage_result["data"],
                'timestamp': datetime.now().isoformat()
            }, room=client_id)
            socketio.emit('analysis_progress', progress_manager.to_dict(), room=client_id)
            socketio.emit('analysis_completed', {
                'task_id': task_id,
                'results': progress_manager.results,
                'duration': progress_manager.end_time - progress_manager.start_time,
                'timestamp': datetime.now().isoformat()
            }, room=client_id)
            
            # 🔧 新架构：任务完成后自动断开任务级连接
            if client_id in connected_clients:
                client_info = connected_clients[client_id]
                if client_info.get('connection_type') == 'task' and client_info.get('task_id') == task_id:
                    logger.info(f"🏁 [任务完成] 准备断开任务级连接: {task_id}")
                    logger.info(f"   - Client ID: {client_id}")
                    logger.info(f"   - 连接类型: {client_info.get('connection_type')}")
                    
                    # 发送任务完成断开通知
                    socketio.emit('task_completed_disconnect', {
                        'task_id': task_id,
                        'message': '任务已完成，连接将断开',
                        'timestamp': datetime.now().isoformat()
                    }, room=client_id)
                    
                    # 延迟断开连接，确保消息发送完毕
                    def disconnect_task_connection():
                        try:
                            socketio.server.disconnect(client_id)
                            logger.info(f"✅ [任务完成] 已断开任务级连接: {task_id}")
                        except Exception as e:
                            logger.error(f"❌ [任务完成] 断开连接失败: {e}")
                    
                    # 3秒后断开连接
                    socketio.sleep(3)
                    disconnect_task_connection()
                    
        logger.info(f"AI智能分析完成 - Task: {task_id}")
        
    except Exception as e:
        logger.error(f"自动分析出错: {e}")
        if task_id in analysis_tasks:
            analysis_tasks[task_id].set_error(str(e))
        
        client_id = validate_and_update_client_mapping(task_id)
        if client_id:
            socketio.emit('analysis_error', {
                'task_id': task_id,
                'error': f'自动分析失败: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }, room=client_id)

def run_single_stage_analysis(task_id: str, stage: str, input_data: Dict[str, Any]):
    """运行单个阶段分析"""
    try:
        progress_manager = analysis_tasks[task_id]
        
        # 获取之前阶段的结果
        for prev_stage in ["document_parsing", "content_analysis"]:
            if prev_stage in progress_manager.results:
                input_data[prev_stage] = progress_manager.results[prev_stage]
        
        # 运行指定阶段
        stage_result = run_stage_analysis(stage, task_id, input_data)
        
        if stage_result["success"]:
            progress_manager.complete_stage(stage, stage_result["data"])
            save_stage_result_to_redis(task_id, stage, stage_result["data"])
            
            socketio.emit('stage_completed', {
                'task_id': task_id,
                'stage': stage,
                'result': stage_result["data"],
                'timestamp': datetime.now().isoformat()
            })
        else:
            progress_manager.set_error(stage_result["error"])
            socketio.emit('stage_error', {
                'task_id': task_id,
                'stage': stage,
                'error': stage_result["error"],
                'timestamp': datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"单阶段分析出错: {e}")
        socketio.emit('stage_error', {
            'task_id': task_id,
            'stage': stage,
            'error': f'阶段分析失败: {str(e)}',
            'timestamp': datetime.now().isoformat()
        })

def run_stage_analysis(stage: str, task_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """运行具体的阶段分析"""
    try:
        if stage == "document_parsing":
            return asyncio.run(document_parser.analyze(task_id, input_data))
        elif stage == "content_analysis":
            return asyncio.run(content_analyzer.analyze(task_id, input_data))
        elif stage == "ai_analysis":
            return asyncio.run(ai_analyzer.analyze(task_id, input_data))
        else:
            return {
                "success": False,
                "error": f"未知的分析阶段: {stage}"
            }
            
    except Exception as e:
        logger.error(f"阶段分析执行出错 - Stage: {stage}, Error: {e}")
        return {
            "success": False,
            "error": f"阶段{stage}执行失败: {str(e)}"
        }

def save_stage_result_to_redis(task_id: str, stage: str, result: Dict[str, Any]):
    """保存阶段结果到Redis"""
    if not redis_client:
        return
        
    try:
        key = f"analysis:{task_id}:{stage}"
        redis_client.setex(key, 3600 * 24, json.dumps(result, ensure_ascii=False))
        logger.info(f"阶段结果已保存到Redis - Task: {task_id}, Stage: {stage}")
    except Exception as e:
        logger.error(f"保存阶段结果到Redis失败: {e}")

def save_final_result_to_redis(task_id: str, results: Dict[str, Any]):
    """保存最终结果到Redis"""
    if not redis_client:
        return
        
    try:
        key = f"analysis:final:{task_id}"
        final_result = {
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "stages": results
        }
        redis_client.setex(key, 3600 * 24 * 7, json.dumps(final_result, ensure_ascii=False))
        logger.info(f"最终结果已保存到Redis - Task: {task_id}")
    except Exception as e:
        logger.error(f"保存最终结果到Redis失败: {e}")

def get_uploaded_file_info(task_id: str) -> Dict[str, Any]:
    """获取已上传文件的信息"""
    try:
        # 首先尝试从Redis获取文件信息
        if redis_client:
            try:
                file_info_key = f"file_upload:{task_id}"
                file_info_str = redis_client.get(file_info_key)
                if file_info_str:
                    file_info = json.loads(file_info_str)
                    logger.info(f"从Redis获取文件信息成功 - Task: {task_id}")
                    return file_info
            except Exception as e:
                logger.warning(f"从Redis获取文件信息失败: {e}")
        
        # 如果Redis中没有，尝试从文件系统查找
        import os
        import glob
        
        upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "temp")
        file_pattern = os.path.join(upload_dir, f"{task_id}_*")
        matching_files = glob.glob(file_pattern)
        
        if matching_files:
            file_path = matching_files[0]  # 取第一个匹配的文件
            file_name = os.path.basename(file_path).replace(f"{task_id}_", "")
            
            # 读取文件内容
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # 尝试以UTF-8解码，如果失败则返回原始字节
            try:
                file_content = file_content.decode('utf-8')
            except UnicodeDecodeError:
                file_content = file_content.decode('utf-8', errors='ignore')
            
            file_info = {
                'file_path': file_path,
                'file_content': file_content,
                'file_name': file_name,
                'task_id': task_id
            }
            
            logger.info(f"从文件系统获取文件信息成功 - Task: {task_id}, File: {file_name}")
            return file_info
        
        logger.error(f"未找到上传的文件 - Task: {task_id}")
        return None
        
    except Exception as e:
        logger.error(f"获取上传文件信息失败 - Task: {task_id}, Error: {e}")
        return None

@socketio.on('test_connection')
def handle_test_connection(data):
    """处理连接测试"""
    try:
        logger.info(f"收到连接测试: {data}")
        emit('test_response', {'status': 'success', 'message': '连接测试成功'})
    except Exception as e:
        logger.error(f"连接测试处理失败: {e}")

@socketio.on('get_status')
def handle_get_status():
    """获取服务器状态"""
    try:
        status = {
            'server_status': 'running',
            'connected_clients': len(connected_clients),
            'active_tasks': len(analysis_tasks),
            'redis_connected': redis_client is not None,
            'llm_available': volcano_client is not None,
            'available_stages': [stage["name"] for stage in ANALYSIS_STAGES],
            'timestamp': datetime.now().isoformat()
        }
        
        emit('server_status', status)
        
    except Exception as e:
        logger.error(f"获取服务器状态时出错: {e}")
        emit('error', {
            'error': f'获取状态失败: {str(e)}',
            'timestamp': datetime.now().isoformat()
        })

def create_app():
    """创建应用实例"""
    return app, socketio

if __name__ == '__main__':
    logger.info("启动WebSocket服务器...")
    socketio.run(app, host='0.0.0.0', port=8081, debug=True) 