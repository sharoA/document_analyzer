#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能文件复用管理器
负责分析现有项目文件，智能决策是否复用现有文件还是创建新文件
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class IntelligentFileReuseManager:
    """智能文件复用管理器 - 优先复用现有文件，智能生成调用链"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.project_structure = {}
        self.existing_files_cache = {}
        self.document_content = ""  # 🔧 添加文档内容存储
        
    def set_document_content(self, document_content: str):
        """设置设计文档内容，用于表结构解析"""
        self.document_content = document_content
        
    def analyze_project_structure(self, project_path: str) -> Dict[str, Any]:
        """分析项目结构，识别所有现有组件"""
        
        logger.info(f"🔍 分析项目结构: {project_path}")
        
        structure = {
            'controllers': {},
            'application_services': {},
            'domain_services': {},
            'mappers': {},
            'feign_clients': {},
            'xml_files': {},
            'base_package': '',
            'modules': set()
        }
        
        # 扫描项目目录
        java_src_path = Path(project_path) / "src" / "main" / "java"
        if not java_src_path.exists():
            logger.warning(f"⚠️ 未找到Java源码目录: {java_src_path}")
            return structure
        
        # 分析Controller文件
        structure['controllers'] = self._scan_controllers(java_src_path)
        
        # 分析Application Service文件
        structure['application_services'] = self._scan_application_services(java_src_path)
        
        # 分析Domain Service文件
        structure['domain_services'] = self._scan_domain_services(java_src_path)
        
        # 分析Mapper文件
        structure['mappers'] = self._scan_mappers(java_src_path)
        
        # 分析Feign Client文件
        structure['feign_clients'] = self._scan_feign_clients(java_src_path)
        
        # 分析XML文件
        xml_path = Path(project_path) / "src" / "main" / "resources" / "mapper"
        if xml_path.exists():
            structure['xml_files'] = self._scan_xml_files(xml_path)
        
        # 推断基础包名和模块
        structure['base_package'], structure['modules'] = self._infer_package_info(java_src_path)
        
        self.project_structure = structure
        logger.info(f"✅ 项目结构分析完成")
        logger.info(f"   Controllers: {len(structure['controllers'])}")
        logger.info(f"   Application Services: {len(structure['application_services'])}")
        logger.info(f"   Domain Services: {len(structure['domain_services'])}")
        logger.info(f"   Mappers: {len(structure['mappers'])}")
        logger.info(f"   Feign Clients: {len(structure['feign_clients'])}")
        logger.info(f"   XML Files: {len(structure['xml_files'])}")
        
        return structure
    
    def decide_file_reuse_strategy(self, api_path: str, interface_name: str, 
                                  business_logic: str) -> Dict[str, Any]:
        """决策文件复用策略"""
        
        logger.info(f"🤔 决策文件复用策略: {interface_name}")
        
        strategy = {
            'controller': {'action': 'unknown', 'target_file': None, 'reason': ''},
            'application_service': {'action': 'unknown', 'target_file': None, 'reason': ''},
            'domain_service': {'action': 'unknown', 'target_file': None, 'reason': ''},
            'mapper': {'action': 'unknown', 'target_file': None, 'reason': ''},
            'feign_client': {'action': 'unknown', 'target_file': None, 'reason': ''},
            'xml_file': {'action': 'unknown', 'target_file': None, 'reason': ''}
        }
        
        # 确保项目结构已初始化
        if not hasattr(self, 'project_structure') or not self.project_structure:
            logger.warning("⚠️ 项目结构未初始化，使用默认策略")
            # 为所有组件设置默认策略
            for component in strategy.keys():
                strategy[component] = {
                    'action': 'create_new',
                    'target_file': None,
                    'reason': '项目结构未分析，创建新文件'
                }
            return strategy
        
        # 从API路径提取模块信息
        module_info = self._extract_module_from_api_path(api_path)
        
        # 决策Controller复用
        strategy['controller'] = self._decide_controller_reuse(
            interface_name, module_info, api_path
        )
        
        # 决策Application Service复用
        strategy['application_service'] = self._decide_application_service_reuse(
            interface_name, module_info, business_logic
        )
        
        # 决策Domain Service复用
        strategy['domain_service'] = self._decide_domain_service_reuse(
            interface_name, module_info, business_logic
        )
        
        # 决策Mapper复用
        strategy['mapper'] = self._decide_mapper_reuse(
            interface_name, module_info, business_logic
        )
        
        # 决策Feign Client复用
        strategy['feign_client'] = self._decide_feign_client_reuse(
            interface_name, module_info, business_logic
        )
        
        # 决策XML文件复用
        strategy['xml_file'] = self._decide_xml_file_reuse(
            interface_name, module_info, strategy['mapper']
        )
        
        logger.info(f"📋 文件复用策略决策完成:")
        for component, decision in strategy.items():
            logger.info(f"   {component}: {decision['action']} - {decision['reason']}")
        
        return strategy
    
    def generate_complete_calling_chain(self, interface_name: str, strategy: Dict[str, Any],
                                      input_params: List[Dict], output_params: Dict,
                                      business_logic: str) -> Dict[str, str]:
        """根据复用策略生成完整的调用链代码"""
        
        logger.info(f"🔗 生成完整调用链: {interface_name}")
        
        generated_code = {}
        
        # 1. 生成Controller调用逻辑
        controller_code = self._generate_controller_calling_logic(
            interface_name, strategy, input_params, output_params, business_logic
        )
        if controller_code:
            generated_code['controller_method'] = controller_code
        
        # 2. 生成Application Service逻辑
        if strategy['application_service']['action'] in ['create_new', 'add_method']:
            app_service_code = self._generate_application_service_logic(
                interface_name, strategy, input_params, output_params, business_logic
            )
            if app_service_code:
                generated_code['application_service'] = app_service_code
        
        # 3. 生成Domain Service逻辑（接口和实现类）
        if strategy['domain_service']['action'] in ['create_new', 'add_method']:
            domain_service_code = self._generate_domain_service_logic(
                interface_name, strategy, input_params, output_params, business_logic
            )
            if domain_service_code:
                # 分离接口和实现类代码
                if "---SERVICE_IMPL_SEPARATOR---" in domain_service_code:
                    service_parts = domain_service_code.split("---SERVICE_IMPL_SEPARATOR---")
                    generated_code['domain_service'] = service_parts[0].strip()
                    generated_code['domain_service_impl'] = service_parts[1].strip()
                else:
                    generated_code['domain_service'] = domain_service_code
        
        # 4. 生成Mapper逻辑
        if strategy['mapper']['action'] in ['create_new', 'add_method']:
            mapper_code = self._generate_mapper_logic(
                interface_name, strategy, input_params, output_params, business_logic
            )
            if mapper_code:
                generated_code['mapper'] = mapper_code
        
        # 5. 生成Feign Client逻辑
        if strategy['feign_client']['action'] in ['create_new', 'add_method']:
            feign_code = self._generate_feign_client_logic(
                interface_name, strategy, input_params, output_params, business_logic
            )
            if feign_code:
                generated_code['feign_client'] = feign_code
        
        # 6. 生成XML映射
        if strategy['xml_file']['action'] in ['create_new', 'add_mapping']:
            xml_code = self._generate_xml_mapping_logic(
                interface_name, strategy, input_params, output_params, business_logic
            )
            if xml_code:
                generated_code['xml_mapping'] = xml_code
        
        logger.info(f"✅ 调用链代码生成完成，包含 {len(generated_code)} 个组件")
        
        return generated_code
    
    def _scan_controllers(self, java_src_path: Path) -> Dict[str, Dict]:
        """扫描Controller文件"""
        
        controllers = {}
        
        # 查找所有Controller文件
        for controller_file in java_src_path.rglob("*Controller.java"):
            relative_path = controller_file.relative_to(java_src_path)
            
            # 读取文件内容分析
            try:
                with open(controller_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 提取类名和RequestMapping
                class_name = self._extract_class_name(content)
                request_mapping = self._extract_request_mapping(content)
                methods = self._extract_controller_methods(content)
                
                controllers[class_name] = {
                    'file_path': str(controller_file),
                    'relative_path': str(relative_path),
                    'class_name': class_name,
                    'request_mapping': request_mapping,
                    'methods': methods,
                    'module': self._infer_module_from_path(relative_path)
                }
                
            except Exception as e:
                logger.warning(f"⚠️ 读取Controller文件失败: {controller_file} - {e}")
        
        return controllers
    
    def _scan_application_services(self, java_src_path: Path) -> Dict[str, Dict]:
        """扫描Application Service文件"""
        
        services = {}
        
        # 查找application/service目录下的文件
        for service_file in java_src_path.rglob("application/service/*.java"):
            relative_path = service_file.relative_to(java_src_path)
            
            try:
                with open(service_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                class_name = self._extract_class_name(content)
                methods = self._extract_service_methods(content)
                dependencies = self._extract_service_dependencies(content)
                
                services[class_name] = {
                    'file_path': str(service_file),
                    'relative_path': str(relative_path),
                    'class_name': class_name,
                    'methods': methods,
                    'dependencies': dependencies,
                    'module': self._infer_module_from_path(relative_path)
                }
                
            except Exception as e:
                logger.warning(f"⚠️ 读取Application Service文件失败: {service_file} - {e}")
        
        return services
    
    def _scan_domain_services(self, java_src_path: Path) -> Dict[str, Dict]:
        """扫描Domain Service文件"""
        
        services = {}
        
        # 查找domain/service目录下的文件
        for service_file in java_src_path.rglob("domain/service/*.java"):
            relative_path = service_file.relative_to(java_src_path)
            
            try:
                with open(service_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                class_name = self._extract_class_name(content)
                methods = self._extract_service_methods(content)
                dependencies = self._extract_service_dependencies(content)
                
                services[class_name] = {
                    'file_path': str(service_file),
                    'relative_path': str(relative_path),
                    'class_name': class_name,
                    'methods': methods,
                    'dependencies': dependencies,
                    'module': self._infer_module_from_path(relative_path)
                }
                
            except Exception as e:
                logger.warning(f"⚠️ 读取Domain Service文件失败: {service_file} - {e}")
        
        return services
    
    def _scan_mappers(self, java_src_path: Path) -> Dict[str, Dict]:
        """扫描Mapper文件"""
        
        mappers = {}
        
        # 查找domain/mapper目录下的文件
        for mapper_file in java_src_path.rglob("domain/mapper/*.java"):
            relative_path = mapper_file.relative_to(java_src_path)
            
            try:
                with open(mapper_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                class_name = self._extract_class_name(content)
                methods = self._extract_mapper_methods(content)
                
                mappers[class_name] = {
                    'file_path': str(mapper_file),
                    'relative_path': str(relative_path),
                    'class_name': class_name,
                    'methods': methods,
                    'module': self._infer_module_from_path(relative_path)
                }
                
            except Exception as e:
                logger.warning(f"⚠️ 读取Mapper文件失败: {mapper_file} - {e}")
        
        return mappers
    
    def _scan_feign_clients(self, java_src_path: Path) -> Dict[str, Dict]:
        """扫描Feign Client文件"""
        
        feign_clients = {}
        
        # 查找application/feign目录下的文件
        for feign_file in java_src_path.rglob("application/feign/*.java"):
            relative_path = feign_file.relative_to(java_src_path)
            
            try:
                with open(feign_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                class_name = self._extract_class_name(content)
                methods = self._extract_feign_methods(content)
                service_name = self._extract_feign_service_name(content)
                
                feign_clients[class_name] = {
                    'file_path': str(feign_file),
                    'relative_path': str(relative_path),
                    'class_name': class_name,
                    'methods': methods,
                    'service_name': service_name,
                    'module': self._infer_module_from_path(relative_path)
                }
                
            except Exception as e:
                logger.warning(f"⚠️ 读取Feign Client文件失败: {feign_file} - {e}")
        
        return feign_clients
    
    def _scan_xml_files(self, xml_path: Path) -> Dict[str, Dict]:
        """扫描XML映射文件"""
        
        xml_files = {}
        
        for xml_file in xml_path.rglob("*.xml"):
            relative_path = xml_file.relative_to(xml_path)
            
            try:
                with open(xml_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                namespace = self._extract_xml_namespace(content)
                mapper_name = xml_file.stem
                sql_statements = self._extract_sql_statements(content)
                
                xml_files[mapper_name] = {
                    'file_path': str(xml_file),
                    'relative_path': str(relative_path),
                    'namespace': namespace,
                    'mapper_name': mapper_name,
                    'sql_statements': sql_statements
                }
                
            except Exception as e:
                logger.warning(f"⚠️ 读取XML文件失败: {xml_file} - {e}")
        
        return xml_files
    
    def _extract_module_from_api_path(self, api_path: str) -> Dict[str, str]:
        """从API路径提取模块信息"""
        
        # 例如: /general/multiorgManage/queryCompanyUnitList
        # 提取: general, multiorgManage
        path_parts = [part for part in api_path.split('/') if part]
        
        return {
            'primary_module': path_parts[0] if path_parts else '',
            'secondary_module': path_parts[1] if len(path_parts) > 1 else '',
            'business_entity': path_parts[-1] if path_parts else ''
        }
    
    def _decide_controller_reuse(self, interface_name: str, module_info: Dict, 
                               api_path: str) -> Dict[str, Any]:
        """决策Controller复用策略"""
        
        # 查找最匹配的Controller
        best_match = None
        best_score = 0
        
        for controller_name, controller_info in self.project_structure['controllers'].items():
            score = self._calculate_controller_match_score(
                controller_info, module_info, api_path
            )
            
            if score > best_score:
                best_score = score
                best_match = controller_info
        
        if best_match and best_score >= 60:  # 阈值可调整
            return {
                'action': 'add_method',
                'target_file': best_match['file_path'],
                'reason': f'找到匹配的Controller ({best_score}分): {best_match["class_name"]}'
            }
        else:
            return {
                'action': 'create_new',
                'target_file': None,
                'reason': f'未找到合适的Controller (最高分数: {best_score})'
            }
    
    def _decide_application_service_reuse(self, interface_name: str, module_info: Dict,
                                        business_logic: str) -> Dict[str, Any]:
        """决策Application Service复用策略"""
        
        # 检查是否需要外部服务调用
        needs_feign = self._analyze_needs_feign_call(business_logic)
        
        if needs_feign:
            # 需要Feign调用，查找或创建Application Service
            best_match = self._find_best_application_service_match(interface_name, module_info)
            
            if best_match:
                return {
                    'action': 'add_method',
                    'target_file': best_match['file_path'],
                    'reason': f'需要Feign调用，复用Application Service: {best_match["class_name"]}'
                }
            else:
                return {
                    'action': 'create_new',
                    'target_file': None,
                    'reason': '需要Feign调用，创建新的Application Service'
                }
        else:
            # 本地调用，可能不需要Application Service
            return {
                'action': 'skip',
                'target_file': None,
                'reason': '本地调用，可直接使用Domain Service'
            }
    
    def _decide_domain_service_reuse(self, interface_name: str, module_info: Dict,
                                   business_logic: str) -> Dict[str, Any]:
        """决策Domain Service复用策略"""
        
        # 查找匹配的Domain Service
        best_match = self._find_best_domain_service_match(interface_name, module_info)
        
        if best_match:
            return {
                'action': 'add_method',
                'target_file': best_match['file_path'],
                'reason': f'找到匹配的Domain Service: {best_match["class_name"]}'
            }
        else:
            return {
                'action': 'create_new',
                'target_file': None,
                'reason': '未找到合适的Domain Service，需要创建'
            }
    
    def _decide_mapper_reuse(self, interface_name: str, module_info: Dict,
                           business_logic: str) -> Dict[str, Any]:
        """决策Mapper复用策略"""
        
        # 检查是否需要数据库操作
        needs_database = self._analyze_needs_database_operation(business_logic)
        
        if not needs_database:
            return {
                'action': 'skip',
                'target_file': None,
                'reason': '不需要数据库操作'
            }
        
        # 查找匹配的Mapper
        best_match = self._find_best_mapper_match(interface_name, module_info)
        
        if best_match:
            return {
                'action': 'add_method',
                'target_file': best_match['file_path'],
                'reason': f'找到匹配的Mapper: {best_match["class_name"]}'
            }
        else:
            return {
                'action': 'create_new',
                'target_file': None,
                'reason': '未找到合适的Mapper，需要创建'
            }
    
    def _decide_feign_client_reuse(self, interface_name: str, module_info: Dict,
                                 business_logic: str) -> Dict[str, Any]:
        """决策Feign Client复用策略"""
        
        # 检查是否需要外部服务调用
        needs_feign = self._analyze_needs_feign_call(business_logic)
        
        if not needs_feign:
            return {
                'action': 'skip',
                'target_file': None,
                'reason': '不需要外部服务调用'
            }
        
        # 查找匹配的Feign Client
        best_match = self._find_best_feign_client_match(interface_name, module_info, business_logic)
        
        if best_match:
            return {
                'action': 'add_method',
                'target_file': best_match['file_path'],
                'reason': f'找到匹配的Feign Client: {best_match["class_name"]}'
            }
        else:
            return {
                'action': 'create_new',
                'target_file': None,
                'reason': '未找到合适的Feign Client，需要创建'
            }
    
    def _decide_xml_file_reuse(self, interface_name: str, module_info: Dict,
                             mapper_strategy: Dict) -> Dict[str, Any]:
        """决策XML文件复用策略"""
        
        if mapper_strategy['action'] == 'skip':
            return {
                'action': 'skip',
                'target_file': None,
                'reason': '不需要Mapper，跳过XML文件'
            }
        
        if mapper_strategy['action'] == 'add_method':
            # 查找对应的XML文件
            mapper_file_path = mapper_strategy['target_file']
            mapper_name = Path(mapper_file_path).stem  # 获取文件名（不含扩展名）
            
            for xml_name, xml_info in self.project_structure['xml_files'].items():
                if xml_name == mapper_name:
                    return {
                        'action': 'add_mapping',
                        'target_file': xml_info['file_path'],
                        'reason': f'找到对应的XML文件: {xml_name}.xml'
                    }
            
            return {
                'action': 'create_new',
                'target_file': None,
                'reason': f'未找到对应的XML文件: {mapper_name}.xml'
            }
        
        return {
            'action': 'create_new',
            'target_file': None,
            'reason': '需要创建新的XML文件'
        }
    
    # 工具方法 - 代码生成部分
    def _generate_controller_calling_logic(self, interface_name: str, strategy: Dict[str, Any],
                                         input_params: List[Dict], output_params: Dict,
                                         business_logic: str) -> str:
        """生成Controller调用逻辑"""
        
        # 📋 关键修复：根据复用策略决定生成内容
        controller_strategy = strategy.get('controller', {})
        action = controller_strategy.get('action', 'create_new')
        
        # 根据策略决定调用链
        if strategy['application_service']['action'] != 'skip':
            # Controller -> Application Service
            service_call = f"return {interface_name.lower()}Application.{interface_name}(request);"
            service_injection = f"@Autowired\n    private {interface_name}Application {interface_name.lower()}Application;"
        elif strategy['domain_service']['action'] != 'skip':
            # Controller -> Domain Service
            service_call = f"return {interface_name.lower()}DomainService.{interface_name}(request);"
            service_injection = f"@Autowired\n    private {interface_name}DomainService {interface_name.lower()}DomainService;"
        else:
            # 默认调用
            service_call = f"// TODO: 实现{interface_name}业务逻辑\n        return new {interface_name}Resp();"
            service_injection = ""
        
        # 🔧 关键修复：根据action决定生成内容
        if action == 'add_method':
            # 只生成方法，用于添加到现有Controller
            method_code = f"""
    /**
     * {business_logic}
     */
    @PostMapping("/{interface_name}")
    @ApiOperation(value = "{business_logic}")
    public Response<{interface_name}Resp> {interface_name}(@RequestBody @Valid {interface_name}Req request) {{
        try {{
            logger.info("开始执行{interface_name}，请求参数: {{}}", request);
            
            {service_call}
            
        }} catch (Exception e) {{
            logger.error("执行{interface_name}失败", e);
            return Response.error("执行失败: " + e.getMessage());
        }}
    }}"""
            
            if service_injection:
                return f"{service_injection}\n{method_code}"
            else:
                return method_code
                
        else:
            # action == 'create_new' - 生成完整的Controller类
            base_package = self.project_structure.get('base_package', 'com.yljr.crcl.limit')
            
            controller_code = f"""
