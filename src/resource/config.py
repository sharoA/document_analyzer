#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
用于管理应用程序的配置信息
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class Config:
    """配置管理类"""
    
    def __init__(self, config_file: str = None):
        """
        初始化配置
        
        Args:
            config_file: 配置文件路径，如果为None则自动查找项目根目录的config.yaml
        """
        # 首先加载环境变量
        load_dotenv()
        
        # 如果没有指定配置文件，自动查找项目根目录的config.yaml
        if config_file is None:
            # 获取项目根目录（从src/resource往上两级）
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            config_file = os.path.join(project_root, "config.yaml")
        
        self.config_file = config_file
        self.config_data = {}
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    if self.config_file.endswith('.yaml') or self.config_file.endswith('.yml'):
                        self.config_data = yaml.safe_load(f) or {}
                    else:
                        self.config_data = json.load(f)
                logger.info(f"配置文件加载成功: {self.config_file}")
            else:
                logger.warning(f"配置文件不存在: {self.config_file}")
                self._create_default_config()
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            self._create_default_config()
    
    def _create_default_config(self):
        """创建默认配置"""
        # 从环境变量读取配置
        load_dotenv()
        
        self.config_data = {
            "app": {
                "name": "AnalyDesign",
                "version": "1.0.0",
                "debug": False,
                "host": "0.0.0.0",
                "port": 8000
            },
            "directories": {
                "logs": "logs",
                "uploads": "uploads",
                "temp": "uploads/temp",
                "analysis_results": "uploads/analysis_results",
                "cache": "uploads/cache"
            },
            "file_upload": {
                "max_size": 21 * 1024 * 1024,  # 21MB
                "allowed_extensions": [".txt", ".md", ".pdf", ".docx", ".doc", ".pptx", ".ppt"],
                "temp_dir": "uploads/temp"
            },
            "analysis": {
                "max_content_length": 100000,
                "chunk_size": 1000,
                "overlap_size": 200,
                "enable_ai_analysis": True,
                "enable_content_analysis": True
            },

            "volcengine": {
                "api_key": "7fcb3541-9363-4bfa-90aa-19e9f691bc25",
                "endpoint": "https://ark.cn-beijing.volces.com/api/v3",
                "model": "ep-20250605091804-wmw6w",
                #"model": "ep-20250605091804-wmw6w",
                "temperature": 0.7,
                "max_tokens": 4000
            },
            "openai": {
                "api_key": os.getenv("OPENAI_API_KEY", ""),
                "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                "model": "gpt-3.5-turbo",
                "temperature": 0.7,
                "max_tokens": 4000
            },
            "vector_database": {
                "type": "faiss",
                "dimension": 768,
                "faiss": {
                    "index_file": "uploads/cache/vector_index.faiss",
                    "metadata_file": "uploads/cache/vector_metadata.json"
                },
                "weaviate": {
                    "host": "localhost",
                    "port": 8080,
                    "grpc_port": 50051,
                    "scheme": "http",
                    "api_key": "root-user-key",
                    "timeout": 30,
                    "default_collection": {
                        "name": "AnalyDesignDocuments",
                        "vectorizer": "none",
                        "vector_dimension": 768
                    }
                }
            },
            "redis": {
                "host": "localhost",
                "port": 6379,
                "db": 0,
                "password": "",
                "decode_responses": True,
                "socket_timeout": 30,
                "socket_connect_timeout": 30,
                "socket_keepalive": True,
                "socket_keepalive_options": {},
                "connection_pool": {
                    "max_connections": 50
                },
                "cache": {
                    "default_ttl": 3600,
                    "key_prefix": "analydesign:"
                }
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "logs/app.log",
                "max_size": 10 * 1024 * 1024,  # 10MB
                "backup_count": 5
            },
            "validation": {
                "max_content_length": 10 * 1024 * 1024,  # 10MB
                "min_content_length": 1,
                "allowed_file_types": [
                    'text/plain', 'application/pdf', 'application/msword',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'text/markdown', 'application/json', 'text/html', 'application/xml'
                ],
                "max_file_size": 50 * 1024 * 1024  # 50MB
            }
        }
        self.save_config()
    
    def save_config(self):
        """保存配置到文件"""
        try:
            # 获取配置文件的目录
            config_dir = os.path.dirname(self.config_file)
            # 只有当目录不为空时才创建目录
            if config_dir:
                os.makedirs(config_dir, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                if self.config_file.endswith('.yaml') or self.config_file.endswith('.yml'):
                    yaml.dump(self.config_data, f, default_flow_style=False, allow_unicode=True)
                else:
                    json.dump(self.config_data, f, indent=2, ensure_ascii=False)
            logger.info(f"配置文件保存成功: {self.config_file}")
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config_data
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """
        设置配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            value: 配置值
        """
        keys = key.split('.')
        config = self.config_data
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def update(self, updates: Dict[str, Any]):
        """
        批量更新配置
        
        Args:
            updates: 更新的配置字典
        """
        for key, value in updates.items():
            self.set(key, value)
    
    def get_app_config(self) -> Dict[str, Any]:
        """获取应用配置"""
        return self.get('app', {})
    
    def get_directories_config(self) -> Dict[str, str]:
        """获取目录配置"""
        return self.get('directories', {})
    
    def get_file_upload_config(self) -> Dict[str, Any]:
        """获取文件上传配置"""
        return self.get('file_upload', {})
    
    def get_analysis_config(self) -> Dict[str, Any]:
        """获取分析配置"""
        return self.get('analysis', {})
    
    def get_llm_config(self) -> Dict[str, Any]:
        """获取LLM配置 - 现在返回火山引擎配置"""
        return self.get_volcengine_config()
    
    def get_volcengine_config(self) -> Dict[str, Any]:
        """获取火山引擎配置"""
        return self.get('volcengine', {})
    
    def get_openai_config(self) -> Dict[str, Any]:
        """获取OpenAI配置"""
        return self.get('openai', {})
    
    def get_vector_database_config(self) -> Dict[str, Any]:
        """获取向量数据库配置"""
        return self.get('vector_database', {})
    
    def get_weaviate_config(self) -> Dict[str, Any]:
        """获取Weaviate配置"""
        return self.get('vector_database.weaviate', {
            'host': 'localhost',
            'port': 8080,
            'grpc_port': 50051,
            'scheme': 'http',
            'api_key': 'root-user-key',
            'timeout': 30,
            'default_collection': {
                'name': 'AnalyDesignDocuments',
                'vectorizer': 'none',
                'vector_dimension': 768
            }
        })
    
    def get_redis_config(self) -> Dict[str, Any]:
        """获取Redis配置"""
        return self.get('redis', {
            'host': 'localhost',
            'port': 6379,
            'db': 0,
            'password': '',
            'decode_responses': True,
            'socket_timeout': 30,
            'socket_connect_timeout': 30,
            'socket_keepalive': True,
            'socket_keepalive_options': {},
            'connection_pool': {
                'max_connections': 50
            },
            'cache': {
                'default_ttl': 3600,
                'key_prefix': 'analydesign:'
            }
        })
    
    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return self.get('logging', {})
    
    def get_validation_config(self) -> Dict[str, Any]:
        """获取验证配置"""
        return self.get('validation', {
            'max_content_length': 10 * 1024 * 1024,  # 10MB
            'min_content_length': 1,
            'allowed_file_types': [
                'text/plain', 'application/pdf', 'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'text/markdown', 'application/json', 'text/html', 'application/xml'
            ],
            'max_file_size': 50 * 1024 * 1024  # 50MB
        })

# 全局配置实例
_config = None

def get_config() -> Config:
    """获取全局配置实例"""
    global _config
    if _config is None:
        _config = Config()
    return _config

def get_logs_dir() -> str:
    """获取日志目录"""
    config = get_config()
    logs_dir = config.get('directories.logs', 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    return logs_dir

def get_uploads_dir() -> str:
    """获取上传目录"""
    # 确保使用项目根目录的uploads
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    uploads_dir = os.path.join(project_root, 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    return uploads_dir

def get_temp_dir() -> str:
    """获取临时目录"""
    # 确保使用项目根目录的uploads/temp
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    temp_dir = os.path.join(project_root, 'uploads', 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir

def get_analysis_results_dir() -> str:
    """获取分析结果目录"""
    # 确保使用项目根目录的uploads/analysis_results
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    results_dir = os.path.join(project_root, 'uploads', 'analysis_results')
    os.makedirs(results_dir, exist_ok=True)
    return results_dir

def get_cache_dir() -> str:
    """获取缓存目录"""
    # 确保使用项目根目录的uploads/cache
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    cache_dir = os.path.join(project_root, 'uploads', 'cache')
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir 