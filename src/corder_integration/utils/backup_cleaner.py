#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
备份文件清理工具
专门用于清理代码生成过程中产生的各种备份文件和目录
"""

import os
import glob
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class BackupCleaner:
    """备份文件清理器"""
    
    @staticmethod
    def cleanup_project_backups(project_path: str, patterns: List[str] = None) -> Dict[str, Any]:
        """
        清理项目中的所有备份文件和目录
        
        Args:
            project_path: 项目路径
            patterns: 备份目录模式，默认为常见的备份模式
            
        Returns:
            清理结果统计
        """
        if patterns is None:
            patterns = [
                "backup/strategy1_backup_*",
                "backup/function_calling_backup_*",
                "**/*.backup",
                "**/backup_*"
            ]
        
        result = {
            'success': True,
            'cleaned_directories': 0,
            'cleaned_files': 0,
            'errors': [],
            'cleaned_paths': []
        }
        
        try:
            project_path = Path(project_path).resolve()
            logger.info(f"🧹 开始清理项目备份: {project_path}")
            
            # 递归清理所有匹配的备份模式
            for pattern in patterns:
                BackupCleaner._cleanup_pattern(project_path, pattern, result)
            
            # 特殊处理：清理嵌套的备份目录
            BackupCleaner._cleanup_nested_backups(project_path, result)
            
            logger.info(f"🎉 备份清理完成: 删除 {result['cleaned_directories']} 目录, {result['cleaned_files']} 文件")
            
        except Exception as e:
            logger.error(f"❌ 备份清理失败: {e}")
            result['success'] = False
            result['errors'].append(str(e))
        
        return result
    
    @staticmethod
    def _cleanup_pattern(project_path: Path, pattern: str, result: Dict[str, Any]):
        """清理指定模式的备份"""
        
        try:
            # 使用glob查找匹配的路径
            search_pattern = str(project_path / pattern)
            matches = glob.glob(search_pattern, recursive=True)
            
            for match_path in matches:
                match_path = Path(match_path)
                
                try:
                    if match_path.is_dir():
                        # 删除目录
                        shutil.rmtree(match_path)
                        result['cleaned_directories'] += 1
                        result['cleaned_paths'].append(str(match_path))
                        logger.info(f"🗑️ 删除备份目录: {match_path}")
                        
                    elif match_path.is_file():
                        # 删除文件
                        match_path.unlink()
                        result['cleaned_files'] += 1
                        result['cleaned_paths'].append(str(match_path))
                        logger.info(f"🗑️ 删除备份文件: {match_path}")
                        
                except Exception as e:
                    error_msg = f"无法删除 {match_path}: {e}"
                    result['errors'].append(error_msg)
                    logger.warning(f"⚠️ {error_msg}")
            
        except Exception as e:
            error_msg = f"模式匹配失败 {pattern}: {e}"
            result['errors'].append(error_msg)
            logger.warning(f"⚠️ {error_msg}")
    
    @staticmethod
    def _cleanup_nested_backups(project_path: Path, result: Dict[str, Any]):
        """
        清理嵌套的备份目录
        特别处理像 backup/strategy1_backup_xxx/backup/strategy1_backup_yyy 这种嵌套情况
        """
        
        try:
            # 查找所有包含"backup"的目录
            for root, dirs, files in os.walk(project_path):
                # 过滤出backup相关的目录
                backup_dirs = [d for d in dirs if 'backup' in d.lower()]
                
                for backup_dir in backup_dirs:
                    backup_path = Path(root) / backup_dir
                    
                    # 检查是否是嵌套的备份目录
                    if BackupCleaner._is_nested_backup(backup_path):
                        try:
                            shutil.rmtree(backup_path)
                            result['cleaned_directories'] += 1
                            result['cleaned_paths'].append(str(backup_path))
                            logger.info(f"🗑️ 删除嵌套备份目录: {backup_path}")
                        except Exception as e:
                            error_msg = f"无法删除嵌套备份 {backup_path}: {e}"
                            result['errors'].append(error_msg)
                            logger.warning(f"⚠️ {error_msg}")
        
        except Exception as e:
            error_msg = f"嵌套备份清理失败: {e}"
            result['errors'].append(error_msg)
            logger.warning(f"⚠️ {error_msg}")
    
    @staticmethod
    def _is_nested_backup(backup_path: Path) -> bool:
        """判断是否是嵌套的备份目录"""
        
        # 检查路径中是否包含多个backup片段
        path_parts = backup_path.parts
        backup_count = sum(1 for part in path_parts if 'backup' in part.lower())
        
        # 如果路径中有多个backup，或者是strategy1_backup_开头的目录
        if backup_count > 1 or backup_path.name.startswith('strategy1_backup_'):
            return True
        
        # 检查目录内容，如果只包含备份相关的文件，也认为是备份目录
        try:
            if backup_path.is_dir():
                contents = list(backup_path.iterdir())
                if len(contents) == 0:
                    return True  # 空目录
                
                # 如果所有内容都是.java.backup或类似的备份文件
                backup_files = [f for f in contents if '.backup' in f.name or f.name.startswith('backup_')]
                if len(backup_files) == len(contents):
                    return True
        except Exception:
            pass
        
        return False
    
    @staticmethod
    def force_cleanup_specific_path(backup_path: str) -> bool:
        """
        强制清理指定的备份路径
        
        Args:
            backup_path: 要清理的备份路径
            
        Returns:
            是否清理成功
        """
        try:
            backup_path = Path(backup_path)
            
            if backup_path.exists():
                if backup_path.is_dir():
                    shutil.rmtree(backup_path)
                    logger.info(f"🗑️ 强制删除备份目录: {backup_path}")
                else:
                    backup_path.unlink()
                    logger.info(f"🗑️ 强制删除备份文件: {backup_path}")
                return True
            else:
                logger.info(f"ℹ️ 备份路径不存在: {backup_path}")
                return True
                
        except Exception as e:
            logger.error(f"❌ 强制清理失败 {backup_path}: {e}")
            return False