package {base_package}.interfaces;

import {base_package}.interfaces.dto.{interface_name}Req;
import {base_package}.interfaces.dto.{interface_name}Resp;
import com.yljr.common.dto.Response;
import org.springframework.web.bind.annotation.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.validation.annotation.Validated;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import io.swagger.annotations.ApiOperation;

import javax.validation.Valid;

/**
 * {interface_name} Controller
 * {business_logic}
 */
@Validated
@RestController
@RequestMapping("/api/{interface_name.lower()}")
public class {interface_name}Controller {{

    private final Logger logger = LoggerFactory.getLogger(this.getClass());
    
    {service_injection}

    /**
     * {business_logic}
     */
    @PostMapping("/{interface_name}")
    @ApiOperation(value = "{business_logic}")
    public Response<{interface_name}Resp> {interface_name}(@RequestBody @Valid {interface_name}Req request) {{
        try {{
            logger.info("开始执行{interface_name}，请求参数: {{}}", request);
            
            {service_call}
            
        }} catch (Exception e) {{
            logger.error("执行{interface_name}失败", e);
            return Response.error("执行失败: " + e.getMessage());
        }}
    }}
}}"""
            
            return controller_code
    
    def _generate_application_service_logic(self, interface_name: str, strategy: Dict[str, Any],
                                          input_params: List[Dict], output_params: Dict,
                                          business_logic: str) -> str:
        """生成Application Service逻辑"""
        
        # 判断调用类型
        if strategy['feign_client']['action'] != 'skip':
            # 调用Feign接口
            feign_call = f"return {interface_name.lower()}FeignClient.{interface_name}(request);"
            dependencies = f"@Autowired\n    private {interface_name}FeignClient {interface_name.lower()}FeignClient;"
        elif strategy['domain_service']['action'] != 'skip':
            # 调用Domain Service
            feign_call = f"return {interface_name.lower()}DomainService.{interface_name}(request);"
            dependencies = f"@Autowired\n    private {interface_name}DomainService {interface_name.lower()}DomainService;"
        else:
            # 默认实现
            feign_call = f"// TODO: 实现{interface_name}业务逻辑\n        return new {interface_name}Resp();"
            dependencies = ""
        
        # 获取基础包名，提供默认值
        base_package = self.project_structure.get('base_package', 'com.yljr.crcl.limit')
        
        class_code = f"""
