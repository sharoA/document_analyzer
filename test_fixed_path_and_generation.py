#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试修复后的路径选择和Service接口生成功能
"""

import json
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.apis.project_analysis_api import ProjectAnalysisAPI
from src.corder_integration.langgraph.nodes.intelligent_coding_node import IntelligentCodingAgent
from src.utils.logger_config import setup_logger

# 配置日志
logger = setup_logger(__name__)

def test_path_priority_fix():
    """测试修复后的路径优先级计算"""
    
    print("🧪 测试路径优先级修复...")
    
    api = ProjectAnalysisAPI()
    
    # 模拟两个候选路径
    test_paths = [
        {
            'name': 'crcl-open项目',
            'path': 'D:/gitlab/create_project/链数中建一局_1752029983/crcl-open',
            'java_files': 150  # 大量Java文件
        },
        {
            'name': 'zqyl-user-center-service深层路径',
            'path': 'D:/gitlab/create_project/链数中建一局_1752029983/zqyl-user-center-service/user-basic-service/user-basic-general',
            'java_files': 50  # 较少Java文件，但路径匹配度高
        }
    ]
    
    service_name = 'user-center-service'
    
    print(f"🎯 目标服务: {service_name}")
    print("\n📊 路径优先级计算结果:")
    
    for path_info in test_paths:
        priority = api._calculate_path_priority(
            path_info['path'], 
            service_name, 
            path_info['java_files']
        )
        print(f"\n📁 {path_info['name']}")
        print(f"   路径: {path_info['path']}")
        print(f"   Java文件: {path_info['java_files']}个")
        print(f"   优先级分数: {priority}")
    
    # 确定最佳路径
    best_path = max(test_paths, key=lambda x: api._calculate_path_priority(x['path'], service_name, x['java_files']))
    print(f"\n✅ 最佳路径选择: {best_path['name']}")
    print(f"   预期: zqyl-user-center-service深层路径应该获胜")
    
    return best_path['name'] == 'zqyl-user-center-service深层路径'

def test_service_interface_generation():
    """测试Service接口自动生成功能"""
    
    print("\n🧪 测试Service接口生成功能...")
    
    agent = IntelligentCodingAgent()
    
    # 模拟只有ServiceImpl的代码块
    mock_service_impl = """package com.yljr.crcl.user.application.service;

import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Autowired;

/**
 * 用户服务实现类
 */
@Service
public class UserServiceImpl {

    @Autowired
    private UserMapper userMapper;

    public UserResponse queryUserInfo(UserRequest request) {
        // 业务逻辑实现
        return new UserResponse();
    }
    
    public boolean createUser(UserRequest request) {
        // 创建用户逻辑
        return true;
    }
}"""
    
    # 测试Service接口生成
    generated_code = {
        'service_impl': mock_service_impl
    }
    
    print("📝 输入代码:")
    print(f"   - service_impl: UserServiceImpl (包含2个方法)")
    
    # 调用代码提取方法
    extracted_code = agent._extract_code_from_react_response([mock_service_impl])
    
    print(f"\n📊 提取结果:")
    for code_type, content in extracted_code.items():
        print(f"   - {code_type}: {'✅' if content else '❌'}")
    
    # 检查是否自动生成了Service接口
    has_service_interface = 'service' in extracted_code
    has_service_impl = 'service_impl' in extracted_code
    
    print(f"\n🔍 验证结果:")
    print(f"   Service接口生成: {'✅' if has_service_interface else '❌'}")
    print(f"   ServiceImpl保留: {'✅' if has_service_impl else '❌'}")
    
    if has_service_interface:
        service_content = extracted_code['service']
        method_count = service_content.count('public ')
        print(f"   接口方法数量: {method_count}")
        print(f"   接口声明正确: {'✅' if 'interface' in service_content else '❌'}")
    
    return has_service_interface and has_service_impl

def test_service_class_conversion():
    """测试Service类转换为接口+实现模式"""
    
    print("\n🧪 测试Service类转换功能...")
    
    agent = IntelligentCodingAgent()
    
    # 模拟单一Service类（不是接口模式）
    mock_service_class = """package com.yljr.crcl.user.application.service;

import org.springframework.stereotype.Service;

/**
 * 用户服务类
 */
@Service
public class UserService {

    public UserResponse queryUserInfo(UserRequest request) {
        // 业务逻辑
        return new UserResponse();
    }
    
    public boolean updateUser(UserRequest request) {
        // 更新逻辑
        return true;
    }
}"""
    
    generated_code = {
        'service': mock_service_class
    }
    
    print("📝 输入代码:")
    print(f"   - service: UserService (普通类，非接口模式)")
    
    # 调用代码提取方法
    extracted_code = agent._extract_code_from_react_response([mock_service_class])
    
    print(f"\n📊 转换结果:")
    for code_type, content in extracted_code.items():
        if content:
            is_interface = 'interface' in content
            is_impl = 'implements' in content
            print(f"   - {code_type}: {'接口' if is_interface else ('实现类' if is_impl else '普通类')}")
    
    # 验证转换结果
    has_service_interface = 'service' in extracted_code and 'interface' in extracted_code['service']
    has_service_impl = 'service_impl' in extracted_code and 'implements' in extracted_code['service_impl']
    
    print(f"\n🔍 验证结果:")
    print(f"   转换为接口: {'✅' if has_service_interface else '❌'}")
    print(f"   转换为实现类: {'✅' if has_service_impl else '❌'}")
    
    return has_service_interface and has_service_impl

def main():
    """主测试函数"""
    
    print("🔧 测试修复后的路径选择和Service接口生成功能\n")
    
    test_results = []
    
    # 测试1：路径优先级修复
    try:
        result1 = test_path_priority_fix()
        test_results.append(("路径优先级修复", result1))
        print(f"✅ 路径优先级测试: {'通过' if result1 else '失败'}")
    except Exception as e:
        test_results.append(("路径优先级修复", False))
        print(f"❌ 路径优先级测试失败: {e}")
    
    # 测试2：Service接口自动生成
    try:
        result2 = test_service_interface_generation()
        test_results.append(("Service接口生成", result2))
        print(f"✅ Service接口生成测试: {'通过' if result2 else '失败'}")
    except Exception as e:
        test_results.append(("Service接口生成", False))
        print(f"❌ Service接口生成测试失败: {e}")
    
    # 测试3：Service类转换
    try:
        result3 = test_service_class_conversion()
        test_results.append(("Service类转换", result3))
        print(f"✅ Service类转换测试: {'通过' if result3 else '失败'}")
    except Exception as e:
        test_results.append(("Service类转换", False))
        print(f"❌ Service类转换测试失败: {e}")
    
    # 总结
    print(f"\n📊 测试总结:")
    passed_count = sum(1 for _, result in test_results if result)
    total_count = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")
    
    print(f"\n🎯 总体结果: {passed_count}/{total_count} 测试通过")
    
    if passed_count == total_count:
        print("🎉 所有修复都生效了！可以重新测试生成了。")
    else:
        print("⚠️ 仍有问题需要进一步调试。")

if __name__ == "__main__":
    main() 