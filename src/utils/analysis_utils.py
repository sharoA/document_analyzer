#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析服务工具模块
提供各种实用工具类和函数
"""

import os
import re
import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class TextProcessor:
    """文本处理工具类"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """清理文本内容"""
        if not text:
            return ""
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        # 移除特殊字符（保留基本标点）
        text = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:()[\]{}"\'-]', '', text)
        # 去除首尾空白
        text = text.strip()
        
        return text
    
    @staticmethod
    def extract_sentences(text: str, max_sentences: int = 10) -> List[str]:
        """提取句子"""
        if not text:
            return []
        
        # 简单的句子分割（基于标点符号）
        sentences = re.split(r'[.!?。！？]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # 限制句子数量
        return sentences[:max_sentences]
    
    @staticmethod
    def count_words(text: str) -> Dict[str, int]:
        """统计词频"""
        if not text:
            return {}
        
        # 简单的词频统计
        words = re.findall(r'\b\w+\b', text.lower())
        word_count = {}
        
        for word in words:
            if len(word) > 1:  # 忽略单字符
                word_count[word] = word_count.get(word, 0) + 1
        
        # 按频率排序
        sorted_words = dict(sorted(word_count.items(), 
                                 key=lambda x: x[1], reverse=True))
        
        return sorted_words
    
    @staticmethod
    def extract_keywords(text: str, top_k: int = 10) -> List[str]:
        """提取关键词"""
        if not text:
            return []
        
        word_count = TextProcessor.count_words(text)
        
        # 过滤常见停用词
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            '的', '了', '在', '是', '我', '你', '他', '她', '它', '们', '这', '那',
            '有', '没', '不', '也', '就', '都', '要', '可以', '能够', '如果'
        }
        
        filtered_words = {word: count for word, count in word_count.items() 
                         if word not in stop_words and len(word) > 2}
        
        # 返回前top_k个关键词
        return list(filtered_words.keys())[:top_k]

class DataValidator:
    """数据验证工具类"""
    
    @staticmethod
    def validate_task_id(task_id: str) -> bool:
        """验证任务ID格式"""
        if not task_id:
            return False
        
        # 简单的UUID格式验证
        pattern = r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$'
        return bool(re.match(pattern, task_id, re.IGNORECASE))
    
    @staticmethod
    def validate_content(content: str, max_length: int = 100000) -> bool:
        """验证内容长度"""
        return bool(content) and len(content) <= max_length
    
    @staticmethod
    def validate_file_type(file_type: str) -> bool:
        """验证文件类型"""
        if not file_type:
            return False
        
        supported_types = ['txt', 'md', 'doc', 'docx', 'pdf', 'html', 'json', 'xml']
        return file_type.lower() in supported_types
    
    @staticmethod
    def validate_file_size(file_size: int, max_size: int = None) -> bool:
        """验证文件大小"""
        if max_size is None:
            # 从配置获取最大文件大小
            try:
                from ..resource.config import get_config
                config = get_config()
                max_size = config.get('file_upload.max_size', 50 * 1024 * 1024)
            except:
                max_size = 50 * 1024 * 1024  # 默认50MB
        
        return 0 < file_size <= max_size
    
    @staticmethod
    def validate_file_extension(filename: str) -> bool:
        """验证文件扩展名"""
        if not filename:
            return False
        
        try:
            from ..resource.config import get_config
            config = get_config()
            allowed_extensions = config.get('file_upload.allowed_extensions', [".txt", ".md"])
        except:
            allowed_extensions = [".txt", ".md", ".doc", ".docx", ".pdf"]
        
        file_ext = Path(filename).suffix.lower()
        return file_ext in allowed_extensions
    
    @staticmethod
    def validate_json_structure(data: Any, required_fields: List[str]) -> bool:
        """验证JSON结构"""
        if not isinstance(data, dict):
            return False
        
        for field in required_fields:
            if field not in data:
                return False
        
        return True

class HashGenerator:
    """哈希生成工具类"""
    
    @staticmethod
    def generate_content_hash(content: str) -> str:
        """生成内容哈希"""
        if not content:
            return ""
        
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    @staticmethod
    def generate_task_hash(task_id: str, content: str) -> str:
        """生成任务哈希"""
        combined = f"{task_id}:{content}"
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()
    
    @staticmethod
    def generate_file_hash(file_path: str) -> str:
        """生成文件哈希"""
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5()
                for chunk in iter(lambda: f.read(4096), b""):
                    file_hash.update(chunk)
                return file_hash.hexdigest()
        except Exception:
            return ""

class TimeUtils:
    """时间工具类"""
    
    @staticmethod
    def get_current_timestamp() -> str:
        """获取当前时间戳"""
        return datetime.now().isoformat()
    
    @staticmethod
    def format_duration(start_time: str, end_time: str = None) -> float:
        """计算时间差（秒）"""
        try:
            start = datetime.fromisoformat(start_time)
            end = datetime.fromisoformat(end_time) if end_time else datetime.now()
            return (end - start).total_seconds()
        except Exception:
            return 0.0
    
    @staticmethod
    def get_date_string(date_format: str = "%Y%m%d") -> str:
        """获取日期字符串"""
        return datetime.now().strftime(date_format)
    
    @staticmethod
    def get_datetime_string(datetime_format: str = "%Y%m%d_%H%M%S") -> str:
        """获取日期时间字符串"""
        return datetime.now().strftime(datetime_format)

class FileUtils:
    """文件工具类"""
    
    @staticmethod
    def ensure_directory(directory: str) -> bool:
        """确保目录存在"""
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"创建目录失败: {e}")
            return False
    
    @staticmethod
    def get_safe_filename(filename: str) -> str:
        """获取安全的文件名"""
        # 移除或替换不安全的字符
        safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # 限制长度
        if len(safe_filename) > 255:
            name, ext = Path(safe_filename).stem, Path(safe_filename).suffix
            safe_filename = name[:255-len(ext)] + ext
        return safe_filename
    
    @staticmethod
    def get_unique_filename(directory: str, filename: str) -> str:
        """获取唯一的文件名"""
        file_path = Path(directory) / filename
        if not file_path.exists():
            return filename
        
        name, ext = file_path.stem, file_path.suffix
        counter = 1
        
        while True:
            new_filename = f"{name}_{counter}{ext}"
            new_path = Path(directory) / new_filename
            if not new_path.exists():
                return new_filename
            counter += 1
    
    @staticmethod
    def safe_write_json(file_path: str, data: Any) -> bool:
        """安全写入JSON文件"""
        try:
            # 确保目录存在
            directory = Path(file_path).parent
            FileUtils.ensure_directory(str(directory))
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"写入JSON文件失败: {e}")
            return False
    
    @staticmethod
    def safe_read_json(file_path: str) -> Optional[Any]:
        """安全读取JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"读取JSON文件失败: {e}")
            return None
    
    @staticmethod
    def save_analysis_result(task_id: str, result: Dict[str, Any]) -> str:
        """保存分析结果到文件"""
        try:
            from ..resource.config import get_analysis_results_dir
            results_dir = get_analysis_results_dir()
            FileUtils.ensure_directory(results_dir)
            
            timestamp = TimeUtils.get_datetime_string()
            filename = f"{task_id}_{timestamp}.json"
            file_path = Path(results_dir) / filename
            
            if FileUtils.safe_write_json(str(file_path), result):
                return str(file_path)
            return ""
        except Exception as e:
            logger.error(f"保存分析结果失败: {e}")
            return ""