package {base_package}.application.service;

import {base_package}.interfaces.dto.{interface_name}Req;
import {base_package}.interfaces.dto.{interface_name}Resp;
import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Autowired;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * {interface_name} Application Service
 * {business_logic}
 */
@Service
public class {interface_name}Application {{

    private static final Logger logger = LoggerFactory.getLogger({interface_name}Application.class);
    
    {dependencies}

    /**
     * {business_logic}
     */
    public {interface_name}Resp {interface_name}({interface_name}Req request) {{
        logger.info("Application Service执行{interface_name}，参数: {{}}", request);
        
        try {{
            {feign_call}
        }} catch (Exception e) {{
            logger.error("Application Service执行{interface_name}失败", e);
            throw new RuntimeException("执行失败: " + e.getMessage(), e);
        }}
    }}
}}"""
        
        return class_code
    
    def _generate_domain_service_logic(self, interface_name: str, strategy: Dict[str, Any],
                                     input_params: List[Dict], output_params: Dict,
                                     business_logic: str) -> str:
        """生成Domain Service接口和实现类"""
        
        # 🔧 修复：生成驼峰命名的方法名
        method_name = self._first_char_lower(interface_name)
        
        # 获取基础包名，提供默认值
        base_package = self.project_structure.get('base_package', 'com.yljr.crcl.limit')
        
        # 生成Service接口
        service_interface = f"""
