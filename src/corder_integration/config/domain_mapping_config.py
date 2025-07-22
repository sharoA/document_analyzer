#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
业务领域映射配置管理器
负责读取和管理业务领域映射配置
"""

import os
import logging
import yaml
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class DomainMappingConfig:
    """业务领域映射配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，如果不指定则使用默认路径
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config_data = None
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        current_dir = Path(__file__).parent
        return str(current_dir / "domain_mapping.yaml")
    
    def _load_config(self):
        """加载配置文件"""
        try:
            if not os.path.exists(self.config_path):
                logger.warning(f"⚠️ 业务领域映射配置文件不存在: {self.config_path}")
                self.config_data = self._get_default_config()
                return
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config_data = yaml.safe_load(f)
            
            logger.info(f"✅ 成功加载业务领域映射配置: {self.config_path}")
            
            # 验证配置结构
            if not isinstance(self.config_data, dict):
                raise ValueError("配置文件格式错误：根节点必须是字典")
            
            if 'domain_mappings' not in self.config_data:
                logger.warning("⚠️ 配置文件中缺少 domain_mappings 节点")
                self.config_data['domain_mappings'] = []
            
        except Exception as e:
            logger.error(f"❌ 加载业务领域映射配置失败: {e}")
            self.config_data = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'domain_mappings': [
                {
                    'api_keyword': 'lsLimit',
                    'domain': 'limit',
                    'description': 'ls前缀的limit相关接口映射到额度领域',
                    'priority': 100
                },
                {
                    'api_keyword': 'limit',
                    'domain': 'limit',
                    'description': '直接的limit关键字映射到额度领域',
                    'priority': 90
                },
                {
                    'api_keyword': 'open',
                    'domain': 'open',
                    'description': '开放相关接口映射到开立领域',
                    'priority': 90
                }
            ],
            'domain_priority': {
                'limit': 100,
                'credit': 90,
                'open': 80,
                'general': 70,
                'user': 60,
                'company': 50
            }
        }
    
    def map_api_keyword_to_domain(self, api_keyword: str) -> str:
        """
        将API关键字映射到业务领域
        
        Args:
            api_keyword: API关键字
            
        Returns:
            业务领域名称
        """
        if not api_keyword:
            return api_keyword
        
        logger.info(f"🔍 映射API关键字到业务领域: {api_keyword}")
        
        # 1. 精确匹配（不区分大小写）
        exact_match = self._find_exact_match(api_keyword)
        if exact_match:
            logger.info(f"✅ 精确匹配: {api_keyword} -> {exact_match}")
            return exact_match
        
        # 2. 智能前缀处理（特别处理ls前缀）
        prefix_match = self._find_prefix_match(api_keyword)
        if prefix_match:
            logger.info(f"✅ 前缀匹配: {api_keyword} -> {prefix_match}")
            return prefix_match
        
        # 3. 关键词包含匹配
        keyword_match = self._find_keyword_match(api_keyword)
        if keyword_match:
            logger.info(f"✅ 关键词匹配: {api_keyword} -> {keyword_match}")
            return keyword_match
        
        # 4. 如果都没有匹配，返回原关键字的小写形式
        default_domain = api_keyword.lower()
        logger.info(f"⚠️ 未找到匹配规则，使用默认: {api_keyword} -> {default_domain}")
        return default_domain
    
    def _find_exact_match(self, api_keyword: str) -> Optional[str]:
        """查找精确匹配的映射"""
        domain_mappings = self.config_data.get('domain_mappings', [])
        
        # 按优先级排序
        sorted_mappings = sorted(domain_mappings, key=lambda x: x.get('priority', 0), reverse=True)
        
        for mapping in sorted_mappings:
            if mapping.get('api_keyword', '').lower() == api_keyword.lower():
                return mapping.get('domain')
        
        return None
    
    def _find_prefix_match(self, api_keyword: str) -> Optional[str]:
        """查找前缀匹配的映射（智能处理ls前缀）"""
        api_keyword_lower = api_keyword.lower()
        
        # 特殊处理ls前缀
        if api_keyword_lower.startswith('ls') and len(api_keyword_lower) > 2:
            # 去除ls前缀，获取核心业务词
            core_keyword = api_keyword_lower[2:]
            logger.info(f"🔧 检测到ls前缀，提取核心词: {api_keyword} -> {core_keyword}")
            
            # 检查核心词是否有直接匹配
            core_match = self._find_exact_match(core_keyword)
            if core_match:
                logger.info(f"✅ ls前缀核心词匹配: {core_keyword} -> {core_match}")
                return core_match
        
        return None
    
    def _find_keyword_match(self, api_keyword: str) -> Optional[str]:
        """查找关键词包含匹配的映射"""
        domain_mappings = self.config_data.get('domain_mappings', [])
        api_keyword_lower = api_keyword.lower()
        
        matches = []
        for mapping in domain_mappings:
            keyword = mapping.get('api_keyword', '').lower()
            domain = mapping.get('domain')
            priority = mapping.get('priority', 0)
            
            # 检查是否包含关键词
            if keyword in api_keyword_lower or api_keyword_lower in keyword:
                domain_priority = self._get_domain_priority(domain)
                total_priority = priority + domain_priority
                matches.append((domain, total_priority, keyword))
        
        if matches:
            # 返回优先级最高的匹配
            matches.sort(key=lambda x: x[1], reverse=True)
            best_match = matches[0]
            logger.info(f"🎯 关键词匹配: {api_keyword} 包含 '{best_match[2]}' -> {best_match[0]} (优先级: {best_match[1]})")
            return best_match[0]
        
        return None
    
    def _get_domain_priority(self, domain: str) -> int:
        """获取业务领域的优先级"""
        domain_priority = self.config_data.get('domain_priority', {})
        return domain_priority.get(domain, 0)
    
    def get_all_domain_mappings(self) -> List[Dict[str, Any]]:
        """获取所有业务领域映射"""
        return self.config_data.get('domain_mappings', [])
    
    def get_domain_priority_map(self) -> Dict[str, int]:
        """获取业务领域优先级映射"""
        return self.config_data.get('domain_priority', {})
    
    def add_domain_mapping(self, api_keyword: str, domain: str, 
                          description: str = "", priority: int = 50):
        """
        添加新的业务领域映射
        
        Args:
            api_keyword: API关键字
            domain: 业务领域
            description: 映射描述
            priority: 优先级
        """
        if not self.config_data:
            self.config_data = self._get_default_config()
        
        domain_mappings = self.config_data.get('domain_mappings', [])
        
        # 检查是否已存在
        for mapping in domain_mappings:
            if mapping.get('api_keyword', '').lower() == api_keyword.lower():
                # 更新现有映射
                mapping.update({
                    'domain': domain,
                    'description': description,
                    'priority': priority
                })
                logger.info(f"✅ 更新业务领域映射: {api_keyword} -> {domain}")
                return
        
        # 添加新映射
        new_mapping = {
            'api_keyword': api_keyword,
            'domain': domain,
            'description': description,
            'priority': priority
        }
        domain_mappings.append(new_mapping)
        self.config_data['domain_mappings'] = domain_mappings
        
        logger.info(f"✅ 添加新的业务领域映射: {api_keyword} -> {domain}")
    
    def save_config(self):
        """保存配置到文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config_data, f, default_flow_style=False, 
                         allow_unicode=True, sort_keys=False)
            
            logger.info(f"✅ 业务领域映射配置已保存: {self.config_path}")
            
        except Exception as e:
            logger.error(f"❌ 保存业务领域映射配置失败: {e}")
    
    def reload_config(self):
        """重新加载配置"""
        logger.info("🔄 重新加载业务领域映射配置")
        self._load_config()


# 全局配置实例
_domain_mapping_config = None


def get_domain_mapping_config() -> DomainMappingConfig:
    """获取全局业务领域映射配置实例"""
    global _domain_mapping_config
    if _domain_mapping_config is None:
        _domain_mapping_config = DomainMappingConfig()
    return _domain_mapping_config


def map_api_keyword_to_domain(api_keyword: str) -> str:
    """便捷函数：将API关键字映射到业务领域"""
    config = get_domain_mapping_config()
    return config.map_api_keyword_to_domain(api_keyword)


if __name__ == "__main__":
    # 测试代码
    config = DomainMappingConfig()
    
    # 测试映射
    test_keywords = ["lsLimit", "limit", "open", "multiorgManage", "credit", "company", "unknown"]
    
    print("业务领域映射测试:")
    print("=" * 50)
    for keyword in test_keywords:
        mapped_domain = config.map_api_keyword_to_domain(keyword)
        print(f"{keyword:15} -> {mapped_domain}")
    
    print("\n配置信息:")
    print("=" * 50)
    print(f"配置文件路径: {config.config_path}")
    print(f"映射规则数量: {len(config.get_all_domain_mappings())}")
    print(f"业务领域优先级: {config.get_domain_priority_map()}")