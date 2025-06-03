#!/usr/bin/env python3
"""
OpenAI客户端组件
支持火山引擎、OpenAI、DeepSeek等多种兼容API
默认使用火山引擎API
"""

import os
import time
import logging
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass

try:
    from openai import OpenAI
except ImportError:
    raise ImportError("请安装OpenAI包: pip install openai")

# 导入配置
try:
    from .config import settings
    from .llm_logger import log_llm_request, log_llm_response, log_llm_stream_chunk
except ImportError:
    # 如果在测试环境中，直接加载环境变量
    from dotenv import load_dotenv
    load_dotenv()
    
    class MockSettings:
        VOLCENGINE_API_KEY = os.getenv("VOLCENGINE_API_KEY", "")
        VOLCENGINE_MODEL_ID = os.getenv("VOLCENGINE_MODEL_ID", "ep-20250528194304-wbvcf")
        VOLCENGINE_BASE_URL = os.getenv("VOLCENGINE_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
        DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
        DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        DEFAULT_TEMPERATURE = 0.7
        DEFAULT_MAX_TOKENS = 2000
        DEFAULT_TIMEOUT = 120  # 调整为2分钟，适应大模型响应时间
    
    settings = MockSettings()
    
    # 如果导入失败，创建空的日志函数
    def log_llm_request(*args, **kwargs):
        return f"openai_{int(time.time() * 1000)}"
    
    def log_llm_response(*args, **kwargs):
        pass
    
    def log_llm_stream_chunk(*args, **kwargs):
        pass

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AIClientConfig:
    """AI客户端配置"""
    api_key: str
    base_url: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 120  # 调整为2分钟，适应大模型响应时间

class OpenAIClient:
    """OpenAI兼容客户端"""
    
    def __init__(self, config: AIClientConfig):
        """
        初始化OpenAI客户端
        
        Args:
            config: API配置
        """
        self.config = config
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout
        )
        
        logger.info(f"OpenAI客户端初始化成功: {config.model}")
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[str, Any]:
        """
        聊天完成
        
        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式输出
            **kwargs: 其他参数
            
        Returns:
            响应内容或流对象
        """
        # 准备请求参数
        used_model = model or self.config.model
        request_params = {
            "model": used_model,
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
            "stream": stream,
            **kwargs
        }
        
        # 记录请求日志
        request_id = log_llm_request(
            provider=self.config.model.lower().replace(" ", "_"),
            model=used_model,
            messages=messages,
            parameters=request_params
        )
        
        start_time = time.time()
        
        try:
            response = self.client.chat.completions.create(
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
            
            logger.error(f"API调用失败: {e}")
            raise
    
    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs
    ):
        """
        流式聊天
        
        Args:
            messages: 消息列表
            model: 模型名称
            **kwargs: 其他参数
            
        Yields:
            流式响应内容
        """
        # 准备请求参数
        used_model = model or self.config.model
        request_params = {
            "model": used_model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "stream": True,
            **kwargs
        }
        
        # 记录请求日志
        request_id = log_llm_request(
            provider=self.config.model.lower().replace(" ", "_"),
            model=used_model,
            messages=messages,
            parameters=request_params
        )
        
        start_time = time.time()
        chunk_index = 0
        full_response = ""
        
        try:
            stream = self.client.chat.completions.create(
                messages=messages,
                **request_params
            )
            
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    chunk_content = chunk.choices[0].delta.content
                    full_response += chunk_content
                    
                    # 记录流式响应块
                    log_llm_stream_chunk(
                        request_id=request_id,
                        chunk_content=chunk_content,
                        chunk_index=chunk_index
                    )
                    
                    chunk_index += 1
                    yield chunk_content
            
            # 记录完整响应
            response_time = time.time() - start_time
            log_llm_response(
                request_id=request_id,
                response_content=full_response,
                response_time=response_time,
                token_usage=None  # 流式响应通常不返回token使用情况
            )
                    
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = str(e)
            
            # 记录错误日志
            log_llm_response(
                request_id=request_id,
                response_content=full_response,
                response_time=response_time,
                error=error_msg
            )
            
            logger.error(f"流式API调用失败: {e}")
            raise

