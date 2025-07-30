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

# 导入统一日志配置
try:
    from ..utils.logger_config import initialize_logging, get_logger, log_api_request, log_analysis_step
except ImportError:
    # 如果相对导入失败，使用绝对导入
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from src.utils.logger_config import initialize_logging, get_logger, log_api_request, log_analysis_step

# 初始化日志系统
initialize_logging()

# 获取日志器
logger = get_logger('api_server')

# 导入配置和工具类
try:
    from ..resource.config import get_config
    from ..utils.volcengine_client import VolcengineClient, VolcengineConfig
    from ..utils.llm_logger import LLMLogger
    from ..utils.task_storage import get_task_storage
    from ..utils.redis_task_storage import get_redis_task_storage
    from ..utils.markdown_storage import get_markdown_storage
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
    # 导入编码智能体API
    from ..apis.coder_agent_api import coder_agent_api
    try:
        from ..utils.enhanced_analyzer import EnhancedAnalyzer
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
    from src.utils.redis_task_storage import get_redis_task_storage
    from src.utils.markdown_storage import get_markdown_storage
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
    # 导入编码智能体API
    from src.apis.coder_agent_api import coder_agent_api
    try:
        from src.utils.enhanced_analyzer import EnhancedAnalyzer
        ENHANCED_ANALYZER_AVAILABLE = True
    except ImportError:
        ENHANCED_ANALYZER_AVAILABLE = False
        logger.warning("enhanced_analyzer不可用，将使用基础文本处理")

# 获取配置
config = get_config()
task_storage = get_task_storage()
redis_task_storage = get_redis_task_storage()
markdown_storage = get_markdown_storage()

