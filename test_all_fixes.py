#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面测试所有问题修复
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.corder_integration.code_generator.intelligent_file_reuse_manager import IntelligentFileReuseManager

def test_all_fixes():
    """全面测试所有问题修复"""
    
    print("🧪 开始全面测试所有问题修复...")
    
    # 创建智能文件复用管理器
    manager = IntelligentFileReuseManager()
    
    # 设置测试文档内容（使用combined_document_demo.txt的内容）
    test_document = """
    CREATE TABLE t_cust_multiorg_unit (
        id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
        org_code VARCHAR(50) NOT NULL COMMENT '组织代码',
        org_name VARCHAR(100) NOT NULL COMMENT '组织名称',
        parent_code VARCHAR(50) COMMENT '上级组织代码',
        org_level INTEGER COMMENT '组织层级',
        status VARCHAR(20) DEFAULT 'ACTIVE' COMMENT '状态：ACTIVE-激活，INACTIVE-停用',
        create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='组织单元表';
    """
    
    manager.set_document_content(test_document)
    
    # 测试用例
    test_cases = [
        {
            'name': '方法命名测试',
            'interface_name': 'CompanyUnitList',
            'expected_method': 'companyUnitList'
        },
        {
            'name': '服务结构测试',
            'interface_name': 'QueryUserInfo',
            'expected_method': 'queryUserInfo'
        }
    ]
    
    all_tests_passed = True
    
    for test_case in test_cases:
        print(f"\n🔍 测试：{test_case['name']}")
        print(f"   接口名：{test_case['interface_name']}")
        print(f"   预期方法名：{test_case['expected_method']}")
        
        try:
            # 设置测试参数
            interface_name = test_case['interface_name']
            strategy = {
                'mapper': {'action': 'create_new', 'target_file': None}
            }
            input_params = [
                {'name': 'orgCode', 'type': 'String', 'description': '组织代码'},
                {'name': 'status', 'type': 'String', 'description': '状态'}
            ]
            output_params = {
                'dataList': {'type': 'List', 'description': '数据列表'},
                'totalCount': {'type': 'Integer', 'description': '总数'}
            }
            business_logic = "查询组织单元列表"
            
            # 测试1：方法命名问题
            print("   ✓ 测试方法命名...")
            domain_service_code = manager._generate_domain_service_logic(
                interface_name, strategy, input_params, output_params, business_logic
            )
            
            if test_case['expected_method'] + "(" in domain_service_code:
                print("   ✅ 方法名正确使用驼峰命名")
            else:
                print("   ❌ 方法名不是驼峰命名")
                all_tests_passed = False
            
            # 测试2：服务结构问题
            print("   ✓ 测试服务结构...")
            if "---SERVICE_IMPL_SEPARATOR---" in domain_service_code:
                print("   ✅ 正确生成了Interface + ServiceImpl结构")
            else:
                print("   ❌ 没有生成Interface + ServiceImpl结构")
                all_tests_passed = False
            
            # 测试3：XML字段映射问题
            print("   ✓ 测试XML字段映射...")
            xml_code = manager._generate_xml_mapping_logic(
                interface_name, strategy, input_params, output_params, business_logic
            )
            
            # 检查是否包含实际的表字段
            expected_fields = ['org_code', 'org_name', 'parent_code', 'org_level', 'status']
            fields_found = 0
            for field in expected_fields:
                if field in xml_code:
                    fields_found += 1
            
            if fields_found >= 3:  # 至少包含3个实际字段
                print(f"   ✅ XML包含实际表字段（{fields_found}/{len(expected_fields)}）")
            else:
                print(f"   ❌ XML字段映射不完整（{fields_found}/{len(expected_fields)}）")
                all_tests_passed = False
            
            # 测试4：模板字符串格式
            print("   ✓ 测试模板字符串格式...")
            if "{interface_name}" in domain_service_code or "{interface_name}" in xml_code:
                print("   ❌ 代码中仍然包含未替换的模板变量")
                all_tests_passed = False
            else:
                print("   ✅ 所有模板变量都已正确替换")
                
        except Exception as e:
            print(f"   ❌ 测试失败: {e}")
            all_tests_passed = False
    
    # 额外测试：设计文档内容传递
    print(f"\n🔍 测试：设计文档内容传递")
    try:
        # 测试表结构解析
        table_structure = manager._extract_table_structure_from_context("CompanyUnitList", business_logic)
        
        if table_structure['columns'] and len(table_structure['columns']) > 5:
            print("   ✅ 成功解析表结构，包含多个字段")
        else:
            print("   ❌ 表结构解析不完整")
            all_tests_passed = False
            
        # 打印解析的字段
        print("   📋 解析的字段:")
        for col in table_structure['columns'][:5]:  # 显示前5个字段
            print(f"      - {col['column_name']} ({col['jdbc_type']}): {col['comment']}")
            
    except Exception as e:
        print(f"   ❌ 设计文档内容传递测试失败: {e}")
        all_tests_passed = False
    
    return all_tests_passed

if __name__ == "__main__":
    success = test_all_fixes()
    
    if success:
        print("\n🎉 所有问题修复测试通过！")
        print("✅ 方法命名问题已修复")
        print("✅ 服务结构问题已修复") 
        print("✅ XML字段映射问题已修复")
        print("✅ 模板字符串格式问题已修复")
    else:
        print("\n💥 仍有问题需要修复！")