#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略1实现管理器
统一管理策略1的完整实现流程：分析项目结构 -> LLM决策 -> 大模型自主生成代码并写入文件
"""

import logging
from typing import Dict, List, Any, Optional

from .project_structure_analyzer import ProjectStructureAnalyzer
from .llm_decision_maker import LLMDecisionMaker
from .function_calling_code_generator import FunctionCallingCodeGenerator

logger = logging.getLogger(__name__)


class Strategy1Manager:
    """策略1管理器 - 统一管理整个策略1的实现流程"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        
        # 初始化各个模块
        self.structure_analyzer = ProjectStructureAnalyzer()
        self.decision_maker = LLMDecisionMaker(llm_client)
        self.code_generator = None  # 将在execute_strategy1中初始化
        
    def execute_strategy1(self, project_path: str, api_keyword: str, 
                         api_path: str, business_logic: str, 
                         task_parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行策略1的完整流程
        
        Args:
            project_path: 项目路径
            api_keyword: API关键字
            api_path: API路径
            business_logic: 业务逻辑描述
            task_parameters: 完整的任务参数（包含request_params、response_params等）
            
        Returns:
            执行结果
        """
        logger.info(f"🚀 开始执行策略1: {api_keyword}")
        
        # 🔧 修复项目路径：确保使用项目根目录而不是深度Java路径
        actual_project_path = self._normalize_to_project_root(project_path)
        logger.info(f"📁 原始路径: {project_path}")
        logger.info(f"📁 项目根路径: {actual_project_path}")
        
        result = {
            'success': False,
            'stage': 'unknown',
            'project_structure': None,
            'decision': None,
            'generation_results': [],
            'files_modified': [],
            'error': None,
            'original_path': project_path,
            'actual_project_path': actual_project_path
        }
        
        try:
            # 第1步：分析项目结构
            logger.info("📊 第1步：分析项目结构")
            result['stage'] = 'analyzing_structure'
            project_structure = self.structure_analyzer.analyze_project_structure(actual_project_path)
            result['project_structure'] = project_structure
            
            if not project_structure:
                raise Exception("项目结构分析失败")
            
            # 第2步：LLM决策
            logger.info("🤖 第2步：LLM决策实现方案")
            result['stage'] = 'making_decision'
            decision = self.decision_maker.decide_implementation_classes(
                project_structure, api_keyword, business_logic, task_parameters
            )
            result['decision'] = decision

            # 打印决策日志
            logger.info("📋 决策结果:")
            for layer, layer_decision in decision.items():
                logger.info(f"  {layer}:")
                logger.info(f"    - 操作: {layer_decision.get('action', 'unknown')}")
                logger.info(f"    - 目标类: {layer_decision.get('target_class', 'unknown')}")
                logger.info(f"    - 包路径: {layer_decision.get('package_path', 'unknown')}")
                logger.info(f"    - 原因: {layer_decision.get('reason', 'unknown')}")
            
            # 第3步：初始化代码生成器（基于项目路径）
            logger.info("🔧 第3步：初始化代码生成器")
            result['stage'] = 'initializing_generator'
            self.code_generator = FunctionCallingCodeGenerator(self.llm_client, actual_project_path)
            
            # 第4步：大模型自主生成代码并写入文件
            logger.info("💻 第4步：大模型自主生成代码并写入文件")
            result['stage'] = 'generating_and_writing_code'
            
            # 准备代码生成的上下文信息
            generation_context = {
                'api_keyword': api_keyword,
                'api_path': api_path,
                'business_logic': business_logic,
                'base_package': project_structure.get('base_package', 'com.yljr.crcl'),
                'project_structure': project_structure,
                'decision': decision,
                'task_parameters': task_parameters or {}  # 🔧 添加完整的任务参数
            }
            
            # 生成各层代码
            layers_to_generate = self._determine_layers_to_generate(decision)
            
            for layer in layers_to_generate:
                layer_decision = decision.get(layer, {})
                if layer_decision.get('action') in ['enhance_existing', 'create_new']:
                    logger.info(f"🔨 生成{layer}层代码")
                    
                    generation_result = self.code_generator.generate_code_with_file_operations(
                        layer, layer_decision, generation_context
                    )
                    
                    result['generation_results'].append(generation_result)
                    
                    # 收集修改的文件
                    if generation_result.get('files_modified'):
                        result['files_modified'].extend(generation_result['files_modified'])
                    
                    if not generation_result.get('success'):
                        logger.warning(f"⚠️ {layer}层代码生成失败: {generation_result.get('error')}")
            
            # 检查整体成功状态
            successful_generations = [r for r in result['generation_results'] if r.get('success')]
            result['success'] = len(successful_generations) > 0
            
            logger.info(f"✅ 策略1执行完成，成功生成{len(successful_generations)}层代码")
            
        except Exception as e:
            logger.error(f"❌ 策略1执行失败: {e}")
            result['error'] = str(e)
            result['success'] = False
        
        return result
    
    def _normalize_to_project_root(self, path: str) -> str:
        """
        将深度Java路径规范化为项目根目录
        
        Args:
            path: 可能的深度Java路径
            
        Returns:
            项目根目录路径
        """
        import os
        from pathlib import Path
        
        path = Path(path)
        
        # 如果路径包含src/main/java，则提取到src/main/java之前的部分作为项目根
        path_parts = path.parts
        
        # 寻找src/main/java的位置
        src_main_java_found = False
        for i, part in enumerate(path_parts):
            if (i + 2 < len(path_parts) and 
                part == 'src' and 
                path_parts[i + 1] == 'main' and 
                path_parts[i + 2] == 'java'):
                # 找到src/main/java，取到src之前的路径作为项目根
                project_root_parts = path_parts[:i]
                if project_root_parts:
                    project_root = Path(*project_root_parts)
                    logger.info(f"🔧 从路径 {path} 提取项目根目录: {project_root}")
                    return str(project_root)
                src_main_java_found = True
                break
        
        # 如果没有找到src/main/java模式，检查是否已经是项目根
        # 通过检查是否包含pom.xml或build.gradle来判断
        if (path / "pom.xml").exists() or (path / "build.gradle").exists():
            logger.info(f"🔧 路径 {path} 已经是项目根目录")
            return str(path)
        
        # 如果都没有找到，向上搜索直到找到项目根
        current = path
        while current.parent != current:  # 避免到达根目录
            if ((current / "pom.xml").exists() or 
                (current / "build.gradle").exists() or
                (current / "src" / "main" / "java").exists()):
                logger.info(f"🔧 向上搜索找到项目根目录: {current}")
                return str(current)
            current = current.parent
        
        # 如果仍然没有找到，返回原路径
        logger.warning(f"⚠️ 无法确定项目根目录，使用原路径: {path}")
        return str(path)
    
    def _determine_layers_to_generate(self, decision: Dict[str, Any]) -> List[str]:
        """根据决策确定需要生成的层级"""
        
        layers = []
        
        # 按照DDD架构的依赖顺序生成
        layer_order = [
            'dto',           # 首先生成DTO，其他层会依赖
            'entity',        # 然后生成实体
            'mapper',        # 数据访问层
            'domain_service', # 领域服务层
            'feign_client',  # 外部服务调用
            'application_service', # 应用服务层
            'controller'     # 最后生成控制器
        ]
        
        for layer in layer_order:
            layer_decision = decision.get(layer, {})
            if layer_decision.get('action') in ['enhance_existing', 'create_new']:
                layers.append(layer)
        
        return layers
    
    def get_execution_summary(self, result: Dict[str, Any]) -> str:
        """获取执行摘要"""
        
        summary = f"策略1执行摘要:\n"
        summary += f"成功: {result['success']}\n"
        summary += f"阶段: {result['stage']}\n"
        
        if result.get('error'):
            summary += f"错误: {result['error']}\n"
        
        # 项目结构摘要
        if result.get('project_structure'):
            structure = result['project_structure']
            summary += f"\n项目结构:\n"
            summary += f"- 基础包名: {structure.get('base_package', 'N/A')}\n"
            summary += f"- Controllers: {len(structure.get('controllers', {}))}\n"
            summary += f"- Services: {len(structure.get('services', {}))}\n"
            summary += f"- Mappers: {len(structure.get('mappers', {}))}\n"
            summary += f"- Entities: {len(structure.get('entities', {}))}\n"
        
        # 决策摘要
        if result.get('decision'):
            decision = result['decision']
            summary += f"\n实现决策:\n"
            for component, decision_info in decision.items():
                action = decision_info.get('action', 'unknown')
                target_class = decision_info.get('target_class', 'N/A')
                summary += f"- {component}: {action}"
                if target_class:
                    summary += f" ({target_class})"
                summary += "\n"
        
        # 代码生成摘要
        if result.get('generation_results'):
            summary += f"\n代码生成结果:\n"
            for gen_result in result['generation_results']:
                layer = gen_result.get('layer', 'unknown')
                success = gen_result.get('success', False)
                summary += f"- {layer}: {'成功' if success else '失败'}\n"
        
        # 文件修改摘要
        if result.get('files_modified'):
            summary += f"\n修改的文件 ({len(result['files_modified'])} 个):\n"
            for file_path in result['files_modified']:
                summary += f"- {file_path}\n"
        
        return summary