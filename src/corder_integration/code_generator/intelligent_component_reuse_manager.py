"""
智能组件复用管理器
处理Controller接口之间的组件复用和接口逻辑合并
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
import logging

logger = logging.getLogger(__name__)


class IntelligentComponentReuseManager:
    """智能组件复用管理器"""
    
    def __init__(self, llm_client=None):
        """
        初始化智能组件复用管理器
        
        Args:
            llm_client: LLM客户端，用于智能分析
        """
        self.llm_client = llm_client
        self.component_cache = {}  # 缓存已分析的组件
        self.interface_patterns = {}  # 接口模式缓存
        
    def analyze_controller_component_dependencies(self, controller_path: str) -> Dict[str, any]:
        """
        分析Controller中的组件依赖关系
        
        Args:
            controller_path: Controller文件路径
            
        Returns:
            组件依赖分析结果
        """
        logger.info(f"🔍 分析Controller组件依赖: {controller_path}")
        
        try:
            with open(controller_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取组件依赖信息
            dependencies = self._extract_component_dependencies(content)
            
            # 分析Feign Client依赖
            feign_clients = self._extract_feign_clients(content, controller_path)
            
            # 分析Service依赖
            service_dependencies = self._extract_service_dependencies(content)
            
            # 分析方法模式
            method_patterns = self._analyze_method_patterns(content)
            
            return {
                'controller_path': controller_path,
                'dependencies': dependencies,
                'feign_clients': feign_clients,
                'service_dependencies': service_dependencies,
                'method_patterns': method_patterns,
                'analysis_timestamp': self._get_timestamp()
            }
            
        except Exception as e:
            logger.error(f"❌ 分析Controller组件依赖失败: {e}")
            return {'error': str(e)}
    
    def find_reusable_feign_clients(self, target_controller: str, api_path: str, 
                                   business_domain: str) -> List[Dict[str, any]]:
        """
        查找可复用的Feign Client类
        
        Args:
            target_controller: 目标Controller路径
            api_path: API路径
            business_domain: 业务域
            
        Returns:
            可复用的Feign Client列表
        """
        logger.info(f"🔍 查找可复用的Feign Client: {business_domain}")
        
        reusable_clients = []
        
        # 提取业务域关键字
        domain_keywords = self._extract_domain_keywords(api_path, business_domain)
        
        # 搜索项目中的Feign Client
        project_root = self._find_project_root(target_controller)
        feign_clients = self._scan_feign_clients(project_root)
        
        for client in feign_clients:
            # 计算相似度
            similarity_score = self._calculate_feign_client_similarity(
                client, domain_keywords, api_path
            )
            
            if similarity_score > 0.6:  # 相似度阈值
                reusable_clients.append({
                    'client_info': client,
                    'similarity_score': similarity_score,
                    'reuse_recommendation': self._generate_reuse_recommendation(client, similarity_score)
                })
        
        # 按相似度排序
        reusable_clients.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        logger.info(f"✅ 找到 {len(reusable_clients)} 个可复用的Feign Client")
        return reusable_clients
    
    def merge_similar_interface_logic(self, interface_name: str, existing_methods: List[Dict], 
                                     new_interface_type: str) -> Dict[str, any]:
        """
        合并相似接口逻辑
        
        Args:
            interface_name: 接口名称
            existing_methods: 现有方法列表
            new_interface_type: 新接口类型 (query_list, export_list, etc.)
            
        Returns:
            合并策略结果
        """
        logger.info(f"🔄 分析接口逻辑合并: {interface_name} ({new_interface_type})")
        
        # 识别相似接口模式
        similar_patterns = self._identify_similar_patterns(interface_name, existing_methods, new_interface_type)
        
        if similar_patterns:
            # 生成合并策略
            merge_strategy = self._generate_merge_strategy(similar_patterns, new_interface_type)
            
            return {
                'can_merge': True,
                'merge_strategy': merge_strategy,
                'similar_patterns': similar_patterns,
                'shared_logic': self._extract_shared_logic(similar_patterns),
                'special_handling': self._get_special_handling(new_interface_type)
            }
        else:
            return {
                'can_merge': False,
                'reason': '未找到相似的接口模式',
                'recommendation': '创建独立的接口实现'
            }
    
    def generate_shared_service_method(self, base_method: Dict[str, any], 
                                     interface_variants: List[str]) -> Dict[str, any]:
        """
        生成共享的Service方法
        
        Args:
            base_method: 基础方法信息
            interface_variants: 接口变体列表 (query, export, etc.)
            
        Returns:
            共享方法生成结果
        """
        logger.info(f"🏗️ 生成共享Service方法: {base_method.get('name', 'unknown')}")
        
        # 分析方法签名
        method_signature = self._analyze_method_signature(base_method)
        
        # 生成共享的核心逻辑
        shared_logic = self._generate_shared_logic(method_signature, interface_variants)
        
        # 生成接口特定的处理逻辑
        variant_handlers = {}
        for variant in interface_variants:
            variant_handlers[variant] = self._generate_variant_handler(variant, method_signature)
        
        return {
            'shared_method': {
                'name': f"{method_signature['base_name']}Data",
                'signature': self._build_shared_method_signature(method_signature),
                'logic': shared_logic,
                'return_type': 'List<Map<String, Object>>'
            },
            'variant_methods': variant_handlers,
            'dependencies': self._extract_method_dependencies(base_method)
        }
    
    def generate_export_enhanced_method(self, base_method: Dict[str, any], 
                                      export_config: Dict[str, any]) -> str:
        """
        生成导出增强方法
        
        Args:
            base_method: 基础查询方法
            export_config: 导出配置
            
        Returns:
            导出方法代码
        """
        logger.info(f"📄 生成导出增强方法: {base_method.get('name', 'unknown')}")
        
        base_name = base_method.get('name', 'query')
        export_method_name = f"{base_name}Export"
        
        # 生成导出方法代码
        export_method_code = f"""
    /**
     * {base_method.get('description', '数据')}导出
     * 基于{base_name}方法的数据，生成Excel文件
     */
    @GetMapping("/{base_name}/export")
    public ResponseEntity<byte[]> {export_method_name}(@RequestParam Map<String, Object> params) {{
        try {{
            // 1. 调用基础查询方法获取数据
            List<Map<String, Object>> data = {base_name}Data(params);
            
            // 2. 生成Excel文件
            String fileName = "{base_method.get('description', '数据')}导出_" + 
                            LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss"));
            
            byte[] excelBytes = excelExportService.exportToExcel(data, 
                "{base_method.get('description', '数据')}导出", {self._generate_excel_columns(base_method)});
            
            // 3. 设置响应头
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_OCTET_STREAM);
            headers.setContentDispositionFormData("attachment", fileName + ".xlsx");
            
            return ResponseEntity.ok()
                    .headers(headers)
                    .body(excelBytes);
                    
        }} catch (Exception e) {{
            logger.error("导出{base_method.get('description', '数据')}失败", e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }}
    }}
    
    /**
     * {base_method.get('description', '数据')}查询 - 共享数据获取逻辑
     */
    private List<Map<String, Object>> {base_name}Data(Map<String, Object> params) {{
        // 调用Feign Client或Service获取数据
        return {base_method.get('service_call', 'dataService.queryData(params)')};
    }}"""
        
        return export_method_code
    
    def update_controller_with_component_reuse(self, controller_path: str, 
                                             reuse_plan: Dict[str, any]) -> Dict[str, any]:
        """
        更新Controller以支持组件复用
        
        Args:
            controller_path: Controller文件路径
            reuse_plan: 复用计划
            
        Returns:
            更新结果
        """
        logger.info(f"🔄 更新Controller支持组件复用: {controller_path}")
        
        try:
            # 读取现有Controller内容
            with open(controller_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            updated_content = content
            added_components = []
            
            # 添加Feign Client依赖
            if 'feign_clients' in reuse_plan:
                for client in reuse_plan['feign_clients']:
                    if not self._is_component_already_injected(content, client['class_name']):
                        updated_content = self._inject_feign_client(updated_content, client)
                        added_components.append(f"FeignClient: {client['class_name']}")
            
            # 添加共享方法
            if 'shared_methods' in reuse_plan:
                for method in reuse_plan['shared_methods']:
                    updated_content = self._add_shared_method(updated_content, method)
                    added_components.append(f"SharedMethod: {method['name']}")
            
            # 添加导出增强方法
            if 'export_methods' in reuse_plan:
                for method in reuse_plan['export_methods']:
                    updated_content = self._add_export_method(updated_content, method)
                    added_components.append(f"ExportMethod: {method['name']}")
            
            # 添加必要的import
            updated_content = self._add_required_imports(updated_content, reuse_plan)
            
            # 保存更新后的文件
            with open(controller_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            return {
                'success': True,
                'message': f"成功更新Controller，添加了 {len(added_components)} 个组件",
                'added_components': added_components
            }
            
        except Exception as e:
            logger.error(f"❌ 更新Controller失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # ==================== 私有方法 ====================
    
    def _extract_component_dependencies(self, content: str) -> List[Dict[str, any]]:
        """提取组件依赖"""
        dependencies = []
        
        # 查找@Autowired注解的字段
        autowired_pattern = re.compile(r'@Autowired\s+private\s+(\w+)\s+(\w+);')
        for match in autowired_pattern.finditer(content):
            dependencies.append({
                'type': 'autowired',
                'class_name': match.group(1),
                'variable_name': match.group(2)
            })
        
        # 查找构造器注入
        constructor_pattern = re.compile(r'public\s+\w+\s*\([^)]*(\w+)\s+(\w+)[^)]*\)')
        for match in constructor_pattern.finditer(content):
            dependencies.append({
                'type': 'constructor',
                'class_name': match.group(1),
                'variable_name': match.group(2)
            })
        
        return dependencies
    
    def _extract_feign_clients(self, content: str, controller_path: str) -> List[Dict[str, any]]:
        """提取Feign Client依赖"""
        feign_clients = []
        
        # 查找Feign Client注入
        feign_pattern = re.compile(r'@Autowired\s+private\s+(\w+)\s+(\w+);')
        for match in feign_pattern.finditer(content):
            class_name = match.group(1)
            variable_name = match.group(2)
            
            # 检查是否是Feign Client（通过命名规则或注解）
            if 'feign' in class_name.lower() or 'client' in class_name.lower():
                feign_clients.append({
                    'class_name': class_name,
                    'variable_name': variable_name,
                    'business_domain': self._extract_business_domain_from_class(class_name),
                    'controller_path': controller_path
                })
        
        return feign_clients
    
    def _extract_service_dependencies(self, content: str) -> List[Dict[str, any]]:
        """提取Service依赖"""
        services = []
        
        service_pattern = re.compile(r'@Autowired\s+private\s+(\w+Service)\s+(\w+);')
        for match in service_pattern.finditer(content):
            services.append({
                'class_name': match.group(1),
                'variable_name': match.group(2)
            })
        
        return services
    
    def _analyze_method_patterns(self, content: str) -> List[Dict[str, any]]:
        """分析方法模式"""
        patterns = []
        
        # 查找公共方法
        method_pattern = re.compile(r'@(\w+Mapping)\s*\([^)]*\)\s*public\s+[^{]+\s+(\w+)\s*\([^)]*\)\s*{')
        for match in method_pattern.finditer(content):
            mapping_type = match.group(1)
            method_name = match.group(2)
            
            # 分析方法类型
            method_type = self._classify_method_type(method_name)
            
            patterns.append({
                'mapping_type': mapping_type,
                'method_name': method_name,
                'method_type': method_type,
                'business_operation': self._extract_business_operation(method_name)
            })
        
        return patterns
    
    def _extract_domain_keywords(self, api_path: str, business_domain: str) -> List[str]:
        """提取业务域关键字"""
        keywords = []
        
        # 从API路径提取
        path_parts = [part for part in api_path.split('/') if part]
        keywords.extend(path_parts)
        
        # 从业务域提取
        if business_domain:
            keywords.append(business_domain)
        
        return list(set(keywords))
    
    def _find_project_root(self, file_path: str) -> str:
        """查找项目根目录"""
        current_path = Path(file_path).parent
        
        while current_path.parent != current_path:
            if (current_path / 'src').exists():
                return str(current_path)
            current_path = current_path.parent
        
        return str(current_path)
    
    def _scan_feign_clients(self, project_root: str) -> List[Dict[str, any]]:
        """扫描项目中的Feign Client"""
        feign_clients = []
        
        for root, dirs, files in os.walk(project_root):
            if 'feign' in root.lower() or 'client' in root.lower():
                for file in files:
                    if file.endswith('.java'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            if '@FeignClient' in content:
                                client_info = self._parse_feign_client(content, file_path)
                                if client_info:
                                    feign_clients.append(client_info)
                        except Exception as e:
                            logger.warning(f"⚠️ 解析Feign Client失败 {file_path}: {e}")
        
        return feign_clients
    
    def _parse_feign_client(self, content: str, file_path: str) -> Optional[Dict[str, any]]:
        """解析Feign Client信息"""
        # 提取类名
        class_match = re.search(r'public\s+interface\s+(\w+)', content)
        if not class_match:
            return None
        
        class_name = class_match.group(1)
        
        # 提取@FeignClient注解信息
        feign_annotation = re.search(r'@FeignClient\s*\([^)]*\)', content)
        feign_config = feign_annotation.group(0) if feign_annotation else ""
        
        # 提取方法签名
        methods = re.findall(r'@\w+Mapping\s*\([^)]*\)\s*[^;]+;', content)
        
        return {
            'class_name': class_name,
            'file_path': file_path,
            'feign_config': feign_config,
            'methods': methods,
            'business_domain': self._extract_business_domain_from_class(class_name)
        }
    
    def _calculate_feign_client_similarity(self, client: Dict[str, any], 
                                         domain_keywords: List[str], api_path: str) -> float:
        """计算Feign Client相似度"""
        score = 0.0
        
        client_name = client['class_name'].lower()
        business_domain = client.get('business_domain', '').lower()
        
        # 关键字匹配
        for keyword in domain_keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in client_name:
                score += 0.3
            if keyword_lower in business_domain:
                score += 0.2
        
        # 路径匹配
        for keyword in domain_keywords:
            if keyword.lower() in api_path.lower():
                score += 0.1
        
        return min(score, 1.0)
    
    def _generate_reuse_recommendation(self, client: Dict[str, any], similarity_score: float) -> str:
        """生成复用建议"""
        if similarity_score > 0.8:
            return f"强烈推荐复用 {client['class_name']}，业务域高度匹配"
        elif similarity_score > 0.6:
            return f"推荐复用 {client['class_name']}，需要适当调整"
        else:
            return f"可以考虑复用 {client['class_name']}，但需要仔细评估"
    
    def _identify_similar_patterns(self, interface_name: str, existing_methods: List[Dict], 
                                 new_interface_type: str) -> List[Dict[str, any]]:
        """识别相似的接口模式"""
        similar_patterns = []
        
        for method in existing_methods:
            method_name = method.get('method_name', '')
            method_type = method.get('method_type', '')
            
            # 检查是否是相似的操作
            if self._is_similar_operation(method_type, new_interface_type):
                similar_patterns.append({
                    'method': method,
                    'similarity_reason': f"{method_type} 与 {new_interface_type} 操作相似",
                    'reuse_potential': self._calculate_reuse_potential(method, new_interface_type)
                })
        
        return similar_patterns
    
    def _is_similar_operation(self, existing_type: str, new_type: str) -> bool:
        """判断是否是相似的操作"""
        # 查询和导出是相似的操作（导出通常基于查询）
        if existing_type == 'query_list' and new_type == 'export_list':
            return True
        elif existing_type == 'export_list' and new_type == 'query_list':
            return True
        elif existing_type == new_type:
            return True
        
        # 其他相似操作组
        similar_groups = [
            ['create', 'add', 'insert'],
            ['update', 'modify', 'edit'],
            ['delete', 'remove']
        ]
        
        for group in similar_groups:
            if existing_type in group and new_type in group:
                return True
        
        return False
    
    def _calculate_reuse_potential(self, method: Dict[str, any], new_interface_type: str) -> float:
        """计算复用潜力"""
        # 基于方法类型和业务逻辑计算复用潜力
        if new_interface_type == 'export_list' and method.get('method_type') == 'query_list':
            return 0.9  # 导出和查询的复用潜力很高
        elif method.get('method_type') == new_interface_type:
            return 0.8  # 相同类型的复用潜力高
        else:
            return 0.3  # 其他情况复用潜力较低
    
    def _generate_merge_strategy(self, similar_patterns: List[Dict[str, any]], 
                               new_interface_type: str) -> Dict[str, any]:
        """生成合并策略"""
        if not similar_patterns:
            return {'strategy': 'create_new', 'reason': '无相似模式'}
        
        best_pattern = max(similar_patterns, key=lambda x: x['reuse_potential'])
        
        if best_pattern['reuse_potential'] > 0.8:
            return {
                'strategy': 'reuse_and_extend',
                'base_method': best_pattern['method'],
                'extension_type': new_interface_type,
                'shared_logic': 'extract_common_data_access',
                'specific_logic': f'add_{new_interface_type}_specific_handling'
            }
        else:
            return {
                'strategy': 'create_similar',
                'reference_method': best_pattern['method'],
                'similarity_level': best_pattern['reuse_potential']
            }
    
    def _extract_shared_logic(self, similar_patterns: List[Dict[str, any]]) -> Dict[str, any]:
        """提取共享逻辑"""
        if not similar_patterns:
            return {}
        
        # 分析共同的数据访问模式
        common_data_access = []
        common_parameters = []
        
        for pattern in similar_patterns:
            method = pattern['method']
            # 提取数据访问逻辑
            if 'feign_call' in method:
                common_data_access.append(method['feign_call'])
            # 提取参数模式
            if 'parameters' in method:
                common_parameters.extend(method['parameters'])
        
        return {
            'data_access_patterns': list(set(common_data_access)),
            'parameter_patterns': list(set(common_parameters)),
            'shared_method_name': 'getData'
        }
    
    def _get_special_handling(self, interface_type: str) -> Dict[str, any]:
        """获取特殊处理逻辑"""
        special_handling = {
            'export_list': {
                'additional_dependencies': ['ExcelExportService'],
                'additional_imports': [
                    'import org.springframework.http.MediaType;',
                    'import org.springframework.http.HttpHeaders;',
                    'import java.time.LocalDateTime;',
                    'import java.time.format.DateTimeFormatter;'
                ],
                'response_type': 'ResponseEntity<byte[]>',
                'additional_logic': 'excel_generation'
            },
            'query_list': {
                'response_type': 'ResponseEntity<List<Map<String, Object>>>',
                'additional_logic': 'pagination_support'
            }
        }
        
        return special_handling.get(interface_type, {})
    
    def _classify_method_type(self, method_name: str) -> str:
        """分类方法类型"""
        method_lower = method_name.lower()
        
        # 检查导出类型（优先检查，避免被其他关键字干扰）
        if any(keyword in method_lower for keyword in ['export', 'download']):
            return 'export_list'
        elif any(keyword in method_lower for keyword in ['list', 'query', 'search', 'find']):
            return 'query_list'
        elif any(keyword in method_lower for keyword in ['create', 'add', 'insert']):
            return 'create'
        elif any(keyword in method_lower for keyword in ['update', 'modify', 'edit']):
            return 'update'
        elif any(keyword in method_lower for keyword in ['delete', 'remove']):
            return 'delete'
        else:
            return 'other'
    
    def _extract_business_operation(self, method_name: str) -> str:
        """提取业务操作"""
        # 移除常见的前缀和后缀
        clean_name = method_name
        for prefix in ['get', 'query', 'list', 'find', 'search', 'export']:
            if clean_name.lower().startswith(prefix):
                clean_name = clean_name[len(prefix):]
                break
        
        return clean_name
    
    def _extract_business_domain_from_class(self, class_name: str) -> str:
        """从类名提取业务域"""
        # 移除常见的后缀
        clean_name = class_name
        suffixes = ['FeignClient', 'Client', 'Service', 'Controller', 'Mapper', 'Repository']
        for suffix in suffixes:
            if clean_name.endswith(suffix):
                clean_name = clean_name[:-len(suffix)]
                break
        
        return clean_name
    
    def _generate_excel_columns(self, base_method: Dict[str, any]) -> str:
        """生成Excel列配置"""
        # 这里应该根据实际的数据结构生成列配置
        return 'Arrays.asList("列1", "列2", "列3")'
    
    def _analyze_method_signature(self, method: Dict[str, any]) -> Dict[str, any]:
        """分析方法签名"""
        method_name = method.get('name', method.get('method_name', ''))
        
        # 直接使用方法名作为基础名称
        base_name = method_name
        
        return {
            'base_name': base_name,
            'original_name': method_name,
            'parameters': method.get('parameters', []),
            'return_type': method.get('return_type', 'Object')
        }
    
    def _generate_shared_logic(self, method_signature: Dict[str, any], 
                             interface_variants: List[str]) -> str:
        """生成共享逻辑"""
        base_name = method_signature['base_name']
        
        return f"""
        // 共享的数据获取逻辑
        try {{
            // 调用Feign Client或Service获取数据
            List<Map<String, Object>> data = feignClient.{base_name}(params);
            
            // 通用数据处理逻辑
            if (data == null || data.isEmpty()) {{
                return new ArrayList<>();
            }}
            
            return data;
        }} catch (Exception e) {{
            logger.error("获取{base_name}数据失败", e);
            throw new RuntimeException("数据获取失败", e);
        }}
        """
    
    def _generate_variant_handler(self, variant: str, method_signature: Dict[str, any]) -> Dict[str, any]:
        """生成变体处理器"""
        base_name = method_signature['base_name']
        
        if variant == 'export':
            return {
                'method_name': f"{base_name}Export",
                'mapping': '@GetMapping("/export")',
                'return_type': 'ResponseEntity<byte[]>',
                'logic': f'使用{base_name}Data()获取数据，然后生成Excel文件'
            }
        elif variant == 'query':
            return {
                'method_name': f"{base_name}List",
                'mapping': '@GetMapping("/list")',
                'return_type': 'ResponseEntity<List<Map<String, Object>>>',
                'logic': f'直接返回{base_name}Data()获取的数据'
            }
        else:
            return {
                'method_name': f"{base_name}{variant.capitalize()}",
                'mapping': f'@GetMapping("/{variant}")',
                'return_type': 'ResponseEntity<Object>',
                'logic': f'基于{base_name}Data()实现{variant}逻辑'
            }
    
    def _build_shared_method_signature(self, method_signature: Dict[str, any]) -> str:
        """构建共享方法签名"""
        base_name = method_signature['base_name']
        return f"private List<Map<String, Object>> {base_name}Data(Map<String, Object> params)"
    
    def _extract_method_dependencies(self, method: Dict[str, any]) -> List[str]:
        """提取方法依赖"""
        dependencies = []
        
        # 基础依赖
        dependencies.extend([
            'logger',
            'feignClient'
        ])
        
        # 根据方法类型添加特定依赖
        method_type = method.get('method_type', '')
        if method_type == 'export_list':
            dependencies.append('excelExportService')
        
        return dependencies
    
    def _is_component_already_injected(self, content: str, class_name: str) -> bool:
        """检查组件是否已经注入"""
        return class_name in content
    
    def _inject_feign_client(self, content: str, client: Dict[str, any]) -> str:
        """注入Feign Client"""
        class_name = client['class_name']
        variable_name = client.get('variable_name', class_name.lower())
        
        # 查找类的开始位置
        class_start = content.find('public class')
        if class_start == -1:
            return content
        
        # 查找第一个字段或方法的位置
        injection_point = content.find('{', class_start) + 1
        
        # 添加Feign Client注入
        injection_code = f"""
    
    @Autowired
    private {class_name} {variable_name};
