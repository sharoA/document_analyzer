"""
Service决策制定器
用于分析Service依赖并决策是否需要新增Service或在现有Service中修改
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ServiceDecisionMaker:
    """Service决策制定器"""
    
    def __init__(self, llm_client=None):
        """
        初始化Service决策制定器
        
        Args:
            llm_client: LLM客户端，用于智能决策
        """
        self.llm_client = llm_client
        self.service_pattern = re.compile(r'@Service|@Component')
        self.application_pattern = re.compile(r'@SpringBootApplication|Application\.class')
        
    def analyze_service_requirements(self, controller_info: Dict[str, str], 
                                   interface_name: str, api_path: str) -> Dict[str, any]:
        """
        分析Service需求
        
        Args:
            controller_info: Controller文件信息
            interface_name: 接口名称
            api_path: API路径
            
        Returns:
            Service需求分析结果
        """
        logger.info(f"🔍 开始分析Service需求: {interface_name}")
        
        existing_services = controller_info.get('services', [])
        controller_path = controller_info.get('file_path', '')
        
        # 分析项目中的Service文件
        project_services = self._scan_project_services(controller_path)
        
        # 分析Application文件
        applications = self._scan_application_files(controller_path)
        
        # 进行智能决策
        decision = self._make_service_decision(
            existing_services, project_services, applications, 
            interface_name, api_path
        )
        
        return {
            'existing_services': existing_services,
            'project_services': project_services,
            'applications': applications,
            'decision': decision,
            'recommendations': self._generate_recommendations(decision)
        }
    
    def _scan_project_services(self, controller_path: str) -> List[Dict[str, str]]:
        """
        扫描项目中的Service文件
        
        Args:
            controller_path: Controller文件路径
            
        Returns:
            Service文件列表
        """
        services = []
        
        # 从Controller路径向上查找项目根目录
        project_root = self._find_project_root(controller_path)
        
        logger.info(f"📂 扫描项目Service文件: {project_root}")
        
        # 扫描所有Java文件，查找Service
        for root, dirs, files in os.walk(project_root):
            for file in files:
                if file.endswith('.java'):
                    file_path = os.path.join(root, file)
                    
                    try:
                        service_info = self._analyze_service_file(file_path)
                        if service_info:
                            services.append(service_info)
                    except Exception as e:
                        logger.warning(f"⚠️ 分析Service文件失败 {file_path}: {e}")
        
        logger.info(f"📊 找到 {len(services)} 个Service文件")
        return services
    
    def _scan_application_files(self, controller_path: str) -> List[Dict[str, str]]:
        """
        扫描Application文件
        
        Args:
            controller_path: Controller文件路径
            
        Returns:
            Application文件列表
        """
        applications = []
        
        # 从Controller路径向上查找项目根目录
        project_root = self._find_project_root(controller_path)
        
        logger.info(f"📂 扫描Application文件: {project_root}")
        
        # 扫描所有Java文件，查找Application
        for root, dirs, files in os.walk(project_root):
            for file in files:
                if file.endswith('.java') and ('Application' in file or 'App.java' in file):
                    file_path = os.path.join(root, file)
                    
                    try:
                        app_info = self._analyze_application_file(file_path)
                        if app_info:
                            applications.append(app_info)
                    except Exception as e:
                        logger.warning(f"⚠️ 分析Application文件失败 {file_path}: {e}")
        
        logger.info(f"📊 找到 {len(applications)} 个Application文件")
        return applications
    
    def _find_project_root(self, file_path: str) -> str:
        """
        查找项目根目录
        
        Args:
            file_path: 文件路径
            
        Returns:
            项目根目录路径
        """
        current_path = Path(file_path).parent
        
        # 向上查找，直到找到src目录的父目录
        while current_path.parent != current_path:
            if (current_path / 'src').exists():
                return str(current_path)
            current_path = current_path.parent
        
        return str(current_path)
    
    def _analyze_service_file(self, file_path: str) -> Optional[Dict[str, str]]:
        """
        分析Service文件
        
        Args:
            file_path: Service文件路径
            
        Returns:
            Service文件信息
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否是Service文件
            if not self.service_pattern.search(content):
                return None
            
            # 提取类名
            class_match = re.search(r'public\s+class\s+(\w+)', content)
            class_name = class_match.group(1) if class_match else "Unknown"
            
            # 提取包名
            package_match = re.search(r'package\s+([^;]+);', content)
            package_name = package_match.group(1) if package_match else ""
            
            # 提取方法名
            methods = self._extract_service_methods(content)
            
            return {
                'file_path': file_path,
                'class_name': class_name,
                'package_name': package_name,
                'methods': methods,
                'content': content
            }
            
        except Exception as e:
            logger.error(f"❌ 读取Service文件失败 {file_path}: {e}")
            return None
    
    def _analyze_application_file(self, file_path: str) -> Optional[Dict[str, str]]:
        """
        分析Application文件
        
        Args:
            file_path: Application文件路径
            
        Returns:
            Application文件信息
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否是Application文件
            if not self.application_pattern.search(content):
                return None
            
            # 提取类名
            class_match = re.search(r'public\s+class\s+(\w+)', content)
            class_name = class_match.group(1) if class_match else "Unknown"
            
            # 提取包名
            package_match = re.search(r'package\s+([^;]+);', content)
            package_name = package_match.group(1) if package_match else ""
            
            return {
                'file_path': file_path,
                'class_name': class_name,
                'package_name': package_name,
                'content': content
            }
            
        except Exception as e:
            logger.error(f"❌ 读取Application文件失败 {file_path}: {e}")
            return None
    
    def _extract_service_methods(self, content: str) -> List[str]:
        """
        提取Service中的方法名
        
        Args:
            content: Service文件内容
            
        Returns:
            方法名列表
        """
        # 查找public方法
        method_pattern = re.compile(r'public\s+\w+\s+(\w+)\s*\([^)]*\)')
        methods = method_pattern.findall(content)
        
        # 过滤掉构造器和getter/setter
        filtered_methods = [
            method for method in methods 
            if not method.startswith('get') 
            and not method.startswith('set')
            and not method[0].isupper()  # 排除构造器
        ]
        
        return filtered_methods
    
    def _make_service_decision(self, existing_services: List[Dict[str, str]], 
                             project_services: List[Dict[str, str]], 
                             applications: List[Dict[str, str]],
                             interface_name: str, api_path: str) -> Dict[str, any]:
        """
        进行Service决策
        
        Args:
            existing_services: Controller中现有的Service
            project_services: 项目中的Service文件
            applications: Application文件
            interface_name: 接口名称
            api_path: API路径
            
        Returns:
            决策结果
        """
        logger.info(f"🤔 进行Service决策: {interface_name}")
        
        # 如果有LLM客户端，使用智能决策
        if self.llm_client:
            return self._make_decision_with_llm(
                existing_services, project_services, applications, 
                interface_name, api_path
            )
        else:
            return self._make_decision_with_rules(
                existing_services, project_services, applications, 
                interface_name, api_path
            )
    
    def _make_decision_with_llm(self, existing_services: List[Dict[str, str]], 
                              project_services: List[Dict[str, str]], 
                              applications: List[Dict[str, str]],
                              interface_name: str, api_path: str) -> Dict[str, any]:
        """
        使用LLM进行智能决策
        
        Returns:
            LLM决策结果
        """
        # 构建提示词
        prompt = self._build_service_decision_prompt(
            existing_services, project_services, applications, 
            interface_name, api_path
        )
        
        try:
            # 调用LLM
            response = self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            # 解析LLM响应
            decision = self._parse_llm_decision_response(response)
            logger.info(f"🤖 LLM决策完成: {decision}")
            return decision
            
        except Exception as e:
            logger.error(f"❌ LLM决策失败: {e}")
            # 回退到规则决策
            return self._make_decision_with_rules(
                existing_services, project_services, applications, 
                interface_name, api_path
            )
    
    def _make_decision_with_rules(self, existing_services: List[Dict[str, str]], 
                                project_services: List[Dict[str, str]], 
                                applications: List[Dict[str, str]],
                                interface_name: str, api_path: str) -> Dict[str, any]:
        """
        使用规则进行决策
        
        Returns:
            规则决策结果
        """
        decision = {
            'action': '',
            'target_service': None,
            'reason': '',
            'need_new_service': False,
            'modify_existing': False
        }
        
        # 规则1: 如果Controller中已有相关Service，优先使用现有Service
        if existing_services:
            for service in existing_services:
                service_name = service.get('type', '')
                if self._is_related_service(service_name, interface_name):
                    decision.update({
                        'action': 'modify_existing',
                        'target_service': service,
                        'reason': f'在现有Service {service_name} 中添加方法',
                        'modify_existing': True
                    })
                    return decision
        
        # 规则2: 查找项目中是否有相关的Service
        for service in project_services:
            service_name = service.get('class_name', '')
            if self._is_related_service(service_name, interface_name):
                decision.update({
                    'action': 'use_existing',
                    'target_service': service,
                    'reason': f'使用项目中现有的Service: {service_name}',
                    'modify_existing': True
                })
                return decision
        
        # 规则3: 创建新的Service
        decision.update({
            'action': 'create_new',
            'target_service': None,
            'reason': f'为{interface_name}创建新的Service',
            'need_new_service': True
        })
        
        return decision
    
    def _is_related_service(self, service_name: str, interface_name: str) -> bool:
        """
        判断Service是否与接口相关
        
        Args:
            service_name: Service名称
            interface_name: 接口名称
            
        Returns:
            是否相关
        """
        # 提取关键词进行匹配
        service_keywords = re.findall(r'[A-Z][a-z]+', service_name)
        interface_keywords = re.findall(r'[A-Z][a-z]+', interface_name)
        
        # 检查是否有交集
        common_keywords = set(service_keywords) & set(interface_keywords)
        return len(common_keywords) > 0
    
    def _build_service_decision_prompt(self, existing_services: List[Dict[str, str]], 
                                     project_services: List[Dict[str, str]], 
                                     applications: List[Dict[str, str]],
                                     interface_name: str, api_path: str) -> str:
        """构建Service决策提示词"""
        
        prompt = f"""
