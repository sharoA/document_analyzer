"""
Controller文件分析器
用于分析Controller文件中的@RequestMapping并匹配API路径关键字
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ControllerAnalyzer:
    """Controller文件分析器"""
    
    def __init__(self):
        """初始化Controller分析器"""
        self.controller_pattern = re.compile(r'@Controller|@RestController')
        self.request_mapping_pattern = re.compile(r'@RequestMapping\s*\(\s*value\s*=\s*["\']([^"\']+)["\']')
        self.class_pattern = re.compile(r'public\s+class\s+(\w+)')
        
    def find_matching_controllers(self, base_path: str, keyword: str) -> List[Dict[str, str]]:
        """
        在指定路径下查找匹配关键字的Controller文件
        
        Args:
            base_path: 基础搜索路径
            keyword: API路径关键字
            
        Returns:
            匹配的Controller文件信息列表
        """
        matching_controllers = []
        
        logger.info(f"🔍 开始分析路径下的Controller文件: {base_path}")
        logger.info(f"🎯 匹配关键字: {keyword}")
        
        # 遍历所有Java文件
        for root, dirs, files in os.walk(base_path):
            for file in files:
                if file.endswith('.java'):
                    file_path = os.path.join(root, file)
                    
                    try:
                        controller_info = self._analyze_controller_file(file_path, keyword)
                        if controller_info:
                            matching_controllers.append(controller_info)
                            logger.info(f"✅ 找到匹配的Controller: {file_path}")
                            
                    except Exception as e:
                        logger.warning(f"⚠️ 分析Controller文件失败 {file_path}: {e}")
        
        logger.info(f"📊 总共找到 {len(matching_controllers)} 个匹配的Controller文件")
        return matching_controllers
    
    def _analyze_controller_file(self, file_path: str, keyword: str) -> Optional[Dict[str, str]]:
        """
        分析单个Controller文件
        
        Args:
            file_path: Controller文件路径
            keyword: 匹配关键字
            
        Returns:
            Controller信息字典，如果不匹配则返回None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否是Controller文件
            if not self.controller_pattern.search(content):
                return None
            
            # 查找@RequestMapping
            mapping_matches = self.request_mapping_pattern.findall(content)
            
            for mapping_value in mapping_matches:
                # 检查是否包含关键字
                if keyword in mapping_value:
                    logger.info(f"🎯 在 {file_path} 中找到匹配的@RequestMapping: {mapping_value}")
                    
                    # 提取类名
                    class_match = self.class_pattern.search(content)
                    class_name = class_match.group(1) if class_match else "Unknown"
                    
                    # 分析依赖的Service
                    services = self._extract_services_from_controller(content)
                    
                    return {
                        'file_path': file_path,
                        'class_name': class_name,
                        'request_mapping': mapping_value,
                        'services': services,
                        'content': content
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 读取Controller文件失败 {file_path}: {e}")
            return None
    
    def _extract_services_from_controller(self, content: str) -> List[Dict[str, str]]:
        """
        从Controller内容中提取Service依赖
        
        Args:
            content: Controller文件内容
            
        Returns:
            Service依赖列表
        """
        services = []
        
        # 查找@Autowired注入的Service
        autowired_pattern = re.compile(r'@Autowired\s*\n\s*private\s+(\w+Service)\s+(\w+);')
        autowired_matches = autowired_pattern.findall(content)
        
        for service_type, service_var in autowired_matches:
            services.append({
                'type': service_type,
                'variable': service_var,
                'injection_type': 'autowired'
            })
        
        # 查找构造器注入的Service
        constructor_pattern = re.compile(r'private\s+final\s+(\w+Service)\s+(\w+);')
        constructor_matches = constructor_pattern.findall(content)
        
        for service_type, service_var in constructor_matches:
            services.append({
                'type': service_type,
                'variable': service_var,
                'injection_type': 'constructor'
            })
        
        logger.info(f"📋 提取到 {len(services)} 个Service依赖")
        return services
    
    def extract_interface_name_from_api_path(self, api_path: str) -> str:
        """
        从API路径中提取接口名称
        
        Args:
            api_path: 完整API路径，如 /crcl-open-api/lsLimit/listUnitLimitByCompanyIdExport
            
        Returns:
            接口名称，如 listUnitLimitByCompanyIdExport
        """
        # 获取路径的最后一部分
        path_parts = api_path.strip('/').split('/')
        interface_name = path_parts[-1] if path_parts else ""
        
        logger.info(f"🔧 从API路径 '{api_path}' 提取接口名称: '{interface_name}'")
        return interface_name
    
    def determine_http_method_from_interface_name(self, interface_name: str) -> str:
        """
        根据接口名称判断HTTP方法
        
        Args:
            interface_name: 接口名称
            
        Returns:
            HTTP方法 (GET, POST, PUT, DELETE)
        """
        interface_lower = interface_name.lower()
        
        if any(prefix in interface_lower for prefix in ['list', 'get', 'query', 'find', 'search']):
            return "GET"
        elif any(prefix in interface_lower for prefix in ['add', 'create', 'insert', 'save']):
            return "POST"
        elif any(prefix in interface_lower for prefix in ['update', 'modify', 'edit']):
            return "PUT"
        elif any(prefix in interface_lower for prefix in ['delete', 'remove']):
            return "DELETE"
        else:
            # 默认GET
            return "GET"
    
    def generate_mapping_annotation(self, interface_name: str, http_method: str) -> str:
        """
        生成映射注解
        
        Args:
            interface_name: 接口名称
            http_method: HTTP方法
            
        Returns:
            映射注解字符串
        """
        if http_method == "GET":
            return f'@GetMapping("/{interface_name}")'
        elif http_method == "POST":
            return f'@PostMapping("/{interface_name}")'
        elif http_method == "PUT":
            return f'@PutMapping("/{interface_name}")'
        elif http_method == "DELETE":
            return f'@DeleteMapping("/{interface_name}")'
        else:
            return f'@RequestMapping(value = "/{interface_name}", method = RequestMethod.{http_method})' 