package {base_package}.domain.service;

import {base_package}.interfaces.dto.{interface_name}Req;
import {base_package}.interfaces.dto.{interface_name}Resp;

/**
 * {interface_name} Domain Service Interface
 * {business_logic}
 */
public interface {interface_name}Service {{

    /**
     * {business_logic}
     */
    {interface_name}Resp {method_name}({interface_name}Req request);
}}"""
        
        # 判断调用类型
        if strategy['mapper']['action'] != 'skip':
            # 调用Mapper
            mapper_call = f"""
        // 调用Mapper查询数据
        List<{interface_name}> dataList = {interface_name.lower()}Mapper.select{interface_name}List(request);
        
        // 构建响应
        {interface_name}Resp response = new {interface_name}Resp();
        response.setDataList(dataList);
        response.setTotalCount(dataList.size());
        
        return response;"""
            dependencies = f"@Autowired\n    private {interface_name}Mapper {interface_name.lower()}Mapper;"
        else:
            # 默认实现
            mapper_call = f"// TODO: 实现{interface_name}业务逻辑\n        return new {interface_name}Resp();"
            dependencies = ""
        
        # 生成Service实现类
        service_impl = f"""
package {base_package}.domain.service.impl;

import {base_package}.domain.service.{interface_name}Service;
import {base_package}.interfaces.dto.{interface_name}Req;
import {base_package}.interfaces.dto.{interface_name}Resp;
import {base_package}.domain.entity.{interface_name};
import {base_package}.domain.mapper.{interface_name}Mapper;
import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Autowired;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import java.util.List;

