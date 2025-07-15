#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细检查生成的代码内容
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.corder_integration.code_generator.intelligent_file_reuse_manager import IntelligentFileReuseManager

def examine_generated_code():
    """详细检查生成的代码内容"""
    
    print("🔍 详细检查生成的代码内容")
    print("=" * 80)
    
    # 初始化文件复用管理器
    file_manager = IntelligentFileReuseManager()
    
    # 设置设计文档内容
    design_document = """
    设计文档：
    
    ## 表结构设计
    
    CREATE TABLE T_CUST_MULTIORG_UNIT (
        ID DECIMAL(22,0) NOT NULL COMMENT '主键ID',
        COMPANY_ID DECIMAL(22,0) NOT NULL COMMENT '公司ID',
        UNIT_CODE VARCHAR(50) NOT NULL COMMENT '组织单元编码',
        UNIT_NAME VARCHAR(100) NOT NULL COMMENT '组织单元名称',
        PARENT_UNIT_ID DECIMAL(22,0) COMMENT '父级组织单元ID',
        UNIT_LEVEL INT COMMENT '组织层级',
        UNIT_TYPE VARCHAR(20) COMMENT '组织类型',
        STATUS VARCHAR(10) DEFAULT 'ACTIVE' COMMENT '状态',
        CREATE_TIME TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        UPDATE_TIME TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        PRIMARY KEY (ID)
    ) ENGINE=InnoDB COMMENT='企业组织单元表';
    
    ## 接口设计
    
    接口路径：/general/multiorgManage/queryCompanyUnitList
    业务逻辑：根据查询条件查询组织单元信息，支持按编码、状态等条件筛选
    需要调用用户服务的/userCenter/server/queryCompanyInfo接口获取组织信息
    """
    
    file_manager.set_document_content(design_document)
    
    # 模拟项目结构分析
    project_path = "/mnt/d/gitlab/create_project/链数中建一局_1752557905/crcl-open"
    if os.path.exists(project_path):
        file_manager.analyze_project_structure(project_path)
    
    # 决策文件复用策略
    api_path = "/general/multiorgManage/queryCompanyUnitList"
    interface_name = "CompanyUnitList"
    business_logic = "根据查询条件查询组织单元信息，支持按编码、状态等条件筛选，需要调用用户服务接口"
    
    strategy = file_manager.decide_file_reuse_strategy(
        api_path, interface_name, business_logic
    )
    
    # 生成完整调用链
    input_params = [
        {"name": "companyId", "type": "Long", "description": "公司ID"},
        {"name": "unitCode", "type": "String", "description": "组织单元编码"},
        {"name": "unitName", "type": "String", "description": "组织单元名称"},
        {"name": "status", "type": "String", "description": "状态"}
    ]
    
    output_params = {
        "type": "CompanyUnitListResp",
        "description": "组织单元列表响应"
    }
    
    generated_code = file_manager.generate_complete_calling_chain(
        interface_name, strategy, input_params, output_params, business_logic
    )
    
    # 详细展示每个组件的代码
    for component_type, code in generated_code.items():
        print(f"\n{'='*60}")
        print(f"📝 {component_type.upper()} 代码:")
        print(f"{'='*60}")
        print(code)
        print(f"\n🔍 代码分析:")
        
        if component_type == 'controller_method':
            if 'companyunitlistApplication.CompanyUnitList' in code:
                print("   ✅ Controller包含具体的Application Service调用")
            elif 'companyunitlistDomainService.CompanyUnitList' in code:
                print("   ✅ Controller包含具体的Domain Service调用")
            elif 'TODO' in code:
                print("   ❌ Controller包含TODO，可能是空实现")
            else:
                print("   ❌ Controller没有具体的业务调用")
        
        if component_type == 'feign_client':
            if 'zqyl-user-auth' in code:
                print("   ✅ Feign Client指向正确的用户服务")
            if '/userCenter/server' in code:
                print("   ✅ Feign Client包含正确的服务路径")
        
        if component_type == 'xml_mapping':
            if 'T_CUST_MULTIORG_UNIT' in code:
                print("   ✅ XML使用正确的表名")
            if 'COMPANY_ID' in code and 'UNIT_CODE' in code:
                print("   ✅ XML包含设计文档中的实际字段")

if __name__ == "__main__":
    examine_generated_code()