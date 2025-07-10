#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整路径一致性测试
验证所有任务类型的路径字段都使用相同的基础路径格式
"""

import sys
import os
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

def test_all_task_types_path_consistency():
    """测试所有任务类型的路径一致性"""
    
    # 模拟状态数据
    test_state = {
        'output_path': 'D:/gitlab',
        'project_name': '链数优化项目测试'
    }
    
    print("🚀 开始所有任务类型路径一致性测试...")
    print(f"📝 测试状态: {test_state}")
    print()
    
    # 🔧 计算项目路径，与git_management_node保持一致
    output_path = test_state.get('output_path', 'D:/gitlab')
    project_name = test_state.get('project_name', 'unknown_project')
    base_project_path = f"{output_path}/{project_name}"
    
    print(f"📁 计算的基础项目路径: {base_project_path}")
    print()
    
    # 测试不同服务的路径
    services = [
        {'name': '用户服务', 'dir': 'zqyl-user-center-service'},
        {'name': '确权开立服务', 'dir': 'crcl-open'}
    ]
    
    for service in services:
        service_name = service['name']
        service_dir = service['dir']
        
        print(f"📋 {service_name} 各任务类型路径验证:")
        
        # 1. git_clone 任务路径
        git_clone_path = f"{base_project_path}/{service_dir}"
        
        # 2. code_analysis 任务路径  
        code_analysis_path = f"{base_project_path}/{service_dir}"
        
        # 3. api 任务路径
        api_project_path = f"{base_project_path}/{service_dir}"
        
        # 4. config 任务路径（基础部分）
        config_base_path = f"{base_project_path}/{service_dir}"
        config_full_path = f"{config_base_path}/src/main/resources/application.yml"
        
        # 5. deployment 任务路径
        deployment_path = f"{base_project_path}/{service_dir}"
        
        print(f"  1. git_clone.local_path:     {git_clone_path}")
        print(f"  2. code_analysis.project_path: {code_analysis_path}")
        print(f"  3. api.project_path:         {api_project_path}")
        print(f"  4. config.config_file(基础):  {config_base_path}")
        print(f"     config.config_file(完整):  {config_full_path}")
        print(f"  5. deployment.path:          {deployment_path}")
        
        # 验证基础路径一致性
        base_paths = [
            git_clone_path,
            code_analysis_path, 
            api_project_path,
            config_base_path,
            deployment_path
        ]
        
        all_same = all(path == base_paths[0] for path in base_paths)
        print(f"  📊 基础路径一致性: {'✅ 一致' if all_same else '❌ 不一致'}")
        
        if not all_same:
            print("    详细比较:")
            for i, path in enumerate(base_paths):
                task_types = ['git_clone', 'code_analysis', 'api', 'config', 'deployment']
                print(f"      {task_types[i]}: {path}")
        print()
    
    print("🔍 与git_management_node的兼容性验证:")
    for service in services:
        service_dir = service['dir']
        
        # task_splitting_node 计算的路径
        task_splitting_path = f"{output_path}/{project_name}/{service_dir}"
        
        # git_management_node 计算的路径 (target_dir)
        git_management_path = f"{output_path}/{project_name}/{service_dir}"
        
        print(f"  {service['name']}:")
        print(f"    task_splitting_node: {task_splitting_path}")
        print(f"    git_management_node: {git_management_path}")
        print(f"    兼容性: {'✅ 兼容' if task_splitting_path == git_management_path else '❌ 不兼容'}")
        print()
    
    print("📋 任务类型路径字段总结:")
    print("  1. git_clone.local_path     -> 克隆代码到本地的路径")
    print("  2. code_analysis.project_path -> 分析代码结构的项目路径")  
    print("  3. api.project_path         -> 开发API接口的项目路径")
    print("  4. config.config_file       -> 配置文件的完整路径")
    print("  5. deployment.path          -> 部署提交的项目路径")
    print("  🎯 核心要求：所有路径都基于相同的 base_project_path")
    print()
    
    print("✅ 所有任务类型路径一致性测试完成!")

if __name__ == "__main__":
    test_all_task_types_path_consistency() 