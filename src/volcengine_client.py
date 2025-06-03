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
    from .simple_config import settings
    from .llm_logger import log_llm_request, log_llm_response, log_llm_stream_chunk
except ImportError:
    from dotenv import load_dotenv
    load_dotenv()
    
    class MockSettings:
        VOLCENGINE_API_KEY = os.getenv("VOLCENGINE_API_KEY", "")
        VOLCENGINE_MODEL_ID = os.getenv("VOLCENGINE_MODEL_ID", "ep-20250528194304-wbvcf")
        VOLCENGINE_BASE_URL = os.getenv("VOLCENGINE_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
        DEFAULT_TEMPERATURE = 0.7
        DEFAULT_MAX_TOKENS = 2000
        DEFAULT_TIMEOUT = 120  # 调整为2分钟，适应大模型响应时间
    
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
    timeout: int = 120  # 调整为2分钟，适应大模型响应时间

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
        chunk_index = 0
        full_response = ""
        
        try:
            stream = self.client.chat.completions.create(
                model=self.config.model_id,
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
            
            logger.error(f"火山引擎流式API调用失败: {e}")
            raise
    
    def analyze_requirement(self, content: str, **kwargs) -> str:
        """
        分析需求文档
        
        Args:
            content: 需求内容
            **kwargs: 其他参数
            
        Returns:
            分析结果
        """
        messages = [
            {
                "role": "system",
                "content": """你是一个专业的需求分析师。请分析以下需求文档，提取关键信息：

## 分析要求：
1. **核心功能点**：列出主要功能模块
2. **业务关键词**：提取业务相关的重要术语
3. **技术关键词**：识别技术栈和技术要求
4. **数据字段需求**：分析需要的数据结构
5. **接口需求**：识别需要的API接口
6. **潜在问题**：指出可能的风险和挑战
7. **实现建议**：提供技术实现建议

请用结构化的Markdown格式输出分析结果。"""
            },
            {
                "role": "user",
                "content": f"需求文档：\n{content}"
            }
        ]
        
        return self.chat(messages, temperature=0.3, **kwargs)
    
    def generate_api_design(self, requirement: str, **kwargs) -> str:
        """
        生成API设计
        
        Args:
            requirement: 需求内容
            **kwargs: 其他参数
            
        Returns:
            API设计文档
        """
        messages = [
            {
                "role": "system",
                "content": """你是一个专业的API设计师。请根据需求设计RESTful API：

## 设计要求：
1. **接口列表**：完整的API端点列表
2. **请求格式**：HTTP方法、URL、请求参数
3. **响应格式**：返回数据结构和状态码
4. **数据模型**：实体类和数据库表结构
5. **错误处理**：错误码和错误信息
6. **认证授权**：安全机制设计
7. **接口文档**：详细的API文档

请用JSON和Markdown混合格式输出设计结果。"""
            },
            {
                "role": "user",
                "content": f"需求：\n{requirement}"
            }
        ]
        
        return self.chat(messages, temperature=0.4, **kwargs)
    
    def generate_design_document(self, requirement: str, doc_type: str = "backend", **kwargs) -> str:
        """
        生成设计文档
        
        Args:
            requirement: 需求内容
            doc_type: 文档类型 (backend/frontend/database)
            **kwargs: 其他参数
            
        Returns:
            设计文档
        """
        if doc_type == "backend":
            system_prompt = """你是一个专业的后端架构师。请根据需求生成后端设计文档：

## 设计内容：
1. **系统架构**：整体架构设计
2. **技术栈**：后端技术选型
3. **数据库设计**：表结构和关系
4. **API设计**：接口规范
5. **业务逻辑**：核心业务流程
6. **安全设计**：认证授权机制
7. **性能优化**：缓存和优化策略
8. **部署方案**：部署架构

请用详细的Markdown格式输出设计文档。"""
        
        elif doc_type == "frontend":
            system_prompt = """你是一个专业的前端架构师。请根据需求生成前端设计文档：

## 设计内容：
1. **页面结构**：页面层次和导航
2. **组件设计**：可复用组件
3. **状态管理**：数据流设计
4. **UI/UX设计**：界面和交互设计
5. **技术栈**：前端技术选型
6. **路由设计**：页面路由规划
7. **API集成**：前后端接口对接
8. **性能优化**：前端优化策略

请用详细的Markdown格式输出设计文档。"""
        
        else:
            system_prompt = """你是一个专业的系统设计师。请根据需求生成系统设计文档：

## 设计内容：
1. **需求分析**：功能和非功能需求
2. **系统架构**：整体架构设计
3. **模块设计**：各模块职责
4. **数据设计**：数据模型和流程
5. **接口设计**：内外部接口
6. **安全设计**：安全策略
7. **性能设计**：性能指标和优化
8. **运维设计**：监控和部署

请用详细的Markdown格式输出设计文档。"""
        
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": f"需求：\n{requirement}"
            }
        ]
        
        return self.chat(messages, temperature=0.5, **kwargs)
    
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
                "content": f"""你是一个专业的{language}程序员。请根据描述生成高质量的代码：

## 代码要求：
1. **完整实现**：功能完整可运行
2. **代码规范**：遵循{language}编码规范
3. **注释文档**：详细的注释和文档
4. **错误处理**：完善的异常处理
5. **测试用例**：基本的测试代码
6. **使用示例**：代码使用示例

请确保代码质量高、可读性强、可维护性好。"""
            },
            {
                "role": "user",
                "content": f"请用{language}实现：\n{description}"
            }
        ]
        
        return self.chat(messages, temperature=0.2, **kwargs)
    
    def test_connection(self) -> bool:
        """
        测试连接
        
        Returns:
            连接是否成功
        """
        try:
            response = self.chat([
                {"role": "user", "content": "你好，请回复'连接成功'"}
            ])
            logger.info("火山引擎连接测试成功")
            return True
        except Exception as e:
            logger.error(f"火山引擎连接测试失败: {e}")
            return False

