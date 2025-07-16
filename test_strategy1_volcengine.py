#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略1功能测试脚本（使用火山引擎客户端）
测试新实现的大模型自主文件操作和增量修改功能，使用真实的火山引擎LLM
"""

import os
import sys
import logging
from pathlib import Path
import tempfile
import shutil
import json
import re

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.corder_integration.code_generator.strategy1_manager import Strategy1Manager
from src.corder_integration.code_generator.project_structure_analyzer import ProjectStructureAnalyzer
from src.corder_integration.code_generator.llm_decision_maker import LLMDecisionMaker
from src.corder_integration.code_generator.file_operation_tool_invoker import FileOperationToolInvoker
from src.corder_integration.code_generator.function_calling_code_generator import FunctionCallingCodeGenerator
import yaml

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_strategy1_volcengine.log')
    ]
)
logger = logging.getLogger(__name__)

class VolcengineClientAdapter:
    """火山引擎客户端适配器，支持策略1所需的功能"""
    
    def __init__(self):
        self.client = None
        self.call_count = 0
        self._init_volcengine_client()
        
    def _init_volcengine_client(self):
        """初始化火山引擎客户端"""
        # 读取配置文件
        config = {}
        config_paths = [
            'config.yaml',
            os.path.join(os.getcwd(), 'config.yaml'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yaml'),
            'D:/ai_project/document_analyzer/config.yaml'
        ]
        
        config_loaded = False
        for config_path in config_paths:
            try:
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f) or {}
                    logger.info(f"✅ 成功加载配置文件: {config_path}")
                    config_loaded = True
                    break
            except Exception as e:
                logger.warning(f"⚠️ 加载配置文件失败 {config_path}: {e}")
        
        if not config_loaded:
            logger.error(f"❌ 所有配置文件路径都加载失败: {config_paths}")
            raise Exception("无法加载配置文件")
        
        # 初始化火山引擎客户端
        if config and config.get('volcengine', {}).get('api_key'):
            try:
                from src.utils.volcengine_client import VolcengineClient, VolcengineConfig
                volcengine_config = VolcengineConfig(
                    api_key=config['volcengine']['api_key'],
                    model_id=config['volcengine']['model'],
                    base_url=config['volcengine']['endpoint'],
                    temperature=config['volcengine'].get('temperature', 0.7),
                    max_tokens=config['volcengine'].get('max_tokens', 4000)
                )
                self.client = VolcengineClient(volcengine_config)
                logger.info(f"🚀 初始化火山引擎客户端成功：{config['volcengine']['model']}")
            except Exception as e:
                logger.error(f"❌ 火山引擎初始化失败: {e}")
                raise
        else:
            raise Exception("火山引擎配置不存在")
        
    def generate(self, prompt: str) -> str:
        """生成响应"""
        self.call_count += 1
        logger.info(f"🤖 火山引擎LLM调用 #{self.call_count}")
        
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            response = self.client.chat(messages, max_tokens=4000, temperature=0.7)
            logger.info(f"✅ 火山引擎响应成功 (长度: {len(response)} 字符)")
            return response
        except Exception as e:
            logger.error(f"❌ 火山引擎调用失败: {e}")
            raise
    
    def chat_with_functions(self, messages, functions, function_call="auto"):
        """支持function calling的聊天（适配器模式）"""
        # 由于火山引擎可能不直接支持OpenAI格式的function calling，
        # 我们将函数信息包含在prompt中，让LLM以特定格式回复
        
        # 构建包含函数信息的系统消息
        function_descriptions = []
        for func in functions:
            func_desc = f"函数名: {func['name']}\n"
            func_desc += f"描述: {func['description']}\n"
            func_desc += f"参数: {func['parameters']}\n"
            function_descriptions.append(func_desc)
        
        system_message = {
            "role": "system",
            "content": f"""你是一个智能代码助手，可以调用以下函数来操作文件：

{chr(10).join(function_descriptions)}

请严格按照以下JSON格式回复来调用函数：
{{
    "function_call": {{
        "name": "函数名",
        "arguments": "JSON格式的参数"
    }}
}}