/**
 * {interface_name} Domain Service Implementation
 * {business_logic}
 */
@Service
public class {interface_name}ServiceImpl implements {interface_name}Service {{

    private static final Logger logger = LoggerFactory.getLogger({interface_name}ServiceImpl.class);
    
    {dependencies}

    /**
     * {business_logic}
     */
    @Override
    public {interface_name}Resp {method_name}({interface_name}Req request) {{
        logger.info("Domain Service执行{interface_name}，参数: {{}}", request);
        
        try {{{mapper_call}
        }} catch (Exception e) {{
            logger.error("Domain Service执行{interface_name}失败", e);
            throw new RuntimeException("执行失败: " + e.getMessage(), e);
        }}
    }}
}}"""
        
        # 返回接口和实现类代码，用特殊分隔符分开
        return f"{service_interface.strip()}\n\n---SERVICE_IMPL_SEPARATOR---\n\n{service_impl.strip()}"
    
    def _generate_mapper_logic(self, interface_name: str, strategy: Dict[str, Any],
                             input_params: List[Dict], output_params: Dict,
                             business_logic: str) -> str:
        """生成Mapper逻辑"""
        
        # 获取基础包名，提供默认值
        base_package = self.project_structure.get('base_package', 'com.yljr.crcl.limit')
        
        mapper_code = f"""
package {base_package}.domain.mapper;

import {base_package}.interfaces.dto.{interface_name}Req;
import {base_package}.domain.entity.{interface_name};
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import java.util.List;

/**
 * {interface_name} Mapper接口
 * {business_logic}
 */
@Mapper
public interface {interface_name}Mapper {{

    /**
     * 根据条件查询{interface_name}列表
     */
    List<{interface_name}> select{interface_name}List(@Param("condition") {interface_name}Req condition);

    /**
     * 根据主键查询{interface_name}
     */
    {interface_name} selectByPrimaryKey(@Param("id") Long id);

    /**
     * 新增{interface_name}记录
     */
    int insert({interface_name} record);

    /**
     * 更新{interface_name}记录
     */
    int updateByPrimaryKey({interface_name} record);

    /**
     * 删除{interface_name}记录
     */
    int deleteByPrimaryKey(@Param("id") Long id);
}}"""
        
        return mapper_code
    
    def _generate_feign_client_logic(self, interface_name: str, strategy: Dict[str, Any],
                                   input_params: List[Dict], output_params: Dict,
                                   business_logic: str) -> str:
        """生成Feign Client逻辑"""
        
        # 获取基础包名，提供默认值
        base_package = self.project_structure.get('base_package', 'com.yljr.crcl.limit')
        
        # 🔧 修复：生成具体的Feign接口而不是通用模板
        # 根据业务逻辑判断调用的外部服务
        if "用户服务" in business_logic or "组织单元" in business_logic:
            service_name = "zqyl-user-auth"
            service_path = "/userCenter/server"
            method_path = "/queryCompanyInfo"
        else:
            service_name = "external-service"
            service_path = "/api"
            method_path = f"/{interface_name.lower()}"
        
        feign_code = f"""
package {base_package}.application.feign;

import {base_package}.interfaces.dto.{interface_name}Req;
import {base_package}.interfaces.dto.{interface_name}Resp;
import com.yljr.common.dto.ResponseInfo;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.http.MediaType;

/**
 * {interface_name} Feign接口
 * {business_logic}
 */
@FeignClient(name = "{service_name}", path = "{service_path}")
public interface {interface_name}FeignClient {{

