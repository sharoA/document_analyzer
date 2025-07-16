#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Java代码结构分析工具
使用javalang进行Java AST解析，支持项目结构分析、注解提取、分层识别等功能
针对企业级微服务架构（interfaces → application → domain）优化
"""

import os
import re
import json
import logging
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
import javalang
import xml.etree.ElementTree as ET
from datetime import datetime

logger = logging.getLogger(__name__)

class JavaCodeAnalyzer:
    """Java代码结构分析器 - 企业级微服务架构优化版本"""
    
    def __init__(self):
        self.spring_annotations = {
            '@Controller', '@RestController', '@Service', '@Repository', 
            '@Component', '@Configuration', '@Entity', '@Table',
            '@FeignClient', '@Mapper', '@RequestMapping', '@GetMapping',
            '@PostMapping', '@PutMapping', '@DeleteMapping', '@Autowired',
            '@Value', '@ConfigurationProperties', '@Validated'
        }
        
        # 优化分层模式 - 针对 interfaces → application → domain 架构
        self.layer_patterns = {
            'interfaces': ['interfaces', 'facade', 'controller', 'web', 'api', 'rest'],
            'application': ['application', 'app', 'service', 'business'],
            'domain': ['domain', 'entity', 'model', 'po', 'mapper', 'persistence'],
            'dto': ['dto', 'req', 'resp', 'request', 'response', 'vo'],
            'config': ['config', 'configuration'],
            'exception': ['exception', 'error'],
            'util': ['util', 'utils', 'helper', 'tool', 'base'],
            'feign': ['feign', 'client', 'api']
        }
        
        # 优化命名模式 - 针对企业项目特点
        self.naming_patterns = {
            'request': r'.*Request$|.*Req$',
            'response': r'.*Response$|.*Resp$',
            'dto': r'.*DTO$|.*Dto$',
            'vo': r'.*VO$|.*Vo$',
            'po': r'.*PO$|.*Po$',
            'entity': r'.*Entity$',
            'exception': r'.*Exception$',
            'mapper': r'.*Mapper$',
            'service': r'.*Service$',
            'controller': r'.*Controller$',
            'feign': r'.*Feign$|.*FeignClient$|.*Client$'
        }
        
        # 企业项目特有模式
        self.enterprise_patterns = {
            'crcl_package': r'com\.yljr\.crcl\.',
            'mybatis_plus': ['@TableId', '@TableField', '@TableName', 'BaseMapper'],
            'dto_patterns': ['Dto', 'DTO', 'Req', 'Resp', 'Request', 'Response', 'Po', 'PO'],
            'layer_markers': ['interfaces', 'application', 'domain']
        }
    
    def analyze_project(self, project_path: str, service_name: str = None) -> Dict[str, Any]:
        """分析整个Java项目 - 企业级架构优化版本"""
        logger.info(f"🔍 开始分析企业级Java项目: {project_path}")
        
        project_path = Path(project_path)
        if not project_path.exists():
            raise FileNotFoundError(f"项目路径不存在: {project_path}")
        
        analysis_result = {
            'project_path': str(project_path),
            'service_name': service_name or project_path.name,
            'analysis_time': datetime.now().isoformat(),
            'project_structure': {},
            'java_files': [],
            'xml_files': [],
            'spring_boot_detected': False,
            'mybatis_plus_detected': False,
            'enterprise_architecture': {},
            'components_detected': {},
            'layer_analysis': {},
            'naming_analysis': {},
            'dependencies': {},
            'package_analysis': {},
            'summary': {}
        }
        
        # 扫描项目文件
        java_files = self._scan_java_files(project_path)
        xml_files = self._scan_xml_files(project_path)
        
        # 分析Java文件
        for java_file in java_files:
            try:
                file_analysis = self._analyze_java_file(java_file)
                analysis_result['java_files'].append(file_analysis)
            except Exception as e:
                logger.warning(f"⚠️ 分析Java文件失败 {java_file}: {e}")
        
        # 分析XML文件
        for xml_file in xml_files:
            try:
                xml_analysis = self._analyze_xml_file(xml_file)
                analysis_result['xml_files'].append(xml_analysis)
            except Exception as e:
                logger.warning(f"⚠️ 分析XML文件失败 {xml_file}: {e}")
        
        # 企业级项目特有分析
        analysis_result['spring_boot_detected'] = self._detect_spring_boot(analysis_result['java_files'])
        analysis_result['mybatis_plus_detected'] = self._detect_mybatis_plus(analysis_result['java_files'])
        analysis_result['enterprise_architecture'] = self._analyze_enterprise_architecture(analysis_result['java_files'])
        analysis_result['components_detected'] = self._analyze_enterprise_components(analysis_result['java_files'])
        analysis_result['layer_analysis'] = self._analyze_enterprise_layers(analysis_result['java_files'])
        analysis_result['naming_analysis'] = self._analyze_naming_patterns(analysis_result['java_files'])
        analysis_result['package_analysis'] = self._analyze_crcl_packages(analysis_result['java_files'])
        analysis_result['dependencies'] = self._analyze_dependencies(analysis_result['java_files'])
        analysis_result['project_structure'] = self._build_project_structure(analysis_result['java_files'])
        
        # 添加项目目录结构分析
        analysis_result['directory_structure'] = self._analyze_directory_structure(project_path)
        analysis_result['file_distribution'] = self._analyze_file_distribution(project_path)
        
        analysis_result['summary'] = self._generate_enterprise_summary(analysis_result)
        
        logger.info(f"✅ 企业级项目分析完成，共分析 {len(java_files)} 个Java文件")
        return analysis_result
    
    def _detect_mybatis_plus(self, java_files: List[Dict[str, Any]]) -> bool:
        """检测是否使用MyBatis Plus"""
        mybatis_plus_indicators = [
            '@TableId', '@TableField', '@TableName', 
            'BaseMapper', 'IService', 'ServiceImpl'
        ]
        
        for file_info in java_files:
            # 检查导入语句
            for import_path in file_info.get('imports', []):
                if 'mybatisplus' in import_path.lower() or 'baomidou' in import_path.lower():
                    return True
            
            # 检查注解
            for annotation in file_info.get('annotations_used', []):
                if any(indicator in annotation for indicator in mybatis_plus_indicators):
                    return True
            
            # 检查类信息
            for class_info in file_info.get('classes', []):
                for annotation in class_info.get('annotations', []):
                    if any(indicator in annotation for indicator in mybatis_plus_indicators):
                        return True
                
                # 检查继承关系
                if class_info.get('extends') and 'BaseMapper' in class_info.get('extends', ''):
                    return True
        
        return False
    
    def _analyze_enterprise_architecture(self, java_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析企业级架构特征"""
        architecture = {
            'architecture_type': 'enterprise_microservice',
            'layer_compliance': True,
            'package_structure': 'com.yljr.crcl.*',
            'dto_usage': 0,
            'feign_usage': 0,
            'mapper_usage': 0,
            'layer_distribution': {},
            'business_domains': set()
        }
        
        total_files = len(java_files)
        dto_count = 0
        feign_count = 0
        mapper_count = 0
        
        for file_info in java_files:
            package_name = file_info.get('package', '')
            
            # 统计DTO使用
            if any(pattern in file_info.get('file_path', '') for pattern in self.enterprise_patterns['dto_patterns']):
                dto_count += 1
            
            # 统计Feign使用
            if '@FeignClient' in str(file_info.get('annotations_used', [])):
                feign_count += 1
            
            # 统计Mapper使用
            if '@Mapper' in str(file_info.get('annotations_used', [])):
                mapper_count += 1
            
            # 提取业务域
            if package_name.startswith('com.yljr.crcl.'):
                parts = package_name.split('.')
                if len(parts) >= 4:
                    business_domain = parts[3]  # com.yljr.crcl.{domain}
                    architecture['business_domains'].add(business_domain)
        
        if total_files > 0:
            architecture['dto_usage'] = round((dto_count / total_files) * 100, 1)
            architecture['feign_usage'] = round((feign_count / total_files) * 100, 1)
            architecture['mapper_usage'] = round((mapper_count / total_files) * 100, 1)
        
        architecture['business_domains'] = list(architecture['business_domains'])
        return architecture
    
    def _analyze_enterprise_components(self, java_files: List[Dict[str, Any]]) -> Dict[str, int]:
        """分析企业级组件使用情况"""
        components = {
            'rest_controllers': 0,
            'feign_clients': 0,
            'services': 0,
            'mappers': 0,
            'entities': 0,
            'dtos': 0,
            'pos': 0,
            'configurations': 0,
            'exceptions': 0
        }
        
        component_patterns = {
            'rest_controllers': ['@RestController', '@Controller'],
            'feign_clients': ['@FeignClient'],
            'services': ['@Service'],
            'mappers': ['@Mapper'],
            'entities': ['@Entity', '@Table'],
            'configurations': ['@Configuration'],
            'exceptions': ['Exception']
        }
        
        for file_info in java_files:
            all_annotations = file_info.get('annotations_used', [])
            file_path = file_info.get('file_path', '')
            file_name = Path(file_path).stem
            
            # 标准组件检测
            for class_info in file_info.get('classes', []):
                all_annotations.extend(class_info.get('annotations', []))
            
            for component, patterns in component_patterns.items():
                if any(pattern in str(all_annotations) for pattern in patterns):
                    components[component] += 1
            
            # DTO检测
            if any(pattern in file_name for pattern in ['Dto', 'DTO', 'Req', 'Resp']):
                components['dtos'] += 1
            
            # PO检测
            if any(pattern in file_name for pattern in ['Po', 'PO']) or 'po' in file_path.lower():
                components['pos'] += 1
        
        return components
    
    def _analyze_enterprise_layers(self, java_files: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """分析企业级分层结构 - interfaces → application → domain"""
        layers = {
            'interfaces': [],
            'application': [],
            'domain': [],
            'dto': [],
            'config': [],
            'exception': [],
            'util': [],
            'feign': [],
            'unknown': []
        }
        
        for file_info in java_files:
            file_path = file_info.get('file_path', '')
            package_name = file_info.get('package', '')
            file_name = Path(file_path).stem
            
            layer_classified = False
            
            # 基于包路径分层
            for layer, patterns in self.layer_patterns.items():
                if any(pattern in package_name.lower() or pattern in file_path.lower() for pattern in patterns):
                    layers[layer].append(file_name)
                    layer_classified = True
                    break
            
            if not layer_classified:
                layers['unknown'].append(file_name)
        
        return layers
    
    def _analyze_crcl_packages(self, java_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析CRCL项目包结构"""
        package_analysis = {
            'total_packages': 0,
            'crcl_packages': 0,
            'business_domains': {},
            'layer_distribution': {},
            'package_depth': {},
            'naming_compliance': 0
        }
        
        packages = set()
        crcl_packages = set()
        
        for file_info in java_files:
            package_name = file_info.get('package', '')
            if package_name:
                packages.add(package_name)
                
                if package_name.startswith('com.yljr.crcl.'):
                    crcl_packages.add(package_name)
                    
                    # 分析业务域
                    parts = package_name.split('.')
                    if len(parts) >= 4:
                        domain = parts[3]  # com.yljr.crcl.{domain}
                        if domain not in package_analysis['business_domains']:
                            package_analysis['business_domains'][domain] = {
                                'package_count': 0,
                                'file_count': 0,
                                'layers': set()
                            }
                        
                        package_analysis['business_domains'][domain]['package_count'] += 1
                        package_analysis['business_domains'][domain]['file_count'] += 1
                        
                        # 分析层次
                        if len(parts) >= 5:
                            layer = parts[4]  # com.yljr.crcl.{domain}.{layer}
                            package_analysis['business_domains'][domain]['layers'].add(layer)
                    
                    # 包深度分析
                    depth = len(parts)
                    package_analysis['package_depth'][depth] = package_analysis['package_depth'].get(depth, 0) + 1
        
        package_analysis['total_packages'] = len(packages)
        package_analysis['crcl_packages'] = len(crcl_packages)
        package_analysis['naming_compliance'] = round((len(crcl_packages) / len(packages)) * 100, 1) if packages else 0
        
        # 转换set为list
        for domain_info in package_analysis['business_domains'].values():
            domain_info['layers'] = list(domain_info['layers'])
        
        return package_analysis
    
    def _determine_enterprise_architecture_style(self, analysis_result: Dict[str, Any]) -> str:
        """判断企业级架构风格"""
        components = analysis_result['components_detected']
        enterprise_arch = analysis_result.get('enterprise_architecture', {})
        
        # 检查是否为标准的企业微服务架构
        has_interfaces = components.get('rest_controllers', 0) > 0
        has_application = components.get('services', 0) > 0
        has_domain = components.get('mappers', 0) > 0 or components.get('entities', 0) > 0
        has_feign = components.get('feign_clients', 0) > 0
        high_dto_usage = enterprise_arch.get('dto_usage', 0) > 30
        
        if has_interfaces and has_application and has_domain:
            if has_feign and high_dto_usage:
                return 'enterprise_microservice_ddd'
            else:
                return 'enterprise_layered_architecture'
        elif has_feign and high_dto_usage:
            return 'microservice_with_feign'
        elif has_interfaces and has_application:
            return 'mvc_with_service_layer'
        else:
            return 'traditional_architecture'
    
    def _generate_enterprise_summary(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成企业级项目分析摘要"""
        java_files_count = len(analysis_result['java_files'])
        xml_files_count = len(analysis_result['xml_files'])
        enterprise_arch = analysis_result.get('enterprise_architecture', {})
        package_analysis = analysis_result.get('package_analysis', {})
        
        return {
            'total_java_files': java_files_count,
            'total_xml_files': xml_files_count,
            'is_spring_boot': analysis_result['spring_boot_detected'],
            'is_mybatis_plus': analysis_result['mybatis_plus_detected'],
            'architecture_type': self._determine_enterprise_architecture_style(analysis_result),
            'components_summary': analysis_result['components_detected'],
            'layer_distribution': {k: len(v) for k, v in analysis_result['layer_analysis'].items()},
            'naming_pattern_distribution': {k: len(v) for k, v in analysis_result['naming_analysis'].items()},
            'business_domains': enterprise_arch.get('business_domains', []),
            'dto_usage_rate': enterprise_arch.get('dto_usage', 0),
            'package_compliance': package_analysis.get('naming_compliance', 0),
            'complexity_score': self._calculate_complexity_score(analysis_result),
            'maintainability_index': self._calculate_enterprise_maintainability_index(analysis_result)
        }
    
    def _calculate_enterprise_maintainability_index(self, analysis_result: Dict[str, Any]) -> float:
        """计算企业级项目可维护性指数"""
        score = 0
        
        # 分层架构分数 (40分)
        layers = analysis_result['layer_analysis']
        if layers.get('interfaces') and layers.get('application') and layers.get('domain'):
            score += 40
        elif layers.get('interfaces') and layers.get('application'):
            score += 25
        
        # 包命名规范分数 (25分)
        package_analysis = analysis_result.get('package_analysis', {})
        compliance = package_analysis.get('naming_compliance', 0)
        score += (compliance / 100) * 25
        
        # DTO使用规范分数 (20分)
        enterprise_arch = analysis_result.get('enterprise_architecture', {})
        dto_usage = enterprise_arch.get('dto_usage', 0)
        if dto_usage >= 50:
            score += 20
        elif dto_usage >= 30:
            score += 15
        elif dto_usage >= 10:
            score += 10
        
        # 技术栈现代化分数 (15分)
        if analysis_result.get('spring_boot_detected'):
            score += 8
        if analysis_result.get('mybatis_plus_detected'):
            score += 7
        
        return round(min(score, 100), 1)
    
    def _generate_enterprise_markdown_report(self, analysis_result: Dict[str, Any]) -> str:
        """生成企业级项目Markdown格式的分析报告"""
        service_name = analysis_result.get('service_name', 'Unknown Service')
        summary = analysis_result.get('summary', {})
        enterprise_arch = analysis_result.get('enterprise_architecture', {})
        package_analysis = analysis_result.get('package_analysis', {})
        
        report = f"""# 企业级Java微服务架构分析报告

## 🏢 项目概览
- **服务名称**: {service_name}
- **分析时间**: {analysis_result.get('analysis_time', 'Unknown')}
- **项目路径**: {analysis_result.get('project_path', 'Unknown')}
- **架构类型**: {summary.get('architecture_type', 'Unknown')}
- **Spring Boot**: {'✅ 是' if summary.get('is_spring_boot') else '❌ 否'}
- **MyBatis Plus**: {'✅ 是' if summary.get('is_mybatis_plus') else '❌ 否'}

## 📊 统计摘要
- **Java文件总数**: {summary.get('total_java_files', 0)}
- **XML配置文件**: {summary.get('total_xml_files', 0)}
- **业务域数量**: {len(summary.get('business_domains', []))}
- **DTO使用率**: {summary.get('dto_usage_rate', 0)}%
- **包命名规范度**: {summary.get('package_compliance', 0)}%
- **复杂度分数**: {summary.get('complexity_score', 0)}/10
- **可维护性指数**: {summary.get('maintainability_index', 0)}/100

## 🏗️ 企业级架构特征

### 分层架构 (interfaces → application → domain)
"""
        
        layers = analysis_result.get('layer_analysis', {})
        for layer_name, layer_files in layers.items():
            if layer_files:
                report += f"\n### {layer_name.title()}层 ({len(layer_files)}个文件)\n"
                # 显示前10个文件
                for file in layer_files[:10]:
                    report += f"- {file}\n"
                if len(layer_files) > 10:
                    report += f"- ... 还有{len(layer_files) - 10}个文件\n"
        
        report += f"""
### 业务域分布
"""
        
        business_domains = package_analysis.get('business_domains', {})
        for domain, domain_info in business_domains.items():
            report += f"- **{domain}**: {domain_info['file_count']}个文件，层次：{', '.join(domain_info['layers'])}\n"
        
        report += f"""
## 🔧 组件分布统计
"""
        
        components = analysis_result.get('components_detected', {})
        component_mapping = {
            'rest_controllers': 'REST控制器',
            'feign_clients': 'Feign客户端',
            'services': '业务服务',
            'mappers': 'MyBatis映射器',
            'entities': 'JPA实体',
            'dtos': '数据传输对象',
            'pos': '持久化对象',
            'configurations': '配置类',
            'exceptions': '异常类'
        }
        
        for component, count in components.items():
            if count > 0:
                chinese_name = component_mapping.get(component, component)
                report += f"- **{chinese_name}**: {count}个\n"
        
        report += f"""
## 📦 包结构分析

### CRCL包命名规范
- **总包数**: {package_analysis.get('total_packages', 0)}
- **CRCL包数**: {package_analysis.get('crcl_packages', 0)}
- **命名规范度**: {package_analysis.get('naming_compliance', 0)}%

### 包深度分布
"""
        
        for depth, count in package_analysis.get('package_depth', {}).items():
            report += f"- **{depth}层包**: {count}个\n"
        
        report += """
## 🎯 命名模式分析
"""
        
        patterns = analysis_result.get('naming_analysis', {})
        pattern_mapping = {
            'request': '请求对象',
            'response': '响应对象', 
            'dto': '数据传输对象',
            'vo': '视图对象',
            'po': '持久化对象',
            'entity': 'JPA实体',
            'mapper': 'MyBatis映射器',
            'service': '业务服务',
            'controller': '控制器',
            'feign': 'Feign客户端'
        }
        
        for pattern, files in patterns.items():
            if files:
                chinese_name = pattern_mapping.get(pattern, pattern)
                report += f"\n### {chinese_name}模式 ({len(files)}个文件)\n"
                for file in files[:5]:
                    report += f"- {file}\n"
                if len(files) > 5:
                    report += f"- ... 还有{len(files) - 5}个文件\n"
        
        # 添加主要类详情
        report += "\n## 📋 主要类详情\n"
        displayed_files = 0
        for file_info in analysis_result.get('java_files', []):
            if displayed_files >= 20:  # 限制显示数量
                break
            
            if file_info.get('classes') and file_info.get('package', '').startswith('com.yljr.crcl'):
                report += f"\n### {Path(file_info['file_path']).stem}\n"
                report += f"- **包名**: {file_info.get('package', 'N/A')}\n"
                report += f"- **层级**: {file_info.get('layer_classification', 'unknown')}\n"
                
                annotations = file_info.get('annotations_used', [])
                if annotations:
                    report += f"- **注解**: {', '.join(annotations)}\n"
                
                for class_info in file_info['classes'][:2]:  # 每个文件最多显示2个类
                    report += f"\n#### 类: {class_info['name']}\n"
                    if class_info.get('annotations'):
                        report += f"- **类注解**: {', '.join(class_info['annotations'])}\n"
                    if class_info.get('extends'):
                        report += f"- **继承**: {class_info['extends']}\n"
                    if class_info.get('implements'):
                        report += f"- **实现接口**: {', '.join(class_info['implements'])}\n"
                    if class_info.get('methods'):
                        report += f"- **方法数量**: {len(class_info['methods'])}\n"
                    if class_info.get('fields'):
                        report += f"- **字段数量**: {len(class_info['fields'])}\n"
                
                displayed_files += 1
        
        report += "\n## 💡 架构分析建议\n"
        report += self._generate_enterprise_recommendations(analysis_result)
        
        return report
    
    def _generate_enterprise_recommendations(self, analysis_result: Dict[str, Any]) -> str:
        """生成企业级项目改进建议"""
        recommendations = []
        summary = analysis_result.get('summary', {})
        enterprise_arch = analysis_result.get('enterprise_architecture', {})
        package_analysis = analysis_result.get('package_analysis', {})
        
        # 架构分析
        maintainability = summary.get('maintainability_index', 0)
        if maintainability >= 80:
            recommendations.append("- ✅ 项目架构优秀，符合企业级微服务标准")
        elif maintainability >= 60:
            recommendations.append("- ⚠️ 项目架构良好，建议进一步优化分层结构")
        else:
            recommendations.append("- ❌ 建议重构项目架构，提高分层清晰度")
        
        # 分层建议
        layers = analysis_result.get('layer_analysis', {})
        if not all([layers.get('interfaces'), layers.get('application'), layers.get('domain')]):
            recommendations.append("- 🏗️ 建议完善 interfaces → application → domain 三层架构")
        
        # DTO使用建议
        dto_usage = enterprise_arch.get('dto_usage', 0)
        if dto_usage < 30:
            recommendations.append("- 📦 建议增加DTO使用，提高数据传输层的封装性")
        elif dto_usage > 80:
            recommendations.append("- ✅ DTO使用充分，数据传输层封装良好")
        
        # 包命名建议
        compliance = package_analysis.get('naming_compliance', 0)
        if compliance < 80:
            recommendations.append("- 📝 建议统一包命名规范，遵循com.yljr.crcl.*标准")
        
        # Feign使用建议
        components = analysis_result.get('components_detected', {})
        if components.get('feign_clients', 0) == 0:
            recommendations.append("- 🌐 建议使用Feign Client实现服务间调用")
        
        if not recommendations:
            recommendations.append("- 🎉 项目架构完美，符合企业级微服务最佳实践")
        
        return "\n".join(recommendations)
    
    def export_analysis_report(self, analysis_result: Dict[str, Any], output_dir: str = "outputs") -> str:
        """导出企业级分析报告"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        service_name = analysis_result.get('service_name', 'unknown_service')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"{service_name}_java_analysis_{timestamp}.md"
        report_path = output_path / report_filename
        
        # 生成企业级Markdown报告
        report_content = self._generate_enterprise_markdown_report(analysis_result)
        
        # 添加项目整体结构分析
        structure_overview = self.generate_project_overview_structure(analysis_result)
        
        # 添加层级结构分析
        hierarchy_content = self.generate_project_hierarchy(analysis_result)
        
        # 组合完整报告
        full_report = report_content + "\n\n" + structure_overview + "\n\n" + hierarchy_content
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(full_report)
        
        logger.info(f"📄 企业级分析报告已导出: {report_path}")
        return str(report_path)
    
    def _scan_java_files(self, project_path: Path) -> List[Path]:
        """扫描所有Java文件"""
        java_files = []
        for java_file in project_path.rglob("*.java"):
            # 排除测试文件和构建目录
            if not any(part in str(java_file) for part in ['target', 'build', '.git']):
                java_files.append(java_file)
        return java_files
    
    def _scan_xml_files(self, project_path: Path) -> List[Path]:
        """扫描XML配置文件"""
        xml_files = []
        for xml_file in project_path.rglob("*.xml"):
            # 只关注mapper和配置文件
            if any(keyword in str(xml_file).lower() for keyword in ['mapper', 'mybatis', 'config']):
                xml_files.append(xml_file)
        return xml_files
    
    def _analyze_java_file(self, file_path: Path) -> Dict[str, Any]:
        """分析单个Java文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='gbk') as f:
                content = f.read()
        
        try:
            tree = javalang.parse.parse(content)
        except Exception as e:
            logger.warning(f"⚠️ 解析Java文件失败 {file_path}: {e}")
            return self._create_basic_file_info(file_path, content)
        
        file_info = {
            'file_path': str(file_path),
            'relative_path': str(file_path).replace(str(file_path.parents[3]), ''),
            'package': tree.package.name if tree.package else '',
            'imports': [imp.path for imp in tree.imports] if tree.imports else [],
            'classes': [],
            'interfaces': [],
            'enums': [],
            'annotations_used': set(),
            'layer_classification': self._classify_layer(file_path),
            'naming_pattern': self._detect_naming_pattern(file_path.stem)
        }
        
        # 分析类型声明
        for type_decl in tree.types:
            if isinstance(type_decl, javalang.tree.ClassDeclaration):
                class_info = self._analyze_class(type_decl)
                file_info['classes'].append(class_info)
                file_info['annotations_used'].update(class_info['annotations'])
            elif isinstance(type_decl, javalang.tree.InterfaceDeclaration):
                interface_info = self._analyze_interface(type_decl)
                file_info['interfaces'].append(interface_info)
                file_info['annotations_used'].update(interface_info['annotations'])
            elif isinstance(type_decl, javalang.tree.EnumDeclaration):
                enum_info = self._analyze_enum(type_decl)
                file_info['enums'].append(enum_info)
        
        file_info['annotations_used'] = list(file_info['annotations_used'])
        return file_info
    
    def _create_basic_file_info(self, file_path: Path, content: str) -> Dict[str, Any]:
        """创建基本文件信息（当AST解析失败时）"""
        # 使用正则表达式提取基本信息
        package_match = re.search(r'package\s+([\w.]+);', content)
        class_matches = re.findall(r'(?:public\s+)?class\s+(\w+)', content)
        annotation_matches = re.findall(r'@(\w+)', content)
        
        return {
            'file_path': str(file_path),
            'relative_path': str(file_path).replace(str(file_path.parents[3]), ''),
            'package': package_match.group(1) if package_match else '',
            'imports': [],
            'classes': [{'name': name, 'annotations': [], 'methods': [], 'fields': []} for name in class_matches],
            'interfaces': [],
            'enums': [],
            'annotations_used': list(set(annotation_matches)),
            'layer_classification': self._classify_layer(file_path),
            'naming_pattern': self._detect_naming_pattern(file_path.stem),
            'parse_error': True
        }
    
    def _analyze_class(self, class_decl) -> Dict[str, Any]:
        """分析类声明"""
        class_info = {
            'name': class_decl.name,
            'modifiers': class_decl.modifiers or [],
            'annotations': self._extract_annotations(class_decl.annotations),
            'extends': class_decl.extends.name if class_decl.extends else None,
            'implements': [impl.name for impl in class_decl.implements] if class_decl.implements else [],
            'fields': [],
            'methods': [],
            'constructors': []
        }
        
        # 分析类成员
        for member in class_decl.body:
            if isinstance(member, javalang.tree.FieldDeclaration):
                for declarator in member.declarators:
                    field_info = {
                        'name': declarator.name,
                        'type': self._get_type_name(member.type),
                        'modifiers': member.modifiers or [],
                        'annotations': self._extract_annotations(member.annotations)
                    }
                    class_info['fields'].append(field_info)
            
            elif isinstance(member, javalang.tree.MethodDeclaration):
                method_info = {
                    'name': member.name,
                    'return_type': self._get_type_name(member.return_type) if member.return_type else 'void',
                    'modifiers': member.modifiers or [],
                    'annotations': self._extract_annotations(member.annotations),
                    'parameters': [
                        {
                            'name': param.name,
                            'type': self._get_type_name(param.type)
                        } for param in member.parameters
                    ] if member.parameters else []
                }
                class_info['methods'].append(method_info)
        
        return class_info
    
    def _analyze_interface(self, interface_decl) -> Dict[str, Any]:
        """分析接口声明"""
        interface_info = {
            'name': interface_decl.name,
            'modifiers': interface_decl.modifiers or [],
            'annotations': self._extract_annotations(interface_decl.annotations),
            'extends': [ext.name for ext in interface_decl.extends] if interface_decl.extends else [],
            'methods': []
        }
        
        # 分析接口方法
        for member in interface_decl.body:
            if isinstance(member, javalang.tree.MethodDeclaration):
                method_info = {
                    'name': member.name,
                    'return_type': self._get_type_name(member.return_type) if member.return_type else 'void',
                    'modifiers': member.modifiers or [],
                    'annotations': self._extract_annotations(member.annotations),
                    'parameters': [
                        {
                            'name': param.name,
                            'type': self._get_type_name(param.type)
                        } for param in member.parameters
                    ] if member.parameters else []
                }
                interface_info['methods'].append(method_info)
        
        return interface_info
    
    def _analyze_enum(self, enum_decl) -> Dict[str, Any]:
        """分析枚举声明"""
        return {
            'name': enum_decl.name,
            'modifiers': enum_decl.modifiers or [],
            'annotations': self._extract_annotations(enum_decl.annotations),
            'constants': [const.name for const in enum_decl.body.constants] if enum_decl.body and enum_decl.body.constants else []
        }
    
    def _extract_annotations(self, annotations) -> List[str]:
        """提取注解信息"""
        if not annotations:
            return []
        
        result = []
        for annotation in annotations:
            if hasattr(annotation, 'name'):
                result.append(f"@{annotation.name}")
            elif hasattr(annotation, 'type') and hasattr(annotation.type, 'name'):
                result.append(f"@{annotation.type.name}")
        
        return result
    
    def _get_type_name(self, type_obj) -> str:
        """获取类型名称"""
        if not type_obj:
            return 'unknown'
        
        if hasattr(type_obj, 'name'):
            return type_obj.name
        elif hasattr(type_obj, 'type') and hasattr(type_obj.type, 'name'):
            return type_obj.type.name
        else:
            return str(type_obj)
    
    def _classify_layer(self, file_path: Path) -> str:
        """根据文件路径和名称分类层级"""
        path_str = str(file_path).lower()
        file_name = file_path.stem.lower()
        
        for layer, patterns in self.layer_patterns.items():
            if any(pattern in path_str or pattern in file_name for pattern in patterns):
                return layer
        
        return 'unknown'
    
    def _detect_naming_pattern(self, class_name: str) -> str:
        """检测命名模式"""
        for pattern_name, pattern in self.naming_patterns.items():
            if re.match(pattern, class_name):
                return pattern_name
        
        return 'unknown'
    
    def _analyze_xml_file(self, xml_path: Path) -> Dict[str, Any]:
        """分析XML配置文件"""
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            xml_info = {
                'file_path': str(xml_path),
                'type': 'unknown',
                'namespace': root.tag,
                'content': {}
            }
            
            # 检测MyBatis Mapper文件
            if root.tag.endswith('mapper') or 'mapper' in str(xml_path).lower():
                xml_info['type'] = 'mybatis_mapper'
                xml_info['content'] = self._analyze_mybatis_mapper(root)
            
            return xml_info
        
        except Exception as e:
            logger.warning(f"⚠️ 解析XML文件失败 {xml_path}: {e}")
            return {
                'file_path': str(xml_path),
                'type': 'unknown',
                'error': str(e)
            }
    
    def _analyze_mybatis_mapper(self, root) -> Dict[str, Any]:
        """分析MyBatis Mapper XML"""
        mapper_info = {
            'namespace': root.get('namespace', ''),
            'select_statements': [],
            'insert_statements': [],
            'update_statements': [],
            'delete_statements': [],
            'result_maps': []
        }
        
        for child in root:
            if child.tag == 'select':
                mapper_info['select_statements'].append({
                    'id': child.get('id', ''),
                    'result_type': child.get('resultType', ''),
                    'parameter_type': child.get('parameterType', '')
                })
            elif child.tag == 'insert':
                mapper_info['insert_statements'].append({
                    'id': child.get('id', ''),
                    'parameter_type': child.get('parameterType', '')
                })
            elif child.tag == 'update':
                mapper_info['update_statements'].append({
                    'id': child.get('id', ''),
                    'parameter_type': child.get('parameterType', '')
                })
            elif child.tag == 'delete':
                mapper_info['delete_statements'].append({
                    'id': child.get('id', ''),
                    'parameter_type': child.get('parameterType', '')
                })
            elif child.tag == 'resultMap':
                mapper_info['result_maps'].append({
                    'id': child.get('id', ''),
                    'type': child.get('type', '')
                })
        
        return mapper_info
    
    def _detect_spring_boot(self, java_files: List[Dict[str, Any]]) -> bool:
        """检测是否为Spring Boot项目"""
        spring_boot_indicators = [
            '@SpringBootApplication',
            '@EnableAutoConfiguration',
            'SpringApplication'
        ]
        
        for file_info in java_files:
            for annotation in file_info.get('annotations_used', []):
                if any(indicator in annotation for indicator in spring_boot_indicators):
                    return True
            
            for class_info in file_info.get('classes', []):
                for annotation in class_info.get('annotations', []):
                    if any(indicator in annotation for indicator in spring_boot_indicators):
                        return True
        
        return False
    
    def _analyze_naming_patterns(self, java_files: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """分析命名模式"""
        patterns = {
            'request': [],
            'response': [],
            'dto': [],
            'vo': [],
            'po': [],
            'entity': [],
            'exception': [],
            'mapper': [],
            'service': [],
            'controller': [],
            'feign': [],
            'unknown': []
        }
        
        for file_info in java_files:
            pattern = file_info.get('naming_pattern', 'unknown')
            file_name = Path(file_info['file_path']).stem
            
            if pattern in patterns:
                patterns[pattern].append(file_name)
            else:
                patterns['unknown'].append(file_name)
        
        return patterns
    
    def _analyze_dependencies(self, java_files: List[Dict[str, Any]]) -> Dict[str, Set[str]]:
        """分析依赖关系"""
        dependencies = {}
        
        for file_info in java_files:
            file_name = Path(file_info['file_path']).stem
            file_deps = set()
            
            # 从imports中提取依赖
            for import_path in file_info.get('imports', []):
                if not import_path.startswith('java.'):  # 排除标准库
                    file_deps.add(import_path.split('.')[-1])
            
            dependencies[file_name] = file_deps
        
        # 转换Set为List以便JSON序列化
        return {k: list(v) for k, v in dependencies.items()}
    
    def _build_project_structure(self, java_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """构建项目结构树"""
        structure = {}
        package_stats = {}
        
        for file_info in java_files:
            package = file_info.get('package', '')
            file_name = Path(file_info['file_path']).stem
            
            # 构建包结构
            if package:
                parts = package.split('.')
                current = structure
                
                for part in parts:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                
                # 添加文件信息
                current[file_name] = {
                    'type': 'class',
                    'layer': file_info.get('layer_classification'),
                    'pattern': file_info.get('naming_pattern'),
                    'annotations': file_info.get('annotations_used', [])
                }
                
                # 统计包信息
                if package not in package_stats:
                    package_stats[package] = {
                        'file_count': 0,
                        'classes': [],
                        'main_layer': 'unknown',
                        'annotation_count': {}
                    }
                
                package_stats[package]['file_count'] += 1
                package_stats[package]['classes'].append(file_name)
                
                # 统计主要层级
                layer = file_info.get('layer_classification', 'unknown')
                if package_stats[package]['main_layer'] == 'unknown' or layer != 'unknown':
                    package_stats[package]['main_layer'] = layer
                
                # 统计注解使用
                for annotation in file_info.get('annotations_used', []):
                    package_stats[package]['annotation_count'][annotation] = \
                        package_stats[package]['annotation_count'].get(annotation, 0) + 1
        
        return {
            'package_tree': structure,
            'package_statistics': package_stats
        }
    
    def _calculate_complexity_score(self, analysis_result: Dict[str, Any]) -> float:
        """计算复杂度分数（1-10分）"""
        java_files_count = len(analysis_result['java_files'])
        
        # 基于文件数量和组件数量计算复杂度
        base_score = min(java_files_count / 10, 5)  # 文件数量因子
        
        components = analysis_result['components_detected']
        component_score = sum(components.values()) / 10  # 组件因子
        
        return round(min(base_score + component_score, 10), 1)
    
    def generate_project_hierarchy(self, analysis_result: Dict[str, Any]) -> str:
        """生成项目层级结构报告"""
        project_structure = analysis_result.get('project_structure', {})
        package_stats = project_structure.get('package_statistics', {})
        
        hierarchy_report = []
        hierarchy_report.append("# 项目层级结构分析\n")
        
        # 按包分组显示
        hierarchy_report.append("## 📦 包结构统计\n")
        
        # 按文件数量排序包
        sorted_packages = sorted(package_stats.items(), key=lambda x: x[1]['file_count'], reverse=True)
        
        for package_name, stats in sorted_packages[:20]:  # 只显示前20个最大的包
            hierarchy_report.append(f"### {package_name}")
            hierarchy_report.append(f"- **文件数量**: {stats['file_count']}")
            hierarchy_report.append(f"- **主要层级**: {stats['main_layer']}")
            
            # 显示主要注解
            if stats['annotation_count']:
                top_annotations = sorted(stats['annotation_count'].items(), 
                                       key=lambda x: x[1], reverse=True)[:3]
                annotation_list = [f"{ann}({count})" for ann, count in top_annotations]
                hierarchy_report.append(f"- **主要注解**: {', '.join(annotation_list)}")
            
            # 显示部分类名
            class_sample = stats['classes'][:5]
            hierarchy_report.append(f"- **示例类**: {', '.join(class_sample)}")
            if len(stats['classes']) > 5:
                hierarchy_report.append(f"  (还有{len(stats['classes']) - 5}个类)")
            hierarchy_report.append("")
        
        return "\n".join(hierarchy_report)

    def _analyze_directory_structure(self, project_path: Path) -> Dict[str, Any]:
        """分析项目目录结构"""
        directory_info = {
            'total_files': 0,
            'total_directories': 0,
            'root_level_files': [],
            'root_level_directories': [],
            'deepest_level': 0,
            'level_distribution': {}
        }
        
        # 计算相对于项目根目录的层级
        def get_relative_depth(path: Path) -> int:
            """计算相对于项目根目录的深度"""
            try:
                relative = path.relative_to(project_path)
                return len(relative.parts) - 1  # 文件本身不算层级
            except ValueError:
                return 0
        
        # 首先扫描所有文件，确定最大深度
        max_depth = 0
        for path in project_path.rglob('*'):
            if path.is_file():
                depth = get_relative_depth(path)
                max_depth = max(max_depth, depth)
        
        directory_info['deepest_level'] = max_depth
        
        # 初始化层级分布字典
        for i in range(max_depth + 1):
            directory_info['level_distribution'][i] = 0
        
        # 扫描根目录直接内容
        try:
            for item in project_path.iterdir():
                if item.is_file():
                    directory_info['root_level_files'].append(item.name)
                elif item.is_dir():
                    directory_info['root_level_directories'].append(item.name)
        except PermissionError:
            pass
        
        # 递归统计所有文件和目录
        def count_items(path: Path):
            """递归统计文件和目录数量"""
            try:
                for item in path.iterdir():
                    if item.is_file():
                        directory_info['total_files'] += 1
                        # 计算文件的层级分布
                        depth = get_relative_depth(item)
                        if depth in directory_info['level_distribution']:
                            directory_info['level_distribution'][depth] += 1
                    elif item.is_dir():
                        directory_info['total_directories'] += 1
                        count_items(item)  # 递归处理子目录
            except PermissionError:
                pass  # 忽略无权限访问的目录
        
        count_items(project_path)
        
        return directory_info

    def _analyze_file_distribution(self, project_path: Path) -> Dict[str, Any]:
        """分析文件类型分布"""
        file_types = {}
        total_size = 0
        file_count = 0
        
        for file_path in project_path.rglob('*'):
            if file_path.is_file():
                file_count += 1
                file_ext = file_path.suffix.lower()
                if file_ext in file_types:
                    file_types[file_ext] += 1
                else:
                    file_types[file_ext] = 1
                
                try:
                    total_size += file_path.stat().st_size
                except (OSError, PermissionError):
                    pass  # 忽略无法访问的文件
        
        # 按数量排序
        sorted_file_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'total_files': file_count,
            'top_file_types': sorted_file_types[:10],
            'total_size_bytes': total_size,
            'average_file_size_bytes': total_size / file_count if file_count > 0 else 0,
            'file_extension_distribution': file_types
        }

    def generate_directory_tree(self, project_path: Path, max_depth: int = 4, exclude_patterns: List[str] = None) -> str:
        """生成项目目录树结构"""
        if exclude_patterns is None:
            exclude_patterns = ['.git', 'target', 'build', 'node_modules', '.idea', '.vscode', '__pycache__']
        
        tree_lines = []
        tree_lines.append(f"📁 {project_path.name}/")
        
        def should_exclude(path: Path) -> bool:
            """检查是否应该排除该路径"""
            return any(pattern in str(path) for pattern in exclude_patterns)
        
        def add_tree_item(path: Path, prefix: str = "", depth: int = 0, is_last: bool = True):
            """递归添加目录树项目"""
            if depth > max_depth or should_exclude(path):
                return
            
            # 获取当前层级的所有项目
            try:
                items = sorted([item for item in path.iterdir() if not should_exclude(item)], 
                             key=lambda x: (x.is_file(), x.name.lower()))
            except PermissionError:
                return
            
            for i, item in enumerate(items):
                is_last_item = (i == len(items) - 1)
                
                # 设置树形结构的连接符
                if depth == 0:
                    current_prefix = ""
                    next_prefix = ""
                else:
                    current_prefix = prefix + ("└── " if is_last_item else "├── ")
                    next_prefix = prefix + ("    " if is_last_item else "│   ")
                
                # 添加当前项目
                if item.is_dir():
                    # 统计目录下的文件数量
                    try:
                        file_count = len([f for f in item.rglob('*') if f.is_file() and not should_exclude(f)])
                        tree_lines.append(f"{current_prefix}📁 {item.name}/ ({file_count} files)")
                        
                        # 递归处理子目录
                        if depth < max_depth:
                            add_tree_item(item, next_prefix, depth + 1, is_last_item)
                    except PermissionError:
                        tree_lines.append(f"{current_prefix}📁 {item.name}/ (permission denied)")
                else:
                    # 文件大小格式化
                    try:
                        size = item.stat().st_size
                        if size < 1024:
                            size_str = f"{size}B"
                        elif size < 1024 * 1024:
                            size_str = f"{size/1024:.1f}KB"
                        else:
                            size_str = f"{size/(1024*1024):.1f}MB"
                        
                        # 根据文件类型选择图标
                        icon = self._get_file_icon(item.suffix.lower())
                        tree_lines.append(f"{current_prefix}{icon} {item.name} ({size_str})")
                    except (PermissionError, OSError):
                        tree_lines.append(f"{current_prefix}📄 {item.name} (unknown size)")
        
        add_tree_item(project_path, "", 0)
        return "\n".join(tree_lines)
    
    def _get_file_icon(self, file_extension: str) -> str:
        """根据文件扩展名返回相应的图标"""
        icon_map = {
            '.java': '☕',
            '.xml': '📋',
            '.yml': '⚙️',
            '.yaml': '⚙️',
            '.properties': '🔧',
            '.json': '📄',
            '.md': '📝',
            '.txt': '📄',
            '.sql': '🗃️',
            '.gitignore': '🚫',
            '.dockerfile': '🐳',
            '.sh': '📜',
            '.bat': '📜',
            '.jar': '📦',
            '.war': '📦',
            '.zip': '📦',
            '.log': '📊'
        }
        return icon_map.get(file_extension, '📄')
    
    def generate_project_overview_structure(self, analysis_result: Dict[str, Any]) -> str:
        """生成项目整体结构概览"""
        project_path = Path(analysis_result.get('project_path', ''))
        directory_structure = analysis_result.get('directory_structure', {})
        file_distribution = analysis_result.get('file_distribution', {})
        
        overview = []
        overview.append("# 🏗️ 项目整体结构分析\n")
        
        # 基本统计信息
        overview.append("## 📊 项目规模统计")
        overview.append(f"- **项目根目录**: {project_path.name}")
        overview.append(f"- **总文件数**: {directory_structure.get('total_files', 0)}")
        overview.append(f"- **总目录数**: {directory_structure.get('total_directories', 0)}")
        overview.append(f"- **最大目录深度**: {directory_structure.get('deepest_level', 0)} 层")
        
        # 文件大小信息
        total_size = file_distribution.get('total_size_bytes', 0)
        if total_size > 1024 * 1024 * 1024:
            size_str = f"{total_size / (1024 * 1024 * 1024):.2f} GB"
        elif total_size > 1024 * 1024:
            size_str = f"{total_size / (1024 * 1024):.2f} MB"
        elif total_size > 1024:
            size_str = f"{total_size / 1024:.2f} KB"
        else:
            size_str = f"{total_size} bytes"
        
        overview.append(f"- **项目总大小**: {size_str}")
        overview.append("")
        
        # 文件类型分布
        overview.append("## 📁 文件类型分布")
        top_file_types = file_distribution.get('top_file_types', [])
        for ext, count in top_file_types[:8]:
            ext_name = ext if ext else '无扩展名'
            percentage = (count / file_distribution.get('total_files', 1)) * 100
            overview.append(f"- **{ext_name}**: {count} 个文件 ({percentage:.1f}%)")
        overview.append("")
        
        # 根目录结构
        overview.append("## 🌟 根目录结构")
        root_dirs = directory_structure.get('root_level_directories', [])
        root_files = directory_structure.get('root_level_files', [])
        
        overview.append(f"### 📁 根目录文件夹 ({len(root_dirs)} 个)")
        for dir_name in sorted(root_dirs)[:10]:
            overview.append(f"- {dir_name}/")
        if len(root_dirs) > 10:
            overview.append(f"- ... 还有 {len(root_dirs) - 10} 个目录")
        overview.append("")
        
        overview.append(f"### 📄 根目录文件 ({len(root_files)} 个)")
        for file_name in sorted(root_files)[:10]:
            overview.append(f"- {file_name}")
        if len(root_files) > 10:
            overview.append(f"- ... 还有 {len(root_files) - 10} 个文件")
        overview.append("")
        
        # 目录树结构
        overview.append("## 🌳 完整目录树结构")
        overview.append("```")
        directory_tree = self.generate_directory_tree(project_path, max_depth=10)
        overview.append(directory_tree)
        overview.append("```")
        overview.append("")
        
        return "\n".join(overview)

if __name__ == "__main__":
    # 示例用法
    analyzer = JavaCodeAnalyzer()
    
    # 分析指定的Java项目
    project_path = input("请输入Java项目路径: ").strip()
    if project_path and os.path.exists(project_path):
        result = analyzer.analyze_project(project_path)
        report_path = analyzer.export_analysis_report(result)
        print(f"分析报告已生成: {report_path}")
    else:
        print("项目路径不存在")