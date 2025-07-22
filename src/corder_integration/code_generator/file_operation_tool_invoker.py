#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件操作工具调用器
为大模型提供安全的文件操作能力，支持function calling
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
import json
import datetime

logger = logging.getLogger(__name__)


class FileOperationToolInvoker:
    """文件操作工具调用器 - 为大模型提供安全的文件操作能力"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.backup_dir = None
        self._init_backup_dir()
        
        # 定义可供大模型调用的函数
        self.available_functions = {
            'read_file': self._read_file,
            'write_file': self._write_file,
            'replace_text': self._replace_text,
            'list_files': self._list_files,
            'file_exists': self._file_exists,
            'create_directory': self._create_directory,
            'backup_file': self._backup_file
        }
        
        # 定义函数签名，用于function calling
        self.function_schemas = {
            'read_file': {
                'name': 'read_file',
                'description': '读取项目中的文件内容',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'file_path': {
                            'type': 'string',
                            'description': '相对于项目根目录的文件路径，如: src/main/java/com/example/Controller.java'
                        }
                    },
                    'required': ['file_path']
                }
            },
            'write_file': {
                'name': 'write_file',
                'description': '写入文件内容（会自动备份原文件）',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'file_path': {
                            'type': 'string',
                            'description': '相对于项目根目录的文件路径'
                        },
                        'content': {
                            'type': 'string',
                            'description': '要写入的文件内容'
                        },
                        'mode': {
                            'type': 'string',
                            'enum': ['overwrite', 'append'],
                            'description': '写入模式：overwrite（覆盖）或append（追加）',
                            'default': 'overwrite'
                        }
                    },
                    'required': ['file_path', 'content']
                }
            },
            'replace_text': {
                'name': 'replace_text',
                'description': '在文件中替换指定的文本内容（适用于局部修改，避免重写整个大文件）。常用于在类中添加新方法：将类的最后一个 } 替换为 [新方法代码]\n}',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'file_path': {
                            'type': 'string',
                            'description': '相对于项目根目录的文件路径'
                        },
                        'old_text': {
                            'type': 'string',
                            'description': '要被替换的原始文本（必须精确匹配）。添加方法时通常是类的最后一个右花括号 }'
                        },
                        'new_text': {
                            'type': 'string',
                            'description': '新的文本内容。添加方法时格式为：[新方法的完整代码]\n}'
                        },
                        'occurrence': {
                            'type': 'string',
                            'enum': ['first', 'last', 'all'],
                            'description': '替换策略：first（第一个匹配）、last（最后一个匹配，推荐用于添加方法）、all（所有匹配）',
                            'default': 'last'
                        }
                    },
                    'required': ['file_path', 'old_text', 'new_text']
                }
            },
            'list_files': {
                'name': 'list_files',
                'description': '列出目录中的文件',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'directory_path': {
                            'type': 'string',
                            'description': '相对于项目根目录的目录路径，如: src/main/java',
                            'default': '.'
                        },
                        'pattern': {
                            'type': 'string',
                            'description': '文件名模式，支持通配符，如: *.java',
                            'default': '*'
                        }
                    }
                }
            },
            'file_exists': {
                'name': 'file_exists',
                'description': '检查文件是否存在',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'file_path': {
                            'type': 'string',
                            'description': '相对于项目根目录的文件路径'
                        }
                    },
                    'required': ['file_path']
                }
            },
            'create_directory': {
                'name': 'create_directory',
                'description': '创建目录',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'directory_path': {
                            'type': 'string',
                            'description': '相对于项目根目录的目录路径'
                        }
                    },
                    'required': ['directory_path']
                }
            },
            'backup_file': {
                'name': 'backup_file',
                'description': '备份文件',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'file_path': {
                            'type': 'string',
                            'description': '相对于项目根目录的文件路径'
                        }
                    },
                    'required': ['file_path']
                }
            }
        }
    
    def _init_backup_dir(self):
        """初始化备份目录"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = self.project_path / "backup" / f"strategy1_backup_{timestamp}"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 初始化备份目录: {self.backup_dir}")
    
    def get_function_schemas(self) -> List[Dict[str, Any]]:
        """获取function calling的函数定义"""
        return list(self.function_schemas.values())
    
    def call_function(self, function_name: str, **kwargs) -> Dict[str, Any]:
        """调用函数"""
        if function_name not in self.available_functions:
            return {
                'success': False,
                'error': f'未知函数: {function_name}',
                'available_functions': list(self.available_functions.keys())
            }
        
        try:
            func = self.available_functions[function_name]
            result = func(**kwargs)
            logger.info(f"✅ 函数调用成功: {function_name}")
            return {
                'success': True,
                'result': result,
                'function_name': function_name
            }
        except Exception as e:
            logger.error(f"❌ 函数调用失败: {function_name}, 错误: {e}")
            return {
                'success': False,
                'error': str(e),
                'function_name': function_name
            }
    
    def _read_file(self, file_path: str) -> str:
        """读取文件内容"""
        full_path = self.project_path / file_path
        
        # 安全检查：确保文件在项目目录内
        if not self._is_safe_path(full_path):
            raise ValueError(f"文件路径不安全: {file_path}")
        
        if not full_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        try:
            content = full_path.read_text(encoding='utf-8')
            logger.info(f"📖 读取文件: {file_path} ({len(content)} 字符)")
            return content
        except UnicodeDecodeError:
            # 尝试其他编码
            content = full_path.read_text(encoding='gbk')
            logger.info(f"📖 读取文件 (GBK): {file_path} ({len(content)} 字符)")
            return content
    
    def _write_file(self, file_path: str, content: str, mode: str = 'overwrite') -> str:
        """写入文件内容"""
        full_path = self.project_path / file_path
        
        # 安全检查：确保文件在项目目录内
        if not self._is_safe_path(full_path):
            raise ValueError(f"文件路径不安全: {file_path}")
        
        # 创建父目录
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 如果文件存在，先备份
        if full_path.exists():
            self._backup_file(file_path)
        
        # 写入文件
        if mode == 'append':
            with open(full_path, 'a', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"📝 追加写入文件: {file_path} (+{len(content)} 字符)")
        else:
            full_path.write_text(content, encoding='utf-8')
            logger.info(f"📝 覆盖写入文件: {file_path} ({len(content)} 字符)")
        
        return f"文件写入成功: {file_path}"
    
    def _replace_text(self, file_path: str, old_text: str, new_text: str, occurrence: str = 'last') -> str:
        """在文件中替换指定的文本内容"""
        full_path = self.project_path / file_path
        
        # 安全检查
        if not self._is_safe_path(full_path):
            raise ValueError(f"文件路径不安全: {file_path}")
        
        if not full_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 读取文件内容
        try:
            content = full_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = full_path.read_text(encoding='gbk')
        
        # 先备份文件
        self._backup_file(file_path)
        
        # 执行替换
        if old_text not in content:
            raise ValueError(f"未找到要替换的文本: {old_text[:100]}...")
        
        if occurrence == 'first':
            # 替换第一个匹配
            new_content = content.replace(old_text, new_text, 1)
            count = 1
        elif occurrence == 'last':
            # 替换最后一个匹配
            parts = content.rsplit(old_text, 1)
            if len(parts) < 2:  # 如果未找到匹配，rsplit返回整个字符串
                raise ValueError(f"未找到要替换的文本: {old_text[:100]}...")
            new_content = new_text.join(parts)
            count = 1
        else:  # occurrence == 'all'
            # 替换所有匹配
            count = content.count(old_text)
            new_content = content.replace(old_text, new_text)
        
        # 写入修改后的内容
        full_path.write_text(new_content, encoding='utf-8')
        
        logger.info(f"🔄 文本替换成功: {file_path} (替换了 {count} 处匹配)")
        logger.info(f"   原文本长度: {len(old_text)} 字符")
        logger.info(f"   新文本长度: {len(new_text)} 字符")
        
        return f"文本替换成功: {file_path}, 替换了 {count} 处匹配"
    
    def _list_files(self, directory_path: str = '.', pattern: str = '*') -> List[str]:
        """列出目录中的文件"""
        full_path = self.project_path / directory_path
        
        # 安全检查：确保目录在项目目录内
        if not self._is_safe_path(full_path):
            raise ValueError(f"目录路径不安全: {directory_path}")
        
        if not full_path.exists():
            raise FileNotFoundError(f"目录不存在: {directory_path}")
        
        files = []
        for file_path in full_path.glob(pattern):
            if file_path.is_file():
                relative_path = file_path.relative_to(self.project_path)
                files.append(str(relative_path))
        
        logger.info(f"📂 列出文件: {directory_path} ({len(files)} 个文件)")
        return files
    
    def _file_exists(self, file_path: str) -> bool:
        """检查文件是否存在"""
        full_path = self.project_path / file_path
        
        # 安全检查：确保文件在项目目录内
        if not self._is_safe_path(full_path):
            raise ValueError(f"文件路径不安全: {file_path}")
        
        exists = full_path.exists()
        logger.info(f"🔍 检查文件存在: {file_path} = {exists}")
        return exists
    
    def _create_directory(self, directory_path: str) -> str:
        """创建目录"""
        full_path = self.project_path / directory_path
        
        # 安全检查：确保目录在项目目录内
        if not self._is_safe_path(full_path):
            raise ValueError(f"目录路径不安全: {directory_path}")
        
        full_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 创建目录: {directory_path}")
        return f"目录创建成功: {directory_path}"
    
    def _backup_file(self, file_path: str) -> str:
        """备份文件"""
        full_path = self.project_path / file_path
        
        # 安全检查：确保文件在项目目录内
        if not self._is_safe_path(full_path):
            raise ValueError(f"文件路径不安全: {file_path}")
        
        if not full_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 创建备份文件路径
        backup_file = self.backup_dir / file_path
        backup_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 复制文件
        import shutil
        shutil.copy2(full_path, backup_file)
        
        logger.info(f"📋 备份文件: {file_path} -> {backup_file}")
        return f"文件备份成功: {file_path}"
    
    def _is_safe_path(self, path: Path) -> bool:
        """检查路径是否安全（在项目目录内）"""
        try:
            # 解析路径并检查是否在项目目录内
            resolved_path = path.resolve()
            project_resolved = self.project_path.resolve()
            
            # 检查是否为项目目录的子路径
            return str(resolved_path).startswith(str(project_resolved))
        except Exception:
            return False
    
    def get_operation_summary(self) -> Dict[str, Any]:
        """获取操作摘要"""
        return {
            'project_path': str(self.project_path),
            'backup_dir': str(self.backup_dir),
            'available_functions': list(self.available_functions.keys()),
            'function_schemas_count': len(self.function_schemas)
        }