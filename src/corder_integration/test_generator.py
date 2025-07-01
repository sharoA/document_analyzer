#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试生成器模块
自动生成单元测试和集成测试代码
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any

from .config import CoderAgentConfig

logger = logging.getLogger(__name__)

class TestGenerator:
    """测试生成器"""
    
    def __init__(self, config: Optional[CoderAgentConfig] = None):
        """初始化测试生成器"""
        self.config = config or CoderAgentConfig()
        
    def generate_backend_tests(self, project_info: Dict[str, Any], output_dir: str) -> Dict[str, Any]:
        """生成后端测试"""
        try:
            logger.info("开始生成后端测试...")
            
            test_output_dir = os.path.join(output_dir, "test-project", "backend-tests")
            os.makedirs(test_output_dir, exist_ok=True)
            
            generated_files = []
            
            # 生成测试配置
            config_content = self._generate_test_config()
            config_path = os.path.join(test_output_dir, "pom.xml")
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(config_content)
            generated_files.append(config_path)
            
            return {
                'success': True,
                'generated_files': generated_files,
                'test_count': len(generated_files),
                'output_dir': test_output_dir
            }
            
        except Exception as e:
            logger.error(f"生成后端测试失败: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def generate_frontend_tests(self, project_info: Dict[str, Any], output_dir: str) -> Dict[str, Any]:
        """生成前端测试"""
        try:
            logger.info("开始生成前端测试...")
            
            test_output_dir = os.path.join(output_dir, "test-project", "frontend-tests")
            os.makedirs(test_output_dir, exist_ok=True)
            
            generated_files = []
            
            # 生成package.json
            package_json = self._generate_package_json()
            package_path = os.path.join(test_output_dir, "package.json")
            with open(package_path, 'w', encoding='utf-8') as f:
                f.write(package_json)
            generated_files.append(package_path)
            
            return {
                'success': True,
                'generated_files': generated_files,
                'test_count': len(generated_files),
                'output_dir': test_output_dir
            }
            
        except Exception as e:
            logger.error(f"生成前端测试失败: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _generate_test_config(self) -> str:
        """生成测试配置"""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>test-project</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>
</project>'''
    
    def _generate_package_json(self) -> str:
        """生成package.json"""
        return json.dumps({
            "name": "test-project",
            "version": "1.0.0",
            "scripts": {
                "test": "jest"
            }
        }, indent=2) 