app = Flask(__name__)
# 配置CORS，允许所有来源和方法
CORS(app, 
     origins=["http://localhost:3000", "http://127.0.0.1:3000"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"],
     supports_credentials=True)

# 注册编码智能体API蓝图
app.register_blueprint(coder_agent_api)

# 添加请求日志中间件
@app.before_request
def log_request_info():
    """记录请求信息"""
    import time
    request.start_time = time.time()

@app.after_request  
def log_request_result(response):
    """记录请求结果"""
    import time
    duration = time.time() - getattr(request, 'start_time', time.time())
    log_api_request(
        method=request.method,
        endpoint=request.endpoint or request.path,
        status_code=response.status_code,
        duration=duration
    )
    return response

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
    # 从配置文件读取向量数据库类型和配置
    vector_db_config = config.get_vector_database_config()
    vector_db_type = vector_db_config.get('type', 'mock')  # 默认使用mock
    
    # 准备向量数据库参数
    vector_db_kwargs = {}
    if vector_db_type.lower() == 'weaviate':
        weaviate_config = vector_db_config.get('weaviate', {})
        vector_db_kwargs.update({
            'host': weaviate_config.get('host', 'localhost'),
            'port': weaviate_config.get('port', 8080),
            'grpc_port': weaviate_config.get('grpc_port', 50051),
            'scheme': weaviate_config.get('scheme', 'http'),
            'api_key': weaviate_config.get('api_key'),
            'collection_name': weaviate_config.get('default_collection', {}).get('name', 'AnalyDesignDocuments')
        })
        logger.info(f"Weaviate配置: {weaviate_config.get('scheme', 'http')}://{weaviate_config.get('host', 'localhost')}:{weaviate_config.get('port', 8080)}")
    
    analysis_service_manager = initialize_analysis_service_manager(
        llm_client=volcano_client,
        vector_db_type=vector_db_type,
        **vector_db_kwargs
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
    def __init__(self, task_id: str, file_info: dict, file_path: str = None):
        self.id = task_id
        self.file_info = file_info
        self.file_content = None  # 不再存储文件内容，只存储路径
        self.file_path = file_path
        self.status = "pending"
        self.progress = 0
        self.steps = []
        self.result = None
        self.content_analysis = None
        self.ai_analysis = None
        self.markdown_content = None
        self.error = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        
        # 立即保存到数据库
        self._save_to_db()
    
    def _save_to_db(self):
        """保存任务到数据库"""
        try:
            # 保存到SQLite数据库
            task_storage.create_task(
                filename=self.file_info.get('filename', ''),
                file_size=self.file_info.get('size', 0),
                file_type=self.file_info.get('type', ''),
                task_id=self.id
            )
            # 同时保存到Redis
            redis_task_storage.create_task(
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
            "markdown_content": self.markdown_content,
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
        task.markdown_content = data.get('markdown_content')
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
            return analyzer.transform_file(file_content, file_name)
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
            return analyzer.transform_file(file_content, file_name)
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

def extract_text_from_file(file_path: str) -> str:
    """从文件路径中提取文本内容"""
    try:
        logger.info(f"从文件路径读取: {file_path}")
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 获取文件扩展名
        file_name = os.path.basename(file_path)
        file_ext = file_name.lower().split('.')[-1] if '.' in file_name else ''
        
        logger.info(f"使用通用文件分析方法: {file_name}")
        
        # 读取文件内容
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # 使用增强分析器处理文件
        if ENHANCED_ANALYZER_AVAILABLE:
            try:
                current_analyzer = EnhancedAnalyzer()
                
                if file_name.lower().endswith(('.doc', '.docx')) or file_ext in ['doc', 'docx']:
                    logger.info(f"检测到Word文档，使用Markdown转换: {file_name}")
                    transform_result = current_analyzer.parse_word_document(file_content, file_name)
                    extracted_text = transform_result.get("text_content", "Word文档解析失败")
                    if extracted_text and any(marker in extracted_text for marker in ['#', '|', '**', '*', '-']):
                        logger.info(f"Word文档已成功转换为Markdown格式，长度: {len(extracted_text)} 字符")
                    else:
                        logger.warning("Word文档转换结果可能不是标准Markdown格式")
                else:
                    # 对于其他文件类型，尝试直接解码
                    try:
                        extracted_text = file_content.decode('utf-8')
                    except UnicodeDecodeError:
                        try:
                            extracted_text = file_content.decode('gbk')
                        except UnicodeDecodeError:
                            extracted_text = file_content.decode('utf-8', errors='ignore')
                
                logger.info("提取的文本内容已准备完毕")
                return extracted_text
                
            except Exception as e:
                logger.error(f"增强分析器处理失败: {e}")
                # 降级到基础文本处理
                pass
        
        # 基础文本处理（fallback）
        try:
            extracted_text = file_content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                extracted_text = file_content.decode('gbk')
            except UnicodeDecodeError:
                extracted_text = file_content.decode('utf-8', errors='ignore')
        
        logger.info("使用基础方法提取文本内容完成")
        return extracted_text
        
    except Exception as e:
        logger.error(f"文件文本提取失败: {e}")
        return f"文件读取失败: {str(e)}"

# 文件处理函数
def process_file_parsing(task: FileParsingTask):
    """处理文件解析任务 - 使用分析服务模块"""
    try:
        log_analysis_step(task.id, "文件解析", "开始", f"文件: {task.file_info.get('name', 'unknown')}")
        task.update_progress(10, "开始解析文件", "parsing")
        
        file_info = task.file_info
        file_name = file_info.get("name", "")
        file_type = file_info.get("type", "")
        

        # 直接调用新方法
        extracted_text = extract_text_from_file(task.file_path)
        logger.info("提取的文本内容已准备完毕")
        extracted_preview = extracted_text.replace('{', '{{').replace('}', '}}') if extracted_text else "无内容"
        logger.info(f"转换后内容预览: {extracted_preview}")

        # 安全的日志记录，避免格式化错误
        logger.info("提取的文本内容已准备完毕")
        extracted_preview = extracted_text.replace('{', '{{').replace('}', '}}') if extracted_text else "无内容"
        logger.info(f"转换后内容预览: {extracted_preview}")

        
        # 验证输入 - 使用提取的文本内容进行验证
        validation = validate_input(task.id, extracted_text, file_type)
        if not all(validation.values()):
            raise ValueError(f"输入验证失败: {validation}")
        
        task.update_progress(40, "使用分析服务解析文档", "parsing")
        
        # 使用分析服务管理器进行文档解析
        if analysis_service_manager:
            parsing_result = analysis_service_manager.parse_document_sync(
                task_id=task.id,
                file_content=extracted_text,
                file_type=file_type.split('/')[-1] if '/' in file_type else file_type,
                file_name=file_name
            )
            
            # 更新任务结果
            task.result = parsing_result
            # 保存解析结果到Redis
            redis_task_storage.save_parsing_result(task.id, parsing_result)
            task.update_progress(100, "文档解析完成", "parsed")
            log_analysis_step(task.id, "文件解析", "完成", f"解析结果已保存")
            analysis_logger.info(f"✅ 文件解析完成: {task.id}")
        else:
            # 降级到原有的解析逻辑 - 需要读取文件内容
            task.update_progress(60, "使用传统方法解析文档", "parsing")
            
            # 读取文件内容用于传统解析方法
            with open(task.file_path, 'rb') as f:
                file_content = f.read()
            
            if file_name.lower().endswith(('.doc', '.docx')) or 'word' in file_type.lower():
                result = parse_word_document(file_content, file_name)
            elif file_name.lower().endswith('.pdf') or file_type == 'application/pdf':
                result = parse_pdf_document(file_content, file_name)
            elif file_name.lower().endswith(('.txt', '.md')) or 'text' in file_type.lower():
                result = parse_text_document(file_content, file_name)
            else:
                raise ValueError(f"不支持的文件类型: {file_type}")
            
            task.result = result
            # 保存解析结果到Redis
            redis_task_storage.save_parsing_result(task.id, result)
            task.update_progress(100, "文档解析完成", "parsed")
            logger.info(f"文件解析完成: {task.id}")
        
    except Exception as e:
        error_msg = f"文件解析失败: {str(e)}"
        logger.error(f"任务 {task.id} 解析失败: {e}")
        log_analysis_step(task.id, "文件解析", "失败", str(e))
        analysis_logger.error(f"❌ 任务 {task.id} 解析失败: {e}")
        task.error = error_msg
        task.status = "failed"
        task.update_progress(task.progress, error_msg, "failed")

def process_content_analysis(task: FileParsingTask, parsing_result: dict):
    """处理内容分析任务 - 使用分析服务模块"""
    try:
        # 检查前置条件 - 允许 content_analyzing 状态（V2流程中已经预先设置了状态）
        if task.status not in ["parsed", "content_analyzing"]:
            raise ValueError(f"任务状态不正确，期望 'parsed' 或 'content_analyzing'，实际 '{task.status}'")
        
        if not task.result:
            raise ValueError("解析结果不存在，无法进行内容分析")
        
        log_analysis_step(task.id, "内容分析", "开始", f"状态: {task.status}, 进度: {task.progress}%")
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
        content = extract_text_from_file(task.file_path)
        task.update_progress(30, "获取到上传文件", "content_analyzing")
        analysis_logger.info(f"📄 提取到文档内容，长度: {len(content)} 字符")
        
        # 使用分析服务管理器进行内容分析
        if analysis_service_manager:
            task.update_progress(35, "内容分析管理器开始分析", "content_analyzing")
            try:
                content_result = analysis_service_manager.analyze_content_sync(
                    task_id=task.id,
                    parsing_result=parsing_result,
                    document_content=content
                )
                
                # 保存内容分析结果到Redis
                redis_task_storage.save_content_analysis(task.id, content_result)
                task.update_progress(100, "内容分析完成", "content_analyzed")
                analysis_logger.info(f"✅ 内容分析完成: {task.id}")
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
        # 保存内容分析结果到Redis
        redis_task_storage.save_content_analysis(task.id, analysis_result)
        task.update_progress(100, "内容分析完成", "content_analyzed")
        analysis_logger.info(f"✅ 内容分析完成: {task.id}")
        
    except Exception as e:
        error_msg = f"内容分析失败: {str(e)}"
        logger.error(f"任务 {task.id} 内容分析失败: {e}")
        analysis_logger.error(f"❌ 任务 {task.id} 内容分析失败: {e}")
        task.error = error_msg
        task.status = "failed"
        task.update_progress(task.progress, error_msg, "failed")

def process_ai_analysis(task: FileParsingTask, analysis_type: str = "comprehensive", content_analysis_result: dict = None, parsing_result: dict = None):
    """处理AI分析任务 - 使用分析服务模块"""
    try:
        # 检查前置条件 - 允许 ai_analyzing 状态（V2流程中已经预先设置了状态）
        if task.status not in ["content_analyzed", "ai_analyzing"]:
            raise ValueError(f"任务状态不正确，期望 'content_analyzed' 或 'ai_analyzing'，实际 '{task.status}'")
        
        if not content_analysis_result:
            raise ValueError("内容分析结果不存在，无法进行AI分析")
        
        analysis_logger.info(f"🤖 开始AI分析任务: {task.id}")
        
        # 设置状态为AI分析中
        task.status = "ai_analyzing"
        task.update_progress(10, "开始AI设计方案", "ai_analyzing")
        
        # 使用分析服务管理器进行AI分析
        if analysis_service_manager:
            task.update_progress(30, "使用分析服务进行AI分析", "ai_analyzing")
            
            # 创建进度回调函数
            def progress_callback(stage: int, message: str, status: str = "ai_analyzing"):
                # 将AI分析的进度映射到30-100的范围
                mapped_progress = int(30 + (stage * 0.7))  # 30% + (stage% * 70%)
                task.update_progress(mapped_progress, message, status)
            
            # 从内容分析结果中提取数据
            content_data = content_analysis_result
            ai_result = analysis_service_manager.ai_analyze_sync(
                task_id=task.id,
                content_analysis=content_data,
                parsing_result=parsing_result,
                progress_callback=progress_callback
            )
            
            # 检查AI分析结果是否成功
            analysis_logger.info(f"🔍 AI分析结果检查: {task.id}, success={ai_result.get('success')}, 结果类型={type(ai_result)}")
            if not ai_result.get("success", False):
                analysis_logger.error(f"❌ AI分析服务返回失败: {task.id}, 错误={ai_result.get('error', '未知错误')}, 完整结果={str(ai_result)[:500]}")
                raise ValueError(f"AI分析服务返回失败: {ai_result.get('error', '未知错误')}")
            
            # 尝试保存AI分析结果到Redis（允许失败）
            try:
                redis_task_storage.save_ai_analysis(task.id, ai_result)
                analysis_logger.info(f"✅ AI分析结果已保存到Redis: {task.id}")
            except Exception as redis_error:
                analysis_logger.warning(f"⚠️ AI分析结果保存到Redis失败（不影响任务状态）: {redis_error}")
            
            # 无论Redis保存是否成功，都要更新任务状态为完成
            task.update_progress(100, "AI分析完成", "ai_analyzed")
            analysis_logger.info(f"✅ AI分析完成: {task.id}")
            
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
            "analysis_result": "/api/file/result/<task_id>",
            "static_files": "/uploads/<path:filename>"
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

# ==================== 静态文件服务接口 ====================

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """静态文件服务 - 提供uploads目录下的文件访问"""
    try:
        # 获取项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        uploads_dir = os.path.join(project_root, 'uploads')
        
        # 构建完整的文件路径
        file_path = os.path.join(uploads_dir, filename)
        
        # 安全检查：确保文件路径在uploads目录内（防止路径遍历攻击）
        uploads_dir_abs = os.path.abspath(uploads_dir)
        file_path_abs = os.path.abspath(file_path)
        
        if not file_path_abs.startswith(uploads_dir_abs):
            logger.warning(f"非法文件访问尝试: {filename}")
            return jsonify({"error": "非法文件路径"}), 403
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            logger.warning(f"文件不存在: {file_path}")
            return jsonify({"error": "文件不存在"}), 404
        
        # 获取文件的目录和文件名
        directory = os.path.dirname(file_path)
        basename = os.path.basename(file_path)
        
        # 使用Flask的send_from_directory发送文件
        from flask import send_from_directory
        return send_from_directory(directory, basename, as_attachment=False)
        
    except Exception as e:
        logger.error(f"静态文件服务错误: {e}")
        return jsonify({"error": f"文件访问失败: {str(e)}"}), 500

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
        uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "temp")
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
            executor.submit(process_ai_analysis, task, analysis_type, content_analysis_result, parsing_result)
            
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
    """获取完整分析结果 - 从Redis获取数据"""
    try:
        # 优先从Redis获取分析结果
        parsing_result = redis_task_storage.get_parsing_result(task_id) or {}
        content_analysis = redis_task_storage.get_content_analysis(task_id) or {}
        ai_analysis = redis_task_storage.get_ai_analysis(task_id) or {}
        
        # 添加详细的类型检查日志
        logger.info(f"🔍 数据类型诊断 - parsing_result: {type(parsing_result)}")
        logger.info(f"🔍 数据类型诊断 - content_analysis: {type(content_analysis)}")
        logger.info(f"🔍 数据类型诊断 - ai_analysis: {type(ai_analysis)}")
        
        # 如果是字符串，尝试解析
        if isinstance(parsing_result, str):
            logger.warning(f"⚠️ parsing_result是字符串，尝试JSON解析: {parsing_result[:200]}...")
            try:
                parsing_result = json.loads(parsing_result)
                logger.info("✅ parsing_result JSON解析成功")
            except Exception as e:
                logger.error(f"❌ parsing_result JSON解析失败: {e}")
                parsing_result = {}
        
        if isinstance(content_analysis, str):
            logger.warning(f"⚠️ content_analysis是字符串，尝试JSON解析: {content_analysis[:200]}...")
            try:
                content_analysis = json.loads(content_analysis)
                logger.info("✅ content_analysis JSON解析成功")
            except Exception as e:
                logger.error(f"❌ content_analysis JSON解析失败: {e}")
                content_analysis = {}
        
        if isinstance(ai_analysis, str):
            logger.warning(f"⚠️ ai_analysis是字符串，尝试JSON解析: {ai_analysis[:200]}...")
            try:
                ai_analysis = json.loads(ai_analysis)
                logger.info("✅ ai_analysis JSON解析成功")
            except Exception as e:
                logger.error(f"❌ ai_analysis JSON解析失败: {e}")
                ai_analysis = {}
        
        # 从SQLite获取任务基本信息
        task = get_task(task_id)
        if task:
            
            # 获取生成的markdown内容 - 从Redis获取，因为内存中的任务对象可能不是最新的
            markdown_content = redis_task_storage.get_markdown_content(task_id) or ""
            
            # 构建最终的整合结果
            result = {
                "success": True,
                "task_id": task_id,
        
                  # 基本信息
                "basic_info": {
                    "filename": task.file_info.get("filename", "Unknown"),
                    "filesize": f"{task.file_info.get('size', 0) / 1024:.1f} KB",
                    "file_type": task.file_info.get("type", "Unknown")
                },
                #文档解析返回结果
                "document_parsing": parsing_result,
                #内容分析返回结果
                "content_analysis": content_analysis,
                #AI分析返回结果
                "ai_analysis": ai_analysis,
                # 后端生成的markdown内容 - 修复：从Redis获取而非从task对象
                "markdown_content": markdown_content,
                "summary": {
                    "complexity_level": content_analysis.get("complexity_level", "中等"),
                    "crud_operations_count": len(content_analysis.get("crud_analysis", {}).get("operations", [])),
                    "api_interfaces_count": len(ai_analysis.get("api_interfaces", [])),
                    "mq_topics_count": len(ai_analysis.get("mq_configuration", {}).get("topics", [])),
                    "estimated_development_time": content_analysis.get("business_insights", {}).get("estimated_development_time", "未知")
                },
                "error": task.error or "",
                "file_info": task.file_info or {},
                "timestamps": {
                    "created_at": task.created_at.isoformat() if task.created_at else "",
                    "updated_at": task.updated_at.isoformat() if task.updated_at else "",
                    "parsing_completed": task.created_at.isoformat() if task.created_at else "",
                    "content_analysis_completed":content_analysis.get("analysis_metadata", {}).get("analyzed_at", ""),
                    "ai_analysis_completed": ai_analysis.get("analyzed_at", "")
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

@app.route('/api/v2/analysis/start', methods=['POST'])
def start_analysis_v2():
    """V2版本：启动完整流程（自动执行4阶段）"""
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
            
            # 安全记录文件信息，避免base64内容过长
            logger.info(f"file_info包含content字段，长度: {len(file_info['content'])}")
            # 解码base64文件内容
            try:
                import base64
                file_content = base64.b64decode(file_info['content'])

                logger.info(f"base64解码成功，file_content类型: {type(file_content)}, 大小: {len(file_content)} bytes")
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
        
        # 保存文件到uploads/temp目录
        uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "temp")
        os.makedirs(uploads_dir, exist_ok=True)
        file_path = os.path.join(uploads_dir, f"{task_id}_{filename}")
        
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
       
        # 创建解析任务
        task = FileParsingTask(
            task_id=task_id,
            file_info=file_info,
            file_path=file_path
        )
        
        # 设置初始进度状态为"启动中"
        task.update_progress(0, "分析流程启动中", "starting")
        
        # 启动完整的4阶段分析流程
        executor.submit(run_full_analysis_pipeline, task)
        
        logger.info(f"V2 完整分析启动成功: {filename}, 任务ID: {task_id}, 大小: {len(file_content)} bytes")
        analysis_logger.info(f"🚀 V2 完整分析启动: {filename}, 任务ID: {task_id}")
        
        return jsonify({
            "success": True,
            "task_id": task_id,
            "file_info": file_info,
            "message": "完整分析流程已启动",
            "stages": [
                {"name": "document_parsing", "title": "文档解析", "status": "pending"},
                {"name": "content_analysis", "title": "内容分析", "status": "pending"},
                {"name": "ai_analysis", "title": "AI设计方案", "status": "pending"},
                {"name": "document_generation", "title": "生成文档", "status": "pending"}
            ],
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"V2 分析启动失败: {e}")
        analysis_logger.error(f"❌ V2 分析启动失败: {e}")
        return jsonify({
            "success": False,
            "error": f"分析启动失败: {str(e)}"
        }), 500

@app.route('/api/v2/analysis/progress/<task_id>', methods=['GET'])
def get_analysis_progress_v2(task_id):
    """V2版本：获取实时进度更新"""
    try:
        task = get_task(task_id)
        if not task:
            return jsonify({
                "success": False,
                "error": "任务不存在"
            }), 404
        
        # 计算各阶段进度（只保留3个阶段）
        stages = {
            "document_parsing": {
                "title": "文档解析",
                "status": "pending",
                "progress": 0,
                "message": "等待开始"
            },
            "content_analysis": {
                "title": "内容分析", 
                "status": "pending",
                "progress": 0,
                "message": "等待开始"
            },
            "ai_analysis": {
                "title": "设计方案",
                "status": "pending", 
                "progress": 0,
                "message": "等待开始"
            }
        }
        
        # 获取最新的步骤描述
        def get_latest_description(task):
            if task.steps and len(task.steps) > 0 and isinstance(task.steps[-1], dict):
                return task.steps[-1].get("description", "处理中...")
            return "处理中..."
        
        # 根据任务状态更新阶段信息
        if task.status in ["parsing", "parsed"]:
            stages["document_parsing"]["status"] = "running" if task.status == "parsing" else "completed"
            stages["document_parsing"]["progress"] = task.progress if task.status == "parsing" else 100
            stages["document_parsing"]["message"] = get_latest_description(task) if task.status == "parsing" else "文档解析完成"
            
        if task.status in ["content_analyzing", "content_analyzed"]:
            stages["document_parsing"]["status"] = "completed"
            stages["document_parsing"]["progress"] = 100
            stages["document_parsing"]["message"] = "文档解析完成"
            
            stages["content_analysis"]["status"] = "running" if task.status == "content_analyzing" else "completed"
            stages["content_analysis"]["progress"] = task.progress if task.status == "content_analyzing" else 100
            stages["content_analysis"]["message"] = get_latest_description(task) if task.status == "content_analyzing" else "内容分析完成"
            
        if task.status in ["ai_analyzing", "ai_analyzed", "fully_completed"]:
            stages["document_parsing"]["status"] = "completed"
            stages["document_parsing"]["progress"] = 100
            stages["document_parsing"]["message"] = "文档解析完成"
            
            stages["content_analysis"]["status"] = "completed"
            stages["content_analysis"]["progress"] = 100
            stages["content_analysis"]["message"] = "内容分析完成"
            
            stages["ai_analysis"]["status"] = "running" if task.status == "ai_analyzing" else "completed"
            stages["ai_analysis"]["progress"] = task.progress if task.status == "ai_analyzing" else 100
            stages["ai_analysis"]["message"] = get_latest_description(task) if task.status == "ai_analyzing" else "AI分析完成"
        
        # 计算整体进度（基于3个阶段）
        total_progress = 0
        completed_stages = 0
        
        for stage in stages.values():
            if stage["status"] == "completed":
                completed_stages += 1
                total_progress += 100
            elif stage["status"] == "running":
                total_progress += stage["progress"]
        
        overall_progress = total_progress // 3  # 改为3个阶段
        
        # 确定整体状态
        overall_status = "pending"
        if task.status == "fully_completed":
            overall_status = "completed"
        elif task.status in ["failed", "ai_failed", "content_failed"]:
            overall_status = "failed"
        elif completed_stages > 0 or any(stage["status"] == "running" for stage in stages.values()):
            overall_status = "running"
        
        return jsonify({
            "success": True,
            "task_id": task_id,
            "overall_status": overall_status,
            "overall_progress": overall_progress,
            "current_stage": task.status,
            "stages": stages,
            "file_info": task.file_info,
            "error": task.error,
            "started_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"获取V2进度失败: {e}")
        logger.error(f"详细错误信息: {error_details}")
        return jsonify({
            "success": False,
            "error": f"获取进度失败: {str(e)}"
        }), 500

def run_full_analysis_pipeline(task: FileParsingTask):
    """
    运行完整的分析流程（优化版）
    阶段1: 文档解析 (0-30%)
    阶段2: 内容分析 (30-70%)  
    阶段3: AI分析并生成form_data (70-100%)
    """
    try:
        logger.info(f"开始完整分析流程: {task.id}")
        analysis_logger.info(f"🚀 完整分析流程启动: {task.id}")
        
        # 阶段1: 文档解析
        task.update_progress(10, "开始文档解析", "parsing")
        process_file_parsing(task)
        
        # 检查文档解析是否成功
        if task.status != "parsed":
            logger.error(f"文档解析失败: {task.id}")
            return
        
        # 获取解析结果
        parsing_result = redis_task_storage.get_parsing_result(task.id)
        if not parsing_result:
            logger.error(f"无法获取解析结果: {task.id}")
            return
        
        # 阶段2: 内容分析  
        task.update_progress(40, "开始内容分析", "content_analyzing")
        process_content_analysis(task, parsing_result)
        
        # 检查内容分析是否成功
        if task.status != "content_analyzed":
            logger.error(f"内容分析失败: {task.id}")
            return
        
        # 获取内容分析结果
        content_analysis = redis_task_storage.get_content_analysis(task.id)
        
        # 阶段3: AI设计方案
        task.update_progress(70, "开始AI设计方案", "ai_analyzing")
        process_ai_analysis(task, "comprehensive", content_analysis, parsing_result)
        
        # 检查AI分析是否成功
        if task.status != "ai_analyzed":
            logger.error(f"AI分析失败: {task.id}, 当前状态: {task.status}, 错误信息: {task.error}")
            # 即使AI分析状态不是ai_analyzed，如果form_data已经生成，也应该继续
            try:
                form_data_check = redis_task_storage.redis_manager.get(f"form_data:{task.id}")
                if form_data_check:
                    logger.info(f"检测到form_data已生成，继续完成流程: {task.id}")
                    task.update_progress(100, "完整分析流程完成", "fully_completed")
                    logger.info(f"完整分析流程成功完成: {task.id}")
                    analysis_logger.info(f"🎉 完整分析流程完成: {task.id}")
                    return
            except Exception as check_error:
                logger.error(f"检查form_data时出错: {check_error}")
            return
        
        # AI分析完成即完成所有流程（form_data已在AI分析阶段生成并保存）
        task.update_progress(100, "完整分析流程完成", "fully_completed")
        logger.info(f"完整分析流程成功完成: {task.id}")
        analysis_logger.info(f"🎉 完整分析流程完成: {task.id}")
        
    except Exception as e:
        logger.error(f"完整分析流程失败: {task.id}, 错误: {e}")
        task.error = f"分析流程失败: {str(e)}"
        task.status = "failed"
        task.update_progress(task.progress, f"分析失败: {str(e)}", "failed")


@app.route('/api/file/design-form/<task_id>', methods=['PUT'])
def update_design_form_data(task_id):
    """更新任务的设计方案表单数据"""
    try:
        # 记录API调用
        logger.info(f"收到设计方案表单数据更新请求: 任务ID={task_id}")
        
        # 获取请求数据
        data = request.get_json()
        if not data:
            logger.warning(f"表单数据更新请求缺少数据: {data}")
            return jsonify({
                "success": False,
                "error": "缺少请求数据"
            }), 400
        
        form_data = data.get('form_data', {})
        markdown_content = data.get('markdown_content', '')
        
        # 验证表单数据
        if not isinstance(form_data, dict):
            return jsonify({
                "success": False,
                "error": "form_data必须是对象类型"
            }), 400
        
        # 验证markdown内容
        if not isinstance(markdown_content, str):
            return jsonify({
                "success": False,
                "error": "markdown_content必须是字符串类型"
            }), 400
        
        # 验证任务是否存在
        task = get_task(task_id)
        if not task:
            logger.warning(f"尝试更新不存在的任务表单数据: {task_id}")
            return jsonify({
                "success": False,
                "error": "任务不存在"
            }), 404
        
        # 保存表单数据到Redis存储（使用redis_task_storage）
        try:
            # 使用现有的redis_task_storage来保存表单数据
            redis_task_storage.redis_manager.set(
                f"form_data:{task_id}", 
                form_data,  # RedisManager的set方法会自动JSON序列化
                ttl=86400 * 7  # 7天过期
            )
        except Exception as e:
            logger.error(f"保存表单数据到Redis失败: {e}")
            return jsonify({
                "success": False,
                "error": "保存表单数据失败"
            }), 500
        
        # 同时保存markdown内容
        if markdown_content:
            success = markdown_storage.save_markdown(task_id, markdown_content)
            if not success:
                logger.warning(f"保存Markdown内容失败，但表单数据已保存: {task_id}")
        
        # 更新任务对象
        task.form_data = form_data
        task.markdown_content = markdown_content
        
        # 记录操作日志
        logger.info(f"设计方案表单数据更新成功: 任务ID={task_id}, 表单字段数={len(form_data)}, Markdown长度={len(markdown_content)}")
        
        return jsonify({
            "success": True,
            "task_id": task_id,
            "form_fields_count": len(form_data),
            "markdown_length": len(markdown_content),
            "updated_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"更新设计方案表单数据失败: {e}")
        return jsonify({
            "success": False,
            "error": f"更新失败: {str(e)}"
        }), 500

@app.route('/api/file/design-form/<task_id>', methods=['GET'])
def get_design_form_data(task_id):
    """获取任务的设计方案表单数据"""
    try:
        # 记录API调用
        logger.info(f"收到设计方案表单数据获取请求: 任务ID={task_id}")
        
        # 验证任务是否存在
        task = get_task(task_id)
        if not task:
            logger.warning(f"尝试获取不存在的任务表单数据: {task_id}")
            return jsonify({
                "success": False,
                "error": "任务不存在"
            }), 404
        
        # 从Redis获取表单数据
        try:
            form_data = redis_task_storage.redis_manager.get(f"form_data:{task_id}")
            
            if form_data is None:
                logger.info(f"任务 {task_id} 尚未生成表单数据")
                return jsonify({
                    "success": False,
                    "error": "表单数据不存在",
                    "message": "该任务尚未生成设计方案表单数据"
                }), 404
        except Exception as e:
            logger.error(f"从Redis获取表单数据失败: {e}")
            return jsonify({
                "success": False,
                "error": "获取表单数据失败"
            }), 500
        
        # 同时获取markdown内容
        markdown_content = markdown_storage.get_markdown_content_only(task_id) or ""
        
        logger.info(f"设计方案表单数据获取成功: 任务ID={task_id}, 表单字段数={len(form_data)}")
        
        return jsonify({
            "success": True,
            "task_id": task_id,
            "form_data": form_data,
            "markdown_content": markdown_content,
            "form_fields_count": len(form_data),
            "markdown_length": len(markdown_content),
            "storage_source": "Redis存储",
            "retrieved_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取设计方案表单数据失败: {e}")
        return jsonify({
            "success": False,
            "error": f"获取失败: {str(e)}"
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8082, debug=True)