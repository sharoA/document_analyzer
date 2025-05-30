#!/usr/bin/env python3
"""
大模型交互日志记录器
专门用于记录与大模型的请求和响应
"""

import os
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

class LLMLogger:
    """大模型交互日志记录器"""
    
    def __init__(self, log_dir: str = "logs"):
        """
        初始化日志记录器
        
        Args:
            log_dir: 日志目录
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 创建日志记录器
        self.logger = logging.getLogger("llm_interaction")
        self.logger.setLevel(logging.INFO)
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """设置日志处理器"""
        # 文件处理器 - 详细日志
        log_file = self.log_dir / f"llm_interactions_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # JSON格式处理器 - 结构化日志
        json_log_file = self.log_dir / f"llm_interactions_{datetime.now().strftime('%Y%m%d')}.json"
        json_handler = logging.FileHandler(json_log_file, encoding='utf-8')
        json_handler.setLevel(logging.INFO)
        
        # 控制台处理器 - 简要信息
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 设置格式
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s - LLM - %(message)s'
        )
        
        file_handler.setFormatter(detailed_formatter)
        json_handler.setFormatter(logging.Formatter('%(message)s'))
        console_handler.setFormatter(simple_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(json_handler)
        self.logger.addHandler(console_handler)
        
        # 保存JSON处理器引用，用于结构化日志
        self.json_handler = json_handler
    
    def log_request(
        self,
        provider: str,
        model: str,
        messages: List[Dict[str, str]],
        parameters: Dict[str, Any],
        request_id: Optional[str] = None
    ) -> str:
        """
        记录请求日志
        
        Args:
            provider: 提供商名称 (volcengine, openai, deepseek等)
            model: 模型名称
            messages: 消息列表
            parameters: 请求参数
            request_id: 请求ID
            
        Returns:
            生成的请求ID
        """
        if request_id is None:
            request_id = f"{provider}_{int(time.time() * 1000)}"
        
        timestamp = datetime.now().isoformat()
        
        # 详细日志
        self.logger.info(f"🚀 LLM请求开始 - Provider: {provider}, Model: {model}, ID: {request_id}")
        
        # 结构化日志
        log_data = {
            "type": "request",
            "timestamp": timestamp,
            "request_id": request_id,
            "provider": provider,
            "model": model,
            "messages": messages,
            "parameters": parameters,
            "message_count": len(messages),
            "total_chars": sum(len(msg.get("content", "")) for msg in messages)
        }
        
        # 写入JSON日志
        json_log_line = json.dumps(log_data, ensure_ascii=False, separators=(',', ':'))
        self.json_handler.stream.write(json_log_line + '\n')
        self.json_handler.stream.flush()
        
        return request_id
    
    def log_response(
        self,
        request_id: str,
        response_content: str,
        response_time: float,
        token_usage: Optional[Dict[str, int]] = None,
        error: Optional[str] = None
    ):
        """
        记录响应日志
        
        Args:
            request_id: 请求ID
            response_content: 响应内容
            response_time: 响应时间（秒）
            token_usage: Token使用情况
            error: 错误信息
        """
        timestamp = datetime.now().isoformat()
        
        if error:
            self.logger.error(f"❌ LLM请求失败 - ID: {request_id}, Error: {error}")
            status = "error"
        else:
            self.logger.info(f"✅ LLM请求完成 - ID: {request_id}, 耗时: {response_time:.2f}s, 响应长度: {len(response_content)}字符")
            status = "success"
        
        # 结构化日志
        log_data = {
            "type": "response",
            "timestamp": timestamp,
            "request_id": request_id,
            "status": status,
            "response_time": response_time,
            "response_length": len(response_content) if response_content else 0,
            "response_content": response_content,
            "token_usage": token_usage,
            "error": error
        }
        
        # 写入JSON日志
        json_log_line = json.dumps(log_data, ensure_ascii=False, separators=(',', ':'))
        self.json_handler.stream.write(json_log_line + '\n')
        self.json_handler.stream.flush()
    
    def log_stream_chunk(
        self,
        request_id: str,
        chunk_content: str,
        chunk_index: int
    ):
        """
        记录流式响应块
        
        Args:
            request_id: 请求ID
            chunk_content: 块内容
            chunk_index: 块索引
        """
        timestamp = datetime.now().isoformat()
        
        # 结构化日志
        log_data = {
            "type": "stream_chunk",
            "timestamp": timestamp,
            "request_id": request_id,
            "chunk_index": chunk_index,
            "chunk_content": chunk_content,
            "chunk_length": len(chunk_content)
        }
        
        # 写入JSON日志
        json_log_line = json.dumps(log_data, ensure_ascii=False, separators=(',', ':'))
        self.json_handler.stream.write(json_log_line + '\n')
        self.json_handler.stream.flush()
    
    def log_conversation_summary(
        self,
        session_id: str,
        total_requests: int,
        total_response_time: float,
        total_tokens: Optional[int] = None
    ):
        """
        记录对话会话总结
        
        Args:
            session_id: 会话ID
            total_requests: 总请求数
            total_response_time: 总响应时间
            total_tokens: 总Token数
        """
        timestamp = datetime.now().isoformat()
        
        self.logger.info(f"📊 会话总结 - Session: {session_id}, 请求数: {total_requests}, 总耗时: {total_response_time:.2f}s")
        
        # 结构化日志
        log_data = {
            "type": "session_summary",
            "timestamp": timestamp,
            "session_id": session_id,
            "total_requests": total_requests,
            "total_response_time": total_response_time,
            "average_response_time": total_response_time / total_requests if total_requests > 0 else 0,
            "total_tokens": total_tokens
        }
        
        # 写入JSON日志
        json_log_line = json.dumps(log_data, ensure_ascii=False, separators=(',', ':'))
        self.json_handler.stream.write(json_log_line + '\n')
        self.json_handler.stream.flush()

# 全局日志记录器实例
_llm_logger = None

def get_llm_logger() -> LLMLogger:
    """
    获取大模型日志记录器实例（单例模式）
    
    Returns:
        LLMLogger实例
    """
    global _llm_logger
    if _llm_logger is None:
        _llm_logger = LLMLogger()
    return _llm_logger

# 便捷函数
def log_llm_request(provider: str, model: str, messages: List[Dict[str, str]], 
                   parameters: Dict[str, Any], request_id: Optional[str] = None) -> str:
    """记录LLM请求的便捷函数"""
    logger = get_llm_logger()
    return logger.log_request(provider, model, messages, parameters, request_id)

def log_llm_response(request_id: str, response_content: str, response_time: float,
                    token_usage: Optional[Dict[str, int]] = None, error: Optional[str] = None):
    """记录LLM响应的便捷函数"""
    logger = get_llm_logger()
    logger.log_response(request_id, response_content, response_time, token_usage, error)

def log_llm_stream_chunk(request_id: str, chunk_content: str, chunk_index: int):
    """记录LLM流式响应块的便捷函数"""
    logger = get_llm_logger()
    logger.log_stream_chunk(request_id, chunk_content, chunk_index)

def log_conversation_summary(session_id: str, total_requests: int, 
                           total_response_time: float, total_tokens: Optional[int] = None):
    """记录对话会话总结的便捷函数"""
    logger = get_llm_logger()
    logger.log_conversation_summary(session_id, total_requests, total_response_time, total_tokens) 