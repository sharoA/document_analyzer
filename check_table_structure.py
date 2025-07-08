#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

def check_table_structure():
    conn = sqlite3.connect('coding_agent_workflow.db')
    cursor = conn.cursor()
    
    # 获取表结构
    cursor.execute('PRAGMA table_info(execution_tasks)')
    columns = cursor.fetchall()
    print('execution_tasks表完整结构:')
    for i, col in enumerate(columns):
        print(f'  {i}: {col[1]} ({col[2]}) - 非空: {bool(col[3])} - 默认值: {col[4]} - 主键: {bool(col[5])}')
    
    # 查看表的创建语句
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='execution_tasks'")
    create_sql = cursor.fetchone()
    if create_sql:
        print(f'\n表创建语句:\n{create_sql[0]}')
    else:
        print('\n未找到表创建语句')
    
    # 检查一些示例数据
    cursor.execute('SELECT * FROM execution_tasks LIMIT 3')
    rows = cursor.fetchall()
    print(f'\n示例数据 (前3行):')
    for i, row in enumerate(rows):
        print(f'  行{i}: {row}')
    
    conn.close()

if __name__ == "__main__":
    check_table_structure() 