class MultiAPIManager:
    """多API管理器"""
    
    def __init__(self):
        """初始化多API管理器"""
        self.clients = {}
        self.default_client = None
        self._load_configs()
    
    def _load_configs(self):
        """加载API配置"""
        # 火山引擎配置（优先级最高）
        if settings.VOLCENGINE_API_KEY:
            config = AIClientConfig(
                api_key=settings.VOLCENGINE_API_KEY,
                base_url=settings.VOLCENGINE_BASE_URL,
                model=settings.VOLCENGINE_MODEL_ID,
                temperature=settings.DEFAULT_TEMPERATURE,
                max_tokens=settings.DEFAULT_MAX_TOKENS,
                timeout=settings.DEFAULT_TIMEOUT
            )
            self.add_client("volcengine", config)
        
        # DeepSeek配置
        if settings.DEEPSEEK_API_KEY:
            config = AIClientConfig(
                api_key=settings.DEEPSEEK_API_KEY,
                base_url=settings.DEEPSEEK_BASE_URL,
                model="deepseek-chat",
                temperature=settings.DEFAULT_TEMPERATURE,
                max_tokens=settings.DEFAULT_MAX_TOKENS,
                timeout=settings.DEFAULT_TIMEOUT
            )
            self.add_client("deepseek", config)
        
        # OpenAI配置
        if settings.OPENAI_API_KEY:
            config = AIClientConfig(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL,
                model="gpt-3.5-turbo",
                temperature=settings.DEFAULT_TEMPERATURE,
                max_tokens=settings.DEFAULT_MAX_TOKENS,
                timeout=settings.DEFAULT_TIMEOUT
            )
            self.add_client("openai", config)
        
        # 设置默认客户端（优先使用火山引擎）
        if "volcengine" in self.clients:
            self.default_client = "volcengine"
        elif "deepseek" in self.clients:
            self.default_client = "deepseek"
        elif "openai" in self.clients:
            self.default_client = "openai"
    
    def add_client(self, name: str, config: AIClientConfig):
        """
        添加客户端
        
        Args:
            name: 客户端名称
            config: API配置
        """
        try:
            client = OpenAIClient(config)
            self.clients[name] = client
            logger.info(f"添加客户端成功: {name}")
        except Exception as e:
            logger.error(f"添加客户端失败 {name}: {e}")
    
    def get_client(self, name: Optional[str] = None) -> OpenAIClient:
        """
        获取客户端
        
        Args:
            name: 客户端名称，为None时使用默认客户端
            
        Returns:
            OpenAI客户端
        """
        client_name = name or self.default_client
        
        if not client_name or client_name not in self.clients:
            available = list(self.clients.keys())
            raise ValueError(f"客户端 {client_name} 不存在，可用客户端: {available}")
        
        return self.clients[client_name]
    
    def list_clients(self) -> List[str]:
        """获取可用客户端列表"""
        return list(self.clients.keys())
    
    def test_client(self, name: str) -> bool:
        """
        测试客户端连接
        
        Args:
            name: 客户端名称
            
        Returns:
            测试是否成功
        """
        try:
            client = self.get_client(name)
            messages = [{"role": "user", "content": "Hello"}]
            response = client.chat_completion(messages)
            logger.info(f"客户端 {name} 测试成功")
            return True
        except Exception as e:
            logger.error(f"客户端 {name} 测试失败: {e}")
            return False

# 全局API管理器实例
api_manager = MultiAPIManager()

def get_openai_client(name: Optional[str] = None) -> OpenAIClient:
    """
    获取OpenAI客户端（便捷函数）
    
    Args:
        name: 客户端名称，默认使用火山引擎
        
    Returns:
        OpenAI客户端
    """
    return api_manager.get_client(name)