    /**
     * {business_logic}
     */
    @PostMapping(value = "{method_path}", consumes = MediaType.APPLICATION_JSON_UTF8_VALUE)
    ResponseInfo<{interface_name}Resp> {interface_name}(@RequestBody {interface_name}Req request);
}}"""
        
        return feign_code
    
    def _generate_xml_mapping_logic(self, interface_name: str, strategy: Dict[str, Any],
                                  input_params: List[Dict], output_params: Dict,
                                  business_logic: str) -> str:
        """生成XML映射逻辑 - 基于设计文档中的表结构动态生成"""
        
        # 获取基础包名，提供默认值
        base_package = self.project_structure.get('base_package', 'com.yljr.crcl.limit')
        
        # 🔧 关键修复：从项目上下文中提取表结构信息
        table_structure = self._extract_table_structure_from_context(interface_name, business_logic)
        
        # 生成ResultMap字段映射
        result_map_fields = self._generate_result_map_fields(table_structure)
        
        # 生成列名列表
        column_list = self._generate_column_list(table_structure)
        
        # 生成WHERE条件
        where_conditions = self._generate_where_conditions(table_structure, input_params)
        
        xml_code = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN" "http://mybatis.org/dtd/mybatis-3-mapper.dtd">
<mapper namespace="{base_package}.domain.mapper.{interface_name}Mapper">

    <resultMap id="BaseResultMap" type="{base_package}.domain.entity.{interface_name}">
{result_map_fields}
    </resultMap>

    <sql id="Base_Column_List">
        {column_list}
    </sql>

    <select id="select{interface_name}List" parameterType="{base_package}.interfaces.dto.{interface_name}Req" 
            resultMap="BaseResultMap">
        SELECT 
        <include refid="Base_Column_List" />
        FROM {table_structure['table_name']}
        WHERE 1=1
{where_conditions}
        ORDER BY CREATE_TIME DESC
    </select>

    <select id="selectByPrimaryKey" parameterType="java.lang.Long" resultMap="BaseResultMap">
        SELECT 
        <include refid="Base_Column_List" />
        FROM {table_structure['table_name']}
        WHERE ID = #{{id,jdbcType={table_structure.get('id_jdbc_type', 'BIGINT')}}}
    </select>

    <insert id="insert" parameterType="{base_package}.domain.entity.{interface_name}">
        INSERT INTO {table_structure['table_name']} ({table_structure['insert_columns']})
        VALUES ({table_structure['insert_values']})
    </insert>

    <update id="updateByPrimaryKey" parameterType="{base_package}.domain.entity.{interface_name}">
        UPDATE {table_structure['table_name']}
        SET {table_structure['update_sets']}
        WHERE ID = #{{id}}
    </update>

    <delete id="deleteByPrimaryKey" parameterType="java.lang.Long">
        DELETE FROM {table_structure['table_name']}
        WHERE ID = #{{id,jdbcType={table_structure.get('id_jdbc_type', 'BIGINT')}}}
    </delete>

</mapper>"""
        
        return xml_code
    
    def _extract_table_structure_from_context(self, interface_name: str, business_logic: str) -> Dict[str, Any]:
        """从项目上下文中提取表结构信息"""
        
        # 🔧 修复：使用实例变量中的文档内容
        document_content = self.document_content or ''
        
        # 查找CREATE TABLE语句
        import re
        
        # 根据接口名和业务逻辑推断表名模式
        if "CompanyUnitList" in interface_name or "组织单元" in business_logic:
            table_patterns = [r'T_CUST_MULTIORG_UNIT', r't_cust_multiorg_unit']
        elif "Limit" in interface_name or "限额" in business_logic:
            table_patterns = [r'T_.*LIMIT.*', r't_.*limit.*']
        else:
            # 通用模式
            table_patterns = [f'T_{interface_name.upper()}', f't_{interface_name.lower()}']
        
        table_structure = {
            'table_name': f'T_{interface_name.upper()}',
            'columns': [],
            'id_jdbc_type': 'BIGINT'
        }
        
        # 尝试匹配表结构
        for pattern in table_patterns:
            create_table_pattern = f'CREATE\\s+TABLE\\s+({pattern})\\s*\\((.*?)\\)\\s*(?:ENGINE|;)'
            match = re.search(create_table_pattern, document_content, re.DOTALL | re.IGNORECASE)
            
            if match:
                table_structure['table_name'] = match.group(1).upper()
                columns_text = match.group(2)
                
                logger.info(f"🔍 找到表结构: {table_structure['table_name']}")
                
                # 解析列定义
                column_lines = [line.strip() for line in columns_text.split(',') if line.strip()]
                
                for line in column_lines:
                    if line.startswith('PRIMARY KEY') or line.startswith('KEY') or line.startswith('INDEX'):
                        continue
                    
                    # 解析列定义：列名 数据类型 [约束] [注释]
                    parts = line.split()
                    if len(parts) >= 2:
                        column_name = parts[0].strip('`')
                        column_type = parts[1]
                        
                        # 提取注释
                        comment_match = re.search(r"COMMENT\\s+'([^']*)'", line)
                        comment = comment_match.group(1) if comment_match else ''
                        
                        # 检查是否可空
                        nullable = 'NOT NULL' not in line.upper()
                        
                        # 映射JDBC类型
                        jdbc_type = self._map_sql_type_to_jdbc_type(column_type)
                        
                        # 映射Java属性名
                        java_property = self._snake_to_camel(column_name.lower())
                        
                        table_structure['columns'].append({
                            'column_name': column_name,
                            'column_type': column_type,
                            'jdbc_type': jdbc_type,
                            'java_property': java_property,
                            'comment': comment,
                            'nullable': nullable,
                            'is_primary_key': column_name.upper() == 'ID'
                        })
                        
                        # 记录主键的JDBC类型
                        if column_name.upper() == 'ID':
                            table_structure['id_jdbc_type'] = jdbc_type
                
                logger.info(f"✅ 解析到 {len(table_structure['columns'])} 个字段")
                break
        
        # 如果没有找到表结构，使用默认结构
        if not table_structure['columns']:
            logger.warning(f"⚠️ 未找到表结构定义，使用默认字段")
            table_structure['columns'] = [
                {'column_name': 'ID', 'jdbc_type': 'BIGINT', 'java_property': 'id', 'is_primary_key': True},
                {'column_name': 'NAME', 'jdbc_type': 'VARCHAR', 'java_property': 'name', 'is_primary_key': False},
                {'column_name': 'STATUS', 'jdbc_type': 'VARCHAR', 'java_property': 'status', 'is_primary_key': False},
                {'column_name': 'CREATE_TIME', 'jdbc_type': 'TIMESTAMP', 'java_property': 'createTime', 'is_primary_key': False},
                {'column_name': 'UPDATE_TIME', 'jdbc_type': 'TIMESTAMP', 'java_property': 'updateTime', 'is_primary_key': False}
            ]
        
        # 生成INSERT和UPDATE语句的字段
        table_structure['insert_columns'] = self._generate_insert_columns(table_structure)
        table_structure['insert_values'] = self._generate_insert_values(table_structure)
        table_structure['update_sets'] = self._generate_update_sets(table_structure)
        
        return table_structure
    
    def _generate_insert_columns(self, table_structure: Dict[str, Any]) -> str:
        """生成INSERT语句的列名"""
        
        # 排除主键ID（通常是自增的）
        columns = [col['column_name'] for col in table_structure['columns'] if not col.get('is_primary_key', False)]
        return ', '.join(columns)
    
    def _generate_insert_values(self, table_structure: Dict[str, Any]) -> str:
        """生成INSERT语句的值"""
        
        # 排除主键ID（通常是自增的）
        values = [f"#{{{col['java_property']}}}" for col in table_structure['columns'] if not col.get('is_primary_key', False)]
        return ', '.join(values)
    
    def _generate_update_sets(self, table_structure: Dict[str, Any]) -> str:
        """生成UPDATE语句的SET子句"""
        
        # 排除主键和创建时间
        update_columns = [col for col in table_structure['columns'] 
                         if not col.get('is_primary_key', False) and 'CREATE_TIME' not in col['column_name'].upper()]
        
        sets = [f"{col['column_name']} = #{{{col['java_property']}}}" for col in update_columns]
        return ',\n            '.join(sets)
    
    def _generate_result_map_fields(self, table_structure: Dict[str, Any]) -> str:
        """生成ResultMap字段映射"""
        
        fields = []
        for column in table_structure['columns']:
            if column.get('is_primary_key', False):
                field_xml = f'        <id column="{column["column_name"]}" jdbcType="{column["jdbc_type"]}" property="{column["java_property"]}" />'
            else:
                field_xml = f'        <result column="{column["column_name"]}" jdbcType="{column["jdbc_type"]}" property="{column["java_property"]}" />'
            fields.append(field_xml)
        
        return '\n'.join(fields)
    
    def _generate_column_list(self, table_structure: Dict[str, Any]) -> str:
        """生成列名列表"""
        
        columns = [col['column_name'] for col in table_structure['columns']]
        # 格式化为多行，每行不超过120字符
        result = []
        current_line = []
        current_length = 0
        
        for col in columns:
            if current_length + len(col) + 2 > 120 and current_line:  # +2 for ", "
                result.append(', '.join(current_line))
                current_line = [col]
                current_length = len(col)
            else:
                current_line.append(col)
                current_length += len(col) + 2
        
        if current_line:
            result.append(', '.join(current_line))
        
        return ',\n        '.join(result)
    
    def _generate_where_conditions(self, table_structure: Dict[str, Any], input_params: List[Dict]) -> str:
        """生成WHERE条件"""
        
        conditions = []
        
        # 基于输入参数生成条件
        for param in input_params:
            param_name = param.get('name', '')
            param_type = param.get('type', 'String')
            
            # 查找对应的数据库列
            matching_column = None
            for col in table_structure['columns']:
                if col['java_property'].lower() == param_name.lower():
                    matching_column = col
                    break
            
            if matching_column:
                column_name = matching_column['column_name']
                if param_type == 'String':
                    if 'name' in param_name.lower() or 'title' in param_name.lower():
                        condition = f'''        <if test="condition.{param_name} != null and condition.{param_name} != ''">
            AND {column_name} LIKE CONCAT('%', #{{condition.{param_name}}}, '%')
        </if>'''
                    else:
                        condition = f'''        <if test="condition.{param_name} != null and condition.{param_name} != ''">
            AND {column_name} = #{{condition.{param_name}}}
        </if>'''
                else:
                    condition = f'''        <if test="condition.{param_name} != null">
            AND {column_name} = #{{condition.{param_name}}}
        </if>'''
                
                conditions.append(condition)
        
        # 添加一些常用的查询条件
        status_column = next((col for col in table_structure['columns'] if 'STATUS' in col['column_name'].upper()), None)
        if status_column:
            conditions.append(f'''        <if test="condition.status != null">
            AND {status_column['column_name']} = #{{condition.status}}
        </if>''')
        
        return '\n'.join(conditions)
    
    def _map_sql_type_to_jdbc_type(self, sql_type: str) -> str:
        """映射SQL类型到JDBC类型"""
        
        sql_type_upper = sql_type.upper()
        
        if 'DECIMAL' in sql_type_upper or 'NUMERIC' in sql_type_upper:
            return 'DECIMAL'
        elif 'BIGINT' in sql_type_upper:
            return 'BIGINT'
        elif 'INT' in sql_type_upper:
            return 'INTEGER'
        elif 'VARCHAR' in sql_type_upper or 'CHAR' in sql_type_upper:
            return 'VARCHAR'
        elif 'TEXT' in sql_type_upper:
            return 'LONGVARCHAR'
        elif 'TIMESTAMP' in sql_type_upper or 'DATETIME' in sql_type_upper:
            return 'TIMESTAMP'
        elif 'DATE' in sql_type_upper:
            return 'DATE'
        elif 'TIME' in sql_type_upper:
            return 'TIME'
        else:
            return 'VARCHAR'
    
    # 辅助方法实现
    def _extract_class_name(self, content: str) -> str:
        """提取类名"""
        match = re.search(r'public\s+(?:class|interface)\s+(\w+)', content)
        return match.group(1) if match else 'Unknown'
    
    def _extract_request_mapping(self, content: str) -> str:
        """提取RequestMapping"""
        match = re.search(r'@RequestMapping\s*\(\s*["\']([^"\']+)["\']', content)
        return match.group(1) if match else ''
    
    def _extract_controller_methods(self, content: str) -> List[str]:
        """提取Controller方法"""
        methods = re.findall(r'@(?:GetMapping|PostMapping|PutMapping|DeleteMapping|RequestMapping).*?\n\s*public\s+\w+[<>\w\s]*\s+(\w+)\s*\(', content, re.DOTALL)
        return methods
    
    def _extract_service_methods(self, content: str) -> List[str]:
        """提取Service方法"""
        methods = re.findall(r'public\s+\w+[<>\w\s]*\s+(\w+)\s*\([^)]*\)\s*{', content)
        return methods
    
    def _extract_service_dependencies(self, content: str) -> List[str]:
        """提取Service依赖"""
        dependencies = re.findall(r'@Autowired\s+private\s+(\w+)', content)
        return dependencies
    
    def _extract_mapper_methods(self, content: str) -> List[str]:
        """提取Mapper方法"""
        methods = re.findall(r'^\s*(\w+[<>\w\s]*)\s+(\w+)\s*\([^)]*\)\s*;', content, re.MULTILINE)
        return [method[1] for method in methods]
    
    def _extract_feign_methods(self, content: str) -> List[str]:
        """提取Feign方法"""
        methods = re.findall(r'@(?:GetMapping|PostMapping|PutMapping|DeleteMapping|RequestMapping).*?\n\s*(\w+[<>\w\s]*)\s+(\w+)\s*\(', content, re.DOTALL)
        return [method[1] for method in methods]
    
    def _extract_feign_service_name(self, content: str) -> str:
        """提取Feign服务名"""
        match = re.search(r'@FeignClient\s*\(\s*(?:name\s*=\s*|value\s*=\s*)?["\']([^"\']+)["\']', content)
        return match.group(1) if match else ''
    
    def _extract_xml_namespace(self, content: str) -> str:
        """提取XML命名空间"""
        match = re.search(r'<mapper\s+namespace\s*=\s*["\']([^"\']+)["\']', content)
        return match.group(1) if match else ''
    
    def _extract_sql_statements(self, content: str) -> List[str]:
        """提取SQL语句ID"""
        statements = re.findall(r'<(?:select|insert|update|delete)\s+id\s*=\s*["\']([^"\']+)["\']', content)
        return statements
    
    def _infer_module_from_path(self, path: Path) -> str:
        """从路径推断模块"""
        parts = path.parts
        for part in parts:
            if part in ['credit', 'limit', 'open', 'ls']:
                return part
        return 'unknown'
    
    def _infer_package_info(self, java_src_path: Path) -> Tuple[str, set]:
        """推断包信息和模块"""
        base_package = "com.yljr.crcl"
        modules = set()
        
        # 扫描目录结构推断模块
        for path in java_src_path.rglob("*"):
            if path.is_dir():
                path_str = str(path)
                for module in ['credit', 'limit', 'open', 'ls']:
                    if module in path_str:
                        modules.add(module)
        
        return base_package, modules
    
    def _calculate_controller_match_score(self, controller_info: Dict, 
                                        module_info: Dict, api_path: str) -> int:
        """计算Controller匹配分数"""
        score = 0
        
        # 模块匹配
        if controller_info['module'] == module_info['primary_module']:
            score += 50
        
        # RequestMapping匹配
        controller_mapping = controller_info['request_mapping']
        if module_info['primary_module'] in controller_mapping:
            score += 30
        
        if module_info['secondary_module'] in controller_mapping:
            score += 20
        
        return score
    
    def _analyze_needs_feign_call(self, business_logic: str) -> bool:
        """分析是否需要Feign调用"""
        feign_keywords = ['调用', 'call', '外部', 'external', '服务', 'service', '接口', 'api']
        return any(keyword in business_logic.lower() for keyword in feign_keywords)
    
    def _analyze_needs_database_operation(self, business_logic: str) -> bool:
        """分析是否需要数据库操作"""
        db_keywords = ['查询', 'query', '保存', 'save', '更新', 'update', '删除', 'delete', '数据', 'data']
        return any(keyword in business_logic.lower() for keyword in db_keywords)
    
    def _find_best_application_service_match(self, interface_name: str, module_info: Dict) -> Optional[Dict]:
        """查找最佳Application Service匹配"""
        # 简化实现，实际可以更复杂
        for service_name, service_info in self.project_structure['application_services'].items():
            if service_info['module'] == module_info['primary_module']:
                return service_info
        return None
    
    def _find_best_domain_service_match(self, interface_name: str, module_info: Dict) -> Optional[Dict]:
        """查找最佳Domain Service匹配"""
        for service_name, service_info in self.project_structure['domain_services'].items():
            if service_info['module'] == module_info['primary_module']:
                return service_info
        return None
    
    def _find_best_mapper_match(self, interface_name: str, module_info: Dict) -> Optional[Dict]:
        """查找最佳Mapper匹配"""
        for mapper_name, mapper_info in self.project_structure['mappers'].items():
            if mapper_info['module'] == module_info['primary_module']:
                return mapper_info
        return None
    
    def _find_best_feign_client_match(self, interface_name: str, module_info: Dict, 
                                    business_logic: str) -> Optional[Dict]:
        """查找最佳Feign Client匹配"""
        for feign_name, feign_info in self.project_structure['feign_clients'].items():
            if feign_info['module'] == module_info['primary_module']:
                return feign_info
        return None
    
    def _snake_to_camel(self, snake_str: str) -> str:
        """下划线转驼峰命名"""
        if not snake_str:
            return snake_str
        
        components = snake_str.split('_')
        return components[0] + ''.join(word.capitalize() for word in components[1:])
    
    def _first_char_lower(self, text: str) -> str:
        """将首字母转换为小写"""
        if not text:
            return text
        return text[0].lower() + text[1:] if len(text) > 1 else text.lower()