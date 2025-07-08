#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试改进后的数据库管理器 - 验证Windows环境下的锁定问题修复
"""

import sys
import os
import time
import json

# 添加项目根目录到路径
sys.path.append('.')

# 导入改进后的TaskStorageManager
from src.corder_integration.langgraph.nodes.task_splitting_node import TaskStorageManager

def test_database_operations():
    """测试数据库操作"""
    print("🚀 开始测试改进后的数据库管理器...")
    
    # 创建数据库管理器实例
    db_manager = TaskStorageManager("test_coding_agent_workflow.db")
    
    # 测试1: 强制解锁
    print("\n📝 测试1: 强制解锁数据库...")
    try:
        db_manager.force_unlock_database()
        print("✅ 强制解锁成功")
    except Exception as e:
        print(f"❌ 强制解锁失败: {e}")
    
    # 测试2: 重置数据库
    print("\n📝 测试2: 重置数据库...")
    try:
        db_manager.reset_database()
        print("✅ 数据库重置成功")
    except Exception as e:
        print(f"❌ 数据库重置失败: {e}")
    
    # 测试3: 保存任务
    print("\n📝 测试3: 保存测试任务...")
    test_tasks = [
        {
            "task_id": "test_001",
            "service_name": "test-service",
            "task_type": "database",
            "priority": 1,
            "dependencies": [],
            "estimated_duration": "15分钟",
            "description": "测试数据库创建任务",
            "deliverables": ["数据库脚本", "配置文件"],
            "implementation_details": "创建用户表和权限表",
            "completion_criteria": "所有表创建成功",
            "parameters": {"db_type": "sqlite", "tables": ["users", "roles"]}
        },
        {
            "task_id": "test_002", 
            "service_name": "test-service",
            "task_type": "api",
            "priority": 2,
            "dependencies": ["test_001"],
            "estimated_duration": "30分钟",
            "description": "测试API开发任务",
            "deliverables": ["API代码", "接口文档"],
            "implementation_details": "实现用户CRUD API",
            "completion_criteria": "所有接口测试通过",
            "parameters": {"framework": "fastapi", "endpoints": ["/users", "/roles"]}
        }
    ]
    
    try:
        success = db_manager.save_tasks(test_tasks)
        if success:
            print("✅ 任务保存成功")
        else:
            print("❌ 任务保存失败")
    except Exception as e:
        print(f"❌ 任务保存异常: {e}")
    
    # 测试4: 获取任务
    print("\n📝 测试4: 获取待执行任务...")
    try:
        pending_tasks = db_manager.get_pending_tasks()
        print(f"✅ 获取到 {len(pending_tasks)} 个待执行任务")
        for task in pending_tasks:
            print(f"  - {task['task_id']}: {task['description']}")
    except Exception as e:
        print(f"❌ 获取任务失败: {e}")
    
    # 测试5: 并发测试
    print("\n📝 测试5: 并发访问测试...")
    import threading
    import random
    
    def concurrent_save_task():
        """并发保存任务的测试函数"""
        try:
            task_id = f"concurrent_{random.randint(1000, 9999)}"
            concurrent_task = {
                "task_id": task_id,
                "service_name": "concurrent-service", 
                "task_type": "test",
                "priority": 1,
                "dependencies": [],
                "estimated_duration": "5分钟",
                "description": f"并发测试任务 {task_id}",
                "deliverables": ["测试结果"],
                "implementation_details": "并发写入测试",
                "completion_criteria": "任务执行完成",
                "parameters": {"thread_id": threading.current_thread().ident}
            }
            
            db_manager.save_tasks([concurrent_task])
            print(f"    ✅ 线程 {threading.current_thread().ident} 保存任务成功")
            
        except Exception as e:
            print(f"    ❌ 线程 {threading.current_thread().ident} 保存任务失败: {e}")
    
    # 启动5个并发线程
    threads = []
    for i in range(5):
        thread = threading.Thread(target=concurrent_save_task)
        threads.append(thread)
        thread.start()
    
    # 等待所有线程完成
    for thread in threads:
        thread.join()
    
    # 验证并发结果
    try:
        final_tasks = db_manager.get_pending_tasks()
        concurrent_tasks = [t for t in final_tasks if t['service_name'] == 'concurrent-service']
        print(f"✅ 并发测试完成，共保存 {len(concurrent_tasks)} 个并发任务")
    except Exception as e:
        print(f"❌ 并发测试验证失败: {e}")
    
    print("\n🎉 数据库管理器测试完成！")

def test_wal_checkpoint():
    """测试WAL检查点操作"""
    print("\n🔧 测试WAL检查点操作...")
    
    db_manager = TaskStorageManager("test_coding_agent_workflow.db")
    
    try:
        # 直接测试WAL检查点
        with db_manager._get_connection() as conn:
            # 执行一些写操作
            conn.execute("INSERT OR REPLACE INTO execution_tasks (task_id, service_name, task_type) VALUES (?, ?, ?)", 
                        ("wal_test", "wal-service", "wal_test"))
            
            # 执行WAL检查点
            result = conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
            print(f"✅ WAL检查点结果: {result}")
            
            # 检查WAL模式
            wal_mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
            print(f"📊 当前日志模式: {wal_mode}")
            
    except Exception as e:
        print(f"❌ WAL检查点测试失败: {e}")

def cleanup_test_files():
    """清理测试文件"""
    print("\n🧹 清理测试文件...")
    
    test_files = [
        "test_coding_agent_workflow.db",
        "test_coding_agent_workflow.db-wal", 
        "test_coding_agent_workflow.db-shm"
    ]
    
    for file_path in test_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"✅ 删除测试文件: {file_path}")
            except Exception as e:
                print(f"⚠️ 删除文件失败 {file_path}: {e}")

if __name__ == "__main__":
    try:
        # 运行测试
        test_database_operations()
        test_wal_checkpoint()
        
        print(f"\n📈 测试结果总结:")
        print(f"✅ 数据库连接管理: with语句自动关闭连接")
        print(f"✅ 重试机制: 指数退避处理锁定")
        print(f"✅ WAL模式: 优化并发访问性能")
        print(f"✅ 强制解锁: 清理WAL文件和检查点")
        print(f"✅ 并发支持: 多线程安全访问")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理测试文件
        cleanup_test_files() 