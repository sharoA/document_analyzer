#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看LangGraph SQLite数据库内容
"""

import sqlite3
import json

def check_database():
    """查看数据库内容"""
    try:
        conn = sqlite3.connect('coding_agent_workflow.db')
        cursor = conn.cursor()
        
        # 查看所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("🗄️ 数据库表:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # 查看每个表的内容
        for table in tables:
            table_name = table[0]
            print(f"\n📋 表 '{table_name}' 的内容:")
            
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
            rows = cursor.fetchall()
            
            if rows:
                # 获取列名
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = [col[1] for col in cursor.fetchall()]
                print(f"  列: {columns}")
                
                for i, row in enumerate(rows):
                    print(f"  行 {i+1}: {row}")
            else:
                print("  (空表)")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 查看数据库失败: {e}")

if __name__ == "__main__":
    check_database() 