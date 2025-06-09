#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis 使用示例
展示如何在项目中使用配置好的 Redis 缓存功能
"""

import logging
import time
from datetime import datetime, timedelta
try:
    from .redis_util import (
        get_redis_manager,
        get_redis_client,
        test_redis_connection,
        cache_set,
        cache_get,
        cache_delete,
        cache_exists
    )
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    import sys
    import os
    # 添加项目根目录到 Python 路径
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, project_root)
    from src.utils.redis_util import (
        get_redis_manager,
        get_redis_client,
        test_redis_connection,
        cache_set,
        cache_get,
        cache_delete,
        cache_exists
    )

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def example_basic_cache_operations():
    """基本缓存操作示例"""
    print("=== 基本缓存操作示例 ===")
    
    # 1. 测试连接
    if not test_redis_connection():
        print("❌ Redis 连接失败")
        return
    
    # 2. 使用便捷函数进行缓存操作
    cache_key = "user_profile"
    user_data = {
        "user_id": 12345,
        "username": "john_doe",
        "email": "john@example.com",
        "last_login": datetime.now().isoformat(),
        "preferences": {
            "theme": "dark",
            "language": "zh-CN"
        }
    }
    
    # 设置缓存（默认1小时过期）
    if cache_set(cache_key, user_data):
        print(f"✅ 缓存设置成功: {cache_key}")
    
    # 获取缓存
    cached_data = cache_get(cache_key)
    if cached_data:
        print(f"✅ 缓存获取成功: {cached_data['username']}")
    
    # 检查缓存是否存在
    if cache_exists(cache_key):
        print(f"✅ 缓存存在: {cache_key}")
    
    # 删除缓存
    if cache_delete(cache_key):
        print(f"✅ 缓存删除成功: {cache_key}")

def example_advanced_cache_operations():
    """高级缓存操作示例"""
    print("\n=== 高级缓存操作示例 ===")
    
    manager = get_redis_manager()
    
    # 1. 设置不同过期时间的缓存
    short_term_key = "session_token"
    long_term_key = "user_settings"
    
    # 短期缓存（5分钟）
    session_data = {
        "token": "abc123xyz",
        "expires_at": (datetime.now() + timedelta(minutes=5)).isoformat()
    }
    manager.set(short_term_key, session_data, ttl=300)  # 5分钟
    print(f"✅ 短期缓存设置成功: {short_term_key} (5分钟)")
    
    # 长期缓存（24小时）
    settings_data = {
        "notifications": True,
        "auto_save": True,
        "theme": "light"
    }
    manager.set(long_term_key, settings_data, ttl=86400)  # 24小时
    print(f"✅ 长期缓存设置成功: {long_term_key} (24小时)")
    
    # 2. 检查TTL
    short_ttl = manager.get_ttl(short_term_key)
    long_ttl = manager.get_ttl(long_term_key)
    print(f"⏰ {short_term_key} 剩余时间: {short_ttl} 秒")
    print(f"⏰ {long_term_key} 剩余时间: {long_ttl} 秒")
    
    # 3. 延长过期时间
    if manager.expire(short_term_key, 600):  # 延长到10分钟
        print(f"✅ 延长过期时间成功: {short_term_key}")
        new_ttl = manager.get_ttl(short_term_key)
        print(f"⏰ 新的剩余时间: {new_ttl} 秒")

def example_file_analysis_cache():
    """文件分析结果缓存示例"""
    print("\n=== 文件分析结果缓存示例 ===")
    
    manager = get_redis_manager()
    
    # 模拟文件分析结果
    file_hash = "abc123def456"
    analysis_result = {
        "file_name": "requirements.txt",
        "file_type": "text",
        "analysis_type": "content_analysis",
        "result": {
            "crud_operations": [
                {"type": "CREATE", "entity": "User", "description": "创建用户"},
                {"type": "READ", "entity": "User", "description": "查询用户信息"},
                {"type": "UPDATE", "entity": "User", "description": "更新用户资料"},
                {"type": "DELETE", "entity": "User", "description": "删除用户"}
            ],
            "business_requirements": [
                "用户注册功能",
                "用户登录验证",
                "用户信息管理"
            ]
        },
        "analyzed_at": datetime.now().isoformat(),
        "processing_time": 2.5
    }
    
    # 缓存分析结果（2小时）
    cache_key = f"analysis_result:{file_hash}"
    if manager.set(cache_key, analysis_result, ttl=7200):
        print(f"✅ 文件分析结果缓存成功: {file_hash}")
    
    # 获取缓存的分析结果
    cached_result = manager.get(cache_key)
    if cached_result:
        print(f"✅ 获取缓存的分析结果:")
        print(f"   文件名: {cached_result['file_name']}")
        print(f"   CRUD操作数: {len(cached_result['result']['crud_operations'])}")
        print(f"   业务需求数: {len(cached_result['result']['business_requirements'])}")
        print(f"   处理时间: {cached_result['processing_time']} 秒")

def example_session_management():
    """会话管理示例"""
    print("\n=== 会话管理示例 ===")
    
    manager = get_redis_manager()
    
    # 模拟用户会话
    session_id = "sess_abc123xyz"
    user_session = {
        "user_id": 12345,
        "username": "john_doe",
        "login_time": datetime.now().isoformat(),
        "last_activity": datetime.now().isoformat(),
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    # 设置会话（30分钟过期）
    session_key = f"session:{session_id}"
    if manager.set(session_key, user_session, ttl=1800):
        print(f"✅ 用户会话创建成功: {session_id}")
    
    # 模拟会话活动更新
    time.sleep(1)  # 模拟时间流逝
    
    # 更新最后活动时间
    if manager.exists(session_key):
        session_data = manager.get(session_key)
        session_data["last_activity"] = datetime.now().isoformat()
        
        # 重新设置会话，刷新过期时间
        if manager.set(session_key, session_data, ttl=1800):
            print(f"✅ 会话活动时间更新成功")
    
    # 获取会话信息
    current_session = manager.get(session_key)
    if current_session:
        print(f"👤 当前会话用户: {current_session['username']}")
        print(f"🕐 登录时间: {current_session['login_time']}")
        print(f"🕐 最后活动: {current_session['last_activity']}")

def example_cache_statistics():
    """缓存统计示例"""
    print("\n=== 缓存统计示例 ===")
    
    manager = get_redis_manager()
    
    # 获取 Redis 服务器信息
    info = manager.get_info()
    
    print(f"📊 Redis 服务器统计:")
    print(f"   版本: {info.get('redis_version', 'unknown')}")
    print(f"   运行时间: {info.get('uptime_in_seconds', 0)} 秒")
    print(f"   已用内存: {info.get('used_memory_human', 'unknown')}")
    print(f"   峰值内存: {info.get('used_memory_peak_human', 'unknown')}")
    print(f"   连接数: {info.get('connected_clients', 0)}")
    print(f"   总命令数: {info.get('total_commands_processed', 0)}")
    print(f"   键空间命中率: {info.get('keyspace_hits', 0) / max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0), 1) * 100:.2f}%")

def example_cleanup():
    """清理示例数据"""
    print("\n=== 清理示例数据 ===")
    
    manager = get_redis_manager()
    
    # 清理所有带项目前缀的缓存
    deleted_count = manager.clear_cache()
    print(f"🗑️  清理了 {deleted_count} 个缓存项")

if __name__ == "__main__":
    try:
        # 运行所有示例
        example_basic_cache_operations()
        example_advanced_cache_operations()
        example_file_analysis_cache()
        example_session_management()
        example_cache_statistics()
        
        # 询问是否清理数据
        cleanup = input("\n是否清理示例数据? (y/N): ").lower().strip()
        if cleanup == 'y':
            example_cleanup()
            
    except Exception as e:
        logger.error(f"Redis 示例运行失败: {e}")
        print(f"❌ Redis 示例运行失败: {e}")
    
    print("\n✅ Redis 示例运行完成！") 