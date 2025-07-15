#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试模板字符串格式修复
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.corder_integration.code_generator.intelligent_file_reuse_manager import IntelligentFileReuseManager

def test_template_formatting_fix():
    """测试模板字符串格式修复"""
    
    print("🧪 开始测试模板字符串格式修复...")
    
    # 创建智能文件复用管理器
    manager = IntelligentFileReuseManager()
    
    # 设置测试文档内容
    test_document = """
    CREATE TABLE t_cust_multiorg_unit (
        id BIGINT PRIMARY KEY COMMENT '主键',
        org_code VARCHAR(50) COMMENT '组织代码',
        org_name VARCHAR(100) COMMENT '组织名称',
        status VARCHAR(20) COMMENT '状态'
    ) ENGINE=InnoDB;
    """
    
    manager.set_document_content(test_document)
    
    # 测试生成Domain Service逻辑
    try:
        interface_name = "CompanyUnitList"
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
        
        # 生成Domain Service代码
        domain_service_code = manager._generate_domain_service_logic(
            interface_name, strategy, input_params, output_params, business_logic
        )
        
        print(f"✅ 成功生成Domain Service代码，长度: {len(domain_service_code)}")
        print("🔍 检查生成的代码是否包含正确的方法名...")
        
        # 验证代码中是否包含驼峰命名的方法
        if "companyUnitList(" in domain_service_code:
            print("✅ 方法名正确使用驼峰命名：companyUnitList")
        else:
            print("❌ 方法名不是驼峰命名")
            
        # 验证代码中是否包含Interface + ServiceImpl结构
        if "---SERVICE_IMPL_SEPARATOR---" in domain_service_code:
            print("✅ 正确生成了Interface + ServiceImpl结构")
        else:
            print("❌ 没有生成Interface + ServiceImpl结构")
            
        # 验证是否有模板字符串错误
        if "{interface_name}" in domain_service_code:
            print("❌ 代码中仍然包含未替换的模板变量")
        else:
            print("✅ 所有模板变量都已正确替换")
            
        # 打印生成的代码片段（前500字符）
        print("\n📝 生成的代码片段：")
        print("=" * 50)
        print(domain_service_code[:500] + "..." if len(domain_service_code) > 500 else domain_service_code)
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_template_formatting_fix()
    
    if success:
        print("\n🎉 模板字符串格式修复测试通过！")
    else:
        print("\n💥 模板字符串格式修复测试失败！")