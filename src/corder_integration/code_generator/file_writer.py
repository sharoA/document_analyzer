#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件写入器
专门负责将生成的内容写入到对应的文件中
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class FileWriter:
    """文件写入器 - 单一职责：将生成的内容写入文件"""
    
    def __init__(self):
        self.backup_dir = None
    
    def write_generated_content(self, project_path: str, 
                              generated_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        将生成的内容写入到对应的文件中
        
        Args:
            project_path: 项目路径
            generated_content: 生成的内容
            
        Returns:
            写入结果
        """
        logger.info(f"📝 开始写入生成的内容到项目: {project_path}")
        
        results = {
            'success': True,
            'written_files': [],
            'failed_files': [],
            'backup_dir': None
        }
        
        try:
            # 1. 创建备份目录
            self.backup_dir = self._create_backup_dir(project_path)
            results['backup_dir'] = self.backup_dir
            
            # 2. 写入各类文件
            for content_type, content_data in generated_content.items():
                if content_type == 'controller':
                    self._write_controller_content(project_path, content_data, results)
                elif content_type == 'service':
                    self._write_service_content(project_path, content_data, results)
                elif content_type == 'mapper':
                    self._write_mapper_content(project_path, content_data, results)
                elif content_type == 'entity':
                    self._write_entity_content(project_path, content_data, results)
                elif content_type == 'dto':
                    self._write_dto_content(project_path, content_data, results)
                elif content_type == 'xml':
                    self._write_xml_content(project_path, content_data, results)
            
            logger.info(f"✅ 内容写入完成: {len(results['written_files'])} 个文件成功")
            
        except Exception as e:
            logger.error(f"❌ 写入内容失败: {e}")
            results['success'] = False
            results['error'] = str(e)
        
        return results
    
    def _create_backup_dir(self, project_path: str) -> str:
        """创建备份目录"""
        import datetime
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(project_path) / "backup" / f"backup_{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"📁 创建备份目录: {backup_dir}")
        return str(backup_dir)
    
    def _write_controller_content(self, project_path: str, 
                                 controller_data: Dict[str, Any], 
                                 results: Dict[str, Any]):
        """写入Controller内容"""
        try:
            action = controller_data.get('action', 'create_new')
            target_class = controller_data.get('target_class', '')
            generated_code = controller_data.get('generated_code', '')
            
            if action == 'enhance_existing' and target_class:
                # 增强现有Controller
                self._enhance_existing_file(project_path, target_class, generated_code, 'controller', results)
            else:
                # 创建新Controller
                self._create_new_file(project_path, generated_code, 'controller', results)
                
        except Exception as e:
            logger.error(f"❌ 写入Controller内容失败: {e}")
            results['failed_files'].append(f"Controller: {str(e)}")
    
    def _write_service_content(self, project_path: str, 
                              service_data: Dict[str, Any], 
                              results: Dict[str, Any]):
        """写入Service内容"""
        try:
            action = service_data.get('action', 'create_new')
            target_class = service_data.get('target_class', '')
            generated_code = service_data.get('generated_code', '')
            
            if action == 'enhance_existing' and target_class:
                # 增强现有Service
                self._enhance_existing_file(project_path, target_class, generated_code, 'service', results)
            else:
                # 创建新Service
                self._create_new_file(project_path, generated_code, 'service', results)
                
        except Exception as e:
            logger.error(f"❌ 写入Service内容失败: {e}")
            results['failed_files'].append(f"Service: {str(e)}")
    
    def _write_mapper_content(self, project_path: str, 
                             mapper_data: Dict[str, Any], 
                             results: Dict[str, Any]):
        """写入Mapper内容"""
        try:
            action = mapper_data.get('action', 'create_new')
            target_class = mapper_data.get('target_class', '')
            generated_code = mapper_data.get('generated_code', '')
            
            if action == 'enhance_existing' and target_class:
                # 增强现有Mapper
                self._enhance_existing_file(project_path, target_class, generated_code, 'mapper', results)
            else:
                # 创建新Mapper
                self._create_new_file(project_path, generated_code, 'mapper', results)
                
        except Exception as e:
            logger.error(f"❌ 写入Mapper内容失败: {e}")
            results['failed_files'].append(f"Mapper: {str(e)}")
    
    def _write_entity_content(self, project_path: str, 
                             entity_data: Dict[str, Any], 
                             results: Dict[str, Any]):
        """写入Entity内容"""
        try:
            generated_code = entity_data.get('generated_code', '')
            self._create_new_file(project_path, generated_code, 'entity', results)
                
        except Exception as e:
            logger.error(f"❌ 写入Entity内容失败: {e}")
            results['failed_files'].append(f"Entity: {str(e)}")
    
    def _write_dto_content(self, project_path: str, 
                          dto_data: Dict[str, Any], 
                          results: Dict[str, Any]):
        """写入DTO内容"""
        try:
            generated_code = dto_data.get('generated_code', '')
            self._create_new_file(project_path, generated_code, 'dto', results)
                
        except Exception as e:
            logger.error(f"❌ 写入DTO内容失败: {e}")
            results['failed_files'].append(f"DTO: {str(e)}")
    
    def _write_xml_content(self, project_path: str, 
                          xml_data: Dict[str, Any], 
                          results: Dict[str, Any]):
        """写入XML内容"""
        try:
            generated_code = xml_data.get('generated_code', '')
            self._create_new_xml_file(project_path, generated_code, results)
                
        except Exception as e:
            logger.error(f"❌ 写入XML内容失败: {e}")
            results['failed_files'].append(f"XML: {str(e)}")
    
    def _enhance_existing_file(self, project_path: str, target_class: str, 
                              generated_code: str, file_type: str, 
                              results: Dict[str, Any]):
        """增强现有文件"""
        # 查找目标文件
        target_file = self._find_target_file(project_path, target_class, file_type)
        if not target_file:
            logger.error(f"❌ 找不到目标文件: {target_class}")
            results['failed_files'].append(f"{file_type}: 找不到目标文件 {target_class}")
            return
        
        # 备份原文件
        self._backup_file(target_file)
        
        # 读取原文件内容
        original_content = Path(target_file).read_text(encoding='utf-8')
        
        # 插入新内容
        enhanced_content = self._insert_generated_content(original_content, generated_code, file_type)
        
        # 写入增强后的内容
        Path(target_file).write_text(enhanced_content, encoding='utf-8')
        
        results['written_files'].append(f"{file_type}: {target_file} (enhanced)")
        logger.info(f"✅ 增强文件成功: {target_file}")
    
    def _create_new_file(self, project_path: str, generated_code: str, 
                        file_type: str, results: Dict[str, Any]):
        """创建新文件"""
        # 从生成的代码中提取文件信息
        file_info = self._extract_file_info(generated_code)
        
        if not file_info['class_name']:
            logger.error(f"❌ 无法从生成的代码中提取类名")
            results['failed_files'].append(f"{file_type}: 无法提取类名")
            return
        
        # 构造文件路径
        file_path = self._construct_file_path(project_path, file_info, file_type)
        
        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        file_path.write_text(generated_code, encoding='utf-8')
        
        results['written_files'].append(f"{file_type}: {file_path}")
        logger.info(f"✅ 创建新文件成功: {file_path}")
    
    def _create_new_xml_file(self, project_path: str, generated_code: str, 
                            results: Dict[str, Any]):
        """创建新XML文件"""
        # 从XML代码中提取namespace
        namespace_match = re.search(r'namespace="([^"]+)"', generated_code)
        if not namespace_match:
            logger.error(f"❌ 无法从XML代码中提取namespace")
            results['failed_files'].append("XML: 无法提取namespace")
            return
        
        namespace = namespace_match.group(1)
        # 从namespace中提取文件名
        class_name = namespace.split('.')[-1]
        
        # 构造XML文件路径
        xml_dir = Path(project_path) / "src" / "main" / "resources" / "mapper"
        xml_dir.mkdir(parents=True, exist_ok=True)
        
        xml_file = xml_dir / f"{class_name}.xml"
        
        # 写入XML文件
        xml_file.write_text(generated_code, encoding='utf-8')
        
        results['written_files'].append(f"XML: {xml_file}")
        logger.info(f"✅ 创建XML文件成功: {xml_file}")
    
    def _find_target_file(self, project_path: str, target_class: str, 
                         file_type: str) -> Optional[str]:
        """查找目标文件"""
        java_src_path = Path(project_path) / "src" / "main" / "java"
        
        # 搜索目标类文件
        for java_file in java_src_path.rglob(f"{target_class}.java"):
            return str(java_file)
        
        return None
    
    def _backup_file(self, file_path: str):
        """备份文件"""
        if not self.backup_dir:
            return
        
        source_file = Path(file_path)
        backup_file = Path(self.backup_dir) / source_file.name
        
        try:
            backup_file.write_text(source_file.read_text(encoding='utf-8'), encoding='utf-8')
            logger.debug(f"📋 备份文件: {file_path} -> {backup_file}")
        except Exception as e:
            logger.warning(f"⚠️ 备份文件失败: {e}")
    
    def _extract_file_info(self, generated_code: str) -> Dict[str, str]:
        """从生成的代码中提取文件信息"""
        info = {
            'class_name': '',
            'package': ''
        }
        
        # 提取包名
        package_match = re.search(r'package\\s+([a-zA-Z0-9_.]+);', generated_code)
        if package_match:
            info['package'] = package_match.group(1)
        
        # 提取类名
        class_match = re.search(r'public\\s+class\\s+(\\w+)', generated_code)
        if class_match:
            info['class_name'] = class_match.group(1)
        
        # 提取接口名
        interface_match = re.search(r'public\\s+interface\\s+(\\w+)', generated_code)
        if interface_match:
            info['class_name'] = interface_match.group(1)
        
        return info
    
    def _construct_file_path(self, project_path: str, file_info: Dict[str, str], 
                           file_type: str) -> Path:
        """构造文件路径"""
        # 基础Java源码路径
        java_src_path = Path(project_path) / "src" / "main" / "java"
        
        # 从包名构造目录路径
        package_path = file_info['package'].replace('.', '/')
        
        # 构造完整路径
        file_path = java_src_path / package_path / f"{file_info['class_name']}.java"
        
        return file_path
    
    def _insert_generated_content(self, original_content: str, 
                                 generated_code: str, file_type: str) -> str:
        """将生成的内容插入到原文件中"""
        
        if file_type == 'controller':
            return self._insert_controller_method(original_content, generated_code)
        elif file_type == 'service':
            return self._insert_service_method(original_content, generated_code)
        elif file_type == 'mapper':
            return self._insert_mapper_method(original_content, generated_code)
        
        return original_content
    
    def _insert_controller_method(self, original_content: str, 
                                 generated_code: str) -> str:
        """插入Controller方法"""
        # 查找类的结束位置
        class_end_pattern = r'(\\n\\s*})\\s*$'
        class_end_match = re.search(class_end_pattern, original_content)
        
        if class_end_match:
            # 在类结束前插入新方法
            insert_pos = class_end_match.start(1)
            new_content = (
                original_content[:insert_pos] +
                "\\n\\n" + generated_code + "\\n" +
                original_content[insert_pos:]
            )
            return new_content
        
        return original_content
    
    def _insert_service_method(self, original_content: str, 
                              generated_code: str) -> str:
        """插入Service方法"""
        return self._insert_controller_method(original_content, generated_code)
    
    def _insert_mapper_method(self, original_content: str, 
                             generated_code: str) -> str:
        """插入Mapper方法"""
        return self._insert_controller_method(original_content, generated_code)
    
    def get_write_summary(self, results: Dict[str, Any]) -> str:
        """获取写入摘要"""
        summary = f"文件写入摘要:\\n"
        summary += f"成功: {results['success']}\\n"
        summary += f"备份目录: {results.get('backup_dir', 'N/A')}\\n"
        summary += f"成功写入: {len(results['written_files'])} 个文件\\n"
        summary += f"失败: {len(results['failed_files'])} 个文件\\n"
        
        if results['written_files']:
            summary += "\\n成功写入的文件:\\n"
            for file in results['written_files']:
                summary += f"- {file}\\n"
        
        if results['failed_files']:
            summary += "\\n失败的文件:\\n"
            for file in results['failed_files']:
                summary += f"- {file}\\n"
        
        return summary