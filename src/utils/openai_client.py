#!/usr/bin/env python3
"""
OpenAI API客户端
专门用于OpenAI API的封装和调用
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
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        OPENAI_MODEL_ID = os.getenv("OPENAI_MODEL_ID", "gpt-3.5-turbo")
        OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        DEFAULT_TEMPERATURE = 0.7
        DEFAULT_MAX_TOKENS = 2000
        DEFAULT_TIMEOUT = 120
    
    settings = MockSettings()
    
    # 如果导入失败，创建空的日志函数
    def log_llm_request(*args, **kwargs):
        return f"openai_{int(time.time() * 1000)}"
    
    def log_llm_response(*args, **kwargs):
        pass
    
    def log_llm_stream_chunk(*args, **kwargs):
        pass

# 配置日志
logger = logging.getLogger(__name__)

@dataclass
class OpenAIConfig:
    """OpenAI配置"""
    api_key: str
    model_id: str
    base_url: str = "https://api.openai.com/v1"
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 120

class OpenAIClient:
    """OpenAI客户端"""
    
    def __init__(self, config: Optional[OpenAIConfig] = None):
        """
        初始化OpenAI客户端
        
        Args:
            config: OpenAI配置，如果为None则从环境变量读取
        """
        if config is None:
            config = OpenAIConfig(
                api_key=settings.OPENAI_API_KEY,
                model_id=settings.OPENAI_MODEL_ID,
                base_url=settings.OPENAI_BASE_URL,
                temperature=settings.DEFAULT_TEMPERATURE,
                max_tokens=settings.DEFAULT_MAX_TOKENS,
                timeout=settings.DEFAULT_TIMEOUT
            )
        
        self.config = config
        
        if not self.config.api_key:
            raise ValueError("OpenAI API密钥未设置，请在环境变量中设置OPENAI_API_KEY")
        
        self.client = OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            timeout=self.config.timeout
        )
        
        logger.info("OpenAI客户端初始化成功")
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> str:
        """
        聊天对话
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式输出
            **kwargs: 其他参数
            
        Returns:
            AI回复内容
        """
        # 准备请求参数
        request_params = {
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
            "stream": stream,
            **kwargs
        }
        
        # 记录请求日志
        request_id = log_llm_request(
            provider="openai",
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
                response_content = response.choices[0].message.content
                
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
            
            logger.error(f"OpenAI API调用失败: {e}")
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
            provider="openai",
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
            
            logger.error(f"OpenAI流式API调用失败: {e}")
            raise
    
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
            logger.error(f"OpenAI连接测试失败: {e}")
            return False

# 全局客户端实例
_openai_client = None

def get_openai_client() -> OpenAIClient:
    """获取全局OpenAI客户端实例"""
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAIClient()
    return _openai_client

# 便捷函数
def openai_chat(messages: List[Dict[str, str]], **kwargs) -> str:
    """便捷的聊天函数"""
    return get_openai_client().chat(messages, **kwargs)

def openai_stream_chat(messages: List[Dict[str, str]], **kwargs) -> Generator[str, None, None]:
    """便捷的流式聊天函数"""
    return get_openai_client().stream_chat(messages, **kwargs)

if __name__ == "__main__":
    # 测试代码
    try:
        client = OpenAIClient()
        
        # 测试连接
        if client.test_connection():
            print("✅ OpenAI连接测试成功")
            
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
            print("❌ OpenAI连接测试失败")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}") 