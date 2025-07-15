#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试智能文件复用系统 - 使用真实项目路径
验证用户反馈的三个问题是否已解决
"""

import os
import sys
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.corder_integration.code_generator.intelligent_file_reuse_manager import IntelligentFileReuseManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_with_real_project_paths():
    """测试真实项目路径的文件复用功能"""
    
    print("🚀 测试智能文件复用系统 - 真实项目路径验证")
    print("=" * 80)
    
    # 初始化文件复用管理器
    file_manager = IntelligentFileReuseManager()
    
    # 真实项目路径
    real_project_paths = [
        "/mnt/d/gitlab/create_project/链数中建一局_1752557905/zqyl-user-center-service/user-basic-service/user-basic-general",
        "/mnt/d/gitlab/create_project/链数中建一局_1752557905/crcl-open"
    ]
    
    # 设置设计文档内容，包含CREATE TABLE语句
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
    
    for project_path in real_project_paths:
        print(f"\n🔍 测试项目路径: {project_path}")
        print("-" * 60)
        
        if not os.path.exists(project_path):
            print(f"⚠️ 路径不存在，跳过: {project_path}")
            continue
        
        try:
            # 设置设计文档内容
            file_manager.set_document_content(design_document)
            
            # 分析项目结构
            project_structure = file_manager.analyze_project_structure(project_path)
            
            print(f"📊 项目结构分析结果:")
            print(f"   Controllers: {len(project_structure['controllers'])}")
            print(f"   Application Services: {len(project_structure['application_services'])}")
            print(f"   Domain Services: {len(project_structure['domain_services'])}")
            print(f"   Mappers: {len(project_structure['mappers'])}")
            print(f"   Feign Clients: {len(project_structure['feign_clients'])}")
            print(f"   XML Files: {len(project_structure['xml_files'])}")
            print(f"   Base Package: {project_structure['base_package']}")
            
            # 决策文件复用策略
            api_path = "/general/multiorgManage/queryCompanyUnitList"
            interface_name = "CompanyUnitList"
            business_logic = "根据查询条件查询组织单元信息，支持按编码、状态等条件筛选，需要调用用户服务接口"
            
            strategy = file_manager.decide_file_reuse_strategy(
                api_path, interface_name, business_logic
            )
            
            print(f"\n📋 文件复用策略:")
            for component, decision in strategy.items():
                icon = "🔄" if decision['action'] == 'add_method' else "🆕"
                print(f"   {icon} {component}: {decision['action']} - {decision['reason']}")
                if decision.get('target_file'):
                    print(f"      目标文件: {decision['target_file']}")
            
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
            
            print(f"\n🔗 生成的调用链组件:")
            for component_type, code in generated_code.items():
                print(f"   📝 {component_type}: {len(code)} 字符")
                
                # 检查关键改进点
                if component_type == 'controller_method':
                    if 'Application' in code and 'Service' in code:
                        print(f"      ✅ Controller包含具体的Service调用，非空实现")
                    else:
                        print(f"      ❌ Controller仍然是空实现")
                
                if component_type == 'feign_client':
                    if 'zqyl-user-auth' in code and '/userCenter/server' in code:
                        print(f"      ✅ Feign Client包含具体的服务调用配置")
                    else:
                        print(f"      ❌ Feign Client配置不正确")
                
                if component_type == 'xml_mapping':
                    if 'T_CUST_MULTIORG_UNIT' in code:
                        print(f"      ✅ XML映射使用设计文档中的实际表名")
                    elif 'COMPANY_ID' in code and 'UNIT_CODE' in code:
                        print(f"      ✅ XML映射包含设计文档中的实际字段")
                    else:
                        print(f"      ❌ XML映射仍然使用模板字段")
                
                # 显示代码预览
                preview = code[:150].replace('\n', ' ')
                print(f"      预览: {preview}...")
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🎯 关键改进验证:")
    print(f"   1. Controller路径生成: 检查是否生成在正确的用户服务路径下")
    print(f"   2. XML字段映射: 检查是否使用设计文档中的实际表结构")
    print(f"   3. Controller业务逻辑: 检查是否包含实际的Feign调用而非空实现")
    
    print(f"\n🎉 真实项目路径测试完成")

if __name__ == "__main__":
    test_with_real_project_paths()