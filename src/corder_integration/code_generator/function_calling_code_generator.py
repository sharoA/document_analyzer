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
        # 火山引擎使用标准的chat方法配合tools参数
        has_chat = hasattr(self.llm_client, 'chat')
        logger.info(f"🔧 LLM客户端支持chat方法: {has_chat}")
        
        # 检查是否是火山引擎客户端
        is_volcengine = hasattr(self.llm_client, 'model') or 'volcengine' in str(type(self.llm_client)).lower()
        logger.info(f"🔧 检测到火山引擎客户端: {is_volcengine}")
        
        # 火山引擎通过chat方法支持function calling
        return has_chat
    
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
        logger.info(f"🔧 使用_generate_with_function_calling生成{layer}层代码")
        logger.info(f"  - 操作: {layer_decision.get('action')}")
        logger.info(f"  - 目标类: {layer_decision.get('target_class')}")
        logger.info(f"  - 包路径: {layer_decision.get('package_path')}")
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

        logger.info(f"🔧 使用_generate_with_prompt_description生成{layer}层代码")
        logger.info(f"  - 操作: {layer_decision.get('action')}")
        logger.info(f"  - 目标类: {layer_decision.get('target_class')}")
        logger.info(f"  - 包路径: {layer_decision.get('package_path')}")

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
        
        prompt = f"""你是一个Java Spring Boot项目的DDD架构师，需要根据决策结果和详细业务需求生成{layer}层的代码。

## 🎯 业务需求详情
### API路径：{context.get('api_path', '')}
### 业务逻辑：{business_logic}

### 详细参数信息（如果有）：
{self._extract_detailed_params(context)}

## 📋 任务信息
- 层级: {layer}
- 决策: {action}
- 目标类: {target_class}
- 包路径: {package_path}
- API关键字: {api_keyword}
- 业务逻辑: {business_logic}
- 基础包名: {base_package}

## 📁 完整项目结构
{context.get('project_structure', {}).get('directory_tree', '项目结构信息不可用')}

## 🎯 重要路径规则
⚠️ 文件路径规则（相对于项目根目录）：
- 项目根路径：{context.get('project_structure', {}).get('project_path', '')}
- Java源码根路径：src/main/java/
- 基础包路径：{base_package.replace('.', '/')}

### DDD目录结构示例（相对路径）：
**注意：所有路径都是相对于项目根目录的相对路径！**
- Controller: src/main/java/{base_package.replace('.', '/')}/interfaces/facade/XxxController.java
- DTO Request: src/main/java/{base_package.replace('.', '/')}/interfaces/dto/XxxReq.java  
- DTO Response: src/main/java/{base_package.replace('.', '/')}/interfaces/dto/XxxResp.java
- Application Service: src/main/java/{base_package.replace('.', '/')}/application/service/XxxApplication.java
- Domain Service: src/main/java/{base_package.replace('.', '/')}/domain/service/XxxDomainService.java
- Mapper Interface: src/main/java/{base_package.replace('.', '/')}/domain/mapper/XxxMapper.java
- Entity: src/main/java/{base_package.replace('.', '/')}/domain/entity/XxxEntity.java
- Feign Client: src/main/java/{base_package.replace('.', '/')}/application/feign/XxxFeignClient.java
- XML Mapping: src/main/resources/mapper/XxxMapper.xml

### 路径转换规则：
- 包路径 com.yljr.crcl.limit.interfaces.dto → 文件路径 src/main/java/com/yljr/crcl/limit/interfaces/dto/
- 类名 LsLimitQueryRequest → 文件名 LsLimitQueryRequest.java

### 🚨 关键路径要求：
1. **必须使用相对路径**：所有文件路径必须是相对于项目根目录的相对路径
2. **不要重复路径**：不要在路径中包含项目根路径部分
3. **正确的包名**：使用 {base_package} 作为基础包名，而不是 com.yljr.crcl
4. **文件路径示例**：
   - ✅ 正确：src/main/java/{base_package.replace('.', '/')}/interfaces/dto/XxxReq.java
   - ❌ 错误：任何包含项目根路径的绝对路径

⚠️ 重要：使用file_exists、read_file、write_file时，必须使用完整的相对路径！

## 💻 代码生成要求
1. **完整实现业务逻辑**：根据request_params、response_params、validation_rules生成完整代码
2. **处理外部服务调用**：如果有external_call，要生成对应的Feign Client
3. **数据验证**：根据validation_rules生成参数校验
4. **分页处理**：如果有分页参数，要正确实现分页逻辑
5. **错误处理**：添加适当的异常处理和错误返回

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

## 📋 必须完成的工作流程
请严格按照以下步骤执行，**每个步骤都必须完成**：

### 步骤1：文件检查
- 使用 `file_exists` 检查目标文件是否存在
- 确定采用 create_new 还是 enhance_existing 策略

### 步骤2：现有文件分析（如果需要增强）
- 如果是enhance_existing，使用 `read_file` 读取现有文件内容
- 分析现有的import、字段、方法结构

### 步骤3：生成完整代码
- 根据业务需求生成完整的Java代码
- 包含所有必要的包声明、import、注解、字段和方法
- 如果是增强现有文件，将新方法合并到现有类中

### 步骤4：写入文件（🚨 关键步骤）
- **必须使用 `write_file` 函数写入生成的代码**
- 使用正确的文件路径（基于包路径和类名）
- 写入完整的文件内容，不是代码片段

### 步骤5：确认完成
- 在写入文件后，简要说明生成的内容

## ⚠️ 重要提醒
- **🚨 关键任务：每次必须调用 write_file 函数将代码写入文件！**
- **🚨 不要只检查文件存在性就结束，必须生成并写入代码**
- **🚨 任务未完成标准：如果没有调用write_file写入代码，任务就是失败的**
- 如果文件不存在，要创建新文件
- 如果文件存在且需要增强，要读取后合并再写入
## 📋 必须完成的完整流程
**请严格按照以下流程执行，缺一不可：**
1. 📋 使用 `file_exists` 检查目标文件是否存在
2. 📖 如果文件存在且需要增强，使用 `read_file` 读取现有内容
3. 🔨 生成完整的代码内容（不是代码片段）
4. 📝 **必须使用 `write_file` 函数写入生成的代码**
5. ✅ 确认写入成功

**⛔ 严禁：只执行步骤1就结束！必须完成所有步骤！**

## 注意事项
- 确保生成的代码符合Java语法和DDD架构规范
- 包含完整的package声明、import语句、类定义
- 如果是增强现有文件，保留原有的import、注解和方法
- 生成的是完整文件内容，不是代码片段

现在开始执行任务，请确保完成所有5个步骤！"""
        
        return prompt
    
    def _extract_detailed_params(self, context: Dict[str, Any]) -> str:
        """从上下文中提取详细的API参数信息"""
        task_parameters = context.get('task_parameters', {})
        
        if not task_parameters:
            api_path = context.get('api_path', '')
            business_logic = context.get('business_logic', '')
            return f"""
基础API信息：
- API路径: {api_path}
- 业务描述: {business_logic}
请根据API路径和业务描述推断合理的参数结构和业务实现。
"""
        
        # 构建详细的参数信息
        params_info = f"""
### 📋 完整的API参数规范

**HTTP方法**: {task_parameters.get('http_method', 'GET')}
**Content-Type**: {task_parameters.get('content_type', 'application/json')}

**🔵 请求参数 (request_params)**:
"""
        
        request_params = task_parameters.get('request_params', {})
        for param_name, param_desc in request_params.items():
            params_info += f"- {param_name}: {param_desc}\n"
        
        params_info += f"""
**🔴 响应参数 (response_params)**:
"""
        response_params = task_parameters.get('response_params', {})
        for param_name, param_desc in response_params.items():
            params_info += f"- {param_name}: {param_desc}\n"
            
        params_info += f"""
**🟡 数据来源**: {task_parameters.get('data_source', '未指定')}

**🟢 外部服务调用**: {task_parameters.get('external_call', '无')}

**🔶 验证规则 (validation_rules)**:
"""
        validation_rules = task_parameters.get('validation_rules', {})
        for param_name, rule_desc in validation_rules.items():
            params_info += f"- {param_name}: {rule_desc}\n"
            
        params_info += f"""
**⚡ 业务逻辑说明**: {task_parameters.get('business_logic', '')}

🎯 **重要提示**: 请根据以上详细参数规范生成完整的、生产就绪的代码实现！
"""
        
        return params_info
    
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
                logger.info(f"🔄 Function calling 第{turn + 1}轮开始")
                
                # 🔧 火山引擎Function Calling调用方式
                tools = [{"type": "function", "function": func} for func in functions]
                
                logger.info(f"🔧 调用火山引擎Function Calling，工具数量: {len(tools)}")
                
                # 使用火山引擎标准格式
                response = self.llm_client.chat(
                    messages=messages,
                    tools=tools
                )
                
                logger.info(f"🔧 收到LLM响应，类型: {type(response)}")
                
                # 🔧 修复：处理火山引擎响应格式
                # 火山引擎返回的是ChatCompletion对象，需要正确访问属性
                if hasattr(response, 'choices') and response.choices:
                    message = response.choices[0].message
                elif isinstance(response, dict):
                    # 兼容字典格式
                    message = response.get('choices', [{}])[0].get('message', {})
                else:
                    # 如果response是字符串或其他类型，创建一个默认的message结构
                    logger.warning(f"⚠️ 收到意外的响应格式: {type(response)}")
                    message = {
                        'role': 'assistant',
                        'content': str(response) if response else '',
                        'tool_calls': []
                    }
                
                # 转换为字典格式以便后续处理
                if hasattr(message, 'model_dump'):
                    message_dict = message.model_dump()
                elif hasattr(message, 'dict'):
                    message_dict = message.dict()
                elif isinstance(message, dict):
                    message_dict = message
                else:
                    # 如果message是字符串或其他类型，创建标准字典结构
                    message_dict = {
                        'role': 'assistant',
                        'content': str(message) if message else '',
                        'tool_calls': []
                    }
                
                messages.append(message_dict)
                
                # 检查是否有工具调用
                tool_calls = None
                try:
                    tool_calls = getattr(message, 'tool_calls', None) or message_dict.get('tool_calls', [])
                except Exception as e:
                    logger.warning(f"⚠️ 提取tool_calls时出错: {e}")
                    tool_calls = []
                
                # 确保tool_calls是列表
                if tool_calls is None:
                    tool_calls = []
                elif not isinstance(tool_calls, list):
                    tool_calls = [tool_calls] if tool_calls else []
                
                if tool_calls:
                    for tool_call in tool_calls:
                        try:
                            # 处理tool_call对象或字典
                            if hasattr(tool_call, 'function'):
                                function_call = tool_call.function
                                tool_call_id = tool_call.id
                            elif isinstance(tool_call, dict):
                                function_call = tool_call.get('function', {})
                                tool_call_id = tool_call.get('id', f'call_{turn}')
                            else:
                                logger.warning(f"⚠️ 意外的tool_call格式: {type(tool_call)}")
                                continue
                            
                            # 处理function对象或字典
                            if hasattr(function_call, 'name'):
                                function_name = function_call.name
                                function_args = json.loads(function_call.arguments)
                            elif isinstance(function_call, dict):
                                function_name = function_call.get('name')
                                function_args = json.loads(function_call.get('arguments', '{}'))
                            else:
                                logger.warning(f"⚠️ 意外的function_call格式: {type(function_call)}")
                                continue
                            
                            if not function_name:
                                logger.warning(f"⚠️ 函数名为空，跳过此工具调用")
                                continue
                            
                            logger.info(f"🔧 执行函数: {function_name}")
                            
                            # 执行函数调用
                            result = self.file_tool.call_function(function_name, **function_args)
                            
                            # 记录文件修改
                            if function_name == 'write_file' and result.get('success'):
                                files_modified.append(function_args.get('file_path'))
                            
                            # 将函数结果添加到对话
                            function_result_message = {
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "content": json.dumps(result, ensure_ascii=False)
                            }
                            messages.append(function_result_message)
                            
                            conversation_history.append({
                                'turn': turn + 1,
                                'function_call': {
                                    'name': function_name,
                                    'arguments': function_call.arguments if hasattr(function_call, 'arguments') else function_call.get('arguments', '{}')
                                },
                                'function_result': result
                            })
                            
                        except Exception as e:
                            logger.error(f"❌ 处理工具调用时出错: {e}")
                            # 添加错误消息到对话中
                            error_message = {
                                "role": "tool",
                                "tool_call_id": tool_call_id if 'tool_call_id' in locals() else f'error_{turn}',
                                "content": json.dumps({"error": str(e)}, ensure_ascii=False)
                            }
                            messages.append(error_message)
                            continue
                        
                else:
                    # 没有函数调用，检查是否需要继续
                    try:
                        final_content = getattr(message, 'content', None) or message_dict.get('content', '')
                        if not isinstance(final_content, str):
                            final_content = str(final_content) if final_content else ''
                    except Exception as e:
                        logger.warning(f"⚠️ 提取final_content时出错: {e}")
                        final_content = ''
                    
                    # 🔧 修复：如果只检查了文件存在但没有写文件，强制继续
                    if self._should_continue_conversation(conversation_history, files_modified):
                        continue_prompt = "请继续完成任务：生成完整的代码并使用write_file函数写入文件。不要只检查文件存在性，必须生成并写入代码！"
                        messages.append({"role": "user", "content": continue_prompt})
                        logger.info(f"🔄 检测到需要继续生成代码，添加继续提示")
                        continue
                    
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
    
    def _should_continue_conversation(self, conversation_history: List[Dict], files_modified: List[str]) -> bool:
        """
        判断是否需要继续对话
        
        检查逻辑：
        1. 如果没有写入任何文件，需要继续
        2. 如果只调用了file_exists但没有write_file，需要继续
        3. 如果对话轮数少于2轮且没有写文件，需要继续
        """
        # 如果已经写入了文件，不需要继续
        if files_modified:
            return False
        
        # 如果没有任何对话历史，需要继续
        if not conversation_history:
            return True
        
        # 检查是否只调用了file_exists类型的函数
        function_calls = []
        for history in conversation_history:
            if 'function_call' in history:
                func_info = history['function_call']
                if isinstance(func_info, dict) and 'name' in func_info:
                    function_calls.append(func_info['name'])
        
        # 如果只调用了file_exists、read_file、list_files等查询函数，但没有write_file，需要继续
        write_functions = ['write_file', 'create_directory']
        query_functions = ['file_exists', 'read_file', 'list_files']
        
        has_write_function = any(func in write_functions for func in function_calls)
        has_query_function = any(func in query_functions for func in function_calls)
        
        # 如果有查询函数但没有写入函数，需要继续
        if has_query_function and not has_write_function:
            return True
        
        # 如果对话轮数少于2轮且没有写文件，需要继续
        if len(conversation_history) < 2 and not has_write_function:
            return True
        
        return False

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