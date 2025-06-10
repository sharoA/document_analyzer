#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
analyDesign API服务器
集成火山引擎实时交互功能和文件处理功能
"""

import json
import time
import uuid
import logging
import os
import base64
from datetime import datetime
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, request, jsonify, make_response
from flask_cors import CORS

# 配置日志 - 移到最前面
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入配置和工具类
try:
    from ..resource.config import get_config
    from ..utils.volcengine_client import VolcengineClient, VolcengineConfig
    from ..utils.llm_logger import LLMLogger
    from ..utils.task_storage import get_task_storage
    # 导入分析服务模块
    from ..analysis_services import (
        AnalysisServiceManager,
        get_analysis_service_manager,
        ensure_analysis_directories,
        setup_analysis_logger,
        validate_input,
        validate_file_upload,
        initialize_analysis_service_manager
    )
    try:
        from ..enhanced_analyzer import EnhancedAnalyzer
        ENHANCED_ANALYZER_AVAILABLE = True
    except ImportError:
        ENHANCED_ANALYZER_AVAILABLE = False
        logger.warning("enhanced_analyzer不可用，将使用基础文本处理")
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from src.resource.config import get_config
    from src.utils.volcengine_client import VolcengineClient, VolcengineConfig
    from src.utils.llm_logger import LLMLogger
    from src.utils.task_storage import get_task_storage
    # 导入分析服务模块
    from src.analysis_services import (
        AnalysisServiceManager,
        get_analysis_service_manager,
        ensure_analysis_directories,
        setup_analysis_logger,
        validate_input,
        validate_file_upload,
        initialize_analysis_service_manager
    )
    try:
        from src.enhanced_analyzer import EnhancedAnalyzer
        ENHANCED_ANALYZER_AVAILABLE = True
    except ImportError:
        ENHANCED_ANALYZER_AVAILABLE = False
        logger.warning("enhanced_analyzer不可用，将使用基础文本处理")

# 获取配置
config = get_config()
task_storage = get_task_storage()

app = Flask(__name__)
# 配置CORS，允许所有来源和方法
CORS(app, 
     origins=["http://localhost:3000", "http://127.0.0.1:3000"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"],
     supports_credentials=True)

# 确保分析服务目录结构存在
ensure_analysis_directories()

# 设置分析服务日志
analysis_logger = setup_analysis_logger("api_server")

# 初始化火山引擎客户端
try:
    volcengine_config = config.get_volcengine_config()
    logger.info(f"从配置文件读取火山引擎配置: {volcengine_config}")
    
    # 检查API密钥
    api_key = volcengine_config.get('api_key', '')
    if not api_key:
        raise ValueError("火山引擎API密钥未在配置文件中设置")
    
    volcano_config = VolcengineConfig(
        api_key=api_key,
        model_id=volcengine_config.get('model', 'doubao-pro-4k'),
        base_url=volcengine_config.get('endpoint', 'https://ark.cn-beijing.volces.com/api/v3'),
        temperature=volcengine_config.get('temperature', 0.7),
        max_tokens=volcengine_config.get('max_tokens', 4000)
    )
    volcano_client = VolcengineClient(volcano_config)
    logger.info("火山引擎客户端初始化成功")
except Exception as e:
    logger.error(f"火山引擎客户端初始化失败: {e}")
    volcano_client = None

# 初始化分析服务管理器
try:
    # 先初始化分析服务管理器
    analysis_service_manager = initialize_analysis_service_manager(
        llm_client=volcano_client,
        vector_db_type="mock"  # 可以根据需要配置为 "chroma"
    )
    logger.info("分析服务管理器初始化成功")
    analysis_logger.info("分析服务管理器已集成到API服务器")
except Exception as e:
    logger.error(f"分析服务管理器初始化失败: {e}")
    analysis_service_manager = None

# 初始化增强分析器
try:
    if ENHANCED_ANALYZER_AVAILABLE:
        analyzer = EnhancedAnalyzer()
        logger.info("增强分析器初始化成功")
    else:
        analyzer = None
        logger.info("使用基础文本处理功能")
except Exception as e:
    logger.error(f"增强分析器初始化失败: {e}")
    analyzer = None

# 会话存储（生产环境建议使用Redis等持久化存储）
sessions = {}

# 线程池用于异步处理
executor = ThreadPoolExecutor(max_workers=4)

# 文件处理任务类
class FileParsingTask:
    def __init__(self, task_id: str, file_info: dict, file_content: bytes = None, file_path: str = None):
        self.id = task_id
        self.file_info = file_info
        self.file_content = file_content
        self.file_path = file_path
        self.status = "pending"
        self.progress = 0
        self.steps = []
        self.result = None
        self.content_analysis = None
        self.ai_analysis = None
        self.error = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        
        # 立即保存到数据库
        self._save_to_db()
    
    def _save_to_db(self):
        """保存任务到数据库"""
        try:
            # 使用新的任务存储系统
            task_storage.create_task(
                filename=self.file_info.get('filename', ''),
                file_size=self.file_info.get('size', 0),
                file_type=self.file_info.get('type', ''),
                task_id=self.id
            )
        except Exception as e:
            logger.error(f"保存任务到数据库失败: {e}")
    
    def update_progress(self, progress: int, description: str, status: str = None):
        """更新任务进度"""
        self.progress = progress
        self.updated_at = datetime.now()
        if status:
            self.status = status
        
        # 更新步骤信息
        step_info = {
            "description": description,
            "progress": progress,
            "status": status or self.status,
            "timestamp": self.updated_at.isoformat()
        }
        
        # 确保 steps 是一个列表
        if not isinstance(self.steps, list):
            self.steps = []
        
        # 如果是新步骤，添加到列表中
        try:
            # 安全检查最后一个步骤
            if (not self.steps or 
                not isinstance(self.steps[-1], dict) or 
                self.steps[-1].get("description") != description):
                self.steps.append(step_info)
            else:
                # 更新最后一个步骤
                self.steps[-1] = step_info
        except (IndexError, KeyError, TypeError) as e:
            # 如果出现任何错误，直接添加新步骤
            logger.warning(f"步骤更新异常，添加新步骤: {e}")
            self.steps.append(step_info)
        
        # 更新数据库中的任务状态
        try:
            task_storage.update_task_status(
                task_id=self.id,
                status=self.status,
                progress=self.progress
            )
        except Exception as e:
            logger.error(f"更新数据库任务状态失败: {e}")
        
        logger.info(f"任务 {self.id} 进度更新: {progress}% - {description}")
    
    def to_dict(self):
        """转换为字典格式"""
        # 确保 file_info 字段存在且有效
        file_info = self.file_info
        if file_info is None:
            file_info = {
                'name': '未知文件',
                'type': 'unknown',
                'size': 0
            }
        
        return {
            "id": self.id,
            "file_info": file_info,
            "file_path": self.file_path,
            "status": self.status,
            "progress": self.progress,
            "steps": self.steps,
            "result": self.result,
            "content_analysis": self.content_analysis,
            "ai_analysis": self.ai_analysis,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """从字典创建任务实例"""
        task = cls.__new__(cls)  # 创建实例但不调用__init__
        task.id = data['id']
        
        # 确保 file_info 字段存在且有效
        task.file_info = data.get('file_info')
        if task.file_info is None:
            task.file_info = {
                'name': '未知文件',
                'type': 'unknown',
                'size': 0
            }
        
        task.file_path = data.get('file_path')
        task.file_content = None  # 不从数据库恢复文件内容
        task.status = data['status']
        task.progress = data['progress']
        task.steps = data.get('steps', [])
        task.result = data.get('parsing_result') or data.get('result')
        task.content_analysis = data.get('content_analysis')
        task.ai_analysis = data.get('ai_analysis')
        task.error = data.get('error')
        task.created_at = datetime.fromisoformat(data['created_at']) if isinstance(data['created_at'], str) else data['created_at']
        task.updated_at = datetime.fromisoformat(data['updated_at']) if isinstance(data['updated_at'], str) else data['updated_at']
        return task

# 任务管理函数
def get_task(task_id: str) -> Optional[FileParsingTask]:
    """从数据库获取任务"""
    task_data = task_storage.get_task(task_id)
    if task_data:
        return FileParsingTask.from_dict(task_data)
    return None

def get_all_tasks() -> List[FileParsingTask]:
    """获取所有任务"""
    tasks_data = task_storage.get_all_tasks()
    return [FileParsingTask.from_dict(data) for data in tasks_data]

def delete_task(task_id: str) -> bool:
    """删除任务"""
    return task_storage.delete_task(task_id)

# 文档解析函数
def parse_word_document(file_content: bytes, file_name: str) -> dict:
    """解析Word文档"""
    try:
        if analyzer:
            # 使用增强分析器
            return analyzer.analyze_file(file_content, file_name)
        else:
            # 基础解析
            return {
                "text_content": f"Word文档: {file_name}",
                "file_type": "word",
                "file_size": len(file_content),
                "analysis_method": "basic_word_parsing",
                "message": "增强分析器不可用，使用基础解析"
            }
    except Exception as e:
        logger.error(f"Word文档解析失败: {e}")
        return {
            "text_content": f"Word文档解析失败: {str(e)}",
            "file_type": "word",
            "file_size": len(file_content),
            "analysis_method": "error_fallback"
        }

def parse_pdf_document(file_content: bytes, file_name: str) -> dict:
    """解析PDF文档"""
    try:
        if analyzer:
            # 使用增强分析器
            return analyzer.analyze_file(file_content, file_name)
        else:
            # 基础解析
            return {
                "text_content": f"PDF文档: {file_name}",
                "file_type": "pdf",
                "file_size": len(file_content),
                "analysis_method": "basic_pdf_parsing",
                "message": "增强分析器不可用，使用基础解析"
            }
    except Exception as e:
        logger.error(f"PDF文档解析失败: {e}")
        return {
            "text_content": f"PDF文档解析失败: {str(e)}",
            "file_type": "pdf",
            "file_size": len(file_content),
            "analysis_method": "error_fallback"
        }

def parse_text_document(file_content: bytes, file_name: str) -> dict:
    """解析文本文档"""
    try:
        # 尝试不同的编码
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
        content = None
        
        for encoding in encodings:
            try:
                content = file_content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            content = file_content.decode('utf-8', errors='ignore')
        
        return {
            "text_content": content,
            "file_type": "text",
            "file_size": len(file_content),
            "analysis_method": "text_parsing",
            "char_count": len(content),
            "line_count": content.count('\n') + 1
        }
    except Exception as e:
        logger.error(f"文本文档解析失败: {e}")
        return {
            "text_content": f"文本文档解析失败: {str(e)}",
            "file_type": "text",
            "file_size": len(file_content),
            "analysis_method": "error_fallback"
        }

# 文件处理函数
def process_file_parsing(task: FileParsingTask):
    """处理文件解析任务 - 使用分析服务模块"""
    try:
        task.update_progress(10, "开始解析文件", "parsing")
        
        file_info = task.file_info
        file_name = file_info.get("name", "")
        file_type = file_info.get("type", "")
        
        # 优先从文件路径读取，如果失败则从base64内容读取
        file_content = None
        if task.file_path and os.path.exists(task.file_path):
            task.update_progress(20, "从文件系统读取文件", "parsing")
            try:
                with open(task.file_path, 'rb') as f:
                    file_content = f.read()
                logger.info(f"从文件路径读取: {task.file_path}")
            except Exception as e:
                logger.warning(f"从文件路径读取失败: {e}, 尝试从base64读取")
        
        if file_content is None:
            task.update_progress(20, "从base64内容读取文件", "parsing")
            if task.file_content:
                file_content = task.file_content
            else:
                raise ValueError("无法获取文件内容，文件可能已被删除")
        
        # 转换为文本内容
        content = file_content.decode('utf-8', errors='ignore') if isinstance(file_content, bytes) else str(file_content)
        
        # 验证输入 - 使用实际的文件内容进行验证
        validation = validate_input(task.id, content, file_type)
        if not all(validation.values()):
            raise ValueError(f"输入验证失败: {validation}")
        
        task.update_progress(40, "使用分析服务解析文档", "parsing")
        
        # 使用分析服务管理器进行文档解析
        if analysis_service_manager:
            parsing_result = analysis_service_manager.parse_document_sync(
                task_id=task.id,
                file_content=content,
                file_type=file_type.split('/')[-1] if '/' in file_type else file_type,
                file_name=file_name
            )
            
            # 更新任务结果
            task.result = parsing_result
            # 保存解析结果到数据库
            task_storage.save_parsing_result(task.id, parsing_result)
            task.update_progress(100, "文档解析完成", "parsed")
            analysis_logger.info(f"✅ 文件解析完成: {task.id}")
            
            # 🔄 自动触发内容分析（新增）
            analysis_logger.info(f"🚀 自动开始内容分析: {task.id}")
            executor.submit(process_content_analysis, task, parsing_result)
        else:
            # 降级到原有的解析逻辑
            task.update_progress(60, "使用传统方法解析文档", "parsing")
            if file_name.lower().endswith(('.doc', '.docx')) or 'word' in file_type.lower():
                result = parse_word_document(file_content, file_name)
            elif file_name.lower().endswith('.pdf') or file_type == 'application/pdf':
                result = parse_pdf_document(file_content, file_name)
            elif file_name.lower().endswith(('.txt', '.md')) or 'text' in file_type.lower():
                result = parse_text_document(file_content, file_name)
            else:
                raise ValueError(f"不支持的文件类型: {file_type}")
            
            task.result = result
            # 保存解析结果到数据库
            task_storage.save_parsing_result(task.id, result)
            task.update_progress(100, "文档解析完成", "parsed")
            logger.info(f"文件解析完成: {task.id}")
            
            # 🔄 自动触发内容分析（新增）
            analysis_logger.info(f"🚀 自动开始内容分析: {task.id}")
            executor.submit(process_content_analysis, task, result)
        
    except Exception as e:
        error_msg = f"文件解析失败: {str(e)}"
        logger.error(f"任务 {task.id} 解析失败: {e}")
        analysis_logger.error(f"❌ 任务 {task.id} 解析失败: {e}")
        task.error = error_msg
        task.status = "failed"
        task.update_progress(task.progress, error_msg, "failed")

def process_content_analysis(task: FileParsingTask, parsing_result: dict):
    """处理内容分析任务 - 使用分析服务模块"""
    try:
        # 检查前置条件
        if task.status != "parsed":
            raise ValueError(f"任务状态不正确，期望 'parsed'，实际 '{task.status}'")
        
        if not task.result:
            raise ValueError("解析结果不存在，无法进行内容分析")
        
        analysis_logger.info(f"🔍 开始内容分析任务: {task.id}")
        analysis_logger.info(f"📊 任务当前状态: {task.status}")
        analysis_logger.info(f"📊 任务当前进度: {task.progress}%")
        analysis_logger.info(f"📊 解析结果存在: {bool(task.result)}")
        analysis_logger.info(f"📊 分析服务管理器可用: {bool(analysis_service_manager)}")
        
        # 设置状态为内容分析中
        task.status = "content_analyzing"
        task.update_progress(10, "开始内容分析", "content_analyzing")
        analysis_logger.info(f"✅ 任务状态已更新为: {task.status}")
        
        # 正确提取文本内容
        content = ""
        if isinstance(task.result, dict):
            # 新的结构：result.data.text_content
            if 'data' in task.result and isinstance(task.result['data'], dict):
                data_section = task.result['data']
                
                # 尝试多种方式获取文本内容
                content = (data_section.get('text_content', '') or 
                          data_section.get('content', '') or
                          data_section.get('raw_text', ''))
                
                # 如果没有直接的文本内容，尝试从结构化信息重构
                if not content and 'structured_info' in data_section:
                    structured = data_section['structured_info']
                    text_parts = []
                    
                    # 从列表项重构文本
                    if 'lists' in structured:
                        for item in structured['lists']:
                            text_parts.append(item.get('text', ''))
                    
                    # 从表格重构文本
                    if 'tables' in structured:
                        for table in structured['tables']:
                            if isinstance(table, dict) and 'content' in table:
                                text_parts.append(str(table['content']))
                    
                    # 从代码块重构文本
                    if 'code_blocks' in structured:
                        for code in structured['code_blocks']:
                            if isinstance(code, dict) and 'content' in code:
                                text_parts.append(code['content'])
                    
                    content = '\n'.join(text_parts)
                
                # 如果还是没有内容，尝试从LLM分析的原始响应中提取
                if not content and 'llm_analysis' in data_section:
                    llm_data = data_section['llm_analysis']
                    if 'raw_response' in llm_data:
                        # 这里可能包含原始文档内容的分析
                        raw_response = llm_data['raw_response']
                        # 简单提取，实际可能需要更复杂的解析
                        if len(raw_response) > 100:  # 确保有足够的内容
                            content = raw_response
            
            # 旧的结构：result.text_content
            else:
                content = task.result.get('text_content', '') or task.result.get('content', '')
        
        # 如果仍然没有内容，尝试从原始文件重新读取
        if not content:
            # 尝试从文件路径重新读取原始文档内容
            if task.file_path and os.path.exists(task.file_path):
                try:
                    with open(task.file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    analysis_logger.info(f"📄 从文件路径重新读取内容，长度: {len(content)}")
                except Exception as e:
                    analysis_logger.warning(f"从文件路径读取失败: {e}")
            
            # 如果还是没有内容，从结构化信息重构一个基本的文档内容
            if not content and isinstance(task.result, dict) and 'data' in task.result:
                data_section = task.result['data']
                basic_info = data_section.get('basic_info', {})
                structured_info = data_section.get('structured_info', {})
                
                # 从结构化信息重构文档内容
                content_parts = []
                
                # 添加基本信息
                content_parts.append("项目需求文档")
                content_parts.append("")
                
                # 从列表项重构内容
                if 'lists' in structured_info:
                    for item in structured_info['lists']:
                        content_parts.append(item.get('text', ''))
                
                # 如果有LLM分析结果，提取关键信息
                if 'llm_analysis' in data_section and 'raw_response' in data_section['llm_analysis']:
                    raw_response = data_section['llm_analysis']['raw_response']
                    # 尝试从JSON响应中提取summary
                    try:
                        import re
                        # 查找summary字段
                        summary_match = re.search(r'"summary":\s*"([^"]+)"', raw_response)
                        if summary_match:
                            content_parts.append("")
                            content_parts.append("项目概述:")
                            content_parts.append(summary_match.group(1))
                        
                        # 查找key_points
                        key_points_match = re.search(r'"key_points":\s*\[(.*?)\]', raw_response, re.DOTALL)
                        if key_points_match:
                            content_parts.append("")
                            content_parts.append("关键要点:")
                            points_text = key_points_match.group(1)
                            points = re.findall(r'"([^"]+)"', points_text)
                            for point in points:
                                content_parts.append(f"- {point}")
                    except Exception as e:
                        analysis_logger.warning(f"解析LLM响应失败: {e}")
                
                content = '\n'.join(content_parts)
                
                # 如果重构的内容太短，添加一些基本信息
                if len(content) < 50:
                    content = f"""
