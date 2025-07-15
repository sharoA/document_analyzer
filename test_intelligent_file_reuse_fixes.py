#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试智能文件复用管理器的修复
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MockLLMClient:
    """模拟LLM客户端"""
    
    def chat(self, messages, temperature=0.3):
        """模拟聊天接口"""
        return "Mock LLM Response"

def test_intelligent_file_reuse_fixes():
    """测试智能文件复用管理器的修复"""
    
    try:
        # 1. 导入所需模块
        from src.corder_integration.code_generator.intelligent_file_reuse_manager import IntelligentFileReuseManager
        
        # 2. 读取设计文档
        document_path = "/mnt/d/ai_project/document_analyzer/combined_document_demo.txt"
        with open(document_path, 'r', encoding='utf-8') as f:
            design_document = f.read()
        
        logger.info(f"✅ 读取设计文档成功，长度: {len(design_document)}")
        
        # 3. 初始化智能文件复用管理器（使用模拟客户端）
        mock_client = MockLLMClient()
        file_manager = IntelligentFileReuseManager(mock_client)
        
        # 4. 设置设计文档内容
        file_manager.set_document_content(design_document)
        logger.info("✅ 设置设计文档内容成功")
        
        # 5. 测试项目路径
        test_project_path = "/mnt/d/gitlab/create_project/链数中建一局_1752562693/zqyl-user-center-service"
        
        # 6. 分析项目结构
        project_structure = file_manager.analyze_project_structure(test_project_path)
        logger.info(f"✅ 分析项目结构成功，base_package: {project_structure.get('base_package', 'unknown')}")
        
        # 7. 测试决策文件复用策略
        interface_name = "CompanyUnitList"
        api_path = "/general/multiorgManage/queryCompanyUnitList"
        business_logic = "根据查询条件查询组织单元信息，支持按编码、状态等条件筛选"
        
        reuse_strategy = file_manager.decide_file_reuse_strategy(
            api_path, interface_name, business_logic
        )
        
        logger.info("✅ 文件复用策略决策成功:")
        for component, strategy in reuse_strategy.items():
            logger.info(f"   {component}: {strategy['action']} - {strategy['reason']}")
        
        # 8. 定义测试参数
        input_params = [
            {"name": "unitCode", "type": "String", "description": "组织单元编码"},
            {"name": "openStatus", "type": "Integer", "description": "组织单元状态"},
            {"name": "unitList", "type": "List<Long>", "description": "组织单元id列表"}
        ]
        
        output_params = {
            "unitId": "组织单元id",
            "unitTypeDicType": "组织单元类型",
            "unitTypeId": "组织单元类型表id",
            "openStatus": "组织单元状态",
            "unitCode": "组织编号",
            "unitName": "组织单元名称"
        }
        
        # 9. 生成完整调用链
        complete_calling_chain = file_manager.generate_complete_calling_chain(
            interface_name, reuse_strategy, input_params, output_params, business_logic
        )
        
        if complete_calling_chain:
            logger.info(f"✅ 生成完整调用链成功，包含 {len(complete_calling_chain)} 个组件")
            
            # 10. 验证修复结果
            logger.info("🔍 验证修复结果:")
            
            # 检查Service接口和实现类
            if 'domain_service' in complete_calling_chain:
                service_interface = complete_calling_chain['domain_service']
                logger.info("✅ 生成了Service接口")
                
                # 检查接口声明
                if f"public interface {interface_name}Service" in service_interface:
                    logger.info("✅ Service接口结构正确")
                else:
                    logger.error("❌ Service接口结构错误")
                
                # 检查方法名（驼峰命名）
                method_name = interface_name[0].lower() + interface_name[1:]  # companyUnitList
                if f"{interface_name}Resp {method_name}({interface_name}Req request)" in service_interface:
                    logger.info("✅ 方法名驼峰命名正确")
                else:
                    logger.error("❌ 方法名驼峰命名错误")
                    
            if 'domain_service_impl' in complete_calling_chain:
                service_impl = complete_calling_chain['domain_service_impl']
                logger.info("✅ 生成了ServiceImpl实现类")
                
                # 检查实现类声明
                if f"public class {interface_name}ServiceImpl implements {interface_name}Service" in service_impl:
                    logger.info("✅ ServiceImpl实现类结构正确")
                else:
                    logger.error("❌ ServiceImpl实现类结构错误")
                    
                # 检查@Override注解
                if "@Override" in service_impl:
                    logger.info("✅ 包含@Override注解")
                else:
                    logger.error("❌ 缺少@Override注解")
            
            # 检查XML字段映射
            if 'xml_mapping' in complete_calling_chain:
                xml_mapping = complete_calling_chain['xml_mapping']
                logger.info("✅ 生成了XML映射")
                
                # 检查是否包含设计文档中的字段
                expected_fields = ['company_id', 'mutilorg_id', 'unit_code', 'unit_name', 'platform_type', 'status']
                found_fields = []
                
                for field in expected_fields:
                    if field.upper() in xml_mapping or field.lower() in xml_mapping:
                        found_fields.append(field)
                
                if len(found_fields) > 2:  # 至少找到几个字段
                    logger.info(f"✅ XML包含设计文档字段: {found_fields}")
                else:
                    logger.warning(f"⚠️ XML字段可能不完整，找到: {found_fields}")
                    
                # 检查表名
                if 'T_CUST_MULTIORG_UNIT' in xml_mapping:
                    logger.info("✅ 使用了正确的表名")
                else:
                    logger.warning("⚠️ 可能使用了默认表名")
            
            # 打印部分生成代码用于检查
            logger.info("\n" + "="*50)
            logger.info("生成的Service接口代码片段:")
            logger.info("="*50)
            if 'domain_service' in complete_calling_chain:
                service_lines = complete_calling_chain['domain_service'].split('\n')
                for i, line in enumerate(service_lines[:20]):
                    logger.info(f"{i+1:2d}: {line}")
            
            logger.info("\n" + "="*50)
            logger.info("生成的ServiceImpl实现类代码片段:")
            logger.info("="*50)
            if 'domain_service_impl' in complete_calling_chain:
                impl_lines = complete_calling_chain['domain_service_impl'].split('\n')
                for i, line in enumerate(impl_lines[:25]):
                    logger.info(f"{i+1:2d}: {line}")
            
            logger.info("\n" + "="*50)
            logger.info("生成的XML映射代码片段:")
            logger.info("="*50)
            if 'xml_mapping' in complete_calling_chain:
                xml_lines = complete_calling_chain['xml_mapping'].split('\n')
                for i, line in enumerate(xml_lines[:30]):
                    logger.info(f"{i+1:2d}: {line}")
            
        else:
            logger.error("❌ 生成完整调用链失败")
            
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_intelligent_file_reuse_fixes()