# Service决策分析

## 需要实现的接口
- 接口名称: {interface_name}
- API路径: {api_path}

## Controller中现有的Service依赖
"""
        
        if existing_services:
            for service in existing_services:
                prompt += f"- {service.get('type', 'Unknown')}: {service.get('variable', 'unknown')}\n"
        else:
            prompt += "- 无现有Service依赖\n"
        
        prompt += "\n## 项目中发现的Service文件\n"
        
        if project_services:
            for service in project_services[:5]:  # 限制显示前5个
                methods = ', '.join(service.get('methods', [])[:3])  # 显示前3个方法
                prompt += f"- {service.get('class_name', 'Unknown')}: {methods}\n"
        else:
            prompt += "- 无相关Service文件\n"
        
        prompt += f"""
## 请分析并决策:

1. 是否应该在现有Service中添加{interface_name}方法？
2. 是否应该创建新的Service来实现{interface_name}？
3. 如果修改现有Service，应该选择哪个Service？

请以JSON格式回复决策结果:
{{
    "action": "modify_existing/create_new/use_existing",
    "target_service": "服务名称或null",
    "reason": "决策理由",
    "need_new_service": true/false,
    "modify_existing": true/false
}}
"""
        
        return prompt
    
    def _parse_llm_decision_response(self, response: str) -> Dict[str, any]:
        """
        解析LLM决策响应
        
        Args:
            response: LLM响应
            
        Returns:
            解析后的决策结果
        """
        try:
            import json
            
            # 提取JSON部分
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = response[json_start:json_end]
                decision = json.loads(json_str)
                return decision
            else:
                raise ValueError("无法找到JSON格式的决策结果")
                
        except Exception as e:
            logger.error(f"❌ 解析LLM决策响应失败: {e}")
            # 返回默认决策
            return {
                'action': 'create_new',
                'target_service': None,
                'reason': 'LLM响应解析失败，创建新Service',
                'need_new_service': True,
                'modify_existing': False
            }
    
    def _generate_recommendations(self, decision: Dict[str, any]) -> List[str]:
        """
        生成推荐建议
        
        Args:
            decision: 决策结果
            
        Returns:
            推荐建议列表
        """
        recommendations = []
        
        action = decision.get('action', '')
        
        if action == 'modify_existing':
            recommendations.extend([
                "在现有Service中添加新方法",
                "确保方法命名符合业务逻辑",
                "添加适当的事务处理",
                "编写单元测试验证功能"
            ])
        elif action == 'create_new':
            recommendations.extend([
                "创建新的Service类",
                "实现Service接口",
                "配置依赖注入",
                "添加异常处理机制",
                "编写完整的单元测试"
            ])
        elif action == 'use_existing':
            recommendations.extend([
                "在Controller中注入现有Service",
                "验证Service方法的兼容性",
                "检查返回类型是否匹配",
                "添加适当的错误处理"
            ])
        
        return recommendations 