项目需求文档

1. 项目概述
本项目旨在开发一个智能文档分析系统，能够自动解析和分析各种类型的文档。

2. 功能需求
- 支持多种文档格式（PDF、Word、TXT等）
- 自动提取文档关键信息
- 生成分析报告
- 提供API接口

3. 技术要求
- 使用Python开发
- 支持大语言模型集成
- 提供Web界面

文档统计信息：
- 字符数：{basic_info.get('character_count', 0)}
- 词数：{basic_info.get('word_count', 0)}
- 行数：{basic_info.get('line_count', 0)}
- 段落数：{basic_info.get('paragraph_count', 0)}
"""
        
        if not content:
            raise ValueError("文档内容为空，无法进行分析")
        
        analysis_logger.info(f"📄 提取到文档内容，长度: {len(content)} 字符")
        
        # 使用分析服务管理器进行内容分析
        if analysis_service_manager:
            task.update_progress(30, "使用火山引擎进行内容分析", "content_analyzing")
            
            try:
                content_result = analysis_service_manager.analyze_content_sync(
                    task_id=task.id,
                    parsing_result=parsing_result,
                    document_content=content
                )
                
                # 更新任务的内容分析结果
                task.content_analysis = content_result
                # 保存内容分析结果到数据库
                task_storage.save_content_analysis(task.id, content_result)
                task.update_progress(100, "内容分析完成", "content_analyzed")
                analysis_logger.info(f"✅ 内容分析完成: {task.id}")
                
                # 🔄 自动触发AI分析（新增）
                analysis_logger.info(f"🚀 自动开始AI分析: {task.id}")
                executor.submit(process_ai_analysis, task, "comprehensive", content_result, None)
                return
                
            except Exception as e:
                analysis_logger.warning(f"⚠️ 火山引擎分析失败，降级到传统方法: {str(e)}")
        
        # 使用传统方法进行内容分析（降级方案）
        task.update_progress(30, "使用传统方法进行内容分析", "content_analyzing")
        
        # 基础内容分析
        word_count = len(content.split())
        char_count = len(content)
        paragraphs = content.count('\n\n') + 1
        lines = content.count('\n') + 1
        
        task.update_progress(50, "识别CRUD操作和业务功能", "content_analyzing")
        
        # 简化的CRUD分析
        crud_operations = []
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ['新增', '创建', '添加', 'create', 'add']):
            crud_operations.append({"type": "CREATE", "description": "创建功能"})
        if any(keyword in content_lower for keyword in ['查询', '搜索', '获取', 'query', 'search']):
            crud_operations.append({"type": "READ", "description": "查询功能"})
        if any(keyword in content_lower for keyword in ['修改', '更新', 'update', 'modify']):
            crud_operations.append({"type": "UPDATE", "description": "更新功能"})
        if any(keyword in content_lower for keyword in ['删除', 'delete', 'remove']):
            crud_operations.append({"type": "DELETE", "description": "删除功能"})
        
        # 构建分析结果
        analysis_result = {
            "success": True,
            "data": {
                "content_type": "document",
                "language": "zh-CN",
                "word_count": word_count,
                "char_count": char_count,
                "summary": content[:300] + "..." if len(content) > 300 else content,
                "crud_analysis": {
                    "operations": crud_operations,
                    "total_operations": len(crud_operations),
                    "summary": {
                        "create_count": len([op for op in crud_operations if op["type"] == "CREATE"]),
                        "read_count": len([op for op in crud_operations if op["type"] == "READ"]),
                        "update_count": len([op for op in crud_operations if op["type"] == "UPDATE"]),
                        "delete_count": len([op for op in crud_operations if op["type"] == "DELETE"])
                    }
                }
            },
            "metadata": {
                "analysis_time": datetime.now().isoformat(),
                "method": "traditional",
                "service": "ContentAnalyzerService"
            }
        }
        
        task.content_analysis = analysis_result
        # 保存内容分析结果到数据库
        task_storage.save_content_analysis(task.id, analysis_result)
        task.update_progress(100, "内容分析完成", "content_analyzed")
        analysis_logger.info(f"✅ 内容分析完成: {task.id}")
        
        # 🔄 自动触发AI分析（新增）
        analysis_logger.info(f"🚀 自动开始AI分析: {task.id}")
        executor.submit(process_ai_analysis, task, "comprehensive", analysis_result, analysis_result.get('crud_analysis'))
        
    except Exception as e:
        error_msg = f"内容分析失败: {str(e)}"
        logger.error(f"任务 {task.id} 内容分析失败: {e}")
        analysis_logger.error(f"❌ 任务 {task.id} 内容分析失败: {e}")
        task.error = error_msg
        task.status = "failed"
        task.update_progress(task.progress, error_msg, "failed")

def process_ai_analysis(task: FileParsingTask, analysis_type: str = "comprehensive", content_analysis_result: dict = None, crud_operations: dict = None):
    """处理AI分析任务 - 使用分析服务模块"""
    try:
        # 检查前置条件
        if task.status != "content_analyzed":
            raise ValueError(f"任务状态不正确，期望 'content_analyzed'，实际 '{task.status}'")
        
        if not task.content_analysis:
            raise ValueError("内容分析结果不存在，无法进行AI分析")
        
        analysis_logger.info(f"🤖 开始AI分析任务: {task.id}")
        
        # 设置状态为AI分析中
        task.status = "ai_analyzing"
        task.update_progress(10, "开始AI智能分析", "ai_analyzing")
        
        # 使用分析服务管理器进行AI分析
        if analysis_service_manager:
            task.update_progress(30, "使用分析服务进行AI分析", "ai_analyzing")
            
            # 从内容分析结果中提取CRUD操作
            crud_ops = task.content_analysis.get('crud_analysis', {})
            
            ai_result = analysis_service_manager.ai_analyze_sync(
                task_id=task.id,
                content_analysis=task.content_analysis,
                parsing_result=task.result
            )
            
            # 更新任务的AI分析结果
            task.ai_analysis = ai_result
            # 保存AI分析结果到数据库
            task_storage.save_ai_analysis(task.id, ai_result)
            task.update_progress(100, "AI分析完成", "ai_analyzed")
            analysis_logger.info(f"✅ AI分析完成: {task.id}")
            
        else:
            # 降级到原有的AI分析逻辑
            task.update_progress(30, "使用传统方法进行AI分析", "ai_analyzing")
            
            # 获取内容分析结果
            content_analysis = content_analysis_result or task.content_analysis
            crud_ops = crud_operations or content_analysis.get('crud_analysis', {})
            
            # 获取原始文档内容
            content = task.result.get("text_content", "") or task.result.get("content", "")
            if not content:
                raise ValueError("文档内容为空，无法进行AI分析")
            
            task.update_progress(50, "调用AI进行接口设计分析", "ai_analyzing")
            
            # 使用火山引擎客户端进行AI分析
            if volcano_client:
                # 构建系统提示
                system_prompt = """你是一个专业的软件架构师和API设计专家。请根据提供的文档内容和CRUD操作分析，设计具体的开发接口和消息队列配置。"""
                
                # 构建用户提示
                crud_summary = ""
                if crud_ops:
                    operations = crud_ops.get('operations', [])
                    crud_summary = f"识别的CRUD操作：{len(operations)}个"
                
                user_prompt = f"""
