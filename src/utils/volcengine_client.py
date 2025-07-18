#!/usr/bin/env python3
"""
火山引擎API客户端
专门用于火山引擎API的封装和调用
"""

import os
import logging
import time
from typing import List, Dict, Optional, Any, Generator
from dataclasses import dataclass

try:
    from openai import OpenAI
except ImportError:
    raise ImportError("请安装OpenAI包: pip install openai")

try:
    from ..config import settings
    from .llm_logger import log_llm_request, log_llm_response, log_llm_stream_chunk
except ImportError:
    from dotenv import load_dotenv
    load_dotenv()
    
    class MockSettings:
        VOLCENGINE_API_KEY = os.getenv("VOLCENGINE_API_KEY", "")
        VOLCENGINE_MODEL_ID = os.getenv("VOLCENGINE_MODEL_ID", "ep-20250605091804-wmw6w")
        VOLCENGINE_BASE_URL = os.getenv("VOLCENGINE_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
        DEFAULT_TEMPERATURE = 0.7
        DEFAULT_MAX_TOKENS = 2000
        DEFAULT_TIMEOUT = 600  # 调整为10分钟，适应代码生成等复杂任务
    
    settings = MockSettings()
    
    # 如果导入失败，创建空的日志函数
    def log_llm_request(*args, **kwargs):
        return f"volcengine_{int(time.time() * 1000)}"
    
    def log_llm_response(*args, **kwargs):
        pass
    
    def log_llm_stream_chunk(*args, **kwargs):
        pass

# 配置日志
logger = logging.getLogger(__name__)

@dataclass
class VolcengineConfig:
    """火山引擎配置"""
    api_key: str
    model_id: str
    base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 600  # 调整为10分钟，适应代码生成等复杂任务

class VolcengineClient:
    """火山引擎客户端"""
    
    def __init__(self, config: Optional[VolcengineConfig] = None):
        """
        初始化火山引擎客户端
        
        Args:
            config: 火山引擎配置，如果为None则从环境变量读取
        """
        if config is None:
            config = VolcengineConfig(
                api_key=settings.VOLCENGINE_API_KEY,
                model_id=settings.VOLCENGINE_MODEL_ID,
                base_url=settings.VOLCENGINE_BASE_URL,
                temperature=settings.DEFAULT_TEMPERATURE,
                max_tokens=settings.DEFAULT_MAX_TOKENS,
                timeout=settings.DEFAULT_TIMEOUT
            )
        
        self.config = config
        
        if not self.config.api_key:
            raise ValueError("火山引擎API密钥未设置，请在环境变量中设置VOLCENGINE_API_KEY")
        
        self.client = OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            timeout=self.config.timeout
        )
        
        logger.info("火山引擎客户端初始化成功")
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        聊天对话
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式输出
            tools: Function calling工具列表
            tool_choice: 工具选择策略
            **kwargs: 其他参数
            
        Returns:
            AI回复内容或完整响应对象（支持Function Calling时）
        """
        # 准备请求参数
        request_params = {
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
            "stream": stream,
            **kwargs
        }
        
        # 🔧 添加Function Calling参数
        if tools:
            request_params["tools"] = tools
            if tool_choice:
                request_params["tool_choice"] = tool_choice
        
        # 记录请求日志
        request_id = log_llm_request(
            provider="volcengine",
            model=self.config.model_id,
            messages=messages,
            parameters=request_params
        )
        
        start_time = time.time()
        
        try:
            response = self.client.chat.completions.create(
                model=self.config.model_id,
                messages=messages,
                **request_params
            )
            
            response_time = time.time() - start_time
            
            if stream:
                # 记录流式响应开始
                log_llm_response(
                    request_id=request_id,
                    response_content="[STREAM_START]",
                    response_time=response_time,
                    token_usage=None
                )
                return response
            else:
                # 🔧 处理Function Calling响应
                message = response.choices[0].message
                
                # 如果有工具调用，返回完整响应对象
                if tools and hasattr(message, 'tool_calls') and message.tool_calls:
                    response_content = f"[FUNCTION_CALL] {len(message.tool_calls)} tool calls"
                    
                    # 记录响应日志
                    log_llm_response(
                        request_id=request_id,
                        response_content=response_content,
                        response_time=response_time,
                        token_usage=getattr(response, 'usage', None)
                    )
                    
                    # 返回完整响应对象，支持Function Calling
                    return response
                
                # 普通文本响应
                response_content = message.content
                
                # 提取token使用情况
                token_usage = None
                if hasattr(response, 'usage') and response.usage:
                    token_usage = {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                
                # 记录响应日志
                log_llm_response(
                    request_id=request_id,
                    response_content=response_content,
                    response_time=response_time,
                    token_usage=token_usage
                )
                
                return response_content
                
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = str(e)
            
            # 记录错误日志
            log_llm_response(
                request_id=request_id,
                response_content="",
                response_time=response_time,
                error=error_msg
            )
            
            logger.error(f"火山引擎API调用失败: {e}")
            raise
    
    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Generator[str, None, None]:
        """
        流式聊天
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数
            
        Yields:
            流式响应内容
        """
        # 准备请求参数
        request_params = {
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
            "stream": True,
            **kwargs
        }
        
        # 记录请求日志
        request_id = log_llm_request(
            provider="volcengine",
            model=self.config.model_id,
            messages=messages,
            parameters=request_params
        )
        
        start_time = time.time()
        full_content = ""
        
        try:
            response = self.client.chat.completions.create(
                model=self.config.model_id,
                messages=messages,
                **request_params
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_content += content
                    
                    # 记录流式块
                    log_llm_stream_chunk(
                        request_id=request_id,
                        chunk_content=content,
                        chunk_index=len(full_content)
                    )
                    
                    yield content
            
            response_time = time.time() - start_time
            
            # 记录完整响应
            log_llm_response(
                request_id=request_id,
                response_content=full_content,
                response_time=response_time,
                token_usage=None  # 流式响应通常不返回token使用情况
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = str(e)
            
            # 记录错误日志
            log_llm_response(
                request_id=request_id,
                response_content=full_content,
                response_time=response_time,
                error=error_msg
            )
            
            logger.error(f"火山引擎流式API调用失败: {e}")
            raise
    
    def analyze_requirement(self, content: str, **kwargs) -> str:
        """
        需求分析
        
        Args:
            content: 需求内容
            **kwargs: 其他参数
            
        Returns:
            分析结果
        """
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的需求分析师，请对用户提供的需求进行详细分析，包括功能需求、非功能需求、约束条件等。"
            },
            {
                "role": "user",
                "content": f"请分析以下需求：\n\n{content}"
            }
        ]
        
        return self.chat(messages, **kwargs)
    
    def generate_api_design(self, requirement: str, **kwargs) -> str:
        """
        生成API设计
        
        Args:
            requirement: 需求描述
            **kwargs: 其他参数
            
        Returns:
            API设计文档
        """
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的API设计师，请根据需求生成RESTful API设计，包括接口路径、请求方法、参数、响应格式等。"
            },
            {
                "role": "user",
                "content": f"请为以下需求设计API：\n\n{requirement}"
            }
        ]
        
        return self.chat(messages, **kwargs)
    
    def generate_design_document(self, requirement: str, doc_type: str = "backend", **kwargs) -> str:
        """
        生成设计文档
        
        Args:
            requirement: 需求描述
            doc_type: 文档类型 (backend/frontend/database/system)
            **kwargs: 其他参数
            
        Returns:
            设计文档
        """
        doc_prompts = {
            "backend": "你是一个专业的后端架构师，请根据需求生成后端系统设计文档，包括技术栈选择、架构设计、模块划分、数据流等。",
            "frontend": "你是一个专业的前端架构师，请根据需求生成前端系统设计文档，包括技术栈选择、组件设计、状态管理、路由设计等。",
            "database": "你是一个专业的数据库设计师，请根据需求生成数据库设计文档，包括表结构设计、索引设计、关系设计等。",
            "system": "你是一个专业的系统架构师，请根据需求生成系统架构设计文档，包括整体架构、技术选型、部署方案、性能考虑等。"
        }
        
        system_prompt = doc_prompts.get(doc_type, doc_prompts["backend"])
        
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": f"请为以下需求生成{doc_type}设计文档：\n\n{requirement}"
            }
        ]
        
        return self.chat(messages, **kwargs)
    
    def generate_code(self, description: str, language: str = "python", **kwargs) -> str:
        """
        生成代码
        
        Args:
            description: 代码描述
            language: 编程语言
            **kwargs: 其他参数
            
        Returns:
            生成的代码
        """
        messages = [
            {
                "role": "system",
                "content": f"你是一个专业的{language}开发工程师，请根据描述生成高质量的{language}代码，包含必要的注释和错误处理。"
            },
            {
                "role": "user",
                "content": f"请生成{language}代码：\n\n{description}"
            }
        ]
        
        return self.chat(messages, **kwargs)
    
    def test_connection(self) -> bool:
        """
        测试连接
        
        Returns:
            连接是否成功
        """
        try:
            test_messages = [
                {
                    "role": "user",
                    "content": "Hello"
                }
            ]
            
            response = self.chat(test_messages, max_tokens=10)
            return bool(response)
            
        except Exception as e:
            logger.error(f"火山引擎连接测试失败: {e}")
            return False

# 全局客户端实例
_volcengine_client = None

def get_volcengine_client() -> VolcengineClient:
    """获取全局火山引擎客户端实例"""
    global _volcengine_client
    if _volcengine_client is None:
        # 尝试从配置文件读取配置
        try:
            from ..resource.config import get_config
            config = get_config()
            volcengine_config = config.get_volcengine_config()
            
            if volcengine_config and volcengine_config.get('api_key'):
                volcano_config = VolcengineConfig(
                    api_key=volcengine_config.get('api_key'),
                    model_id=volcengine_config.get('model', 'ep-20250605091804-wmw6w'),
                    base_url=volcengine_config.get('endpoint', 'https://ark.cn-beijing.volces.com/api/v3'),
                    temperature=volcengine_config.get('temperature', 0.7),
                    max_tokens=volcengine_config.get('max_tokens', 4000)
                )
                _volcengine_client = VolcengineClient(volcano_config)
            else:
                # 回退到环境变量
                _volcengine_client = VolcengineClient()
        except ImportError:
            # 如果无法导入配置，使用环境变量
            _volcengine_client = VolcengineClient()
    return _volcengine_client

# 便捷函数
def volcengine_chat(messages: List[Dict[str, str]], **kwargs) -> str:
    """便捷的聊天函数"""
    return get_volcengine_client().chat(messages, **kwargs)

def volcengine_stream_chat(messages: List[Dict[str, str]], **kwargs) -> Generator[str, None, None]:
    """便捷的流式聊天函数"""
    return get_volcengine_client().stream_chat(messages, **kwargs)

def volcengine_analyze_requirement(content: str, **kwargs) -> str:
    """便捷的需求分析函数"""
    return get_volcengine_client().analyze_requirement(content, **kwargs)

def volcengine_generate_api_design(requirement: str, **kwargs) -> str:
    """便捷的API设计生成函数"""
    return get_volcengine_client().generate_api_design(requirement, **kwargs)

def volcengine_generate_design_document(requirement: str, doc_type: str = "backend", **kwargs) -> str:
    """便捷的设计文档生成函数"""
    return get_volcengine_client().generate_design_document(requirement, doc_type, **kwargs)

def volcengine_generate_code(description: str, language: str = "python", **kwargs) -> str:
    """便捷的代码生成函数"""
    return get_volcengine_client().generate_code(description, language, **kwargs)

if __name__ == "__main__":
    # 测试代码
    try:
        client = VolcengineClient()
        
        # 测试连接
        if client.test_connection():
            print("✅ 火山引擎连接测试成功")
            
            # 测试聊天
            test_messages = [
                {
                    "role": "user",
                    "content": "你好，请介绍一下你自己"
                }
            ]
            
            response = client.chat(test_messages)
            print(f"🤖 AI回复: {response}")
            
        else:
            print("❌ 火山引擎连接测试失败")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}") 