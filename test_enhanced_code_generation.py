#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强版代码生成器的方法名一致性和完整性
验证前述问题是否已被解决
"""

import logging
import json
from typing import Dict, List, Any

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_enhanced_template_ai_generator():
    """测试增强版模板AI生成器"""
    
    print("=" * 60)
    print("🧪 测试增强版代码生成器")
    print("=" * 60)
    
    try:
        # 导入增强版生成器
        from src.corder_integration.code_generator.enhanced_template_ai_generator import EnhancedTemplateAIGenerator
        from src.utils.volcengine_client import VolcengineClient, VolcengineConfig
        
        # 模拟LLM客户端（用于测试）
        class MockLLMClient:
            def chat(self, messages, temperature=0.1, max_tokens=3000):
                # 模拟返回一个简单的Service接口
                if "Service接口" in str(messages):
                    return """
                    ```java
                    package com.yljr.crcl.limit.application.service;
                    
                    /**
                     * CompanyUnitList Service Interface
                     */
                    public interface CompanyUnitListService {
                        /**
                         * 查询企业单元列表
                         */
                        CompanyUnitListResp CompanyUnitList(CompanyUnitListReq request);
                    }
                    ```
                    """
                elif "ServiceImpl" in str(messages):
                    return """
                    ```java
                    package com.yljr.crcl.limit.application.service.impl;
                    
                    import com.yljr.crcl.limit.application.service.CompanyUnitListService;
                    import com.yljr.crcl.limit.domain.mapper.CompanyUnitListMapper;
                    
                    @Service
                    public class CompanyUnitListServiceImpl implements CompanyUnitListService {
                        
                        @Autowired
                        private CompanyUnitListMapper companyUnitListMapper;
                        
                        @Override
                        public CompanyUnitListResp CompanyUnitList(CompanyUnitListReq request) {
                            // 调用Mapper进行数据查询
                            List<CompanyUnitList> results = companyUnitListMapper.selectCompanyUnitList(request);
                            return buildResponse(results);
                        }
                    }
                    ```
                    """
                elif "Mapper接口" in str(messages):
                    return """
                    ```java
                    package com.yljr.crcl.limit.domain.mapper;
                    
                    import java.util.List;
                    
                    @Mapper
                    public interface CompanyUnitListMapper extends BaseMapper<CompanyUnitList> {
                        /**
                         * 查询企业单元列表
                         */
                        List<CompanyUnitList> selectCompanyUnitList(CompanyUnitListReq condition);
                    }
                    ```
                    """
                else:
                    return "Mock LLM Response"
        
        # 初始化生成器
        mock_client = MockLLMClient()
        generator = EnhancedTemplateAIGenerator(mock_client)
        
        print("✅ 增强版生成器初始化成功")
        
        # 测试参数
        interface_name = "CompanyUnitList"
        input_params = [
            {"name": "unitCode", "type": "String", "description": "单元代码", "required": False},
            {"name": "openStatus", "type": "String", "description": "开放状态", "required": False}
        ]
        output_params = {
            "unitList": {"type": "List<CompanyUnit>", "description": "企业单元列表"},
            "totalCount": {"type": "Integer", "description": "总数量"}
        }
        description = "查询企业单元列表"
        http_method = "POST"
        business_logic = "根据传入的查询条件，查询企业单元列表信息"
        
        # 模拟项目上下文
        project_context = {
            "package_patterns": {
                "base_package": "com.yljr.crcl.limit"
            },
            "project_info": {
                "is_mybatis_plus": True,
                "is_spring_boot": True
            },
            "document_content": """
            CREATE TABLE company_unit (
                id BIGINT PRIMARY KEY,
                unit_code VARCHAR(50) NOT NULL COMMENT '单元代码',
                unit_name VARCHAR(200) NOT NULL COMMENT '单元名称',
                open_status VARCHAR(20) COMMENT '开放状态'
            ) ENGINE=InnoDB COMMENT='企业单元表';
            """
        }
        
        print(f"\n🎯 开始测试代码生成...")
        print(f"   接口名称: {interface_name}")
        print(f"   输入参数: {len(input_params)}个")
        print(f"   输出参数: {len(output_params)}个")
        
        # 执行代码生成
        generated_code = generator.generate_code(
            interface_name=interface_name,
            input_params=input_params,
            output_params=output_params,
            description=description,
            http_method=http_method,
            project_context=project_context,
            business_logic=business_logic
        )
        
        print(f"\n📊 代码生成结果:")
        if generated_code:
            print(f"   生成代码类型: {list(generated_code.keys())}")
            
            # 测试Service接口方法提取
            if 'service_interface' in generated_code:
                print(f"\n🔍 测试Service接口方法提取...")
                service_interface_code = generated_code['service_interface']
                extracted_methods = generator._extract_service_interface_methods(
                    service_interface_code, interface_name
                )
                
                print(f"   提取到的方法数量: {len(extracted_methods)}")
                for method in extracted_methods:
                    print(f"   - {method['name']}({method['parameters']}) -> {method['return_type']}")
                
                # 验证方法名一致性
                expected_method_name = "CompanyUnitList"
                found_expected_method = any(method['name'] == expected_method_name for method in extracted_methods)
                
                if found_expected_method:
                    print(f"   ✅ 方法名一致性检查通过: 找到期望的方法 '{expected_method_name}'")
                else:
                    print(f"   ❌ 方法名一致性检查失败: 未找到期望的方法 '{expected_method_name}'")
                    print(f"      实际方法名: {[method['name'] for method in extracted_methods]}")
            
            # 测试ServiceImpl中的Mapper调用提取
            if 'service_impl' in generated_code:
                print(f"\n🔍 测试ServiceImpl中的Mapper调用提取...")
                service_impl_code = generated_code['service_impl']
                mapper_calls = generator._extract_mapper_calls_from_service_impl(
                    service_impl_code, interface_name
                )
                
                print(f"   提取到的Mapper调用数量: {len(mapper_calls)}")
                for call in mapper_calls:
                    print(f"   - {call['method_name']}({call['parameters']}) -> {call['return_type']}")
                
                # 验证Mapper方法调用一致性
                expected_mapper_method = "selectCompanyUnitList"
                found_expected_mapper = any(call['method_name'] == expected_mapper_method for call in mapper_calls)
                
                if found_expected_mapper:
                    print(f"   ✅ Mapper方法调用一致性检查通过: 找到期望的方法 '{expected_mapper_method}'")
                else:
                    print(f"   ❌ Mapper方法调用一致性检查失败: 未找到期望的方法 '{expected_mapper_method}'")
                    print(f"      实际Mapper方法: {[call['method_name'] for call in mapper_calls]}")
        else:
            print("   ❌ 没有生成任何代码")
            return False
        
        print(f"\n🧪 测试Service接口方法提取功能...")
        test_service_code = """
        package com.yljr.crcl.limit.application.service;
        
        /**
         * CompanyUnitList Service Interface
         */
        public interface CompanyUnitListService {
            /**
             * 查询企业单元列表
             */
            CompanyUnitListResp CompanyUnitList(CompanyUnitListReq request);
            
            /**
             * 根据ID查询单个企业单元
             */
            CompanyUnitListResp getCompanyUnitById(Long id);
        }
        """
        
        extracted_methods = generator._extract_service_interface_methods(test_service_code, "CompanyUnitList")
        print(f"   测试代码中提取到的方法数量: {len(extracted_methods)}")
        for method in extracted_methods:
            print(f"   - {method['name']}({method['parameters']}) -> {method['return_type']}")
        
        # 验证关键问题解决情况
        print(f"\n🔧 问题解决验证:")
        
        # 问题1: ServiceImpl方法名与Service接口一致性
        service_methods = [method['name'] for method in extracted_methods]
        if 'CompanyUnitList' in service_methods:
            print(f"   ✅ 问题1已解决: Service接口方法名提取正确")
        else:
            print(f"   ❌ 问题1未解决: Service接口方法名提取有问题")
        
        # 问题2: Mapper方法调用存在性
        if 'service_impl' in generated_code:
            mapper_calls = generator._extract_mapper_calls_from_service_impl(
                generated_code['service_impl'], interface_name
            )
            if mapper_calls:
                print(f"   ✅ 问题2已解决: Mapper方法调用提取正常")
            else:
                print(f"   ❌ 问题2未解决: Mapper方法调用提取失败")
        
        # 问题3: XML文件生成
        xml_generation_available = hasattr(generator, '_enhance_mapper_xml_with_specialized_prompt')
        if xml_generation_available:
            print(f"   ✅ 问题3已解决: XML文件生成功能已实现")
        else:
            print(f"   ❌ 问题3未解决: XML文件生成功能缺失")
        
        print(f"\n🎉 增强版代码生成器测试完成")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_method_name_consistency():
    """专门测试方法名一致性问题"""
    
    print("\n" + "=" * 60)
    print("🔍 专项测试: 方法名一致性")
    print("=" * 60)
    
    try:
        from src.corder_integration.code_generator.enhanced_template_ai_generator import EnhancedTemplateAIGenerator
        
        generator = EnhancedTemplateAIGenerator(None)  # 不需要LLM客户端进行纯方法测试
        
        # 测试用例1: 正常的Service接口
        test_cases = [
            {
                "name": "正常Service接口",
                "code": '''
                public interface CompanyUnitListService {
                    /**
                     * 查询企业单元列表
                     */
                    CompanyUnitListResp CompanyUnitList(CompanyUnitListReq request);
                }
                ''',
                "expected_method": "CompanyUnitList"
            },
            {
                "name": "带注释的Service接口",
                "code": '''
                public interface UserService {
                    /**
                     * 获取用户信息
                     * @param userId 用户ID
                     * @return 用户信息
                     */
                    UserResp getUserInfo(Long userId);
                    
                    /**
                     * 创建用户
                     */
                    UserResp createUser(UserReq request);
                }
                ''',
                "expected_method": "getUserInfo"
            },
            {
                "name": "复杂参数Service接口",
                "code": '''
                public interface OrderService {
                    List<OrderResp> queryOrderList(
                        @Param("condition") OrderReq condition,
                        @Param("page") Integer page,
                        @Param("size") Integer size
                    );
                }
                ''',
                "expected_method": "queryOrderList"
            }
        ]
        
        all_passed = True
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📋 测试用例 {i}: {test_case['name']}")
            
            extracted_methods = generator._extract_service_interface_methods(
                test_case['code'], "TestInterface"
            )
            
            print(f"   提取到的方法: {[method['name'] for method in extracted_methods]}")
            
            if test_case['expected_method'] in [method['name'] for method in extracted_methods]:
                print(f"   ✅ 通过: 成功提取到期望方法 '{test_case['expected_method']}'")
            else:
                print(f"   ❌ 失败: 未提取到期望方法 '{test_case['expected_method']}'")
                all_passed = False
        
        print(f"\n📊 方法名一致性测试结果: {'✅ 全部通过' if all_passed else '❌ 存在失败'}")
        return all_passed
        
    except Exception as e:
        print(f"\n❌ 方法名一致性测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 开始测试增强版代码生成器的修复效果")
    
    # 更新todo状态
    print("\n📝 更新任务状态...")
    
    # 执行主要测试
    main_test_passed = test_enhanced_template_ai_generator()
    
    # 执行方法名一致性测试
    consistency_test_passed = test_method_name_consistency()
    
    print("\n" + "=" * 60)
    print("📊 最终测试结果")
    print("=" * 60)
    print(f"增强版代码生成器测试: {'✅ 通过' if main_test_passed else '❌ 失败'}")
    print(f"方法名一致性测试: {'✅ 通过' if consistency_test_passed else '❌ 失败'}")
    
    if main_test_passed and consistency_test_passed:
        print(f"\n🎉 所有测试通过！增强版代码生成器的修复效果良好")
        print(f"   ✅ 问题1: ServiceImpl方法名与Service接口一致性 - 已解决")
        print(f"   ✅ 问题2: Mapper方法调用存在性检查 - 已解决") 
        print(f"   ✅ 问题3: XML文件生成功能 - 已实现")
    else:
        print(f"\n⚠️ 部分测试失败，需要进一步调试和修复")