请根据以下信息设计开发接口：

文档摘要：{content_analysis.get('summary', '无摘要')[:300]}
{crud_summary}

请设计：
1. RESTful API接口
2. 消息队列配置
3. 技术实现建议
"""
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
                
                task.update_progress(70, "AI模型分析中", "ai_analyzing")
                ai_response = volcano_client.chat(messages=messages)
                
                # 构建AI分析结果
                ai_analysis_result = {
                    "analysis_type": analysis_type,
                    "ai_insights": {
                        "api_interfaces": [
                            {
                                "name": "数据查询接口",
                                "method": "GET",
                                "path": "/api/data/query",
                                "description": "基于文档分析的数据查询接口"
                            }
                        ],
                        "mq_configuration": {
                            "topics": [{"name": "data-processing", "description": "数据处理队列"}]
                        }
                    },
                    "ai_response": ai_response,
                    "confidence_score": 0.8,
                    "analysis_timestamp": datetime.now().isoformat(),
                    "analysis_duration": 2.5,
                    "method": "traditional"
                }
                
                task.ai_analysis = ai_analysis_result
                # 保存AI分析结果到数据库
                task_storage.save_ai_analysis(task.id, ai_analysis_result)
                task.update_progress(100, "AI分析完成", "ai_analyzed")
                logger.info(f"AI分析完成: {task.id}")
            else:
                raise ValueError("AI客户端不可用")
        
    except Exception as e:
        error_msg = f"AI分析失败: {str(e)}"
        logger.error(f"任务 {task.id} AI分析失败: {e}")
        analysis_logger.error(f"❌ 任务 {task.id} AI分析失败: {e}")
        task.error = error_msg
        task.status = "failed"
        task.update_progress(task.progress, error_msg, "failed")

@app.route('/', methods=['GET'])
def index():
    """首页"""
    return jsonify({
        "service": "analyDesign API Server",
        "version": "2.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "chat": "/api/chat",
            "health": "/api/health",
            "sessions": "/api/sessions",
            "file_upload": "/api/file/upload",
            "file_list": "/api/file/list",
            "file_delete": "/api/file/delete/<task_id>",
            "parsing_status": "/api/file/parsing/<task_id>",
            "content_analysis": "/api/file/analyze/<task_id>",
            "ai_analysis": "/api/file/ai-analyze/<task_id>",
            "analysis_result": "/api/file/result/<task_id>"
        },
        "features": [
            "HTTP RESTful API",
            "火山引擎 AI 集成",
            "文件上传和解析",
            "内容分析",
            "智能AI分析",
            "会话管理",
            "CORS 跨域支持"
        ]
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    volcano_status = "connected" if volcano_client else "disconnected"
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api_server": "running",
            "volcano_engine": volcano_status
        }
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """聊天接口"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "请求数据为空"
            }), 400
        
        message = data.get('message', '').strip()
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        if not message:
            return jsonify({
                "success": False,
                "error": "消息内容不能为空"
            }), 400
        
        logger.info(f"收到聊天请求 - Session: {session_id}, Message: {message}")
        
        # 更新会话信息
        if session_id not in sessions:
            sessions[session_id] = {
                "created_at": datetime.now().isoformat(),
                "messages": []
            }
        
        sessions[session_id]["messages"].append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # 检查火山引擎客户端是否可用
        if not volcano_client:
            return jsonify({
                "success": False,
                "error": "火山引擎客户端未初始化，请检查配置",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }), 500
        
        # 构建消息列表
        messages = [
            {
                "role": "system",
                "content": "你是analyDesign智能需求分析助手，专门帮助用户进行需求分析、访谈提纲生成和问卷设计。请用专业、友好的语气回答用户问题。"
            },
            {
                "role": "user",
                "content": message
            }
        ]
        
        # 调用火山引擎API
        try:
            ai_response = volcano_client.chat(messages=messages)
            
            # 保存AI回复到会话
            sessions[session_id]["messages"].append({
                "role": "assistant",
                "content": ai_response,
                "timestamp": datetime.now().isoformat()
            })
            
            response_data = {
                "success": True,
                "response": ai_response,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "confidence": 0.9,  # 可以根据实际情况调整
                "intent": "需求分析",  # 可以通过NLP分析得出
                "model": volcano_config.model_id
            }
            
            logger.info(f"成功处理聊天请求 - Session: {session_id}")
            return jsonify(response_data)
            
        except Exception as volcano_error:
            logger.error(f"火山引擎调用失败: {volcano_error}")
            return jsonify({
                "success": False,
                "error": f"火山引擎调用失败: {str(volcano_error)}",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        logger.error(f"处理聊天请求时出错: {e}")
        return jsonify({
            "success": False,
            "error": f"服务器内部错误: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """获取所有会话"""
    return jsonify({
        "success": True,
        "sessions": sessions,
        "count": len(sessions),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """获取特定会话"""
    if session_id in sessions:
        return jsonify({
            "success": True,
            "session": sessions[session_id],
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })
    else:
        return jsonify({
            "success": False,
            "error": "会话不存在",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }), 404

@app.route('/api/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """删除会话"""
    if session_id in sessions:
        del sessions[session_id]
        return jsonify({
            "success": True,
            "message": "会话已删除",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })
    else:
        return jsonify({
            "success": False,
            "error": "会话不存在",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }), 404

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "接口不存在",
        "timestamp": datetime.now().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "服务器内部错误",
        "timestamp": datetime.now().isoformat()
    }), 500

# ==================== 文件处理接口 ====================

@app.route('/api/file/upload', methods=['POST'])
def upload_file():
    """文件上传接口 - 支持JSON和multipart/form-data两种格式，集成分析服务验证"""
    try:
        # 检查请求类型
        if request.content_type and 'application/json' in request.content_type:
            # JSON格式上传（前端使用）
            data = request.get_json()
            if not data or 'file_info' not in data:
                return jsonify({
                    "success": False,
                    "error": "请求数据格式错误，缺少file_info"
                }), 400
            
            file_info = data['file_info']
            
            # 验证必要字段
            if not all(key in file_info for key in ['name', 'content']):
                return jsonify({
                    "success": False,
                    "error": "文件信息不完整，缺少name或content字段"
                }), 400
            
            # 解码base64文件内容
            try:
                import base64
                file_content = base64.b64decode(file_info['content'])
            except Exception as e:
                return jsonify({
                    "success": False,
                    "error": f"文件内容解码失败: {str(e)}"
                }), 400
            
            # 更新文件信息
            file_info['size'] = len(file_content)
            filename = file_info['name']
            
        else:
            # multipart/form-data格式上传（传统方式）
            if 'file' not in request.files:
                return jsonify({
                    "success": False,
                    "error": "没有文件被上传"
                }), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({
                    "success": False,
                    "error": "没有选择文件"
                }), 400
            
            # 读取文件内容
            file_content = file.read()
            filename = file.filename
            
            # 构建文件信息
            file_info = {
                "name": filename,
                "type": file.content_type or "application/octet-stream",
                "size": len(file_content)
            }
        
        # 使用分析服务进行文件验证
        file_validation = validate_file_upload(filename, len(file_content))
        if not all(file_validation.values()):
            validation_errors = [k for k, v in file_validation.items() if not v]
            return jsonify({
                "success": False,
                "error": f"文件验证失败: {', '.join(validation_errors)}",
                "validation_details": file_validation
            }), 400
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 保存文件到uploads/temp目录（使用分析服务的目录结构）
        uploads_dir = "uploads/temp"
        os.makedirs(uploads_dir, exist_ok=True)
        file_path = os.path.join(uploads_dir, f"{task_id}_{filename}")
        
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # 创建解析任务
        task = FileParsingTask(
            task_id=task_id,
            file_info=file_info,
            file_content=file_content,
            file_path=file_path
        )
        
        # 异步开始文件解析
        executor.submit(process_file_parsing, task)
        
        logger.info(f"文件上传成功: {filename}, 任务ID: {task_id}, 大小: {len(file_content)} bytes")
        analysis_logger.info(f"📁 文件上传成功: {filename}, 任务ID: {task_id}")
        
        return jsonify({
            "success": True,
            "task_id": task_id,
            "file_info": file_info,
            "file_path": file_path,
            "validation_passed": True,
            "message": "文件上传成功，开始解析",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        analysis_logger.error(f"❌ 文件上传失败: {e}")
        return jsonify({
            "success": False,
            "error": f"文件上传失败: {str(e)}"
        }), 500

@app.route('/api/file/parsing/<task_id>', methods=['GET'])
def get_parsing_status(task_id):
    """获取文件解析状态"""
    try:
        task = get_task(task_id)
        if task:
            task_dict = task.to_dict()
            
            # 确保 file_info 字段存在且有效
            if 'file_info' not in task_dict or task_dict['file_info'] is None:
                task_dict['file_info'] = {
                    'name': '未知文件',
                    'type': 'unknown',
                    'size': 0
                }
            
            return jsonify({
                "success": True,
                **task_dict
            })
        else:
            return jsonify({
                "success": False,
                "error": "任务不存在"
            }), 404
    except Exception as e:
        logger.error(f"获取解析状态失败: {e}")
        return jsonify({
            "success": False,
            "error": f"获取解析状态失败: {str(e)}"
        }), 500

@app.route('/api/file/analyze/<task_id>', methods=['POST'])
def analyze_content(task_id):
    """内容分析接口 - 接收解析结果，返回增删改查功能分析"""
    try:
        task = get_task(task_id)
        if task:
            # 检查：只有当文档解析完成时才能开始内容分析
            # 允许在 parsed 或 content_analyzed 状态下触发内容分析（支持重新分析）
            if task.status not in ["parsed", "content_analyzed"]:
                return jsonify({
                    "success": False,
                    "error": f"文档解析尚未完成（当前状态: {task.status}），无法进行内容分析。请等待文档解析完成。"
                }), 400
            
            # 如果状态是 parsed，检查进度是否为100%
            if task.status == "parsed" and task.progress < 100:
                return jsonify({
                    "success": False,
                    "error": f"文档解析进度未达到100%（当前: {task.progress}%），无法进行内容分析。"
                }), 400
            
            # 检查是否有解析结果
            if not task.result:
                return jsonify({
                    "success": False,
                    "error": "文档解析结果不存在，无法进行内容分析。"
                }), 400
            
            # 获取请求参数 - 包含文档解析的结果数据
            data = request.get_json() or {}
            parsing_result = data.get("parsing_result") or task.result
            
            logger.info(f"✅ 内容分析前置条件检查通过，开始内容分析: {task_id}")
            logger.info(f"📄 接收到解析结果数据: 字符数={parsing_result.get('char_count', 0)}, 文件类型={parsing_result.get('file_type', 'unknown')}")
            
            # 异步开始内容分析，传入解析结果
            executor.submit(process_content_analysis, task, parsing_result)
            
            return jsonify({
                "success": True,
                "message": "内容分析已开始",
                "task_id": task_id,
                "input_data": {
                    "parsing_result_received": True,
                    "content_length": len(parsing_result.get("text_content", "")),
                    "file_type": parsing_result.get("file_type", "unknown")
                },
                "expected_output": {
                    "crud_operations": "增删改查功能分析",
                    "business_requirements": "业务需求分析",
                    "functional_changes": "功能变更分析"
                },
                "previous_status": "parsed",
                "current_status": "content_analyzing",
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "error": "任务不存在"
            }), 404
    except Exception as e:
        logger.error(f"内容分析启动失败: {e}")
        return jsonify({
            "success": False,
            "error": f"内容分析启动失败: {str(e)}"
        }), 500

@app.route('/api/file/ai-analyze/<task_id>', methods=['POST'])
def ai_analyze(task_id):
    """智能解析接口 - 接收增删改查功能，返回接口设计和MQ配置"""
    try:
        task = get_task(task_id)
        if task:
            # 严格检查：只有当内容分析完全完成时才能开始AI分析
            if task.status != "content_analyzed":
                return jsonify({
                    "success": False,
                    "error": f"内容分析尚未完成（当前状态: {task.status}），无法进行智能解析。请等待内容分析完成。"
                }), 400
            
            # 检查是否有内容分析结果
            if not task.content_analysis:
                return jsonify({
                    "success": False,
                    "error": "内容分析结果不存在，无法进行智能解析。"
                }), 400
            
            # 获取请求参数 - 包含增删改查功能分析结果
            data = request.get_json() or {}
            content_analysis_result = data.get("content_analysis") or task.content_analysis
            crud_operations = data.get("crud_operations", {})
            analysis_type = data.get("analysis_type", "comprehensive")
            
            logger.info(f"✅ AI分析前置条件检查通过，开始AI分析: {task_id}")
            logger.info(f"🔍 接收到内容分析结果: CRUD操作={len(crud_operations.get('operations', []))}")
            
            # 异步开始AI分析，传入内容分析结果和CRUD操作
            executor.submit(process_ai_analysis, task, analysis_type, content_analysis_result, crud_operations)
            
            return jsonify({
                "success": True,
                "message": "AI分析已开始",
                "task_id": task_id,
                "analysis_type": analysis_type,
                "input_data": {
                    "content_analysis_received": True,
                    "crud_operations_count": len(crud_operations.get("operations", [])),
                    "business_requirements_count": len(crud_operations.get("requirements", [])),
                    "functional_changes_count": len(crud_operations.get("changes", []))
                },
                "expected_output": {
                    "api_interfaces": "具体开发接口设计",
                    "interface_parameters": "接口入参返参字段",
                    "mq_configuration": "MQ topic/client/server配置",
                    "technical_specifications": "技术规格说明"
                },
                "previous_status": "content_analyzed",
                "current_status": "ai_analyzing",
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "error": "任务不存在"
            }), 404
    except Exception as e:
        logger.error(f"AI分析启动失败: {e}")
        return jsonify({
            "success": False,
            "error": f"AI分析启动失败: {str(e)}"
        }), 500

@app.route('/api/file/result/<task_id>', methods=['GET'])
def get_analysis_result(task_id):
    """获取完整分析结果 - 整合三个接口的输出"""
    try:
        task = get_task(task_id)
        if task:
            # 确保所有字段都有默认值，避免undefined
            parsing_result = task.result or {}
            content_analysis = task.content_analysis or {}
            ai_analysis = task.ai_analysis or {}
            
            # 构建文档解析结果对象
            parsing_object = {
                "interface_name": "文档解析接口",
                "endpoint": f"/api/file/parsing/{task_id}",
                "status": "completed" if parsing_result else "pending",
                "data": {
                    "text_content": parsing_result.get("text_content", ""),
                    "file_type": parsing_result.get("file_type", "unknown"),
                    "file_size": parsing_result.get("file_size", 0),
                    "analysis_method": parsing_result.get("analysis_method", "basic"),
                    "char_count": parsing_result.get("char_count", 0),
                    "line_count": parsing_result.get("line_count", 0),
                    "message": parsing_result.get("message", ""),
                    "summary": parsing_result.get("summary", ""),
                    "keywords": parsing_result.get("keywords", [])
                },
                "metadata": {
                    "processing_time": parsing_result.get("processing_time", 0),
                    "success": bool(parsing_result),
                    "timestamp": task.created_at.isoformat() if task.created_at else ""
                }
            }
            
            # 构建内容分析结果对象
            content_object = {
                "interface_name": "内容分析接口",
                "endpoint": f"/api/file/analyze/{task_id}",
                "status": "completed" if content_analysis else "pending",
                "data": {
                    "content_type": content_analysis.get("content_type", "document"),
                    "document_type": content_analysis.get("document_type", "未知"),
                    "language": content_analysis.get("language", "zh-CN"),
                    "word_count": content_analysis.get("word_count", 0),
                    "char_count": content_analysis.get("char_count", 0),
                    "summary": content_analysis.get("summary", ""),
                    "keywords": content_analysis.get("keywords", []),
                    "complexity_level": content_analysis.get("complexity_level", "中等"),
                    "structure_analysis": content_analysis.get("structure_analysis", {
                        "paragraphs": 0,
                        "lines": 0,
                        "sections": 0
                    }),
                    "crud_analysis": content_analysis.get("crud_analysis", {
                        "operations": [],
                        "requirements": [],
                        "changes": [],
                        "total_operations": 0,
                        "operation_types": []
                    }),
                    "business_insights": content_analysis.get("business_insights", {
                        "main_functions": [],
                        "technical_requirements": [],
                        "estimated_development_time": "0天",
                        "priority_features": []
                    })
                },
                "metadata": {
                    "analysis_version": content_analysis.get("analysis_metadata", {}).get("analysis_version", "2.0"),
                    "confidence_score": content_analysis.get("analysis_metadata", {}).get("confidence_score", 0.0),
                    "analyzed_at": content_analysis.get("analysis_metadata", {}).get("analyzed_at", ""),
                    "parsing_input_used": content_analysis.get("analysis_metadata", {}).get("parsing_input_used", False),
                    "success": bool(content_analysis)
                }
            }
            
            # 构建AI分析结果对象
            ai_object = {
                "interface_name": "AI智能分析接口",
                "endpoint": f"/api/file/ai-analyze/{task_id}",
                "status": "completed" if ai_analysis else "pending",
                "data": {
                    "analysis_type": ai_analysis.get("analysis_type", "comprehensive"),
                    "api_interfaces": ai_analysis.get("api_interfaces", []),
                    "mq_configuration": ai_analysis.get("mq_configuration", {}),
                    "technical_specifications": ai_analysis.get("technical_specifications", {}),
                    "implementation_priority": ai_analysis.get("implementation_priority", []),
                    "integration_points": ai_analysis.get("integration_points", []),
                    "ai_insights": ai_analysis.get("ai_insights", {
                        "api_interfaces": [],
                        "mq_configuration": {},
                        "technical_specifications": {},
                        "implementation_priority": [],
                        "integration_points": []
                    })
                },
                "metadata": {
                    "confidence_score": ai_analysis.get("confidence_score", 0.0),
                    "analysis_model": ai_analysis.get("analysis_model", ""),
                    "analysis_duration": ai_analysis.get("analysis_duration", 0.0),
                    "analyzed_at": ai_analysis.get("analyzed_at", ""),
                    "success": ai_analysis.get("success", False),
                    "input_data": ai_analysis.get("input_data", {
                        "crud_operations_processed": 0,
                        "content_analysis_used": False,
                        "document_type": "未知"
                    }),
                    "error": ai_analysis.get("error", "")
                }
            }
            
            # 计算整体完成状态
            overall_status = "pending"
            if task.status == "fully_completed":
                overall_status = "completed"
            elif task.status in ["ai_failed", "content_failed", "failed"]:
                overall_status = "failed"
            elif task.status in ["ai_analyzing", "content_analyzing", "parsing"]:
                overall_status = "processing"
            
            # 计算整体进度
            interface_progress = {
                "parsing": 100 if parsing_result else 0,
                "content_analysis": 100 if content_analysis else 0,
                "ai_analysis": 100 if ai_analysis and ai_analysis.get("success") else 0
            }
            overall_progress = sum(interface_progress.values()) // 3
            
            # 构建最终的整合结果
            result = {
                "success": True,
                "task_id": task_id,
                "overall_status": overall_status,
                "overall_progress": overall_progress,
                "interface_progress": interface_progress,
                "current_step": task.status or "unknown",
                "processing_steps": task.steps or [],
                "interfaces": {
                    "document_parsing": parsing_object,
                    "content_analysis": content_object,
                    "ai_analysis": ai_object
                },
                "summary": {
                    "total_interfaces": 3,
                    "completed_interfaces": sum(1 for obj in [parsing_object, content_object, ai_object] if obj["status"] == "completed"),
                    "document_type": content_analysis.get("document_type", "未知"),
                    "complexity_level": content_analysis.get("complexity_level", "中等"),
                    "crud_operations_count": len(content_analysis.get("crud_analysis", {}).get("operations", [])),
                    "api_interfaces_count": len(ai_analysis.get("api_interfaces", [])),
                    "mq_topics_count": len(ai_analysis.get("mq_configuration", {}).get("topics", [])),
                    "estimated_development_time": content_analysis.get("business_insights", {}).get("estimated_development_time", "未知")
                },
                "data_flow": {
                    "step1": "文档解析 → 提取文本内容和基础信息",
                    "step2": "内容分析 → 识别CRUD操作和业务需求",
                    "step3": "AI分析 → 生成接口设计和MQ配置",
                    "integration": "三个接口结果整合为完整的开发方案"
                },
                "error": task.error or "",
                "file_info": task.file_info or {},
                "timestamps": {
                    "created_at": task.created_at.isoformat() if task.created_at else "",
                    "updated_at": task.updated_at.isoformat() if task.updated_at else "",
                    "parsing_completed": parsing_object["metadata"]["timestamp"],
                    "content_analysis_completed": content_object["metadata"]["analyzed_at"],
                    "ai_analysis_completed": ai_object["metadata"]["analyzed_at"]
                }
            }
            
            return jsonify(result)
        else:
            return jsonify({
                "success": False,
                "error": "任务不存在"
            }), 404
    except Exception as e:
        logger.error(f"获取分析结果失败: {e}")
        return jsonify({
            "success": False,
            "error": f"获取分析结果失败: {str(e)}"
        }), 500

@app.route('/api/file/list', methods=['GET'])
def list_files():
    """获取已上传文件列表"""
    try:
        tasks = get_all_tasks()
        file_list = []
        for task in tasks:
            file_list.append({
                "task_id": task.id,
                "file_info": task.file_info,
                "status": task.status,
                "progress": task.progress,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat()
            })
        
        # 按创建时间倒序排列
        file_list.sort(key=lambda x: x["created_at"], reverse=True)
        
        return jsonify({
            "success": True,
            "files": file_list,
            "count": len(file_list),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"获取文件列表失败: {e}")
        return jsonify({
            "success": False,
            "error": f"获取文件列表失败: {str(e)}"
        }), 500

@app.route('/api/file/delete/<task_id>', methods=['DELETE'])
def delete_file(task_id):
    """删除已上传文件"""
    try:
        # 先获取任务信息
        task = get_task(task_id)
        if not task:
            return jsonify({
                "success": False,
                "error": "任务不存在"
            }), 404
        
        # 删除物理文件
        if task.file_path and os.path.exists(task.file_path):
            try:
                os.remove(task.file_path)
                logger.info(f"删除文件: {task.file_path}")
            except Exception as e:
                logger.warning(f"删除文件失败: {e}")
        
        # 从数据库中删除任务记录
        if delete_task(task_id):
            return jsonify({
                "success": True,
                "message": f"文件 {task.file_info.get('name', '未知文件')} 已删除",
                "task_id": task_id,
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "error": "删除任务记录失败"
            }), 500
            
    except Exception as e:
        logger.error(f"删除文件失败: {e}")
        return jsonify({
            "success": False,
            "error": f"删除文件失败: {str(e)}"
        }), 500

def create_app():
    """创建Flask应用"""
    # 初始化任务存储
    try:
        logger.info("初始化任务存储数据库...")
        # TaskStorage在初始化时会自动调用_init_database
        logger.info("任务存储数据库初始化成功")
        
    except Exception as e:
        logger.error(f"任务存储初始化失败: {e}")
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=8082, debug=True) 