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
        
        # 🆕 清理备份文件
        try:
            cleaned_count = self._cleanup_backup_files()
            if cleaned_count > 0:
                logger.info(f"🧹 Function Calling完成后清理了 {cleaned_count} 个备份文件")
        except Exception as e:
            logger.warning(f"⚠️ Function Calling备份清理时出错: {e}")
        
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
{{context.get('project_structure', {{}}).get('directory_tree', '项目结构信息不可用')}}

## 🎯 重要路径规则
⚠️ 文件路径规则（相对于项目根目录）：
- 项目根路径：{{context.get('project_structure', {{}}).get('project_path', '')}}
- Java源码根路径：src/main/java/
- 基础包路径：{{base_package.replace('.', '/')}}

### DDD目录结构示例（相对路径）：
**注意：所有路径都是相对于项目根目录的相对路径！**
- Controller: src/main/java/{{base_package.replace('.', '/')}}/interfaces/XxxController.java
- DTO Request: src/main/java/{{base_package.replace('.', '/')}}/interfaces/dto/XxxReq.java  
- DTO Response: src/main/java/{{base_package.replace('.', '/')}}/interfaces/dto/XxxResp.java
- Application Service: src/main/java/{{base_package.replace('.', '/')}}/application/service/XxxApplication.java
- Domain Service: src/main/java/{{base_package.replace('.', '/')}}/domain/service/XxxDomainService.java
- Mapper Interface: src/main/java/{{base_package.replace('.', '/')}}/domain/mapper/XxxMapper.java
- Entity: src/main/java/{{base_package.replace('.', '/')}}/domain/entity/XxxEntity.java
- Feign Client: src/main/java/{{base_package.replace('.', '/')}}/application/feign/XxxFeignClient.java
- XML Mapping: src/main/resources/mapper/XxxMapper.xml

### 路径转换规则：
- 包路径 com.yljr.crcl.limit.interfaces.dto → 文件路径 src/main/java/com/yljr/crcl/limit/interfaces/dto/
- 类名 LsLimitQueryRequest → 文件名 LsLimitQueryRequest.java

### 🚨 关键路径要求：
1. **必须使用相对路径**：所有文件路径必须是相对于项目根目录的相对路径
2. **不要重复路径**：不要在路径中包含项目根路径部分
3. **正确的包名**：使用 {{base_package}} 作为基础包名，而不是 com.yljr.crcl
4. **文件路径示例**：
   - ✅ 正确：src/main/java/{{base_package.replace('.', '/')}}/interfaces/dto/XxxReq.java
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
优先使用高效的文件操作方式：

**🎯 推荐方法（避免JSON截断）**：
- replace_text: 局部替换文本内容（推荐用于在现有类中添加方法）
- read_file: 读取现有文件内容

**常规方法**：
- write_file: 写入文件内容（仅用于小文件或新文件）
- list_files: 列出目录中的文件
- file_exists: 检查文件是否存在
- create_directory: 创建目录
- backup_file: 备份文件

**💡 添加方法的最佳实践**：
当需要在现有类中添加方法时，使用 `replace_text` 工具：
1. 使用 `read_file` 读取文件，找到类的最后一个 `}}`
2. 使用 `replace_text`，将最后的 `}}` 替换为 `[新方法的完整代码]\\n}}`

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
- 如果是增强现有文件，准备新方法代码

### 步骤4：写入文件（🚨 关键步骤）
**选择合适的写入方式**：
- **新文件或小文件**：使用 `write_file` 函数写入完整内容
- **大文件增强**：使用 `replace_text` 函数局部替换（推荐）
  - 例如：将类的最后 `}}` 替换为 `[新方法代码]\\n}}`

### 步骤5：确认完成
- 在写入文件后，简要说明生成的内容

