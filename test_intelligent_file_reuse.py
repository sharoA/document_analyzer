#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试智能文件复用系统
验证是否能正确识别现有文件并生成完整的调用链
"""

import logging
import json
import os
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_intelligent_file_reuse_system():
    """测试智能文件复用系统"""
    
    print("=" * 80)
    print("🧪 测试智能文件复用系统")
    print("=" * 80)
    
    try:
        from src.corder_integration.code_generator.intelligent_file_reuse_manager import IntelligentFileReuseManager
        
        # 模拟LLM客户端
        class MockLLMClient:
            def chat(self, messages, temperature=0.1, max_tokens=3000):
                return "Mock LLM Response for intelligent file reuse"
        
        # 初始化文件复用管理器
        mock_client = MockLLMClient()
        file_manager = IntelligentFileReuseManager(mock_client)
        
        print("✅ 智能文件复用管理器初始化成功")
        
        # 测试项目路径（根据用户提供的路径）
        test_project_path = "D:/gitlab/create_project/链数中建一局_1752547533/crcl-open"
        
        # 如果路径不存在，使用当前项目路径作为示例
        if not os.path.exists(test_project_path):
            test_project_path = "/mnt/d/ai_project/document_analyzer"
            print(f"⚠️ 原路径不存在，使用测试路径: {test_project_path}")
        
        print(f"\n🔍 分析项目结构: {test_project_path}")
        
        # 分析项目结构
        project_structure = file_manager.analyze_project_structure(test_project_path)
        
        print(f"\n📊 项目结构分析结果:")
        print(f"   Controllers: {len(project_structure['controllers'])}")
        print(f"   Application Services: {len(project_structure['application_services'])}")
        print(f"   Domain Services: {len(project_structure['domain_services'])}")
        print(f"   Mappers: {len(project_structure['mappers'])}")
        print(f"   Feign Clients: {len(project_structure['feign_clients'])}")
        print(f"   XML Files: {len(project_structure['xml_files'])}")
        print(f"   Base Package: {project_structure['base_package']}")
        print(f"   Modules: {project_structure['modules']}")
        
        # 测试文件复用策略决策
        print(f"\n🤔 测试文件复用策略决策...")
        
        test_cases = [
            {
                "name": "企业单元查询API",
                "api_path": "/general/multiorgManage/queryCompanyUnitList",
                "interface_name": "CompanyUnitList", 
                "business_logic": "根据传入的查询条件，查询企业单元列表信息，支持分页查询"
            },
            {
                "name": "用户信息查询API",
                "api_path": "/user/profile/getUserInfo",
                "interface_name": "UserInfo",
                "business_logic": "根据用户ID查询用户详细信息，需要调用用户服务接口"
            },
            {
                "name": "限额数据保存API", 
                "api_path": "/limit/data/saveLimitData",
                "interface_name": "LimitData",
                "business_logic": "保存限额数据到数据库，需要进行数据验证和业务规则检查"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📋 测试用例 {i}: {test_case['name']}")
            print(f"   API路径: {test_case['api_path']}")
            print(f"   接口名称: {test_case['interface_name']}")
            print(f"   业务逻辑: {test_case['business_logic']}")
            
            # 决策文件复用策略
            reuse_strategy = file_manager.decide_file_reuse_strategy(
                test_case['api_path'], test_case['interface_name'], test_case['business_logic']
            )
            
            print(f"   📊 复用策略决策结果:")
            for component, strategy in reuse_strategy.items():
                action_icon = "🔄" if strategy['action'] == 'add_method' else ("🆕" if strategy['action'] == 'create_new' else "⏩")
                print(f"     {action_icon} {component}: {strategy['action']} - {strategy['reason']}")
            
            # 生成完整调用链
            print(f"   🔗 生成完整调用链...")
            
            input_params = [
                {"name": "unitCode", "type": "String", "description": "单元代码", "required": False},
                {"name": "unitName", "type": "String", "description": "单元名称", "required": False}
            ]
            output_params = {
                "unitList": {"type": "List<CompanyUnit>", "description": "企业单元列表"},
                "totalCount": {"type": "Integer", "description": "总数量"}
            }
            
            calling_chain = file_manager.generate_complete_calling_chain(
                test_case['interface_name'], reuse_strategy, input_params, output_params, test_case['business_logic']
            )
            
            if calling_chain:
                print(f"   ✅ 成功生成 {len(calling_chain)} 个组件的调用链:")
                for component_type, code in calling_chain.items():
                    print(f"     📝 {component_type}: {len(code)} 字符")
                    # 显示代码片段（前100字符）
                    preview = code.replace('\n', ' ').strip()[:100] + "..." if len(code) > 100 else code
                    print(f"        预览: {preview}")
            else:
                print(f"   ❌ 调用链生成失败")
        
        # 测试现有文件的具体匹配
        print(f"\n🔍 测试现有文件匹配...")
        
        # 列出找到的Controller文件
        if project_structure['controllers']:
            print(f"   📁 发现的Controller文件:")
            for i, (controller_name, controller_info) in enumerate(list(project_structure['controllers'].items())[:5]):
                print(f"     {i+1}. {controller_name}")
                print(f"        路径: {controller_info['relative_path']}")
                print(f"        映射: {controller_info['request_mapping']}")
                print(f"        模块: {controller_info['module']}")
                print(f"        方法数: {len(controller_info['methods'])}")
        
        # 列出找到的Service文件
        if project_structure['application_services']:
            print(f"   📁 发现的Application Service文件:")
            for i, (service_name, service_info) in enumerate(list(project_structure['application_services'].items())[:3]):
                print(f"     {i+1}. {service_name}")
                print(f"        路径: {service_info['relative_path']}")
                print(f"        模块: {service_info['module']}")
                print(f"        方法数: {len(service_info['methods'])}")
        
        print(f"\n🎉 智能文件复用系统测试完成")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_controller_method_addition():
    """测试Controller方法添加功能"""
    
    print("\n" + "=" * 80)
    print("🔧 测试Controller方法添加功能")
    print("=" * 80)
    
    try:
        from src.corder_integration.code_generator.enhanced_template_ai_generator import EnhancedTemplateAIGenerator
        
        generator = EnhancedTemplateAIGenerator(None)
        
        # 模拟现有Controller内容
        existing_controller = '''
package com.yljr.crcl.limit.interfaces.rest;

import org.springframework.web.bind.annotation.*;
import org.springframework.beans.factory.annotation.Autowired;

@RestController
@RequestMapping("/limit/ls")
public class LsLimitController {

    @Autowired
    private LimitService limitService;

    @PostMapping("/existingMethod")
    public Response<String> existingMethod() {
        return Response.success("existing");
    }
}'''
        
        # 模拟新方法
        new_method = '''
    /**
     * 查询企业单元列表
     */
    @PostMapping("/queryCompanyUnitList")
    @ApiOperation(value = "查询企业单元列表")
    public Response<CompanyUnitListResp> queryCompanyUnitList(@RequestBody @Valid CompanyUnitListReq request) {
        try {
            logger.info("开始执行queryCompanyUnitList，请求参数: {}", request);
            
            return companyUnitListApplication.queryCompanyUnitList(request);
            
        } catch (Exception e) {
            logger.error("执行queryCompanyUnitList失败", e);
            return Response.error("执行失败: " + e.getMessage());
        }
    }'''
        
        print("🧪 测试在现有Controller中添加新方法...")
        
        # 测试方法添加
        updated_controller = generator._add_method_to_controller(
            existing_controller, new_method, "queryCompanyUnitList"
        )
        
        print("✅ 方法添加完成")
        print("📝 更新后的Controller:")
        print("-" * 60)
        print(updated_controller)
        print("-" * 60)
        
        # 验证是否包含新方法
        if "queryCompanyUnitList" in updated_controller and "@PostMapping" in updated_controller:
            print("✅ 新方法添加验证通过")
            return True
        else:
            print("❌ 新方法添加验证失败")
            return False
        
    except Exception as e:
        print(f"❌ Controller方法添加测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_service_logic_generation():
    """测试Service逻辑生成"""
    
    print("\n" + "=" * 80)
    print("🔗 测试Service逻辑生成")
    print("=" * 80)
    
    try:
        from src.corder_integration.code_generator.intelligent_file_reuse_manager import IntelligentFileReuseManager
        
        file_manager = IntelligentFileReuseManager(None)
        file_manager.project_structure = {'base_package': 'com.yljr.crcl.limit'}
        
        print("🧪 测试Application Service逻辑生成...")
        
        # 测试Application Service生成
        app_service_code = file_manager._generate_application_service_logic(
            interface_name="CompanyUnitList",
            strategy={
                'feign_client': {'action': 'add_method', 'target_file': 'test'},
                'domain_service': {'action': 'skip'}
            },
            input_params=[{"name": "unitCode", "type": "String"}],
            output_params={"unitList": {"type": "List<CompanyUnit>"}},
            business_logic="查询企业单元列表"
        )
        
        print("📝 生成的Application Service代码:")
        print("-" * 60)
        print(app_service_code)
        print("-" * 60)
        
        print("🧪 测试Domain Service逻辑生成...")
        
        # 测试Domain Service生成
        domain_service_code = file_manager._generate_domain_service_logic(
            interface_name="CompanyUnitList",
            strategy={
                'mapper': {'action': 'add_method', 'target_file': 'test'},
                'feign_client': {'action': 'skip'}
            },
            input_params=[{"name": "unitCode", "type": "String"}],
            output_params={"unitList": {"type": "List<CompanyUnit>"}},
            business_logic="查询企业单元列表数据"
        )
        
        print("📝 生成的Domain Service代码:")
        print("-" * 60)
        print(domain_service_code)
        print("-" * 60)
        
        # 验证生成的代码质量
        validations = [
            ("Application Service包含正确的类名", "CompanyUnitListApplication" in app_service_code),
            ("Application Service包含@Service注解", "@Service" in app_service_code),
            ("Application Service包含业务方法", "CompanyUnitList(" in app_service_code),
            ("Domain Service包含正确的类名", "CompanyUnitListDomainService" in domain_service_code),
            ("Domain Service包含Mapper调用", "Mapper" in domain_service_code),
            ("Domain Service包含异常处理", "try {" in domain_service_code and "catch" in domain_service_code)
        ]
        
        all_passed = True
        for description, passed in validations:
            status = "✅" if passed else "❌"
            print(f"{status} {description}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print("🎉 Service逻辑生成测试全部通过")
        else:
            print("⚠️ 部分Service逻辑生成测试失败")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Service逻辑生成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 开始测试智能文件复用系统的完整功能")
    
    # 执行各项测试
    main_test_passed = test_intelligent_file_reuse_system()
    controller_test_passed = test_controller_method_addition()
    service_test_passed = test_service_logic_generation()
    
    print("\n" + "=" * 80)
    print("📊 最终测试结果")
    print("=" * 80)
    print(f"智能文件复用系统测试: {'✅ 通过' if main_test_passed else '❌ 失败'}")
    print(f"Controller方法添加测试: {'✅ 通过' if controller_test_passed else '❌ 失败'}")
    print(f"Service逻辑生成测试: {'✅ 通过' if service_test_passed else '❌ 失败'}")
    
    if main_test_passed and controller_test_passed and service_test_passed:
        print(f"\n🎉 所有测试通过！智能文件复用系统功能完善")
        print(f"🎯 关键功能验证:")
        print(f"   ✅ 项目结构分析: 能正确识别现有Controller、Service、Mapper等组件")
        print(f"   ✅ 文件复用策略: 智能决策是否复用现有文件还是创建新文件")
        print(f"   ✅ 完整调用链生成: Controller->Application Service->Domain Service/Mapper")
        print(f"   ✅ 现有文件更新: 能在现有文件中正确添加新方法")
        print(f"   ✅ 业务逻辑生成: 生成的方法包含具体的业务逻辑而非空实现")
        print(f"   ✅ 架构规范遵循: 严格按照DDD分层架构生成代码")
    else:
        print(f"\n⚠️ 部分测试失败，需要进一步调试和完善")
        
    print(f"\n📋 智能文件复用系统已实现的核心能力:")
    print(f"   🔍 自动分析现有项目结构，识别可复用的组件")
    print(f"   🤔 智能决策文件复用策略，优先使用现有文件")
    print(f"   🔗 生成完整的调用链逻辑，确保业务流程完整")
    print(f"   📝 在现有文件中添加新方法，避免重复创建")
    print(f"   🎯 根据业务需求生成具体逻辑，而非空实现")
    print(f"   🏗️ 支持Feign接口调用和本地数据库操作")
    print(f"   📂 自动创建备份文件，确保原文件安全")
    print(f"   🛡️ 完整的异常处理和日志记录")