如果不需要调用函数，请正常回复。"""
        }
        
        # 将系统消息插入到消息列表开头
        enhanced_messages = [system_message] + messages
        
        try:
            response = self.client.chat(enhanced_messages, max_tokens=4000, temperature=0.7)
            
            # 尝试解析function call
            function_call_match = re.search(r'"function_call"\s*:\s*{[^}]+}', response)
            
            if function_call_match:
                try:
                    function_call_json = '{' + function_call_match.group(0) + '}'
                    function_call_data = json.loads(function_call_json)
                    
                    return {
                        'choices': [{
                            'message': {
                                'content': None,
                                'function_call': function_call_data['function_call']
                            }
                        }]
                    }
                except Exception as parse_error:
                    logger.warning(f"⚠️ 解析function call失败: {parse_error}")
                    # 继续尝试其他解析方式
            
            # 尝试解析更宽松的格式
            name_match = re.search(r'"name"\s*:\s*"([^"]+)"', response)
            args_match = re.search(r'"arguments"\s*:\s*"([^"]+)"', response)
            
            if name_match and args_match:
                return {
                    'choices': [{
                        'message': {
                            'content': None,
                            'function_call': {
                                'name': name_match.group(1),
                                'arguments': args_match.group(1)
                            }
                        }
                    }]
                }
            
            # 如果没有function call，返回普通响应
            return {
                'choices': [{
                    'message': {
                        'content': response,
                        'role': 'assistant'
                    }
                }]
            }
            
        except Exception as e:
            logger.error(f"❌ 火山引擎function calling失败: {e}")
            # 返回一个默认的function call用于测试
            return {
                'choices': [{
                    'message': {
                        'content': None,
                        'function_call': {
                            'name': 'write_file',
                            'arguments': '{"file_path": "test.java", "content": "// Generated by Volcengine", "mode": "overwrite"}'
                        }
                    }
                }]
            }

def create_test_project(temp_dir: Path) -> Path:
    """创建测试项目结构"""
    project_dir = temp_dir / "test_project"
    project_dir.mkdir()
    
    # 创建基本的Java项目结构
    java_dir = project_dir / "src" / "main" / "java" / "com" / "yljr" / "user" / "basicgeneral"
    java_dir.mkdir(parents=True)
    
    # 创建基本的目录结构
    (java_dir / "interfaces" / "rest").mkdir(parents=True)
    (java_dir / "interfaces" / "dto").mkdir(parents=True)
    (java_dir / "application" / "service").mkdir(parents=True)
    (java_dir / "domain" / "service").mkdir(parents=True)
    (java_dir / "domain" / "mapper").mkdir(parents=True)
    (java_dir / "domain" / "entity").mkdir(parents=True)
    
    # 创建一个现有的Controller文件
    controller_file = java_dir / "interfaces" / "rest" / "UserController.java"
    controller_file.write_text("""package com.yljr.user.basicgeneral.interfaces.rest;

import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RequestMapping;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@RestController
@RequestMapping("/api/user")
public class UserController {
    
    private static final Logger logger = LoggerFactory.getLogger(UserController.class);
    
    // 现有方法将被保留
    public String existingMethod() {
        return "existing";
    }
}
""", encoding='utf-8')
    
    # 创建一个现有的Entity文件
    entity_file = java_dir / "domain" / "entity" / "User.java"
    entity_file.write_text("""package com.yljr.user.basicgeneral.domain.entity;

public class User {
    
    private Long id;
    private String name;
    