class LoggerUtils:
    """日志工具类"""
    
    @staticmethod
    def setup_logger(name: str, level: str = "INFO", 
                    log_file: str = None) -> logging.Logger:
        """设置日志器"""
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))
        
        # 避免重复添加处理器
        if logger.handlers:
            return logger
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 文件处理器
        if log_file:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            logger.addHandler(file_handler)
        
        # 设置格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        return logger
    
    @staticmethod
    def setup_analysis_logger(name: str) -> logging.Logger:
        """设置分析专用日志器"""
        try:
            from ..resource.config import get_logs_dir
            logs_dir = get_logs_dir()
            FileUtils.ensure_directory(logs_dir)
            
            log_file = Path(logs_dir) / f"{name}.log"
            return LoggerUtils.setup_logger(name, "INFO", str(log_file))
        except Exception as e:
            logger.error(f"设置分析日志器失败: {e}")
            return LoggerUtils.setup_logger(name, "INFO")

class ErrorHandler:
    """错误处理工具类"""
    
    @staticmethod
    def safe_execute(func, *args, default_return=None, **kwargs):
        """安全执行函数"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"执行函数 {func.__name__} 时出错: {e}")
            return default_return
    
    @staticmethod
    def format_error(error: Exception) -> Dict[str, Any]:
        """格式化错误信息"""
        return {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": TimeUtils.get_current_timestamp()
        }
    
    @staticmethod
    def log_error(error: Exception, context: str = ""):
        """记录错误日志"""
        error_info = ErrorHandler.format_error(error)
        logger.error(f"错误上下文: {context}, 错误信息: {error_info}")

# 便捷函数
def clean_text(text: str) -> str:
    """便捷的文本清理函数"""
    return TextProcessor.clean_text(text)

def validate_input(task_id: str, content: str, file_type: str) -> Dict[str, bool]:
    """
    验证输入参数
    使用配置文件中的参数进行验证
    """
    try:
        # 获取配置
        from ..resource.config import get_config
        config = get_config()
        
        # 获取验证配置参数
        validation_config = config.get_validation_config() if hasattr(config, 'get_validation_config') else {}
        
        # 默认验证参数（如果配置文件中没有）
        max_content_length = validation_config.get('max_content_length', 10 * 1024 * 1024)  # 10MB
        min_content_length = validation_config.get('min_content_length', 1)
        allowed_file_types = validation_config.get('allowed_file_types', [
            'text/plain', 'application/pdf', 'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/markdown', 'application/json', 'text/html', 'application/xml'
        ])
        
        validation_result = {
            'task_id_valid': bool(task_id and len(task_id.strip()) > 0),
            'content_valid': bool(content and min_content_length <= len(content) <= max_content_length),
            'file_type_valid': bool(file_type and (
                file_type in allowed_file_types or 
                any(allowed_type in file_type.lower() for allowed_type in ['text', 'pdf', 'word', 'json', 'xml', 'html'])
            ))
        }
        
        return validation_result
        
    except Exception as e:
        # 如果配置读取失败，使用宽松的验证
        return {
            'task_id_valid': bool(task_id),
            'content_valid': bool(content),  # 宽松验证
            'file_type_valid': True  # 宽松验证，允许所有文件类型
        }

def validate_file_upload(filename: str, file_size: int) -> Dict[str, bool]:
    """便捷的文件上传验证函数"""
    return {
        "filename_valid": bool(filename),
        "extension_valid": DataValidator.validate_file_extension(filename),
        "size_valid": DataValidator.validate_file_size(file_size)
    }

def generate_analysis_id(task_id: str, content: str) -> str:
    """便捷的分析ID生成函数"""
    return HashGenerator.generate_task_hash(task_id, content)

def get_timestamp() -> str:
    """便捷的时间戳获取函数"""
    return TimeUtils.get_current_timestamp()

def setup_analysis_logger(name: str, log_file: str = None) -> logging.Logger:
    """便捷的分析日志器设置函数"""
    return LoggerUtils.setup_analysis_logger(name)

def save_analysis_result(task_id: str, result: Dict[str, Any]) -> str:
    """便捷的分析结果保存函数"""
    return FileUtils.save_analysis_result(task_id, result)

def ensure_analysis_directories():
    """确保分析相关目录存在"""
    try:
        from ..resource.config import (
            get_logs_dir,
            get_uploads_dir,
            get_temp_dir,
            get_analysis_results_dir,
            get_cache_dir
        )
        
        directories = [
            get_logs_dir(),
            get_uploads_dir(),
            get_temp_dir(),
            get_analysis_results_dir(),
            get_cache_dir()
        ]
        
        for directory in directories:
            FileUtils.ensure_directory(directory)
            
        logger.info("分析目录初始化完成")
        
    except Exception as e:
        logger.error(f"初始化分析目录失败: {e}")
        # 使用默认目录
        default_dirs = ["logs", "uploads", "uploads/temp", "uploads/analysis_results", "uploads/cache"]
        for directory in default_dirs:
            FileUtils.ensure_directory(directory) 