# 全局火山引擎客户端实例
_volcengine_client = None

def get_volcengine_client() -> VolcengineClient:
    """
    获取火山引擎客户端实例（单例模式）
    
    Returns:
        火山引擎客户端
    """
    global _volcengine_client
    if _volcengine_client is None:
        _volcengine_client = VolcengineClient()
    return _volcengine_client

# 便捷函数
def volcengine_chat(messages: List[Dict[str, str]], **kwargs) -> str:
    """火山引擎聊天便捷函数"""
    client = get_volcengine_client()
    return client.chat(messages, **kwargs)

def volcengine_stream_chat(messages: List[Dict[str, str]], **kwargs) -> Generator[str, None, None]:
    """火山引擎流式聊天便捷函数"""
    client = get_volcengine_client()
    yield from client.stream_chat(messages, **kwargs)

def volcengine_analyze_requirement(content: str, **kwargs) -> str:
    """火山引擎需求分析便捷函数"""
    client = get_volcengine_client()
    return client.analyze_requirement(content, **kwargs)

def volcengine_generate_api_design(requirement: str, **kwargs) -> str:
    """火山引擎API设计便捷函数"""
    client = get_volcengine_client()
    return client.generate_api_design(requirement, **kwargs)

def volcengine_generate_design_document(requirement: str, doc_type: str = "backend", **kwargs) -> str:
    """火山引擎设计文档生成便捷函数"""
    client = get_volcengine_client()
    return client.generate_design_document(requirement, doc_type, **kwargs)

def volcengine_generate_code(description: str, language: str = "python", **kwargs) -> str:
    """火山引擎代码生成便捷函数"""
    client = get_volcengine_client()
    return client.generate_code(description, language, **kwargs)

if __name__ == "__main__":
    # 测试代码
    print("🌋 火山引擎客户端测试")
    print("=" * 50)
    
    try:
        client = get_volcengine_client()
        
        # 测试连接
        if client.test_connection():
            print("✅ 连接测试成功")
            
            # 测试聊天
            response = client.chat([
                {"role": "user", "content": "你好，请简单介绍一下自己"}
            ])
            print(f"✅ 聊天测试: {response[:100]}...")
            
            # 测试需求分析
            analysis = client.analyze_requirement("开发一个用户管理系统")
            print(f"✅ 需求分析测试: {analysis[:100]}...")
            
        else:
            print("❌ 连接测试失败")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}") 