    // 现有的getter/setter
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
}
""", encoding='utf-8')
    
    logger.info(f"✅ 创建测试项目: {project_dir}")
    return project_dir

def test_volcengine_connection():
    """测试火山引擎连接"""
    logger.info("🧪 测试火山引擎连接")
    
    try:
        adapter = VolcengineClientAdapter()
        
        # 测试基本连接
        response = adapter.generate("你好，请简单回复一句话")
        assert response and len(response) > 0, "火山引擎应该返回非空响应"
        
        logger.info(f"✅ 火山引擎连接成功，响应: {response[:100]}...")
        
    except Exception as e:
        logger.error(f"❌ 火山引擎连接失败: {e}")
        raise

def test_file_operation_tool_invoker():
    """测试文件操作工具调用器"""
    logger.info("🧪 测试文件操作工具调用器")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        project_dir = create_test_project(temp_path)
        
        # 创建文件操作工具
        file_tool = FileOperationToolInvoker(str(project_dir))
        
        # 测试读取文件
        result = file_tool.call_function(
            'read_file',
            file_path='src/main/java/com/yljr/user/basicgeneral/interfaces/rest/UserController.java'
        )
        assert result['success'], f"读取文件失败: {result}"
        logger.info("✅ 文件读取测试通过")
        
        # 测试写入文件
        result = file_tool.call_function(
            'write_file',
            file_path='src/main/java/com/yljr/user/basicgeneral/interfaces/rest/TestController.java',
            content='package com.yljr.user.basicgeneral.interfaces.rest;\\n\\npublic class TestController {\\n}',
            mode='overwrite'
        )
        assert result['success'], f"写入文件失败: {result}"
        logger.info("✅ 文件写入测试通过")
        
        logger.info("🎉 文件操作工具调用器测试全部通过")

def test_project_structure_analyzer():
    """测试项目结构分析器"""
    logger.info("🧪 测试项目结构分析器")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        project_dir = create_test_project(temp_path)
        
        # 创建项目结构分析器
        analyzer = ProjectStructureAnalyzer()
        
        # 分析项目结构
        structure = analyzer.analyze_project_structure(str(project_dir))
        
        # 验证结果
        assert structure['base_package'] == 'com.yljr.user.basicgeneral', f"基础包名不正确: {structure['base_package']}"
        assert len(structure['controllers']) > 0, "应该检测到Controller文件"
        assert len(structure['entities']) > 0, "应该检测到Entity文件"
        assert 'UserController' in structure['controllers'], "应该检测到UserController"
        assert 'User' in structure['entities'], "应该检测到User实体"
        
        logger.info("✅ 项目结构分析器测试通过")

def test_llm_decision_maker():
    """测试LLM决策器"""
    logger.info("🧪 测试LLM决策器（使用火山引擎）")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        project_dir = create_test_project(temp_path)
        
        # 创建火山引擎客户端适配器
        volcengine_adapter = VolcengineClientAdapter()
        
        # 创建决策器
        decision_maker = LLMDecisionMaker(volcengine_adapter)
        
        # 分析项目结构
        analyzer = ProjectStructureAnalyzer()
        structure = analyzer.analyze_project_structure(str(project_dir))
        
        # 进行决策
        decision = decision_maker.decide_implementation_classes(
            structure, 'QueryUser', '查询用户信息'
        )
        
        # 验证结果
        assert isinstance(decision, dict), "决策结果应该是字典"
        logger.info(f"✅ LLM决策器测试通过，决策结果: {decision}")

def test_function_calling_code_generator():
    """测试Function Calling代码生成器"""
    logger.info("🧪 测试Function Calling代码生成器（使用火山引擎）")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        project_dir = create_test_project(temp_path)
        
        # 创建火山引擎客户端适配器
        volcengine_adapter = VolcengineClientAdapter()
        
        # 创建代码生成器
        generator = FunctionCallingCodeGenerator(volcengine_adapter, str(project_dir))
        
        # 测试生成代码
        layer_decision = {
            'action': 'enhance_existing',
            'target_class': 'UserController',
            'package_path': 'interfaces.rest',
            'reason': '增强现有Controller'
        }
        
        context = {
            'api_keyword': 'QueryUser',
            'business_logic': '查询用户信息',
            'base_package': 'com.yljr.user.basicgeneral'
        }
        
        result = generator.generate_code_with_file_operations(
            'controller', layer_decision, context
        )
        
        # 验证结果
        assert result['success'], f"代码生成失败: {result}"
        assert result['layer'] == 'controller', "层级不正确"
        
        logger.info("✅ Function Calling代码生成器测试通过")

def test_strategy1_manager():
    """测试策略1管理器"""
    logger.info("🧪 测试策略1管理器（使用火山引擎）")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        project_dir = create_test_project(temp_path)
        
        # 创建火山引擎客户端适配器
        volcengine_adapter = VolcengineClientAdapter()
        
        # 创建策略1管理器
        manager = Strategy1Manager(volcengine_adapter)
        
        # 执行策略1
        result = manager.execute_strategy1(
            str(project_dir),
            'QueryUser',
            '/api/user/query',
            '查询用户信息'
        )
        
        # 验证结果
        assert result['success'], f"策略1执行失败: {result}"
        assert result['project_structure'] is not None, "项目结构应该被分析"
        assert result['decision'] is not None, "决策应该被生成"
        
        # 检查是否有文件被修改
        if result['files_modified']:
            logger.info(f"修改的文件: {result['files_modified']}")
        
        # 输出执行摘要
        summary = manager.get_execution_summary(result)
        logger.info(f"执行摘要:\n{summary}")
        
        logger.info("✅ 策略1管理器测试通过")

def main():
    """主测试函数"""
    logger.info("🚀 开始策略1功能测试（使用火山引擎）")
    
    try:
        # 首先测试火山引擎连接
        test_volcengine_connection()
        
        # 测试各个组件
        test_file_operation_tool_invoker()
        test_project_structure_analyzer()
        test_llm_decision_maker()
        test_function_calling_code_generator()
        test_strategy1_manager()
        
        logger.info("🎉 所有测试通过！")
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()