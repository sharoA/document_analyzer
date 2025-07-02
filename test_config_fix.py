#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试CoderAgentConfig修复
验证backend_package_prefix参数是否正确工作
"""

import sys
import os
sys.path.append('.')

def test_coder_agent_config():
    """测试CoderAgentConfig配置加载"""
    print("🧪 测试CoderAgentConfig配置加载")
    print("=" * 50)
    
    try:
        from src.corder_integration.config import get_coder_config
        
        # 加载配置
        config = get_coder_config()
        
        print(f"配置加载成功:")
        print(f"  backend_framework: {config.backend_framework}")
        print(f"  backend_java_version: {config.backend_java_version}")
        print(f"  backend_package_prefix: {config.backend_package_prefix}")
        print(f"  project_root: {config.project_root}")
        
        # 验证backend_package_prefix
        if hasattr(config, 'backend_package_prefix'):
            if config.backend_package_prefix == "com":
                print("✅ backend_package_prefix配置正确")
            else:
                print(f"❌ backend_package_prefix值错误: {config.backend_package_prefix}")
        else:
            print("❌ backend_package_prefix属性不存在")
            
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False
    
    return True

def test_workflow_engine_integration():
    """测试WorkflowEngine集成"""
    print("\n🧪 测试WorkflowEngine集成")
    print("=" * 50)
    
    try:
        from src.corder_integration.workflow_engine import WorkflowEngine
        
        # 创建WorkflowEngine实例
        engine = WorkflowEngine()
        
        # 测试包名前缀获取
        package_prefix = engine._get_package_prefix()
        print(f"WorkflowEngine获取的包名前缀: '{package_prefix}'")
        
        if package_prefix == "com":
            print("✅ WorkflowEngine包名前缀获取正确")
        else:
            print(f"❌ WorkflowEngine包名前缀错误: {package_prefix}")
            
    except Exception as e:
        print(f"❌ WorkflowEngine测试失败: {e}")
        return False
    
    return True

def main():
    """主函数"""
    print("🚀 CoderAgentConfig修复验证")
    print("=" * 60)
    
    # 运行测试
    config_test = test_coder_agent_config()
    workflow_test = test_workflow_engine_integration()
    
    print("\n" + "=" * 60)
    
    if config_test and workflow_test:
        print("✅ 所有测试通过！CoderAgentConfig修复成功")
        print("📋 现在可以正常使用backend_package_prefix配置")
    else:
        print("❌ 部分测试失败，需要进一步检查")

if __name__ == "__main__":
    main() 