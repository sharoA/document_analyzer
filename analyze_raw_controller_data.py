#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析Java分析器返回的原始数据结构，查找Controller详细信息
"""

import sys
import os
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, '/Users/renyu/Documents/ai_project/document_analyzer')

from src.utils.java_code_analyzer import JavaCodeAnalyzer

def analyze_raw_java_data():
    """分析Java分析器返回的原始数据结构"""
    print("🔍 分析Java分析器原始数据结构")
    print("=" * 60)
    
    # 测试路径
    test_path = "/Users/renyu/Documents/create_project/链数中建一局_1753077194/crcl-open/crcl-open/src/main/java/com/yljr/crcl/limit"
    
    print(f"📁 分析路径: {test_path}")
    
    # 创建分析器
    analyzer = JavaCodeAnalyzer()
    
    try:
        # 执行分析
        result = analyzer.analyze_project(test_path)
        
        print(f"\n📊 原始分析结果的顶级键:")
        for key in result.keys():
            print(f"   {key}")
        
        # 检查java_files中的Controller信息
        java_files = result.get('java_files', [])
        controller_files = []
        
        print(f"\n🔍 在{len(java_files)}个Java文件中查找Controller:")
        
        for file_info in java_files:
            file_path = file_info.get('file_path', '')
            if 'Controller' in file_path:
                controller_files.append(file_info)
        
        print(f"   找到{len(controller_files)}个Controller文件")
        
        # 分析前3个Controller文件的详细结构
        for i, ctrl_file in enumerate(controller_files[:3]):
            print(f"\n📋 Controller {i+1}: {Path(ctrl_file['file_path']).name}")
            print(f"   文件路径: {ctrl_file.get('file_path')}")
            print(f"   包名: {ctrl_file.get('package')}")
            print(f"   导入: {len(ctrl_file.get('imports', []))}个")
            print(f"   注解: {ctrl_file.get('annotations_used', [])}")
            print(f"   类数量: {len(ctrl_file.get('classes', []))}")
            
            # 详细分析类信息
            for j, class_info in enumerate(ctrl_file.get('classes', [])):
                print(f"     类{j+1}: {class_info.get('name')}")
                print(f"       类注解: {class_info.get('annotations', [])}")
                print(f"       继承: {class_info.get('extends')}")
                print(f"       方法数: {len(class_info.get('methods', []))}")
                
                # 显示前3个方法
                methods = class_info.get('methods', [])
                for k, method in enumerate(methods[:3]):
                    print(f"         方法{k+1}: {method.get('name')}")
                    print(f"           注解: {method.get('annotations', [])}")
                    print(f"           返回类型: {method.get('return_type')}")
                    print(f"           参数: {len(method.get('parameters', []))}个")
        
        return True
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = analyze_raw_java_data()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 原始数据分析完成！")
    else:
        print("❌ 原始数据分析失败！")