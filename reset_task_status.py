#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重置失败任务的状态
"""

import sqlite3

def reset_failed_tasks():
    """重置失败任务的状态为pending"""
    
    try:
        conn = sqlite3.connect('coding_agent_workflow.db')
        cursor = conn.cursor()
        
        # 查询当前失败的任务
        cursor.execute("SELECT task_id, task_type, status FROM execution_tasks WHERE status = 'failed'")
        failed_tasks = cursor.fetchall()
        
        print(f"📋 找到 {len(failed_tasks)} 个失败的任务:")
        for task_id, task_type, status in failed_tasks:
            print(f"  🔸 {task_id} ({task_type}) - {status}")
        
        if failed_tasks:
            # 重置失败任务为pending
            cursor.execute("UPDATE execution_tasks SET status = 'pending' WHERE status = 'failed'")
            conn.commit()
            
            print(f"\n✅ 已将 {len(failed_tasks)} 个失败任务重置为 pending 状态")
            
            # 验证重置结果
            cursor.execute("SELECT COUNT(*) FROM execution_tasks WHERE task_type IN ('git_extraction', 'git_clone') AND status = 'pending'")
            git_pending_count = cursor.fetchone()[0]
            print(f"🔍 当前pending状态的Git任务数量: {git_pending_count}")
            
        else:
            print("ℹ️ 没有失败的任务需要重置")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 重置任务状态失败: {e}")

if __name__ == "__main__":
    reset_failed_tasks() 