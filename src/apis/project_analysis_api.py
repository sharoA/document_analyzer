#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目结构分析API - 为智能代码生成提供项目上下文
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

from flask import Flask, request, jsonify
from ..utils.java_code_analyzer import JavaCodeAnalyzer

logger = logging.getLogger(__name__)

class ProjectAnalysisAPI:
    """项目结构分析API - 为代码生成提供深度项目上下文"""
    
    def __init__(self):
        self.java_analyzer = JavaCodeAnalyzer()
        self.analysis_cache = {}  # 缓存分析结果
    
    def analyze_project_for_code_generation(self, project_path: str, service_name: str = None) -> Dict[str, Any]:
        """
        为代码生成分析项目结构
        返回适合大模型理解的项目上下文信息
        """
        logger.info(f"🔍 开始分析项目用于代码生成: {project_path}")
        
        # 检查缓存
        cache_key = f"{project_path}_{service_name or 'default'}"
        if cache_key in self.analysis_cache:
            logger.info("📋 使用缓存的分析结果")
            return self.analysis_cache[cache_key]
        
        try:
            # 首先查找最佳的Java项目路径
            actual_project_path = self._find_best_java_project_path(project_path, service_name)
            logger.info(f"📂 实际分析路径: {actual_project_path}")
            
            # 执行完整项目分析
            analysis_result = self.java_analyzer.analyze_project(actual_project_path, service_name)
            
            # 更新project_path为实际路径
            analysis_result['project_path'] = actual_project_path
            
            # 提取代码生成所需的关键信息
            code_generation_context = self._extract_code_generation_context(analysis_result)
            
            # 缓存结果
            self.analysis_cache[cache_key] = code_generation_context
            
            logger.info("✅ 项目分析完成，已提取代码生成上下文")
            return code_generation_context
            
        except Exception as e:
            logger.error(f"❌ 项目分析失败: {e}")
            raise
    
    def _find_best_java_project_path(self, base_path: str, service_name: str = None) -> str:
        """查找最佳的Java项目路径，支持递归查找深层结构"""
        
        logger.info(f"🔍 在 {base_path} 中查找最佳Java项目路径...")
        logger.info(f"🎯 目标服务名: {service_name}")
        
        potential_paths = []
        
        # 方法1：递归查找所有包含src/main/java的目录
        for root, dirs, files in os.walk(base_path):
            # 跳过不相关的目录以提高搜索效率
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['target', 'build', 'out', 'bin', 'logs', 'tmp']]
            
            if 'src' in dirs:
                src_path = os.path.join(root, 'src')
                java_path = os.path.join(src_path, 'main', 'java')
                
                if os.path.exists(java_path):
                    # 检查Java文件数量
                    java_files_count = 0
                    for java_root, java_dirs, java_files in os.walk(java_path):
                        java_files_count += len([f for f in java_files if f.endswith('.java')])
                    
                    if java_files_count > 0:
                        priority = self._calculate_path_priority(root, service_name, java_files_count)
                        relative_depth = len(Path(root).relative_to(Path(base_path)).parts)
                        
                        potential_paths.append({
                            'path': root,
                            'java_files': java_files_count,
                            'priority': priority,
                            'depth': relative_depth,
                            'relative_path': str(Path(root).relative_to(Path(base_path)))
                        })
                        
                        logger.info(f"   📁 发现Java项目: {Path(root).name}")
                        logger.info(f"      🎯 相对路径: {potential_paths[-1]['relative_path']}")
                        logger.info(f"      📊 Java文件: {java_files_count}个")
                        logger.info(f"      📐 目录深度: {relative_depth}")
                        logger.info(f"      🏆 优先级分数: {priority}")
        
        if not potential_paths:
            logger.warning(f"⚠️ 在 {base_path} 中未找到包含Java文件的src/main/java结构")
            return base_path
        
        # 排序并选择最佳路径
        potential_paths.sort(key=lambda x: x['priority'], reverse=True)
        
        # 记录前3个候选路径
        logger.info(f"📋 排序后的候选路径（前3个）:")
        for i, path_info in enumerate(potential_paths[:3]):
            logger.info(f"   {i+1}. {path_info['relative_path']} (优先级: {path_info['priority']})")
        
        # 选择最佳路径
        best_path = potential_paths[0]
        logger.info(f"✅ 选择最佳Java项目路径:")
        logger.info(f"   📁 完整路径: {best_path['path']}")
        logger.info(f"   📋 相对路径: {best_path['relative_path']}")
        logger.info(f"   🏆 最终优先级: {best_path['priority']}")
        
        return best_path['path']
    
    def _calculate_path_priority(self, path: str, service_name: str, java_files_count: int) -> int:
        """计算路径优先级 - 增强版，修复路径选择问题"""
        priority = 0
        path_lower = path.lower()
        path_parts = Path(path).parts
        
        # 🔧 修复：服务名匹配加分（最重要的因素，权重极高）
        if service_name:
            service_clean = service_name.lower().replace('服务', '').replace('-service', '').replace('_service', '')
            service_keywords = service_clean.split('-')
            
            # 精确匹配服务名关键词
            match_score = 0
            for keyword in service_keywords:
                if keyword and len(keyword) > 2:  # 忽略过短的关键词
                    if keyword in path_lower:
                        match_score += 500  # 🔧 大幅提高服务名匹配的权重
                        logger.info(f"   🎯 服务名关键词匹配: {keyword} -> +500")
            
            # 特别处理：如果路径包含完整的服务名，给予超高优先级
            service_full_name = service_name.lower().replace('服务', '')
            if service_full_name in path_lower:
                match_score += 1000  # 🔧 完整服务名匹配超高优先级
                logger.info(f"   🎯🎯 完整服务名匹配: {service_full_name} -> +1000")
            
            priority += match_score
        
        # 🔧 修复：降低Java文件数量的影响，避免过度权重
        # 基础分数：Java文件数量（降低权重，最多50分）
        priority += min(java_files_count // 20, 50)  # 降低文件数量的影响
        
        # 深度优先：更深的目录结构通常是具体的服务模块
        depth = len(path_parts)
        if depth >= 8:  # 很深的目录结构
            priority += 200
            logger.info(f"   📐 深层目录结构 (深度{depth}) -> +200")
        elif depth >= 6:  # 中等深度
            priority += 100
            logger.info(f"   📐 中等深度结构 (深度{depth}) -> +100")
        
        # 具体服务模块目录名匹配
        service_module_indicators = [
            'user-basic-service', 'user-basic-general', 'basic-service', 'basic-general', 
            'service', 'api', 'web', 'rest', 'main', 'core'
        ]
        for indicator in service_module_indicators:
            if indicator in path_lower:
                priority += 120
                logger.info(f"   📦 服务模块匹配: {indicator} -> +120")
                break  # 只加分一次
        
        # 业务域匹配
        business_domains = [
            'user', 'basic', 'general', 'common', 'core',
            'order', 'payment', 'product', 'manage', 'admin'
        ]
        for domain in business_domains:
            if domain in path_lower:
                priority += 60
                logger.info(f"   🏢 业务域匹配: {domain} -> +60")
                break  # 只加分一次
        
        # 标准架构层级目录加分
        architecture_indicators = [
            'src/main/java', 'interfaces', 'application', 'domain', 
            'controller', 'service', 'mapper', 'entity', 'dto'
        ]
        
        for arch_indicator in architecture_indicators:
            if arch_indicator in path_lower:
                priority += 100
                logger.info(f"   🏗️ 架构层级匹配: {arch_indicator} -> +100")
                break  # 只加分一次
        
        # 🔧 新增：专门针对zqyl-user-center-service项目的深层路径识别
        if 'zqyl-user-center-service' in path_lower:
            if 'user-basic-service' in path_lower and 'user-basic-general' in path_lower:
                priority += 800  # 深层服务模块路径超高优先级
                logger.info(f"   🎯🎯🎯 深层服务模块路径匹配 -> +800")
            elif 'user-basic-service' in path_lower or 'user-basic-general' in path_lower:
                priority += 400  # 部分深层路径匹配
                logger.info(f"   🎯🎯 部分深层路径匹配 -> +400")
        
        # 避免选择根目录或过于通用的目录
        if len(path_parts) <= 4:
            priority -= 100  # 🔧 增加对浅层目录的惩罚
            logger.info(f"   ⚠️ 目录层级过浅 -> -100")
        
        # 避免选择包含测试、示例等的目录
        test_indicators = ['test', 'example', 'demo', 'sample', 'template']
        for test_indicator in test_indicators:
            if test_indicator in path_lower:
                priority -= 50
                logger.info(f"   🚫 测试/示例目录: {test_indicator} -> -50")
        
        return max(priority, 0)  # 确保优先级不为负数
    
    def _extract_code_generation_context(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """提取适合代码生成的项目上下文信息"""
        
        # 基础项目信息
        project_info = {
            'service_name': analysis_result.get('service_name', 'unknown'),
            'project_path': analysis_result.get('project_path'),
            'architecture_type': analysis_result['summary'].get('architecture_type'),
            'is_spring_boot': analysis_result['summary'].get('is_spring_boot'),
            'is_mybatis_plus': analysis_result['summary'].get('is_mybatis_plus')
        }
        
        # 包命名规范
        package_analysis = analysis_result.get('package_analysis', {})
        package_patterns = {
            'base_package': self._extract_base_package(analysis_result),
            'business_domains': package_analysis.get('business_domains', {}),
            'naming_compliance': package_analysis.get('naming_compliance', 0)
        }
        
        # 层级架构模式
        layer_analysis = analysis_result.get('layer_analysis', {})
        architecture_patterns = {
            'layer_distribution': {k: len(v) for k, v in layer_analysis.items()},
            'has_interfaces_layer': len(layer_analysis.get('interfaces', [])) > 0,
            'has_application_layer': len(layer_analysis.get('application', [])) > 0,
            'has_domain_layer': len(layer_analysis.get('domain', [])) > 0,
            'preferred_layer_style': self._determine_layer_style(layer_analysis)
        }
        
        # 组件和注解模式
        components = analysis_result.get('components_detected', {})
        component_patterns = {
            'component_usage': components,
            'common_annotations': self._extract_common_annotations(analysis_result),
            'dto_patterns': self._extract_dto_patterns(analysis_result),
            'service_patterns': self._extract_service_patterns(analysis_result)
        }
        
        # 命名规范
        naming_analysis = analysis_result.get('naming_analysis', {})
        naming_conventions = {
            'class_naming_patterns': self._extract_class_naming_patterns(naming_analysis),
            'method_naming_style': self._analyze_method_naming_style(analysis_result),
            'field_naming_style': self._analyze_field_naming_style(analysis_result)
        }
        
        # 技术栈和依赖
        technology_stack = {
            'spring_boot_version': self._detect_spring_boot_version(analysis_result),
            'mybatis_plus_features': self._extract_mybatis_features(analysis_result),
            'common_dependencies': self._extract_common_dependencies(analysis_result)
        }
        
        # 代码模板和示例
        code_templates = self._generate_code_templates(analysis_result)
        
        return {
            'project_info': project_info,
            'package_patterns': package_patterns,
            'architecture_patterns': architecture_patterns,
            'component_patterns': component_patterns,
            'naming_conventions': naming_conventions,
            'technology_stack': technology_stack,
            'code_templates': code_templates,
            'analysis_summary': self._create_generation_summary(analysis_result),
            'generation_guidelines': self._create_generation_guidelines(analysis_result)
        }
    
    def _extract_base_package(self, analysis_result: Dict[str, Any]) -> str:
        """提取基础包名 - 动态分析实际项目结构"""
        project_path = analysis_result.get('project_path', '')
        
        # 方法1：从Java文件中统计最常见的基础包
        package_counts = {}
        
        for file_info in analysis_result.get('java_files', []):
            package = file_info.get('package', '')
            if package and len(package.split('.')) >= 3:  # 至少3层包结构
                # 提取前3-4层作为基础包
                parts = package.split('.')
                
                # 尝试不同的基础包长度
                for base_length in [4, 3]:  # 优先4层，然后3层
                    if len(parts) >= base_length:
                        base_package = '.'.join(parts[:base_length])
                        package_counts[base_package] = package_counts.get(base_package, 0) + 1
        
        # 选择出现频率最高的基础包
        if package_counts:
            most_common_package = max(package_counts, key=package_counts.get)
            logger.info(f"📦 动态检测到基础包: {most_common_package} (出现{package_counts[most_common_package]}次)")
            return most_common_package
        
        # 方法2：从项目路径推断（如果Java文件分析失败）
        if project_path:
            try:
                # 查找src/main/java目录下的包结构
                src_java_path = None
                for root, dirs, files in os.walk(project_path):
                    if 'src' in dirs:
                        potential_java_path = os.path.join(root, 'src', 'main', 'java')
                        if os.path.exists(potential_java_path):
                            src_java_path = potential_java_path
                            break
                
                if src_java_path:
                    # 分析src/main/java下的目录结构
                    java_root = Path(src_java_path)
                    package_dirs = []
                    
                    # 查找包目录（通常以com, org, cn等开头）
                    for item in java_root.iterdir():
                        if item.is_dir() and item.name in ['com', 'org', 'cn', 'net']:
                            # 深入查找完整包路径
                            self._find_package_structures(item, [], package_dirs, max_depth=4)
                    
                    if package_dirs:
                        # 选择最深的包路径作为基础包
                        deepest_package = max(package_dirs, key=len)
                        inferred_package = '.'.join(deepest_package)
                        logger.info(f"📁 从目录结构推断基础包: {inferred_package}")
                        return inferred_package
                        
            except Exception as e:
                logger.warning(f"⚠️ 从项目路径推断包名失败: {e}")
        
        # 方法3：使用默认包名（最后的fallback）
        default_package = "com.main"
        logger.warning(f"⚠️ 无法动态检测包结构，使用默认包名: {default_package}")
        return default_package
    
    def _find_package_structures(self, current_dir: Path, current_package: List[str], 
                                results: List[List[str]], max_depth: int, current_depth: int = 0):
        """递归查找包结构"""
        if current_depth >= max_depth:
            return
        
        current_package.append(current_dir.name)
        
        # 检查当前目录是否包含Java文件
        has_java_files = any(f.suffix == '.java' for f in current_dir.iterdir() if f.is_file())
        
        if has_java_files and len(current_package) >= 3:
            # 找到了包含Java文件的包目录
            results.append(current_package.copy())
        
        # 继续递归查找子目录
        try:
            for subdir in current_dir.iterdir():
                if subdir.is_dir() and not subdir.name.startswith('.'):
                    self._find_package_structures(subdir, current_package.copy(), results, max_depth, current_depth + 1)
        except PermissionError:
            # 忽略权限错误
            pass
    
    def _determine_layer_style(self, layer_analysis: Dict[str, List[str]]) -> str:
        """确定层级风格"""
        interfaces_count = len(layer_analysis.get('interfaces', []))
        application_count = len(layer_analysis.get('application', []))
        domain_count = len(layer_analysis.get('domain', []))
        
        if interfaces_count > 0 and application_count > 0 and domain_count > 0:
            return "interfaces_application_domain"
        elif interfaces_count > 0 and application_count > 0:
            return "interfaces_application"
        else:
            return "traditional_mvc"
    
    def _extract_common_annotations(self, analysis_result: Dict[str, Any]) -> Dict[str, int]:
        """提取常用注解统计"""
        annotation_counts = {}
        
        for file_info in analysis_result.get('java_files', []):
            for annotation in file_info.get('annotations_used', []):
                annotation_counts[annotation] = annotation_counts.get(annotation, 0) + 1
        
        # 返回前10个最常用的注解
        return dict(sorted(annotation_counts.items(), key=lambda x: x[1], reverse=True)[:10])
    
    def _extract_dto_patterns(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """提取DTO模式"""
        naming_analysis = analysis_result.get('naming_analysis', {})
        
        return {
            'request_suffix': 'Req' if naming_analysis.get('request') else 'Request',
            'response_suffix': 'Resp' if naming_analysis.get('response') else 'Response',
            'dto_suffix': 'DTO' if any('DTO' in name for name in naming_analysis.get('dto', [])) else 'Dto',
            'vo_suffix': 'VO' if any('VO' in name for name in naming_analysis.get('vo', [])) else 'Vo'
        }
    
    def _extract_service_patterns(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """提取服务模式"""
        components = analysis_result.get('components_detected', {})
        
        return {
            'service_suffix': 'Service',
            'controller_suffix': 'Controller',
            'mapper_suffix': 'Mapper',
            'has_service_impl': components.get('services', 0) > 0,
            'has_rest_controllers': components.get('rest_controllers', 0) > 0
        }
    
    def _extract_class_naming_patterns(self, naming_analysis: Dict[str, List[str]]) -> Dict[str, str]:
        """提取类命名模式"""
        patterns = {}
        
        for pattern_type, class_names in naming_analysis.items():
            if class_names:
                # 分析第一个类名的模式
                first_class = class_names[0]
                if pattern_type == 'request':
                    patterns['request_pattern'] = 'Req' if first_class.endswith('Req') else 'Request'
                elif pattern_type == 'response':
                    patterns['response_pattern'] = 'Resp' if first_class.endswith('Resp') else 'Response'
                elif pattern_type == 'service':
                    patterns['service_pattern'] = 'Service'
                elif pattern_type == 'controller':
                    patterns['controller_pattern'] = 'Controller'
        
        return patterns
    
    def _analyze_method_naming_style(self, analysis_result: Dict[str, Any]) -> str:
        """分析方法命名风格"""
        # 分析常见的方法命名模式
        method_patterns = []
        
        for file_info in analysis_result.get('java_files', []):
            for class_info in file_info.get('classes', []):
                for method in class_info.get('methods', []):
                    method_name = method.get('name', '')
                    if method_name.startswith(('get', 'set', 'is', 'has')):
                        continue  # 跳过getter/setter
                    method_patterns.append(method_name)
        
        # 简单返回camelCase（企业项目的标准）
        return "camelCase"
    
    def _analyze_field_naming_style(self, analysis_result: Dict[str, Any]) -> str:
        """分析字段命名风格"""
        return "camelCase"  # 企业项目标准
    
    def _detect_spring_boot_version(self, analysis_result: Dict[str, Any]) -> str:
        """检测Spring Boot版本"""
        # 这里可以通过分析pom.xml或gradle文件来确定版本
        # 简化处理，返回常用版本
        return "2.7.0"
    
    def _extract_mybatis_features(self, analysis_result: Dict[str, Any]) -> List[str]:
        """提取MyBatis Plus特性"""
        features = []
        
        if analysis_result.get('mybatis_plus_detected'):
            components = analysis_result.get('components_detected', {})
            if components.get('mappers', 0) > 0:
                features.extend(['BaseMapper', '@Mapper'])
            if components.get('entities', 0) > 0:
                features.extend(['@TableId', '@TableField', '@TableName'])
        
        return features
    
    def _extract_common_dependencies(self, analysis_result: Dict[str, Any]) -> List[str]:
        """提取常见依赖"""
        dependencies = ['spring-boot-starter-web']
        
        if analysis_result.get('mybatis_plus_detected'):
            dependencies.extend(['mybatis-plus-boot-starter', 'mysql-connector-java'])
        
        if analysis_result.get('components_detected', {}).get('rest_controllers', 0) > 0:
            dependencies.append('spring-boot-starter-validation')
        
        return dependencies
    
    def _generate_code_templates(self, analysis_result: Dict[str, Any]) -> Dict[str, str]:
        """生成代码模板"""
        base_package = self._extract_base_package(analysis_result)
        architecture_type = analysis_result['summary'].get('architecture_type')
        
        templates = {}
        
        # Controller模板
        templates['controller'] = f"""package {base_package}.interfaces.rest;

import org.springframework.web.bind.annotation.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import javax.validation.Valid;

@RestController
@RequestMapping("/api/v1/{{entityName}}")
public class {{EntityName}}Controller {{

    @Autowired
    private {{EntityName}}Service {{entityName}}Service;

    @GetMapping
    public ResponseEntity<List<{{EntityName}}Response>> list() {{
        // TODO: 实现列表查询
        return ResponseEntity.ok(new ArrayList<>());
    }}

    @PostMapping
    public ResponseEntity<{{EntityName}}Response> create(@Valid @RequestBody {{EntityName}}CreateRequest request) {{
        // TODO: 实现创建逻辑
        return ResponseEntity.ok(new {{EntityName}}Response());
    }}
}}"""
        
        # Service模板
        templates['service'] = f"""package {base_package}.application.service;

import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Autowired;

@Service
public class {{EntityName}}Service {{

    @Autowired
    private {{EntityName}}Mapper {{entityName}}Mapper;

    public List<{{EntityName}}> findAll() {{
        // TODO: 实现业务逻辑
        return {{entityName}}Mapper.selectList(null);
    }}

    public {{EntityName}} create({{EntityName}}CreateRequest request) {{
        // TODO: 实现创建业务逻辑
        {{EntityName}} entity = new {{EntityName}}();
        // 设置属性...
        return {{entityName}}Mapper.insert(entity);
    }}
}}"""
        
        # Entity模板（如果使用MyBatis Plus）
        if analysis_result.get('mybatis_plus_detected'):
            templates['entity'] = f"""package {base_package}.domain.entity;

import com.baomidou.mybatisplus.annotation.*;
import java.time.LocalDateTime;

@TableName("{{table_name}}")
public class {{EntityName}} {{

    @TableId(type = IdType.AUTO)
    private Long id;

    private String name;

    private String status;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updatedAt;

    // TODO: 添加getter和setter方法
}}"""
        
        return templates
    
    def _create_generation_summary(self, analysis_result: Dict[str, Any]) -> str:
        """创建生成指导摘要"""
        summary = analysis_result.get('summary', {})
        
        return f"""
项目架构: {summary.get('architecture_type', 'unknown')}
技术栈: Spring Boot({'✓' if summary.get('is_spring_boot') else '✗'}), MyBatis Plus({'✓' if summary.get('is_mybatis_plus') else '✗'})
分层风格: {self._determine_layer_style(analysis_result.get('layer_analysis', {}))}
组件数量: Controllers({summary.get('components_summary', {}).get('rest_controllers', 0)}), Services({summary.get('components_summary', {}).get('services', 0)}), Mappers({summary.get('components_summary', {}).get('mappers', 0)})
可维护性指数: {summary.get('maintainability_index', 0)}/100
        """.strip()
    
    def _create_generation_guidelines(self, analysis_result: Dict[str, Any]) -> List[str]:
        """创建代码生成指导原则"""
        guidelines = []
        
        summary = analysis_result.get('summary', {})
        layer_analysis = analysis_result.get('layer_analysis', {})
        
        # 基础指导原则
        guidelines.append("遵循企业级微服务架构模式")
        guidelines.append("使用统一的异常处理和响应格式")
        guidelines.append("添加完整的参数验证和文档注释")
        
        # 分层指导
        if len(layer_analysis.get('interfaces', [])) > 0:
            guidelines.append("将Controller放在interfaces.rest包下")
        if len(layer_analysis.get('application', [])) > 0:
            guidelines.append("将Service放在application.service包下")
        if len(layer_analysis.get('domain', [])) > 0:
            guidelines.append("将Entity和Mapper放在domain包下")
        
        # 技术栈指导
        if summary.get('is_spring_boot'):
            guidelines.append("使用Spring Boot标准注解和配置")
        if summary.get('is_mybatis_plus'):
            guidelines.append("使用MyBatis Plus的BaseMapper和注解")
        
        # 命名规范指导
        base_package = self._extract_base_package(analysis_result)
        guidelines.append(f"使用包前缀: {base_package}")
        
        return guidelines

# Flask API路由
def create_project_analysis_routes(app: Flask):
    """创建项目分析API路由"""
    
    analysis_api = ProjectAnalysisAPI()
    
    @app.route('/api/project/analyze', methods=['POST'])
    def analyze_project():
        """分析项目结构API"""
        try:
            data = request.get_json()
            project_path = data.get('project_path')
            service_name = data.get('service_name')
            
            if not project_path:
                return jsonify({
                    'success': False,
                    'message': 'project_path参数必填'
                }), 400
            
            if not os.path.exists(project_path):
                return jsonify({
                    'success': False,
                    'message': f'项目路径不存在: {project_path}'
                }), 400
            
            # 执行项目分析
            context = analysis_api.analyze_project_for_code_generation(project_path, service_name)
            
            return jsonify({
                'success': True,
                'message': '项目分析完成',
                'context': context
            })
            
        except Exception as e:
            logger.error(f"❌ 项目分析API失败: {e}")
            return jsonify({
                'success': False,
                'message': f'项目分析失败: {str(e)}'
            }), 500
    
    @app.route('/api/project/context/<path:project_path>', methods=['GET'])
    def get_project_context(project_path: str):
        """获取项目上下文（用于代码生成）"""
        try:
            # URL解码路径
            project_path = project_path.replace('%2F', '/').replace('%5C', '\\')
            
            if not os.path.exists(project_path):
                return jsonify({
                    'success': False,
                    'message': f'项目路径不存在: {project_path}'
                }), 404
            
            # 获取缓存的分析结果
            cache_key = f"{project_path}_default"
            if cache_key in analysis_api.analysis_cache:
                context = analysis_api.analysis_cache[cache_key]
                return jsonify({
                    'success': True,
                    'context': context
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '项目尚未分析，请先调用分析接口'
                }), 404
                
        except Exception as e:
            logger.error(f"❌ 获取项目上下文失败: {e}")
            return jsonify({
                'success': False,
                'message': f'获取上下文失败: {str(e)}'
            }), 500

if __name__ == "__main__":
    # 测试用法
    api = ProjectAnalysisAPI()
    context = api.analyze_project_for_code_generation("D:/example/java_project", "user")
    print(json.dumps(context, indent=2, ensure_ascii=False)) 