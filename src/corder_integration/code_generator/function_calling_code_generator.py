#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于Function Calling的大模型代码生成器
支持大模型自主进行文件操作和增量修改
"""

import logging
import json
from typing import Dict, List, Any, Optional
from pathlib import Path

from .file_operation_tool_invoker import FileOperationToolInvoker

logger = logging.getLogger(__name__)


class FunctionCallingCodeGenerator:
    """基于Function Calling的代码生成器"""
    
    def __init__(self, llm_client, project_path: str):
        self.llm_client = llm_client
        self.project_path = project_path
        self.file_tool = FileOperationToolInvoker(project_path)
        
        # 检查LLM是否支持function calling
        self.supports_function_calling = self._check_function_calling_support()
        
    def _check_function_calling_support(self) -> bool:
        """检查LLM是否支持function calling"""
        # 检查LLM客户端是否有function calling相关方法
        return hasattr(self.llm_client, 'chat_with_functions') or hasattr(self.llm_client, 'function_call')
    
    def generate_code_with_file_operations(self, layer: str, layer_decision: Dict[str, Any], 
                                         context: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用大模型生成代码，支持文件操作
        
        Args:
            layer: 层级名称（controller, service等）
            layer_decision: 层级决策信息
            context: 生成上下文
            
        Returns:
            生成结果
        """
        logger.info(f"🤖 开始生成{layer}代码（支持文件操作）")
        
        try:
            # 准备function calling
            if self.supports_function_calling:
                return self._generate_with_function_calling(layer, layer_decision, context)
            else:
                return self._generate_with_prompt_description(layer, layer_decision, context)
                
        except Exception as e:
            logger.error(f"❌ 生成{layer}代码失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'layer': layer
            }
    
    def _generate_with_function_calling(self, layer: str, layer_decision: Dict[str, Any], 
                                      context: Dict[str, Any]) -> Dict[str, Any]:
        """使用function calling生成代码"""
        
        # 构建提示词
        prompt = self._build_function_calling_prompt(layer, layer_decision, context)
        
        # 获取函数定义
        functions = self.file_tool.get_function_schemas()
        
        # 调用支持function calling的LLM
        conversation_result = self._run_function_calling_conversation(prompt, functions)
        
        return {
            'success': True,
            'layer': layer,
            'conversation_result': conversation_result,
            'files_modified': conversation_result.get('files_modified', []),
            'generated_code': conversation_result.get('final_code', '')
        }
    
    def _generate_with_prompt_description(self, layer: str, layer_decision: Dict[str, Any], 
                                        context: Dict[str, Any]) -> Dict[str, Any]:
        """使用提示词描述文件操作函数"""
        
        # 构建包含文件操作说明的提示词
        prompt = self._build_prompt_with_tool_description(layer, layer_decision, context)
        
        # 调用LLM生成代码和操作指令
        messages = [{"role": "user", "content": prompt}]
        response = self.llm_client.chat(messages)
        
        # 解析并执行文件操作
        operation_result = self._parse_and_execute_operations(response)
        
        return {
            'success': True,
            'layer': layer,
            'llm_response': response,
            'operation_result': operation_result,
            'files_modified': operation_result.get('files_modified', [])
        }
    
    def _build_function_calling_prompt(self, layer: str, layer_decision: Dict[str, Any], 
                                     context: Dict[str, Any]) -> str:
        """构建function calling提示词"""
        
        api_keyword = context.get('api_keyword', '')
        business_logic = context.get('business_logic', '')
        base_package = context.get('base_package', '')
        action = layer_decision.get('action', 'create_new')
        target_class = layer_decision.get('target_class', '')
        package_path = layer_decision.get('package_path', '')
        
        prompt = f"""你是一个Java Spring Boot项目的DDD架构师，需要根据决策结果生成{layer}层的代码。

## 任务信息
- 层级: {layer}
- 决策: {action}
- 目标类: {target_class}
- 包路径: {package_path}
- API关键字: {api_keyword}
- 业务逻辑: {business_logic}
- 基础包名: {base_package}

## DDD架构要求
严格遵循DDD架构的分层原则，确保代码质量和架构一致性。

## 文件操作指导
你可以使用以下文件操作函数：
- read_file: 读取现有文件内容
- write_file: 写入文件内容（支持覆盖和追加）
- list_files: 列出目录中的文件
- file_exists: 检查文件是否存在
- create_directory: 创建目录
- backup_file: 备份文件

## 工作流程
1. 首先检查相关文件是否存在
2. 如果是enhance_existing，读取现有文件内容
3. 生成新的代码（方法或完整类）
4. 将新代码与现有内容合并（如果是增强现有文件）
5. 写入最终的完整文件内容

## 注意事项
- 如果是增强现有文件，请确保保留原有的import、注解和方法
- 新增的方法应该按照合理的顺序插入
- 确保生成的代码符合Java语法和DDD架构规范
- 生成完整的文件内容，不要只生成片段

请开始执行任务，使用文件操作函数来读取、分析和生成代码。"""
        
        return prompt
    
    def _build_prompt_with_tool_description(self, layer: str, layer_decision: Dict[str, Any], 
                                          context: Dict[str, Any]) -> str:
        """构建包含工具描述的提示词"""
        
        api_keyword = context.get('api_keyword', '')
        business_logic = context.get('business_logic', '')
        base_package = context.get('base_package', '')
        action = layer_decision.get('action', 'create_new')
        target_class = layer_decision.get('target_class', '')
        
        prompt = f"""你是一个Java Spring Boot项目的DDD架构师，需要生成{layer}层的代码。

## 任务信息
- 层级: {layer}
- 决策: {action}
- 目标类: {target_class}
- API关键字: {api_keyword}
- 业务逻辑: {business_logic}
- 基础包名: {base_package}

## 可用的文件操作函数
请在你的响应中使用以下格式来调用文件操作：

```function_call
{{
    "function": "read_file",
    "parameters": {{
        "file_path": "src/main/java/com/example/Controller.java"
    }}
}}
```

可用函数：
- read_file(file_path): 读取文件内容
- write_file(file_path, content, mode="overwrite"): 写入文件
- list_files(directory_path=".", pattern="*"): 列出文件
- file_exists(file_path): 检查文件存在
- create_directory(directory_path): 创建目录

## 工作流程
1. 首先检查或读取相关文件
2. 生成所需的代码
3. 写入文件

请开始执行任务，使用function_call格式来操作文件。"""
        
        return prompt
    
    def _run_function_calling_conversation(self, prompt: str, functions: List[Dict]) -> Dict[str, Any]:
        """运行function calling对话"""
        
        conversation_history = []
        files_modified = []
        max_turns = 10  # 最大对话轮数
        
        # 初始消息
        messages = [{"role": "user", "content": prompt}]
        
        for turn in range(max_turns):
            try:
                # 调用LLM（支持function calling）
                if hasattr(self.llm_client, 'chat_with_functions'):
                    response = self.llm_client.chat_with_functions(
                        messages=messages,
                        functions=functions,
                        function_call="auto"
                    )
                else:
                    # 适配不同的LLM客户端
                    response = self.llm_client.chat(
                        messages=messages,
                        functions=functions
                    )
                
                # 处理响应
                message = response.get('choices', [{}])[0].get('message', {})
                messages.append(message)
                
                # 检查是否有函数调用
                if 'function_call' in message:
                    function_call = message['function_call']
                    function_name = function_call.get('name')
                    function_args = json.loads(function_call.get('arguments', '{}'))
                    
                    logger.info(f"🔧 LLM调用函数: {function_name}")
                    
                    # 执行函数调用
                    result = self.file_tool.call_function(function_name, **function_args)
                    
                    # 记录文件修改
                    if function_name == 'write_file' and result.get('success'):
                        files_modified.append(function_args.get('file_path'))
                    
                    # 将函数结果添加到对话
                    function_result_message = {
                        "role": "function",
                        "name": function_name,
                        "content": json.dumps(result, ensure_ascii=False)
                    }
                    messages.append(function_result_message)
                    
                    conversation_history.append({
                        'turn': turn + 1,
                        'function_call': function_call,
                        'function_result': result
                    })
                    
                else:
                    # 没有函数调用，对话结束
                    final_content = message.get('content', '')
                    logger.info(f"✅ Function calling对话完成，共{turn + 1}轮")
                    
                    return {
                        'success': True,
                        'total_turns': turn + 1,
                        'conversation_history': conversation_history,
                        'final_content': final_content,
                        'files_modified': files_modified,
                        'messages': messages
                    }
                    
            except Exception as e:
                logger.error(f"❌ Function calling第{turn + 1}轮失败: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'turn': turn + 1,
                    'conversation_history': conversation_history,
                    'files_modified': files_modified
                }
        
        # 达到最大轮数
        logger.warning(f"⚠️ Function calling达到最大轮数{max_turns}")
        return {
            'success': True,
            'total_turns': max_turns,
            'conversation_history': conversation_history,
            'files_modified': files_modified,
            'messages': messages,
            'warning': '达到最大对话轮数'
        }
    
    def _parse_and_execute_operations(self, response: str) -> Dict[str, Any]:
        """解析并执行文件操作"""
        
        import re
        
        files_modified = []
        operations = []
        
        # 查找function_call块
        function_calls = re.findall(r'```function_call\s*\n(.*?)\n```', response, re.DOTALL)
        
        for call_json in function_calls:
            try:
                call_data = json.loads(call_json)
                function_name = call_data.get('function')
                parameters = call_data.get('parameters', {})
                
                logger.info(f"🔧 执行函数: {function_name}")
                
                # 执行函数调用
                result = self.file_tool.call_function(function_name, **parameters)
                
                operations.append({
                    'function': function_name,
                    'parameters': parameters,
                    'result': result
                })
                
                # 记录文件修改
                if function_name == 'write_file' and result.get('success'):
                    files_modified.append(parameters.get('file_path'))
                    
            except Exception as e:
                logger.error(f"❌ 执行函数调用失败: {e}")
                operations.append({
                    'error': str(e),
                    'raw_call': call_json
                })
        
        return {
            'success': True,
            'operations': operations,
            'files_modified': files_modified,
            'total_operations': len(operations)
        }
    
    def get_generation_summary(self, result: Dict[str, Any]) -> str:
        """获取生成摘要"""
        
        summary = f"代码生成摘要:\n"
        summary += f"成功: {result.get('success', False)}\n"
        summary += f"层级: {result.get('layer', 'unknown')}\n"
        
        if result.get('files_modified'):
            summary += f"修改的文件:\n"
            for file_path in result['files_modified']:
                summary += f"- {file_path}\n"
        
        if result.get('error'):
            summary += f"错误: {result['error']}\n"
        
        return summary