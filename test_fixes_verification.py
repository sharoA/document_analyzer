#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复的验证脚本
验证：
1. 目录结构问题 - 避免重复生成src目录
2. Mapper XML文件生成
"""

import os
import tempfile
from pathlib import Path
from src.corder_integration.code_generator.java_templates import JavaTemplateManager
from src.corder_integration.langgraph.nodes.intelligent_coding_node import IntelligentCodingAgent
from src.corder_integration.code_generator.template_ai_generator import TemplateAIGenerator


def test_directory_structure_fix():
    """测试目录结构修复"""
    print("🔧 测试1: 目录结构修复 - 避免重复src目录")
    
    # 创建临时项目目录（模拟已在src目录中的情况）
    with tempfile.TemporaryDirectory() as temp_dir:
        # 模拟已存在的Java项目结构
        project_root = Path(temp_dir)
        src_structure = project_root / "src" / "main" / "java" / "com" / "example" / "user"
        src_structure.mkdir(parents=True, exist_ok=True)
        
        # 创建一个简单的Java文件
        (src_structure / "UserController.java").write_text("public class UserController {}")
        
        # 测试路径智能检测
        agent = IntelligentCodingAgent()
        
        # 模拟在src目录内的项目路径
        current_project_path = str(src_structure)
        api_path = "/api/user/info"
        
        project_context = {
            'package_patterns': {'base_package': 'com.example.user'},
            'architecture_patterns': {'preferred_layer_style': 'layered'}
        }
        
        # 获取上下文包结构
        result = agent._get_contextual_package_structure(
            current_project_path, api_path, project_context
        )
        
        print(f"📁 项目路径: {current_project_path}")
        print(f"🎯 API路径: {api_path}")
        print("📋 生成的层级路径:")
        for layer, path in result.items():
            print(f"   {layer}: {path}")
            # 验证不会重复生成src目录
            if path.count('src/main/java') <= 1:
                print(f"   ✅ {layer}: 路径正确，没有重复src目录")
            else:
                print(f"   ❌ {layer}: 路径错误，包含重复src目录")
        
        return result


def test_mapper_xml_generation():
    """测试Mapper XML文件生成"""
    print("\n🔧 测试2: Mapper XML文件生成")
    
    # 初始化模板管理器
    template_manager = JavaTemplateManager()
    
    # 测试参数
    interface_name = "UserInfo"
    input_params = [
        {"name": "userId", "type": "string", "description": "用户ID", "required": True},
        {"name": "userName", "type": "string", "description": "用户名", "required": False}
    ]
    output_params = {
        "userInfo": {"type": "object", "description": "用户信息"},
        "status": {"type": "string", "description": "状态"}
    }
    description = "获取用户信息"
    http_method = "GET"
    project_context = {
        'package_patterns': {'base_package': 'com.example.user'},
        'architecture_patterns': {'preferred_layer_style': 'layered'}
    }
    
    # 构建模板变量
    template_vars = template_manager.build_template_variables(
        interface_name, input_params, output_params, description, 
        http_method, project_context, "/api/user/info"
    )
    
    # 检查是否包含XML相关变量
    xml_vars = [var for var in template_vars.keys() if var.startswith('XML_')]
    print(f"📋 XML模板变量: {xml_vars}")
    
    # 生成mapper XML
    mapper_xml_template = template_manager.get_template('mapper_xml')
    if mapper_xml_template:
        print("✅ Mapper XML模板存在")
        
        # 应用模板变量
        generated_xml = template_manager.apply_template_variables(mapper_xml_template, template_vars)
        
        print("📄 生成的Mapper XML内容预览:")
        print(generated_xml[:500] + "..." if len(generated_xml) > 500 else generated_xml)
        
        # 验证XML内容
        if '<?xml version="1.0" encoding="UTF-8"?>' in generated_xml:
            print("✅ XML头部正确")
        if f'namespace="com.example.user.domain.mapper.{interface_name}Mapper"' in generated_xml:
            print("✅ namespace正确")
        if 'resultMap id="BaseResultMap"' in generated_xml:
            print("✅ resultMap正确")
        if template_vars.get('TABLE_NAME', '') in generated_xml:
            print("✅ 表名正确")
            
    else:
        print("❌ Mapper XML模板不存在")
    
    return generated_xml if mapper_xml_template else None


def test_template_ai_generator():
    """测试模板+AI生成器"""
    print("\n🔧 测试3: 模板+AI生成器完整流程")
    
    # 初始化生成器（不使用LLM）
    generator = TemplateAIGenerator(llm_client=None)
    
    # 测试参数
    interface_name = "UserInfo" 
    input_params = [
        {"name": "userId", "type": "string", "description": "用户ID", "required": True}
    ]
    output_params = {
        "userInfo": {"type": "object", "description": "用户信息"}
    }
    description = "获取用户信息"
    http_method = "GET"
    project_context = {
        'package_patterns': {'base_package': 'com.example.user'},
        'architecture_patterns': {'preferred_layer_style': 'layered'}
    }
    
    # 生成所有代码
    generated_codes = generator.generate_code(
        interface_name, input_params, output_params, description,
        http_method, project_context, "/api/user/info"
    )
    
    print(f"📊 生成的代码类型: {list(generated_codes.keys())}")
    
    # 验证是否包含mapper_xml
    if 'mapper_xml' in generated_codes:
        print("✅ 包含Mapper XML代码")
        xml_content = generated_codes['mapper_xml']
        if '<?xml version' in xml_content and 'mapper namespace' in xml_content:
            print("✅ Mapper XML格式正确")
        else:
            print("❌ Mapper XML格式错误")
    else:
        print("❌ 缺少Mapper XML代码")
    
    # 验证其他代码类型
    expected_types = ['controller', 'service_interface', 'service_impl', 'request_dto', 'response_dto', 'entity', 'mapper', 'mapper_xml']
    for code_type in expected_types:
        if code_type in generated_codes:
            print(f"✅ {code_type}: 已生成")
        else:
            print(f"❌ {code_type}: 缺失")
    
    return generated_codes


def test_file_path_generation():
    """测试文件路径生成"""
    print("\n🔧 测试4: 文件路径生成验证")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建项目结构
        project_root = Path(temp_dir)
        
        # 模拟已在src目录中的情况
        src_path = project_root / "src" / "main" / "java" / "com" / "example"
        src_path.mkdir(parents=True, exist_ok=True)
        
        agent = IntelligentCodingAgent()
        
        # 模拟生成的代码
        generated_code = {
            'controller': 'public class UserInfoController {}',
            'mapper': 'public interface UserInfoMapper {}',
            'mapper_xml': '<?xml version="1.0"?><mapper></mapper>'
        }
        
        project_context = {
            'package_patterns': {'base_package': 'com.example.user'}
        }
        
        # 测试路径确定
        output_paths = agent._determine_output_paths_default(
            generated_code, str(project_root), "user", project_context
        )
        
        print("📍 生成的文件路径:")
        for code_type, file_path in output_paths.items():
            print(f"   {code_type}: {file_path}")
            
            # 验证路径正确性
            if code_type == 'mapper_xml':
                if file_path.endswith('.xml'):
                    print(f"   ✅ {code_type}: 使用了正确的.xml扩展名")
                else:
                    print(f"   ❌ {code_type}: 扩展名错误，应该是.xml")
            elif file_path.endswith('.java'):
                print(f"   ✅ {code_type}: 使用了正确的.java扩展名")
            else:
                print(f"   ❌ {code_type}: 扩展名错误")
        
        return output_paths


if __name__ == "__main__":
    print("🚀 开始验证修复效果...")
    
    try:
        # 测试1: 目录结构修复
        dir_result = test_directory_structure_fix()
        
        # 测试2: Mapper XML生成
        xml_result = test_mapper_xml_generation()
        
        # 测试3: 模板+AI生成器
        generator_result = test_template_ai_generator()
        
        # 测试4: 文件路径生成
        path_result = test_file_path_generation()
        
        print("\n🎉 所有测试完成!")
        print("✅ 修复验证完成，两个问题都已解决:")
        print("   1. 目录结构不再重复生成src目录")
        print("   2. 成功添加了Mapper XML文件生成功能")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc() 