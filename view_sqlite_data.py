#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite数据库查看工具
用于查看tasks.db中的所有数据
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional
import os

def connect_db(db_path: str = "tasks.db"):
    """连接数据库"""
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return None
    return sqlite3.connect(db_path)

def show_tables(conn):
    """显示所有表"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("📋 数据库中的表:")
    for table in tables:
        print(f"  • {table[0]}")
    return [table[0] for table in tables]

def show_table_structure(conn, table_name):
    """显示表结构"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    print(f"\n🏗️ 表 '{table_name}' 的结构:")
    for col in columns:
        print(f"  • {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'}")

def show_tasks_overview(conn):
    """显示任务概览"""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM tasks;")
    total_tasks = cursor.fetchone()[0]
    
    cursor.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status;")
    status_counts = cursor.fetchall()
    
    print(f"\n📊 任务概览:")
    print(f"  总任务数: {total_tasks}")
    for status, count in status_counts:
        print(f"  {status}: {count}")

def show_all_tasks(conn, limit: int = 10):
    """显示所有任务"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, filename, status, progress, created_at, 
               CASE 
                   WHEN markdown_content IS NOT NULL THEN '有' 
                   ELSE '无' 
               END as has_markdown
        FROM tasks 
        ORDER BY created_at DESC 
        LIMIT ?
    """, (limit,))
    
    tasks = cursor.fetchall()
    print(f"\n📝 最近 {limit} 个任务:")
    print("-" * 100)
    print(f"{'任务ID':<20} {'文件名':<30} {'状态':<10} {'进度':<6} {'创建时间':<20} {'Markdown':<8}")
    print("-" * 100)
    
    for task in tasks:
        task_id = task[0][:18] + "..." if len(task[0]) > 18 else task[0]
        filename = task[1][:28] + "..." if len(task[1]) > 28 else task[1]
        print(f"{task_id:<20} {filename:<30} {task[2]:<10} {task[3]:<6} {task[4]:<20} {task[5]:<8}")

def show_markdown_content(conn, task_id: Optional[str] = None):
    """显示Markdown内容"""
    cursor = conn.cursor()
    
    if task_id:
        cursor.execute("SELECT id, filename, markdown_content FROM tasks WHERE id = ?", (task_id,))
        tasks = cursor.fetchall()
    else:
        cursor.execute("SELECT id, filename, markdown_content FROM tasks WHERE markdown_content IS NOT NULL")
        tasks = cursor.fetchall()
    
    if not tasks:
        print("❌ 没有找到包含Markdown内容的任务")
        return
    
    for task in tasks:
        print(f"\n📄 任务: {task[0]}")
        print(f"📁 文件: {task[1]}")
        print(f"📝 Markdown内容:")
        print("-" * 80)
        if task[2]:
            # 截取前500字符预览
            content = task[2]
            if len(content) > 500:
                print(content[:500] + "\n...(内容被截断)")
            else:
                print(content)
        else:
            print("(空内容)")
        print("-" * 80)

def interactive_menu():
    """交互式菜单"""
    conn = connect_db()
    if not conn:
        return
    
    try:
        while True:
            print("\n" + "="*60)
            print("🗃️  SQLite数据库查看工具")
            print("="*60)
            print("1. 显示表结构")
            print("2. 任务概览")
            print("3. 查看所有任务")
            print("4. 查看Markdown内容")
            print("5. 查看特定任务的Markdown")
            print("6. 执行自定义SQL查询")
            print("0. 退出")
            print("-"*60)
            
            choice = input("请选择操作 (0-6): ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                tables = show_tables(conn)
                for table in tables:
                    show_table_structure(conn, table)
            elif choice == "2":
                show_tasks_overview(conn)
            elif choice == "3":
                limit = input("显示多少个任务 (默认10): ").strip()
                limit = int(limit) if limit.isdigit() else 10
                show_all_tasks(conn, limit)
            elif choice == "4":
                show_markdown_content(conn)
            elif choice == "5":
                task_id = input("请输入任务ID: ").strip()
                if task_id:
                    show_markdown_content(conn, task_id)
            elif choice == "6":
                sql = input("请输入SQL查询: ").strip()
                try:
                    cursor = conn.cursor()
                    cursor.execute(sql)
                    results = cursor.fetchall()
                    print(f"查询结果 ({len(results)} 行):")
                    for row in results:
                        print(row)
                except Exception as e:
                    print(f"❌ SQL执行错误: {e}")
            else:
                print("❌ 无效选择，请重新输入")
                
    except KeyboardInterrupt:
        print("\n👋 退出程序")
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 启动SQLite数据库查看工具...")
    interactive_menu() 