## ⚠️ 重要提醒
- ** 关键任务：必须调用文件写入函数（write_file 或 replace_text）将代码写入文件！**
- ** 不要只检查文件存在性就结束，必须生成并写入代码**
- ** 任务未完成标准：如果没有调用文件写入函数，任务就是失败的**
- ** 优先使用 replace_text 避免大文件JSON截断问题**
- 如果文件不存在，要创建新文件
- 如果文件存在且需要增强，要读取后使用 replace_text 添加新方法
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
                                try:
                                    function_args = json.loads(function_call.arguments)
                                except json.JSONDecodeError as json_error:
                                    logger.error(f"❌ JSON解析失败: {json_error}")
                                    logger.error(f"原始arguments: {function_call.arguments}")
                                    logger.error(f"错误位置: 第{json_error.lineno}行，第{json_error.colno}列")
                                    
                                    # 🆕 优先检查截断问题，让大模型自主重新生成
                                    if self._handle_truncated_json(function_call.arguments, messages):
                                        break  # 跳出当前轮次，继续下一轮对话
                                    
                                    # 尝试修复常见的JSON错误
                                    fixed_args = self._try_fix_json_string(function_call.arguments)
                                    if fixed_args is not None:
                                        function_args = fixed_args
                                        logger.info("✅ JSON修复成功")
                                    else:
                                        logger.error("❌ JSON修复失败，跳过此工具调用")
                                        continue
                            elif isinstance(function_call, dict):
                                function_name = function_call.get('name')
                                arguments_str = function_call.get('arguments', '{}')
                                try:
                                    function_args = json.loads(arguments_str)
                                except json.JSONDecodeError as json_error:
                                    logger.error(f"❌ JSON解析失败: {json_error}")
                                    logger.error(f"原始arguments: {arguments_str}")
                                    logger.error(f"错误位置: 第{json_error.lineno}行，第{json_error.colno}列")
                                    
                                    # 🆕 优先检查截断问题，让大模型自主重新生成
                                    if self._handle_truncated_json(arguments_str, messages):
                                        break  # 跳出当前轮次，继续下一轮对话
                                    
                                    # 尝试修复常见的JSON错误
                                    fixed_args = self._try_fix_json_string(arguments_str)
                                    if fixed_args is not None:
                                        function_args = fixed_args
                                        logger.info("✅ JSON修复成功")
                                    else:
                                        logger.error("❌ JSON修复失败，跳过此工具调用")
                                        continue
                            else:
                                logger.warning(f"⚠️ 意外的function_call格式: {type(function_call)}")
                                continue
                            
                            if not function_name:
                                logger.warning(f"⚠️ 函数名为空，跳过此工具调用")
                                continue
                            
                            logger.info(f"🔧 执行函数: {function_name}")
                            
                            # 🆕 增加重要文件操作的特殊处理
                            if function_name == 'write_file':
                                # 对write_file进行特殊处理，确保参数正确
                                if not self._validate_write_file_args(function_args):
                                    logger.error("❌ write_file参数验证失败，跳过此工具调用")
                                    continue
                            
                            # 执行函数调用
                            result = self.file_tool.call_function(function_name, **function_args)
                            
                            # 记录文件修改
                            if function_name in ['write_file', 'replace_text'] and result.get('success'):
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
                        continue_prompt = "请继续完成任务：生成完整的代码并使用文件写入函数（write_file 或 replace_text）写入文件。不要只检查文件存在性，必须生成并写入代码！对于大文件，推荐使用 replace_text 避免JSON截断。"
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
                if function_name in ['write_file', 'replace_text'] and result.get('success'):
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
        
        # 如果只调用了file_exists、read_file、list_files等查询函数，但没有写入函数，需要继续
        write_functions = ['write_file', 'replace_text', 'create_directory']
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

    def _try_fix_json_string(self, json_str: str) -> Optional[Dict[str, Any]]:
        """
        尝试修复常见的JSON字符串错误
        
        Args:
            json_str: 可能有错误的JSON字符串
            
        Returns:
            修复后的字典对象，如果修复失败返回None
        """
        if not json_str or not isinstance(json_str, str):
            logger.warning("⚠️ JSON字符串为空或不是字符串类型")
            return None
        
        original_str = json_str.strip()
        logger.info(f"🔧 尝试修复JSON字符串: {original_str[:100]}...")
        
        # 修复策略列表 - 按优先级排序
        fix_strategies = [
            self._fix_large_content_json,        # 🆕 优先处理大内容JSON
            self._fix_double_escaped_quotes,     # 🆕 修复双重转义的引号
            self._fix_unterminated_string,
            self._fix_missing_quotes,
            self._fix_trailing_comma,
            self._fix_unescaped_quotes,
            self._fix_control_characters,
            self._extract_json_from_text,
            self._fix_truncated_json           # 🆕 处理截断的JSON
        ]
        
        for strategy in fix_strategies:
            try:
                fixed_str = strategy(original_str)
                if fixed_str != original_str:
                    logger.info(f"🔧 应用修复策略: {strategy.__name__}")
                    logger.info(f"🔧 修复后字符串: {fixed_str[:100]}...")
                
                # 尝试解析修复后的字符串
                result = json.loads(fixed_str)
                logger.info(f"✅ JSON修复成功，使用策略: {strategy.__name__}")
                return result
                
            except json.JSONDecodeError as e:
                logger.debug(f"策略 {strategy.__name__} 失败: {e}")
                continue
            except Exception as e:
                logger.warning(f"策略 {strategy.__name__} 出现异常: {e}")
                continue
        
        logger.error("❌ 所有JSON修复策略都失败了")
        return None
    
    
    def _fix_double_escaped_quotes(self, json_str: str) -> str:
        """修复Java注解参数的引号转义问题"""
        
        # 问题是LLM生成了错误的JSON转义
        # 在JSON字符串中，@Param("xxx") 会破坏JSON结构
        # 需要转义为 @Param(\\\"xxx\\\")
        
        if '@Param(' not in json_str:
            return json_str
            
        logger.info("🔧 检测到Java @Param注解引号转义错误，开始修复")
        
        # 简单直接的字符串替换方式
        # 先处理具体的参数名
        param_names = ['gwCompanyId', 'unitName', 'limitSource', 'bizType', 'page', 'pageRow']
        
        for param_name in param_names:
            # 将错误的转义格式修复为正确格式
            wrong_pattern = f'@Param("{param_name}")'  # 错误：没有转义
            correct_pattern = f'@Param(\\\\\\\"{param_name}\\\\\\\")'  # 正确：JSON中的正确转义
            
            json_str = json_str.replace(wrong_pattern, correct_pattern)
            
            # 也处理已经部分转义的情况
            wrong_pattern2 = f'@Param(\\"{param_name}\\")'  # 错误：转义不够
            json_str = json_str.replace(wrong_pattern2, correct_pattern)
        
        logger.info("🔧 Java @Param注解引号转义修复完成")
        return json_str
    
    def _fix_large_content_json(self, json_str: str) -> str:
        """修复包含大量内容的JSON（如代码内容）"""
        import re
        
        # 检查是否是大内容JSON（超过1000字符且包含content字段）
        if len(json_str) < 1000 or '"content"' not in json_str:
            return json_str
        
        logger.info("🔧 检测到大内容JSON，应用特殊修复策略")
        
        try:
            # 尝试提取基本结构
            file_path_match = re.search(r'"file_path"\s*:\s*"([^"]+)"', json_str)
            if not file_path_match:
                return json_str
            
            file_path = file_path_match.group(1)
            
            # 查找content字段的开始位置
            content_start = json_str.find('"content"')
            if content_start == -1:
                return json_str
            
            # 查找content值的开始位置
            colon_pos = json_str.find(':', content_start)
            if colon_pos == -1:
                return json_str
            
            # 查找内容开始的引号
            quote_pos = json_str.find('"', colon_pos)
            if quote_pos == -1:
                return json_str
            
            # 提取content之前的部分
            before_content = json_str[:quote_pos + 1]
            
            # 提取content值（从quote_pos+1开始到最后）
            content_part = json_str[quote_pos + 1:]
            
            # 尝试找到content的结束位置（最后一个有效的引号+}）
            # 从后往前查找，寻找 "}的模式
            for i in range(len(content_part) - 1, -1, -1):
                if content_part[i] == '}' and i > 0 and content_part[i-1] == '"':
                    # 找到可能的结束位置
                    content_value = content_part[:i-1]
                    
                    # 清理content内容
                    content_value = self._clean_content_for_json(content_value)
                    
                    # 重新构建JSON
                    reconstructed = f'{before_content}{content_value}"}}'
                    logger.info(f"🔧 重构JSON成功，长度: {len(reconstructed)}")
                    return reconstructed
            
            # 如果上述方法失败，尝试截断策略
            if len(content_part) > 5000:  # 如果内容太长，截断它
                content_value = content_part[:3000]
                content_value = self._clean_content_for_json(content_value)
                content_value += "...[内容已截断]"
                reconstructed = f'{before_content}{content_value}"}}'
                logger.info("🔧 应用截断策略修复JSON")
                return reconstructed
                
        except Exception as e:
            logger.warning(f"⚠️ 大内容JSON修复失败: {e}")
        
        return json_str
    
    def _clean_content_for_json(self, content: str) -> str:
        """清理内容使其适合JSON格式 - 增强版"""
        if not content:
            return ""
        
        # 转义特殊字符 - 首先保护已经转义的
        content = content.replace('\\\\', '__PROTECTED_BACKSLASH__')
        content = content.replace('\\"', '__PROTECTED_QUOTE__')
        content = content.replace('\\n', '__PROTECTED_NEWLINE__')
        content = content.replace('\\r', '__PROTECTED_CARRIAGE__')
        content = content.replace('\\t', '__PROTECTED_TAB__')
        
        # 转义反斜杠（必须在其他转义之前）
        content = content.replace('\\', '\\\\')
        
        # 转义引号
        content = content.replace('"', '\\"')
        
        # 转义控制字符
        content = content.replace('\n', '\\n')
        content = content.replace('\r', '\\r')
        content = content.replace('\t', '\\t')
        
        # 恢复保护的字符
        content = content.replace('__PROTECTED_BACKSLASH__', '\\\\')
        content = content.replace('__PROTECTED_QUOTE__', '\\"')
        content = content.replace('__PROTECTED_NEWLINE__', '\\n')
        content = content.replace('__PROTECTED_CARRIAGE__', '\\r')
        content = content.replace('__PROTECTED_TAB__', '\\t')
        
        # 移除其他控制字符
        import re
        content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', content)
        
        return content
    
    def _fix_truncated_json(self, json_str: str) -> str:
        """修复被截断的JSON"""
        if not json_str.endswith('}'):
            logger.info("🔧 检测到可能被截断的JSON，尝试补全")
            
            # 计算需要多少个闭合括号
            open_braces = json_str.count('{')
            close_braces = json_str.count('}')
            
            if open_braces > close_braces:
                # 需要补充闭合括号
                missing_braces = open_braces - close_braces
                
                # 检查是否需要先关闭字符串
                if json_str.count('"') % 2 == 1:  # 奇数个引号，说明有未关闭的字符串
                    json_str += '"'
                
                # 添加缺失的闭合括号
                json_str += '}' * missing_braces
                logger.info(f"🔧 补充了 {missing_braces} 个闭合括号")
        
        return json_str
    
    def _validate_write_file_args(self, function_args: Dict[str, Any]) -> bool:
        """验证write_file函数的参数"""
        try:
            # 检查必需参数
            if 'file_path' not in function_args:
                logger.error("❌ write_file缺少file_path参数")
                return False
            
            if 'content' not in function_args:
                logger.error("❌ write_file缺少content参数")
                return False
            
            file_path = function_args['file_path']
            content = function_args['content']
            
            # 基本检查
            if not isinstance(file_path, str) or not file_path.strip():
                logger.error("❌ file_path必须是非空字符串")
                return False
            
            if not isinstance(content, str):
                logger.error("❌ content必须是字符串")
                return False
            
            # 内容长度检查（避免过大的内容）
            if len(content) > 100000:  # 100KB限制
                logger.warning(f"⚠️ 文件内容很大 ({len(content)} 字符)，可能影响性能")
                # 不返回False，只是警告
            
            # 路径安全检查
            if '..' in file_path or file_path.startswith('/'):
                logger.error(f"❌ 不安全的文件路径: {file_path}")
                return False
            
            logger.debug(f"✅ write_file参数验证通过: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ write_file参数验证异常: {e}")
            return False
    
    def _fix_unterminated_string(self, json_str: str) -> str:
        """修复未终止的字符串"""
        # 检查是否有未闭合的引号
        if json_str.count('"') % 2 != 0:
            # 如果引号数量是奇数，尝试在末尾添加引号和闭合括号
            if not json_str.endswith('"'):
                json_str = json_str + '"'
            if not json_str.strip().endswith('}'):
                json_str = json_str + '}'
        return json_str
    
    def _fix_missing_quotes(self, json_str: str) -> str:
        """修复缺少引号的键或值"""
        import re
        
        # 修复缺少引号的键
        json_str = re.sub(r'(\w+):', r'"\1":', json_str)
        
        # 修复缺少引号的字符串值（但不影响数字、布尔值等）
        json_str = re.sub(r':\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*([,}])', r': "\1"\2', json_str)
        
        return json_str
    
    def _fix_trailing_comma(self, json_str: str) -> str:
        """修复末尾多余的逗号"""
        import re
        
        # 移除对象末尾的逗号
        json_str = re.sub(r',\s*}', '}', json_str)
        
        # 移除数组末尾的逗号
        json_str = re.sub(r',\s*]', ']', json_str)
        
        return json_str
    
    def _fix_unescaped_quotes(self, json_str: str) -> str:
        """修复未转义的引号"""
        # 这个比较复杂，简单处理：在字符串值内部的引号前添加反斜杠
        # 注意：这是一个简化的实现，可能不能处理所有情况
        import re
        
        # 查找字符串值内部的未转义引号
        def escape_quotes_in_strings(match):
            content = match.group(1)
            # 转义内部的引号
            content = content.replace('\\"', '"').replace('"', '\\"')
            return f'"{content}"'
        
        # 匹配 "..." 格式的字符串，但排除已经正确转义的
        json_str = re.sub(r'"([^"\\]*(?:\\.[^"\\]*)*)"', escape_quotes_in_strings, json_str)
        
        return json_str
    
    def _fix_control_characters(self, json_str: str) -> str:
        """修复控制字符 - 增强版"""
        logger.info("🔧 修复控制字符")
        import re
        
        # 处理换行问题 - 首先保护已经正确转义的
        json_str = json_str.replace('\\n', '__PROTECTED_NEWLINE__')
        json_str = json_str.replace('\\r', '__PROTECTED_CARRIAGE__')
        json_str = json_str.replace('\\t', '__PROTECTED_TAB__')
        
        # 转义真实的控制字符
        json_str = json_str.replace('\n', '\\n')
        json_str = json_str.replace('\r', '\\r')
        json_str = json_str.replace('\t', '\\t')
        
        # 恢复保护的字符
        json_str = json_str.replace('__PROTECTED_NEWLINE__', '\\n')
        json_str = json_str.replace('__PROTECTED_CARRIAGE__', '\\r')
        json_str = json_str.replace('__PROTECTED_TAB__', '\\t')
        
        # 移除其他控制字符
        json_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', json_str)
        
        return json_str
    
    def _extract_json_from_text(self, text: str) -> str:
        """从文本中提取JSON部分"""
        import re
        
        # 尝试提取第一个看起来像JSON的部分
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        if matches:
            return matches[0]
        
        # 如果没找到完整的JSON，尝试构建一个基本的JSON
        if 'file_path' in text:
            # 看起来像文件操作参数
            import re
            file_path_match = re.search(r'file_path["\s:]+([^",\s}]+)', text)
            if file_path_match:
                file_path = file_path_match.group(1).strip('"')
                return f'{{"file_path": "{file_path}"}}'
        
        return text

    def _handle_truncated_json(self, json_str: str, messages: list) -> bool:
        """
        处理截断的JSON - 简化版 + 上下文优化
        
        Args:
            json_str: 可能被截断的JSON字符串
            messages: 对话消息列表
            
        Returns:
            bool: True表示检测到截断并已处理，需要继续对话；False表示没有截断
        """
        if not json_str or not isinstance(json_str, str):
            return False
        
        json_str = json_str.strip()
        
        # 🔍 简单粗暴的截断检测
        is_truncated = (
            not json_str.endswith('}') or  # 没有正常结束
            json_str.count('{') > json_str.count('}') or  # 括号不匹配
            len(json_str) > 3000 or  # 内容太长了
            json_str.count('"') % 2 != 0  # 引号不匹配（可能在字符串中被截断）
        )
        
        if is_truncated:
            logger.warning(f"🚨 检测到JSON截断，长度: {len(json_str)}字符")
            
            # 🆕 提取前面500字符作为上下文，让LLM知道写到哪里了
            context_preview = json_str[:500] if len(json_str) > 500 else json_str
            
            # 🔧 分析截断的严重程度，给出不同的指导
            open_braces = json_str.count('{')
            close_braces = json_str.count('}')
            missing_braces = open_braces - close_braces
            
            if missing_braces > 3 or len(json_str) > 5000:
                # 严重截断，建议拆分
                retry_message = {
                    "role": "user",
                    "content": f"""🚨 你的JSON响应被严重截断了！这是被截断内容的开头部分：

```json
{context_preview}...
```

**问题分析：**
- 当前长度: {len(json_str)}字符  
- 缺少: {missing_braces}个闭合括号
- 建议: 内容太大，需要拆分

**请重新生成，并主动拆分成多个小的write_file调用：**
1. 🏗️ 先写文件头部（package、import、类声明）
2. 📝 再写方法签名和基础结构  
3. 🔧 最后写具体的方法实现

每个write_file调用保持在100行代码以内，现在从第一步开始！"""
                }
            else:
                # 轻微截断，继续生成
                retry_message = {
                    "role": "user", 
                    "content": f"""🚨 你的JSON响应被截断了！这是被截断内容的开头：

```json
{context_preview}...
```

请根据这个上下文重新生成完整的JSON，如果内容较大就主动分成几个write_file调用。

现在重新开始吧！"""
                }
            
            messages.append(retry_message)
            logger.info("📤 已发送截断恢复请求给大模型")
            return True
        
        return False

    def _cleanup_backup_files(self) -> int:
        """
        清理Function Calling生成的备份文件
        
        Returns:
            清理的备份目录数量
        """
        cleaned_count = 0
        
        try:
            import glob
            import shutil
            import os
            
            # 获取项目路径
            project_path = str(self.project_path)
            
            # 清理FileOperationToolInvoker创建的备份目录
            backup_dir = os.path.join(project_path, "backup")
            if os.path.exists(backup_dir):
                # 查找所有strategy1_backup_*目录
                backup_dirs = glob.glob(os.path.join(backup_dir, "strategy1_backup_*"))
                
                for backup_dir_path in backup_dirs:
                    if os.path.isdir(backup_dir_path):
                        try:
                            shutil.rmtree(backup_dir_path)
                            logger.info(f"🗑️ Function Calling清理备份目录: {backup_dir_path}")
                            cleaned_count += 1
                        except Exception as e:
                            logger.warning(f"⚠️ 无法删除备份目录 {backup_dir_path}: {e}")
                
                # 如果backup目录为空，也删除它
                try:
                    if not os.listdir(backup_dir):  # 目录为空
                        os.rmdir(backup_dir)
                        logger.info(f"🗑️ 删除空的备份根目录: {backup_dir}")
                except Exception as e:
                    logger.debug(f"备份根目录非空或删除失败: {e}")
            
            logger.info(f"🧹 Function Calling备份清理完成，删除了 {cleaned_count} 个目录")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"❌ Function Calling备份清理失败: {e}")
            return 0

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