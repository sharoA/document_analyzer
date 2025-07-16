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
                         api_path: str, business_logic: str) -> Dict[str, Any]:
        """
        执行策略1的完整流程
        
        Args:
            project_path: 项目路径
            api_keyword: API关键字
            api_path: API路径
            business_logic: 业务逻辑描述
            
        Returns:
            执行结果
        """
        logger.info(f"🚀 开始执行策略1: {api_keyword}")
        
        result = {
            'success': False,
            'stage': 'unknown',
            'project_structure': None,
            'decision': None,
            'generation_results': [],
            'files_modified': [],
            'error': None
        }
        
        try:
            # 第1步：分析项目结构
            logger.info("📊 第1步：分析项目结构")
            result['stage'] = 'analyzing_structure'
            project_structure = self.structure_analyzer.analyze_project_structure(project_path)
            result['project_structure'] = project_structure
            
            if not project_structure:
                raise Exception("项目结构分析失败")
            
            # 第2步：LLM决策
            logger.info("🤖 第2步：LLM决策实现方案")
            result['stage'] = 'making_decision'
            decision = self.decision_maker.decide_implementation_classes(
                project_structure, api_keyword, business_logic
            )
            result['decision'] = decision
            
            # 第3步：初始化代码生成器（基于项目路径）
            logger.info("🔧 第3步：初始化代码生成器")
            result['stage'] = 'initializing_generator'
            self.code_generator = FunctionCallingCodeGenerator(self.llm_client, project_path)
            
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
                'decision': decision
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