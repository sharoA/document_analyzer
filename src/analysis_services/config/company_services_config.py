"""
公司服务配置加载器
用于加载和管理公司现有服务信息，为AI生成提供参考
"""

import yaml
import os
import logging
from typing import Dict, List, Any, Optional

class CompanyServicesConfig:
    """公司服务配置管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config_data = None
        self.config_file_path = None
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        # 获取配置文件路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file_path = os.path.join(current_dir, "company_services.yaml")
        
        try:
            if os.path.exists(self.config_file_path):
                with open(self.config_file_path, 'r', encoding='utf-8') as f:
                    self.config_data = yaml.safe_load(f)
                self.logger.info(f"✅ 公司服务配置加载成功: {self.config_file_path}")
                self.logger.info(f"📊 加载了 {len(self.get_existing_services())} 个现有服务")
            else:
                self.logger.warning(f"⚠️ 公司服务配置文件不存在: {self.config_file_path}")
                self.config_data = None
        except Exception as e:
            self.logger.error(f"❌ 加载公司服务配置失败: {e}")
            self.config_data = None
    


    def get_existing_services(self) -> List[Dict[str, Any]]:
        """获取现有服务列表"""
        if self.config_data is None:
            return []
        return self.config_data.get("existing_services", [])
    
    def get_naming_conventions(self) -> Dict[str, str]:
        """获取命名规范"""
        return self.config_data.get("naming_conventions", {})
    
    def get_tech_standards(self) -> Dict[str, Any]:
        """获取技术规范"""
        return self.config_data.get("tech_standards", {})
    
    def get_service_reference_text(self) -> str:
        """获取公司服务参考文本，用于AI生成时的参考"""
        if self.config_data is None:
            return "暂无公司现有服务信息参考。"
        
        existing_services = self.get_existing_services()
        if not existing_services:
            return "暂无公司现有服务信息参考。"
        
        # 构建参考文本
        reference_lines = ["公司现有服务参考信息："]
        
        for idx, service in enumerate(existing_services, 1):
            service_name = service.get("service_name", "未知服务")
            english_name = service.get("service_english_name", "unknown")
            description = service.get("description", "无描述")
            git_repository = service.get("git_repository", "通用")
            
            reference_lines.append(f"{idx}. {service_name} ({english_name})")
            reference_lines.append(f"   业务域: {git_repository}")
            reference_lines.append(f"   描述: {description}")
            
            # 添加技术信息（如果有）
            tech_info = service.get("tech_stack", {})
            if tech_info:
                reference_lines.append(f"   技术栈: {', '.join(tech_info.values()) if isinstance(tech_info, dict) else str(tech_info)}")
            
            reference_lines.append("")  # 空行分隔
        

        return "\n".join(reference_lines)

    
    def suggest_service_name(self, business_description: str) -> Optional[Dict[str, str]]:
        """根据业务描述建议服务名称"""
        conventions = self.get_naming_conventions()
        
        # 简单的业务域提取逻辑（可以后续优化）
        domain_mapping = {
            "用户": "user",
            "订单": "order", 
            "支付": "payment",
            "通知": "notification",
            "文件": "file",
            "数据": "data",
            "分析": "analytics",
            "管理": "management",
            "服务": "service",
            "业务": "business",
            "额度": "limit",
            "组织": "organization"
        }
        
        # 提取关键词
        for chinese, english in domain_mapping.items():
            if chinese in business_description:
                service_pattern = conventions.get("service_pattern", "{business-domain}-service")
                english_name = service_pattern.replace("{business-domain}", english)
                chinese_name = f"{chinese}服务"
                
                return {
                    "service_name": chinese_name,
                    "service_english_name": english_name,
                    "suggested_git": conventions.get("repository_pattern", "").replace("{service-english-name}", english_name)
                }
        
        return None
    
   
    
    def reload_config(self):
        """重新加载配置文件"""
        self._load_config()


# 单例实例
_company_services_config = None

def get_company_services_config() -> CompanyServicesConfig:
    """获取公司服务配置单例"""
    global _company_services_config
    if _company_services_config is None:
        _company_services_config = CompanyServicesConfig()
    return _company_services_config