"""
Controller接口管理器
统一管理Controller文件分析、接口添加和Service决策的完整流程
"""
import os
from typing import Dict, List, Optional, Tuple
import logging

from .controller_analyzer import ControllerAnalyzer
from .interface_adder import InterfaceAdder
from .service_decision_maker import ServiceDecisionMaker

logger = logging.getLogger(__name__)


class ControllerInterfaceManager:
    """Controller接口管理器"""
    
    def __init__(self, llm_client=None):
        """
        初始化Controller接口管理器
        
        Args:
            llm_client: LLM客户端，用于智能分析和决策
        """
        self.llm_client = llm_client
        self.analyzer = ControllerAnalyzer()
        self.interface_adder = InterfaceAdder()
        self.service_decision_maker = ServiceDecisionMaker(llm_client)
        
    def process_api_interface_request(self, existing_path: str, keyword: str, 
                                    api_path: str, description: str = "") -> Dict[str, any]:
        """
        处理API接口请求的完整流程
        
        Args:
            existing_path: 找到的现有路径
            keyword: API路径关键字
            api_path: 完整API路径
            description: 接口描述
            
        Returns:
            处理结果
        """
        logger.info(f"🚀 开始处理API接口请求: {api_path}")
        
        try:
            # 步骤1: 分析Controller文件并查找匹配
            matching_controllers = self.analyzer.find_matching_controllers(existing_path, keyword)
            
            if not matching_controllers:
                logger.info(f"⚠️ 未找到匹配关键字 '{keyword}' 的Controller文件")
                return {
                    'success': False,
                    'message': f"未找到匹配关键字 '{keyword}' 的Controller文件",
                    'suggestion': '考虑创建新的Controller文件'
                }
            
            # 步骤2: 提取接口名称并确定HTTP方法
            interface_name = self.analyzer.extract_interface_name_from_api_path(api_path)
            http_method = self.analyzer.determine_http_method_from_interface_name(interface_name)
            
            results = []
            
            # 步骤3: 为每个匹配的Controller处理接口添加
            for controller_info in matching_controllers:
                logger.info(f"📝 处理Controller: {controller_info['class_name']}")
                
                # 步骤4: 分析Service需求
                service_analysis = self.service_decision_maker.analyze_service_requirements(
                    controller_info, interface_name, api_path
                )
                
                # 步骤5: 在Controller中添加新接口
                updated_content = self.interface_adder.add_interface_to_controller(
                    controller_info, interface_name, http_method, api_path, description
                )
                
                # 步骤6: 保存更新后的文件
                save_success = self.interface_adder.save_updated_controller(
                    controller_info['file_path'], updated_content
                )
                
                # 收集结果
                result = {
                    'controller_file': controller_info['file_path'],
                    'controller_class': controller_info['class_name'],
                    'interface_name': interface_name,
                    'http_method': http_method,
                    'service_analysis': service_analysis,
                    'file_updated': save_success
                }
                
                results.append(result)
                
                logger.info(f"✅ Controller {controller_info['class_name']} 处理完成")
            
            return {
                'success': True,
                'message': f"成功处理 {len(results)} 个Controller文件",
                'results': results,
                'interface_name': interface_name,
                'http_method': http_method
            }
            
        except Exception as e:
            logger.error(f"❌ 处理API接口请求失败: {e}")
            return {
                'success': False,
                'message': f"处理失败: {str(e)}",
                'error': str(e)
            }
    
    def analyze_existing_controller_structure(self, existing_path: str) -> Dict[str, any]:
        """
        分析现有Controller结构
        
        Args:
            existing_path: 现有路径
            
        Returns:
            结构分析结果
        """
        logger.info(f"🔍 分析现有Controller结构: {existing_path}")
        
        try:
            # 扫描所有Controller文件
            all_controllers = []
            
            for root, dirs, files in os.walk(existing_path):
                for file in files:
                    if file.endswith('.java'):
                        file_path = os.path.join(root, file)
                        
                        try:
                            controller_info = self.analyzer._analyze_controller_file(file_path, "")
                            if controller_info:
                                # 不需要匹配关键字，只是分析结构
                                controller_info['request_mapping'] = self._extract_all_request_mappings(
                                    controller_info['content']
                                )
                                all_controllers.append(controller_info)
                        except Exception as e:
                            logger.warning(f"⚠️ 分析文件失败 {file_path}: {e}")
            
            # 分析结构统计
            structure_stats = {
                'total_controllers': len(all_controllers),
                'controllers_with_services': len([c for c in all_controllers if c['services']]),
                'common_request_mappings': self._analyze_common_mappings(all_controllers),
                'service_patterns': self._analyze_service_patterns(all_controllers)
            }
            
            return {
                'success': True,
                'controllers': all_controllers,
                'structure_stats': structure_stats
            }
            
        except Exception as e:
            logger.error(f"❌ 分析Controller结构失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_all_request_mappings(self, content: str) -> List[str]:
        """提取所有@RequestMapping值"""
        import re
        pattern = re.compile(r'@RequestMapping\s*\(\s*value\s*=\s*["\']([^"\']+)["\']')
        return pattern.findall(content)
    
    def _analyze_common_mappings(self, controllers: List[Dict]) -> List[Dict[str, any]]:
        """分析常见的RequestMapping模式"""
        mapping_count = {}
        
        for controller in controllers:
            mappings = controller.get('request_mapping', [])
            if isinstance(mappings, list):
                for mapping in mappings:
                    mapping_count[mapping] = mapping_count.get(mapping, 0) + 1
        
        # 排序并返回前10个
        sorted_mappings = sorted(mapping_count.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {'mapping': mapping, 'count': count}
            for mapping, count in sorted_mappings[:10]
        ]
    
    def _analyze_service_patterns(self, controllers: List[Dict]) -> Dict[str, any]:
        """分析Service使用模式"""
        service_types = {}
        injection_types = {'autowired': 0, 'constructor': 0}
        
        for controller in controllers:
            services = controller.get('services', [])
            for service in services:
                service_type = service.get('type', 'Unknown')
                service_types[service_type] = service_types.get(service_type, 0) + 1
                
                injection_type = service.get('injection_type', 'unknown')
                if injection_type in injection_types:
                    injection_types[injection_type] += 1
        
        return {
            'service_types': service_types,
            'injection_patterns': injection_types
        }
    
    def preview_interface_addition(self, controller_path: str, interface_name: str, 
                                 http_method: str, api_path: str, description: str = "") -> Dict[str, any]:
        """
        预览接口添加效果（不实际修改文件）
        
        Args:
            controller_path: Controller文件路径
            interface_name: 接口名称
            http_method: HTTP方法
            api_path: API路径
            description: 接口描述
            
        Returns:
            预览结果
        """
        logger.info(f"👀 预览接口添加: {interface_name} 到 {controller_path}")
        
        try:
            # 读取并分析Controller文件
            controller_info = self.analyzer._analyze_controller_file(controller_path, "")
            
            if not controller_info:
                return {
                    'success': False,
                    'message': f"文件 {controller_path} 不是有效的Controller文件"
                }
            
            # 分析Service需求
            service_analysis = self.service_decision_maker.analyze_service_requirements(
                controller_info, interface_name, api_path
            )
            
            # 生成接口方法代码（不保存）
            new_method_code = self.interface_adder._generate_interface_method(
                interface_name, http_method, api_path, description, 
                controller_info['services']
            )
            
            # 生成需要添加的import
            required_imports = self._get_required_imports(http_method)
            existing_content = controller_info['content']
            missing_imports = [
                imp for imp in required_imports 
                if imp not in existing_content
            ]
            
            return {
                'success': True,
                'controller_info': {
                    'file_path': controller_path,
                    'class_name': controller_info['class_name'],
                    'existing_services': controller_info['services']
                },
                'interface_info': {
                    'name': interface_name,
                    'http_method': http_method,
                    'mapping_annotation': self.analyzer.generate_mapping_annotation(interface_name, http_method)
                },
                'service_analysis': service_analysis,
                'new_method_code': new_method_code,
                'missing_imports': missing_imports
            }
            
        except Exception as e:
            logger.error(f"❌ 预览接口添加失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_required_imports(self, http_method: str) -> List[str]:
        """获取所需的import语句"""
        base_imports = [
            "import org.springframework.http.ResponseEntity;",
            "import org.springframework.http.HttpStatus;",
            "import java.util.Map;"
        ]
        
        if http_method == "GET":
            base_imports.extend([
                "import org.springframework.web.bind.annotation.GetMapping;",
                "import org.springframework.web.bind.annotation.RequestParam;"
            ])
        elif http_method == "POST":
            base_imports.extend([
                "import org.springframework.web.bind.annotation.PostMapping;",
                "import org.springframework.web.bind.annotation.RequestBody;"
            ])
        elif http_method == "PUT":
            base_imports.extend([
                "import org.springframework.web.bind.annotation.PutMapping;",
                "import org.springframework.web.bind.annotation.RequestBody;"
            ])
        elif http_method == "DELETE":
            base_imports.extend([
                "import org.springframework.web.bind.annotation.DeleteMapping;",
                "import org.springframework.web.bind.annotation.RequestParam;"
            ])
        
        return base_imports
    
    def generate_service_recommendations(self, service_analysis: Dict[str, any]) -> List[str]:
        """
        基于Service分析生成具体的实施建议
        
        Args:
            service_analysis: Service分析结果
            
        Returns:
            实施建议列表
        """
        recommendations = []
        decision = service_analysis.get('decision', {})
        action = decision.get('action', '')
        
        if action == 'modify_existing':
            target_service = decision.get('target_service', {})
            service_name = target_service.get('type', 'Service')
            
            recommendations.extend([
                f"在现有Service {service_name} 中添加新方法",
                f"建议方法签名: public XxxResp methodName(Map<String, Object> params)",
                "添加适当的业务逻辑和数据验证",
                "确保异常处理和事务管理正确",
                "更新Service接口定义（如果存在）"
            ])
            
        elif action == 'create_new':
            recommendations.extend([
                "创建新的Service接口和实现类",
                "定义清晰的业务方法签名",
                "配置Spring依赖注入",
                "实现完整的业务逻辑",
                "添加事务管理和异常处理",
                "编写单元测试和集成测试"
            ])
            
        elif action == 'use_existing':
            target_service = decision.get('target_service', {})
            service_name = target_service.get('class_name', 'Service')
            
            recommendations.extend([
                f"在Controller中注入现有Service: {service_name}",
                "验证现有方法是否满足需求",
                "如需要，扩展现有方法的功能",
                "确保方法调用的参数和返回值匹配"
            ])
        
        return recommendations 