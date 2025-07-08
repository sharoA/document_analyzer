#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Git克隆
"""

import subprocess
import os
from pathlib import Path

def test_git_clone():
    """测试Git克隆两个仓库"""
    
    repos = [
        {
            'name': 'zqyl-user-center-service',
            'url': 'https://gitlab.local/zqyl/zqyl-user-center-service.git',
            'target': r'D:\gitlab\test_clone\zqyl-user-center-service'
        },
        {
            'name': 'crcl-open', 
            'url': 'http://gitlab.local/ls/crcl-open.git',
            'target': r'D:\gitlab\test_clone\crcl-open'
        }
    ]
    
    for repo in repos:
        print(f"\n🔍 测试克隆仓库: {repo['name']}")
        print(f"   URL: {repo['url']}")
        print(f"   目标: {repo['target']}")
        
        # 确保目标目录不存在
        if os.path.exists(repo['target']):
            print(f"   ⚠️ 目标目录已存在，跳过: {repo['target']}")
            continue
        
        # 确保父目录存在
        Path(repo['target']).parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # 执行git clone，指定编码
            result = subprocess.run(
                ["git", "clone", repo['url'], repo['target']],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=60
            )
            
            if result.returncode == 0:
                print(f"   ✅ 克隆成功")
                print(f"   输出: {result.stdout.strip()}")
                
                # 检查目录是否存在
                if os.path.exists(repo['target']):
                    file_count = len(list(Path(repo['target']).rglob('*')))
                    print(f"   📁 目录创建成功，包含 {file_count} 个文件/目录")
                else:
                    print(f"   ❌ 目录未创建: {repo['target']}")
            else:
                print(f"   ❌ 克隆失败 (exit code: {result.returncode})")
                print(f"   错误: {result.stderr}")
                print(f"   输出: {result.stdout}")
                
        except subprocess.TimeoutExpired:
            print(f"   ⏰ 克隆超时 (60秒)")
        except Exception as e:
            print(f"   💥 异常: {e}")

if __name__ == "__main__":
    test_git_clone() 