def chat_with_ai(
    messages: List[Dict[str, str]],
    client_name: Optional[str] = None,
    **kwargs
) -> str:
    """
    与AI聊天（便捷函数）
    
    Args:
        messages: 消息列表
        client_name: 客户端名称，默认使用火山引擎
        **kwargs: 其他参数
        
    Returns:
        AI回复
    """
    client = get_openai_client(client_name)
    return client.chat_completion(messages, **kwargs)

def stream_chat_with_ai(
    messages: List[Dict[str, str]],
    client_name: Optional[str] = None,
    **kwargs
):
    """
    流式聊天（便捷函数）
    
    Args:
        messages: 消息列表
        client_name: 客户端名称，默认使用火山引擎
        **kwargs: 其他参数
        
    Yields:
        流式响应
    """
    client = get_openai_client(client_name)
    yield from client.stream_chat(messages, **kwargs)

# 预定义的任务函数
def analyze_requirement(content: str, client_name: Optional[str] = None) -> str:
    """
    分析需求文档
    
    Args:
        content: 需求内容
        client_name: 客户端名称，默认使用火山引擎
        
    Returns:
        分析结果
    """
    messages = [
        {
            "role": "system",
            "content": """你是一个专业的需求分析师。请分析以下需求文档，提取：
1. 核心功能点
2. 业务关键词
3. 技术关键词
4. 数据字段需求
5. 潜在问题和建议

请用结构化的方式输出分析结果。"""
        },
        {
            "role": "user",
            "content": f"需求文档：\n{content}"
        }
    ]
    
    return chat_with_ai(messages, client_name, temperature=0.3)

def generate_api_design(requirement: str, client_name: Optional[str] = None) -> str:
    """
    生成API设计
    
    Args:
        requirement: 需求内容
        client_name: 客户端名称，默认使用火山引擎
        
    Returns:
        API设计
    """
    messages = [
        {
            "role": "system",
            "content": """你是一个专业的API设计师。请根据需求设计RESTful API，包括：
1. 接口列表
2. 请求/响应格式
3. 数据模型
4. 错误处理

请用JSON格式输出API设计。"""
        },
        {
            "role": "user",
            "content": f"需求：\n{requirement}"
        }
    ]
    
    return chat_with_ai(messages, client_name, temperature=0.4)

def generate_code(description: str, language: str = "python", client_name: Optional[str] = None) -> str:
    """
    生成代码
    
    Args:
        description: 代码描述
        language: 编程语言
        client_name: 客户端名称，默认使用火山引擎
        
    Returns:
        生成的代码
    """
    messages = [
        {
            "role": "system",
            "content": f"""你是一个专业的{language}程序员。请根据描述生成高质量的代码，包括：
1. 完整的代码实现
2. 必要的注释
3. 错误处理
4. 使用示例

请确保代码规范、可读性强。"""
        },
        {
            "role": "user",
            "content": f"请用{language}实现：\n{description}"
        }
    ]
    
    return chat_with_ai(messages, client_name, temperature=0.2)

if __name__ == "__main__":
    # 测试代码
    print("🤖 OpenAI客户端组件测试")
    print("=" * 50)
    
    # 列出可用客户端
    clients = api_manager.list_clients()
    print(f"📋 可用客户端: {clients}")
    
    if not clients:
        print("❌ 没有可用的客户端，请设置API密钥")
    else:
        # 测试默认客户端
        default_client = api_manager.default_client
        print(f"🎯 默认客户端: {default_client}")
        
        # 测试聊天功能
        try:
            response = chat_with_ai([
                {"role": "user", "content": "你好，请简单介绍一下自己"}
            ])
            print(f"✅ 聊天测试成功: {response[:100]}...")
        except Exception as e:
            print(f"❌ 聊天测试失败: {e}")
        
        # 测试需求分析
        try:
            analysis = analyze_requirement("开发一个用户管理系统，包含注册、登录、个人信息管理功能")
            print(f"✅ 需求分析测试成功: {analysis[:100]}...")
        except Exception as e:
            print(f"❌ 需求分析测试失败: {e}") 