"""
        
        return content[:injection_point] + injection_code + content[injection_point:]
    
    def _add_shared_method(self, content: str, method: Dict[str, any]) -> str:
        """添加共享方法"""
        # 在类的结尾前添加方法
        last_brace = content.rfind('}')
        if last_brace == -1:
            return content
        
        method_code = method.get('code', '')
        return content[:last_brace] + f"\n{method_code}\n" + content[last_brace:]
    
    def _add_export_method(self, content: str, method: Dict[str, any]) -> str:
        """添加导出方法"""
        return self._add_shared_method(content, method)
    
    def _add_required_imports(self, content: str, reuse_plan: Dict[str, any]) -> str:
        """添加必要的import"""
        required_imports = []
        
        # 检查是否需要导出相关的import
        if 'export_methods' in reuse_plan:
            required_imports.extend([
                'import org.springframework.http.MediaType;',
                'import org.springframework.http.HttpHeaders;',
                'import java.time.LocalDateTime;',
                'import java.time.format.DateTimeFormatter;'
            ])
        
        # 查找package声明的位置
        package_end = content.find(';', content.find('package')) + 1
        if package_end == -1:
            return content
        
        # 添加import
        for import_stmt in required_imports:
            if import_stmt not in content:
                content = content[:package_end] + f"\n{import_stmt}" + content[package_end:]
        
        return content
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        import datetime
        return datetime.datetime.now().isoformat()
    
    def _build_shared_method_signature(self, method_signature: Dict[str, any]) -> str:
        """构建共享方法签名"""
        base_name = method_signature['base_name']
        return f"private List<Map<String, Object>> {base_name}Data(Map<String, Object> params)"
    
    def _generate_variant_handler(self, variant: str, method_signature: Dict[str, any]) -> Dict[str, any]:
        """生成变体处理器"""
        base_name = method_signature['base_name']
        
        if variant == 'query':
            return {
                'type': 'query',
                'method_name': f"{base_name}",
                'description': f"查询{base_name}接口"
            }
        elif variant == 'export':
            return {
                'type': 'export',
                'method_name': f"{base_name}Export",
                'description': f"导出{base_name}接口"
            }
        else:
            return {
                'type': 'other',
                'method_name': f"{base_name}",
                'description': f"处理{base_name}接口"
            }
    
    def _extract_method_dependencies(self, base_method: Dict[str, any]) -> Dict[str, any]:
        """提取方法依赖"""
        return {
            'logger': 'private static final Logger logger = LoggerFactory.getLogger(this.getClass());',
            'feignClient': 'Feign Client dependency',
            'excelService': 'Excel service dependency for export operations'
        }