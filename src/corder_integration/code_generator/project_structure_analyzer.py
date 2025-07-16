#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目结构分析器
专门负责分析项目结构，获取项目的文件组织信息
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from utils.java_code_analyzer import JavaCodeAnalyzer
logger = logging.getLogger(__name__)


class ProjectStructureAnalyzer:
    """项目结构分析器 - 单一职责：分析项目结构"""
    
    def __init__(self):
        self.project_structure = {}
    
    def analyze_project_structure(self, project_path: str) -> Dict[str, Any]:
        """
        分析项目结构，获取完整的项目信息
        
        Args:
            project_path: 项目路径
            
        Returns:
            项目结构信息字典
        """
        logger.info(f"🔍 开始分析项目结构: {project_path}")
        
        structure = {
            'project_path': project_path,
            'base_package': '',
            'controllers': {},
            'services': {},
            'mappers': {},
            'entities': {},
            'dtos': {},
            'java_files': [],
            'xml_files': [],
            'modules': set(),
            'directory_tree': ''
        }
        
        # 检查项目路径是否存在
        if not os.path.exists(project_path):
            logger.error(f"❌ 项目路径不存在: {project_path}")
            return structure
        
        # 生成目录树结构用于后续分析
        java_code_analyzer = JavaCodeAnalyzer()
        directory_tree = java_code_analyzer.generate_directory_tree(Path(project_path), max_depth=10)
        structure['directory_tree'] = directory_tree
        logger.info(f"📁 目录树结构生成完成，总体结构:")
        logger.info(f"\n{directory_tree}")
        
        # 寻找所有可能的Java源码目录
        java_src_paths = self._find_java_source_paths(project_path)
        logger.info(f"🔍 找到 {len(java_src_paths)} 个Java源码路径:")
        for path in java_src_paths:
            logger.info(f"   - {path}")
        
        # 分析每个Java源码目录
        for java_src_path in java_src_paths:
            logger.info(f"📊 分析Java源码目录: {java_src_path}")
            src_result = self._analyze_java_sources(java_src_path)
            
            # 合并结果
            structure['java_files'].extend(src_result['java_files'])
            structure['controllers'].update(src_result['controllers'])
            structure['services'].update(src_result['services'])
            structure['mappers'].update(src_result['mappers'])
            structure['entities'].update(src_result['entities'])
            structure['dtos'].update(src_result['dtos'])
        
        # 分析资源目录
        resources_paths = self._find_resources_paths(project_path)
        for resources_path in resources_paths:
            logger.info(f"📊 分析资源目录: {resources_path}")
            res_result = self._analyze_resources(resources_path)
            structure['xml_files'].extend(res_result['xml_files'])
        
        # 推断基础包名
        structure['base_package'] = self._infer_base_package(structure['java_files'])
        
        logger.info(f"✅ 项目结构分析完成")
        logger.info(f"   基础包名: {structure['base_package']}")
        logger.info(f"   总Java文件: {len(structure['java_files'])}")
        logger.info(f"   Controllers: {len(structure['controllers'])}")
        logger.info(f"   Services: {len(structure['services'])}")
        logger.info(f"   Mappers: {len(structure['mappers'])}")
        logger.info(f"   Entities: {len(structure['entities'])}")
        logger.info(f"   DTOs: {len(structure['dtos'])}")
        
        self.project_structure = structure
        return structure
    
    def _analyze_java_sources(self, java_src_path: Path) -> Dict[str, Any]:
        """分析Java源码文件"""
        result = {
            'controllers': {},
            'services': {},
            'mappers': {},
            'entities': {},
            'dtos': {},
            'java_files': []
        }
        
        if not java_src_path.exists():
            logger.warning(f"⚠️ Java源码路径不存在: {java_src_path}")
            return result
        
        # 遍历所有Java文件
        java_files = list(java_src_path.rglob("*.java"))
        logger.info(f"📋 在 {java_src_path} 中找到 {len(java_files)} 个Java文件")
        
        for java_file in java_files:
            try:
                content = java_file.read_text(encoding='utf-8')
                file_info = self._analyze_java_file(java_file, content)
                result['java_files'].append(file_info)
                
                # 根据文件类型分类
                file_type = file_info['type']
                class_name = file_info['class_name']
                
                if file_type == 'controller':
                    result['controllers'][class_name] = file_info
                    logger.debug(f"✅ 发现Controller: {class_name} ({file_info['package']})")
                elif file_type == 'service':
                    result['services'][class_name] = file_info
                    logger.debug(f"✅ 发现Service: {class_name} ({file_info['package']})")
                elif file_type == 'mapper':
                    result['mappers'][class_name] = file_info
                    logger.debug(f"✅ 发现Mapper: {class_name} ({file_info['package']})")
                elif file_type == 'entity':
                    result['entities'][class_name] = file_info
                    logger.debug(f"✅ 发现Entity: {class_name} ({file_info['package']})")
                elif file_type == 'dto':
                    result['dtos'][class_name] = file_info
                    logger.debug(f"✅ 发现DTO: {class_name} ({file_info['package']})")
                else:
                    logger.debug(f"🔍 其他类型文件: {class_name} ({file_type})")
                    
            except Exception as e:
                logger.warning(f"⚠️ 分析Java文件失败 {java_file}: {e}")
        
        logger.info(f"📊 {java_src_path} 分析结果:")
        logger.info(f"   Controllers: {len(result['controllers'])}")
        logger.info(f"   Services: {len(result['services'])}")
        logger.info(f"   Mappers: {len(result['mappers'])}")
        logger.info(f"   Entities: {len(result['entities'])}")
        logger.info(f"   DTOs: {len(result['dtos'])}")
        
        return result
    
    def _analyze_java_file(self, java_file: Path, content: str) -> Dict[str, Any]:
        """分析单个Java文件"""
        file_info = {
            'file_path': str(java_file),
            'class_name': '',
            'package': '',
            'type': 'unknown',
            'annotations': [],
            'methods': [],
            'imports': [],
            'interfaces': [],
            'extends': ''
        }
        
        # 提取包名
        package_match = re.search(r'package\s+([a-zA-Z0-9_.]+);', content)
        if package_match:
            file_info['package'] = package_match.group(1)
        
        # 提取类名
        class_match = re.search(r'public\s+class\s+(\w+)', content)
        if class_match:
            file_info['class_name'] = class_match.group(1)
        
        # 提取接口名
        interface_match = re.search(r'public\s+interface\s+(\w+)', content)
        if interface_match:
            file_info['class_name'] = interface_match.group(1)
        
        # 提取注解
        annotations = re.findall(r'@(\w+)', content)
        file_info['annotations'] = list(set(annotations))
        
        # 提取导入
        imports = re.findall(r'import\s+([a-zA-Z0-9_.]+);', content)
        file_info['imports'] = imports
        
        # 提取方法
        methods = re.findall(r'public\s+\w+\s+(\w+)\s*\([^)]*\)', content)
        file_info['methods'] = methods
        
        # 判断文件类型
        file_info['type'] = self._determine_file_type(java_file, content, file_info)
        
        return file_info
    
    def _determine_file_type(self, java_file: Path, content: str, file_info: Dict) -> str:
        """判断Java文件类型"""
        file_path = str(java_file).replace('\\', '/')
        annotations = file_info['annotations']
        class_name = file_info['class_name']
        package = file_info['package']
        
        # 1. 根据注解判断（最高优先级）
        if 'Controller' in annotations or 'RestController' in annotations:
            return 'controller'
        elif 'Service' in annotations:
            return 'service'
        elif 'Mapper' in annotations:
            return 'mapper'
        elif 'Entity' in annotations or 'Table' in annotations:
            return 'entity'
        elif 'Component' in annotations or 'Repository' in annotations:
            return 'component'
        elif 'FeignClient' in annotations:
            return 'feign'
        
        # 2. 根据包名判断（中等优先级）
        if package:
            package_lower = package.lower()
            if '.controller' in package_lower or '.web' in package_lower:
                return 'controller'
            elif '.service' in package_lower:
                return 'service'
            elif '.mapper' in package_lower or '.dao' in package_lower:
                return 'mapper'
            elif '.entity' in package_lower or '.model' in package_lower or '.po' in package_lower:
                return 'entity'
            elif '.dto' in package_lower or '.vo' in package_lower:
                return 'dto'
            elif '.config' in package_lower:
                return 'config'
            elif '.exception' in package_lower:
                return 'exception'
            elif '.util' in package_lower:
                return 'util'
            elif '.feign' in package_lower:
                return 'feign'
        
        # 3. 根据文件路径判断（中等优先级）
        if '/controller/' in file_path or '/web/' in file_path:
            return 'controller'
        elif '/service/' in file_path:
            return 'service'
        elif '/mapper/' in file_path or '/dao/' in file_path:
            return 'mapper'
        elif '/entity/' in file_path or '/model/' in file_path or '/po/' in file_path:
            return 'entity'
        elif '/dto/' in file_path or '/vo/' in file_path:
            return 'dto'
        elif '/config/' in file_path:
            return 'config'
        elif '/exception/' in file_path:
            return 'exception'
        elif '/util/' in file_path:
            return 'util'
        elif '/feign/' in file_path:
            return 'feign'
        
        # 4. 根据类名判断（最低优先级）
        if class_name:
            if class_name.endswith('Controller'):
                return 'controller'
            elif class_name.endswith('Service') or class_name.endswith('ServiceImpl'):
                return 'service'
            elif class_name.endswith('Mapper') or class_name.endswith('Dao'):
                return 'mapper'
            elif class_name.endswith('Entity') or class_name.endswith('PO'):
                return 'entity'
            elif (class_name.endswith('Req') or class_name.endswith('Resp') or 
                  class_name.endswith('DTO') or class_name.endswith('VO') or
                  class_name.endswith('Request') or class_name.endswith('Response')):
                return 'dto'
            elif class_name.endswith('Config') or class_name.endswith('Configuration'):
                return 'config'
            elif class_name.endswith('Exception') or class_name.endswith('Error'):
                return 'exception'
            elif class_name.endswith('Util') or class_name.endswith('Utils') or class_name.endswith('Helper'):
                return 'util'
            elif 'Client' in class_name:
                return 'feign'
        
        return 'unknown'
    
    def _analyze_resources(self, resources_path: Path) -> Dict[str, Any]:
        """分析资源文件"""
        result = {
            'xml_files': []
        }
        
        # 分析XML映射文件
        mapper_path = resources_path / "mapper"
        if mapper_path.exists():
            for xml_file in mapper_path.rglob("*.xml"):
                try:
                    content = xml_file.read_text(encoding='utf-8')
                    xml_info = self._analyze_xml_file(xml_file, content)
                    result['xml_files'].append(xml_info)
                except Exception as e:
                    logger.warning(f"⚠️ 分析XML文件失败 {xml_file}: {e}")
        
        return result
    
    def _analyze_xml_file(self, xml_file: Path, content: str) -> Dict[str, Any]:
        """分析XML映射文件"""
        xml_info = {
            'file_path': str(xml_file),
            'namespace': '',
            'sql_statements': []
        }
        
        # 提取namespace
        namespace_match = re.search(r'namespace="([^"]+)"', content)
        if namespace_match:
            xml_info['namespace'] = namespace_match.group(1)
        
        # 提取SQL语句
        sql_patterns = [
            r'<select[^>]*id="([^"]+)"',
            r'<insert[^>]*id="([^"]+)"',
            r'<update[^>]*id="([^"]+)"',
            r'<delete[^>]*id="([^"]+)"'
        ]
        
        for pattern in sql_patterns:
            matches = re.findall(pattern, content)
            xml_info['sql_statements'].extend(matches)
        
        return xml_info
    
    def _infer_base_package(self, java_files: List[Dict]) -> str:
        """推断基础包名"""
        package_counts = {}
        
        for file_info in java_files:
            package = file_info.get('package', '')
            if package:
                # 提取基础包名（通常是com.yljr.xxx.xxx的格式）
                parts = package.split('.')
                if len(parts) >= 4 and parts[0] == 'com' and parts[1] == 'yljr':
                    base_package = '.'.join(parts[:4])
                    package_counts[base_package] = package_counts.get(base_package, 0) + 1
        
        # 返回出现次数最多的基础包名
        if package_counts:
            return max(package_counts, key=package_counts.get)
        
        return 'com.yljr.crcl'
    
    def get_project_structure_summary(self) -> str:
        """获取项目结构摘要信息"""
        if not self.project_structure:
            return "项目结构尚未分析"
        
        structure = self.project_structure
        summary = f"""项目结构摘要：
基础包名: {structure['base_package']}
项目路径: {structure['project_path']}

文件统计:
- Controllers: {len(structure['controllers'])}
- Services: {len(structure['services'])}
- Mappers: {len(structure['mappers'])}
- Entities: {len(structure['entities'])}
- DTOs: {len(structure['dtos'])}
- XML文件: {len(structure['xml_files'])}

主要Controller类:
{chr(10).join([f"- {name}: {info['package']}" for name, info in list(structure['controllers'].items())[:5]])}

主要Service类:
{chr(10).join([f"- {name}: {info['package']}" for name, info in list(structure['services'].items())[:5]])}

主要Mapper类:
{chr(10).join([f"- {name}: {info['package']}" for name, info in list(structure['mappers'].items())[:5]])}
"""
        return summary