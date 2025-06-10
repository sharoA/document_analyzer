#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket连接和事件传输测试脚本
用于验证Socket.IO服务器是否正常工作
"""

import time
import socketio
import json
from datetime import datetime

# 创建Socket.IO客户端
sio = socketio.Client(
    logger=True,
    engineio_logger=True
)

# 存储接收到的事件
received_events = []

def log_event(event_name, data=None):
    """记录事件"""
    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    print(f"[{timestamp}] {event_name}: {data}")
    received_events.append({
        'timestamp': timestamp,
        'event': event_name,
        'data': data
    })

@sio.event
def connect():
    log_event("✅ 连接成功", f"Session ID: {sio.sid}")

@sio.event  
def disconnect():
    log_event("❌ 连接断开")

@sio.event
def connected(data):
    log_event("📨 收到连接确认", data)

@sio.event
def analysis_progress(data):
    log_event("📊 收到进度更新", {
        'task_id': data.get('task_id'),
        'overall_progress': data.get('overall_progress'),
        'status': data.get('status')
    })

@sio.event
def stage_completed(data):
    log_event("✅ 阶段完成", {
        'task_id': data.get('task_id'),
        'stage': data.get('stage')
    })

@sio.event
def analysis_completed(data):
    log_event("🎉 分析完成", {
        'task_id': data.get('task_id')
    })

@sio.event
def analysis_error(data):
    log_event("❌ 分析错误", data)

@sio.event
def task_binding_confirmed(data):
    log_event("🔗 任务绑定确认", data)

@sio.event
def task_binding_error(data):
    log_event("❌ 任务绑定错误", data)

# 捕获所有事件
@sio.on('*')
def catch_all(event, data):
    if event not in ['connect', 'disconnect']:
        log_event(f"🎯 捕获事件: {event}", data)

def test_websocket_connection():
    """测试WebSocket连接"""
    print("🚀 开始WebSocket连接测试...")
    print("=" * 60)
    
    try:
        # 连接到WebSocket服务器
        print("📡 正在连接到 ws://localhost:8081...")
        sio.connect('http://localhost:8081', transports=['websocket'])
        
        print(f"✅ 连接成功！Session ID: {sio.sid}")
        
        # 等待一段时间接收事件
        print("⏰ 等待5秒接收事件...")
        time.sleep(5)
        
        # 测试获取当前任务进度
        print("📋 测试获取任务进度...")
        test_task_id = "05056589-87ad-4d73-aa40-cf22a5fc9743"  # 从日志中获取的任务ID
        
        sio.emit('get_analysis_progress', {
            'task_id': test_task_id
        })
        
        print(f"📤 已发送进度查询请求，任务ID: {test_task_id}")
        
        # 等待响应
        print("⏰ 等待10秒接收进度响应...")
        time.sleep(10)
        
        # 测试任务绑定
        print("🔗 测试任务绑定...")
        sio.emit('establish_task_binding', {
            'task_id': test_task_id,
            'session_id': sio.sid,
            'action': 'strong_binding'
        })
        
        print("📤 已发送任务绑定请求")
        
        # 再次等待
        print("⏰ 等待5秒接收绑定响应...")
        time.sleep(5)
        
        # 再次查询进度
        print("📋 再次查询任务进度...")
        sio.emit('get_analysis_progress', {
            'task_id': test_task_id
        })
        
        # 最后等待
        print("⏰ 最后等待10秒...")
        time.sleep(10)
        
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False
    
    finally:
        # 断开连接
        print("🔌 断开连接...")
        sio.disconnect()
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    print(f"📨 总共接收到 {len(received_events)} 个事件")
    
    if received_events:
        print("\n📋 事件列表:")
        for event in received_events:
            print(f"  [{event['timestamp']}] {event['event']}")
            if event['data']:
                print(f"    数据: {json.dumps(event['data'], ensure_ascii=False, indent=6)}")
    else:
        print("❌ 没有接收到任何事件！")
    
    # 检查关键事件
    progress_events = [e for e in received_events if e['event'] == '📊 收到进度更新']
    binding_events = [e for e in received_events if e['event'] == '🔗 任务绑定确认']
    
    print(f"\n🔍 关键事件统计:")
    print(f"  📊 进度更新事件: {len(progress_events)}")
    print(f"  🔗 任务绑定事件: {len(binding_events)}")
    
    if progress_events:
        print("✅ WebSocket进度事件传输正常")
        return True
    else:
        print("❌ WebSocket进度事件传输异常")
        return False

def test_frontend_simulation():
    """模拟前端WebSocket连接测试"""
    print("\n🎭 模拟前端连接测试...")
    print("=" * 60)
    
    # 使用前端相同的连接配置
    frontend_sio = socketio.Client(
        logger=False,
        engineio_logger=False
    )
    
    frontend_events = []
    
    def log_frontend_event(event_name, data=None):
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        print(f"[前端] [{timestamp}] {event_name}")
        if data and 'overall_progress' in str(data):
            print(f"       进度: {data.get('overall_progress', 'N/A')}%")
        frontend_events.append({'event': event_name, 'data': data})
    
    @frontend_sio.event
    def connect():
        log_frontend_event("连接成功")
    
    @frontend_sio.event  
    def analysis_progress(data):
        log_frontend_event("收到analysis_progress事件", data)
    
    @frontend_sio.on('*')
    def catch_all_frontend(event, data):
        if event not in ['connect', 'disconnect', 'pong']:
            log_frontend_event(f"收到事件: {event}", data)
    
    try:
        # 使用前端相同的连接参数
        frontend_sio.connect('http://localhost:8081', 
                           transports=['websocket'],
                           timeout=20)
        
        print(f"✅ 前端模拟连接成功！Session ID: {frontend_sio.sid}")
        
        # 立即绑定任务
        test_task_id = "05056589-87ad-4d73-aa40-cf22a5fc9743"
        print("🔗 立即绑定任务...")
        
        frontend_sio.emit('establish_task_binding', {
            'task_id': test_task_id,
            'session_id': frontend_sio.sid,
            'action': 'strong_binding'
        })
        
        # 等待绑定确认
        time.sleep(2)
        
        # 查询进度
        print("📋 查询当前进度...")
        frontend_sio.emit('get_analysis_progress', {
            'task_id': test_task_id
        })
        
        # 等待事件
        print("⏰ 等待15秒接收事件...")
        time.sleep(15)
        
        print(f"\n📊 前端模拟测试结果: 接收到 {len(frontend_events)} 个事件")
        for event in frontend_events:
            print(f"  - {event['event']}")
            
    except Exception as e:
        print(f"❌ 前端模拟连接失败: {e}")
    
    finally:
        frontend_sio.disconnect()

if __name__ == "__main__":
    print("🧪 WebSocket连接和事件传输测试")
    print("目标服务器: ws://localhost:8081")
    print("测试时间:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("=" * 60)
    
    # 执行基础连接测试
    basic_test_passed = test_websocket_connection()
    
    # 执行前端模拟测试
    test_frontend_simulation()
    
    print("\n" + "=" * 60)
    if basic_test_passed:
        print("🎉 WebSocket服务器工作正常！")
        print("💡 如果前端仍然没有响应，问题可能在前端代码逻辑。")
    else:
        print("❌ WebSocket服务器可能存在问题！")
        print("�� 请检查后端服务是否正常运行。") 