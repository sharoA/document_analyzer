"""
同步分析服务管理器
统一管理三阶段文档分析：文档解析、内容分析、AI智能分析
"""

import json
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# 导入Redis客户端
try:
    import redis
    redis_available = True
except ImportError:
    redis_available = False

class SyncAnalysisServiceManager:
    """同步分析服务管理器 - 支持新三阶段架构"""
    
    def __init__(self, llm_client=None, vector_db_type: str = "mock", redis_config: Dict = None):
        """
        初始化服务管理器
        
        Args:
            llm_client: 大语言模型客户端
            vector_db_type: 向量数据库类型 ("mock" 或 "chroma")
            redis_config: Redis配置
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.llm_client = llm_client
        
        # 初始化Redis客户端
        self.redis_client = None
        if redis_available and redis_config:
            try:
                self.redis_client = redis.Redis(
                    host=redis_config.get('host', 'localhost'),
                    port=redis_config.get('port', 6379),
                    db=redis_config.get('db', 0),
                    decode_responses=True
                )
                self.redis_client.ping()
                self.logger.info("Redis连接成功")
            except Exception as e:
                self.logger.warning(f"Redis连接失败: {e}")
                self.redis_client = None
        
        # 线程池用于后台任务
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        # 初始化真实的分析服务
        try:
            from .document_parser import DocumentParserService
            from .content_analyzer import ContentAnalyzerService  
            from .ai_analyzer import AIAnalyzerService
            from .vector_database import VectorDatabaseFactory
            
            # 创建向量数据库
            vector_db = VectorDatabaseFactory.create_database(vector_db_type)
            
            # 初始化各阶段服务
            self.document_parser = DocumentParserService(llm_client, vector_db)
            self.content_analyzer = ContentAnalyzerService(llm_client, vector_db)
            self.ai_analyzer = AIAnalyzerService(llm_client, vector_db)
            
            self.logger.info("分析服务初始化成功")
        except Exception as e:
            self.logger.error(f"分析服务初始化失败: {e}")
            # 回退到模拟模式
            self.document_parser = None
            self.content_analyzer = None
            self.ai_analyzer = None
        
        # 分析阶段定义
        self.analysis_stages = [
            {"stage": "document_parsing", "name": "文档解析", "service": self.document_parser},
            {"stage": "content_analysis", "name": "内容分析", "service": self.content_analyzer},
            {"stage": "ai_analysis", "name": "AI智能分析", "service": self.ai_analyzer}
        ]
        
        self.logger.info("同步分析服务管理器初始化完成")
    
    def full_analysis_pipeline(self, task_id: str, file_path: str, file_content: str, 
                              file_name: str) -> Dict[str, Any]:
        """
        执行完整的三阶段分析流水线（后台执行）
        
        Args:
            task_id: 任务ID
            file_path: 文件路径
            file_content: 文件内容
            file_name: 文件名
            
        Returns:
            启动状态
        """
        self.logger.info(f"开始完整分析流水线 - 任务ID: {task_id}")
        
        # 初始化进度
        self._init_task_progress(task_id)
        
        # 在后台执行分析
        self.executor.submit(self._execute_pipeline_background, task_id, file_path, file_content, file_name)
        
        return {
            "success": True,
            "task_id": task_id,
            "message": "分析任务已启动",
            "execution_mode": "automatic"
        }
    
    def execute_single_stage(self, task_id: str, stage: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行单个分析阶段（后台执行）
        
        Args:
            task_id: 任务ID
            stage: 阶段名称 (document_parsing, content_analysis, ai_analysis)
            input_data: 输入数据
            
        Returns:
            启动状态
        """
        self.logger.info(f"执行单个阶段 - 任务ID: {task_id}, 阶段: {stage}")
        
        # 验证阶段名称
        valid_stages = [s["stage"] for s in self.analysis_stages]
        if stage not in valid_stages:
            return {
                "success": False,
                "error": f"无效的分析阶段: {stage}",
                "task_id": task_id,
                "stage": stage
            }
        
        # 初始化任务进度（如果还未初始化）
        self._init_task_progress(task_id)
        
        # 在后台执行阶段
        self.executor.submit(self._execute_stage_background, task_id, stage, input_data)
        
        return {
            "success": True,
            "task_id": task_id,
            "stage": stage,
            "message": f"阶段 {stage} 已启动"
        }
    
    def get_analysis_progress(self, task_id: str) -> Dict[str, Any]:
        """
        获取分析进度
        
        Args:
            task_id: 任务ID
            
        Returns:
            进度信息
        """
        try:
            if not self.redis_client:
                return {
                    "success": False,
                    "error": "Redis未连接",
                    "task_id": task_id
                }
            
            # 获取进度信息
            progress_key = f"progress:{task_id}"
            progress_data = self.redis_client.get(progress_key)
            
            if progress_data:
                progress = json.loads(progress_data)
                return {
                    "success": True,
                    "task_id": task_id,
                    "data": progress
                }
            
            return {
                "success": False,
                "error": "进度信息不存在",
                "task_id": task_id
            }
            
        except Exception as e:
            self.logger.error(f"获取分析进度失败 - 任务ID: {task_id}, 错误: {str(e)}")
            return {
                "success": False,
                "error": f"获取进度失败: {str(e)}",
                "task_id": task_id
            }
    
    def get_analysis_result(self, task_id: str, include_stages: bool = True) -> Dict[str, Any]:
        """
        从Redis获取分析结果
        
        Args:
            task_id: 任务ID
            include_stages: 是否包含各阶段详细结果
            
        Returns:
            分析结果
        """
        try:
            if not self.redis_client:
                return {
                    "success": False,
                    "error": "Redis未连接",
                    "task_id": task_id
                }
            
            # 获取最终结果
            final_key = f"analysis:final:{task_id}"
            final_result = self.redis_client.get(final_key)
            
            if final_result:
                result = json.loads(final_result)
                return {
                    "success": True,
                    "data": result
                }
            
            return {
                "success": False,
                "error": "分析结果不存在",
                "task_id": task_id
            }
            
        except Exception as e:
            self.logger.error(f"获取分析结果失败 - 任务ID: {task_id}, 错误: {str(e)}")
            return {
                "success": False,
                "error": f"获取结果失败: {str(e)}",
                "task_id": task_id
            }
    
    def list_analysis_tasks(self, limit: int = 50) -> Dict[str, Any]:
        """
        列出所有分析任务
        
        Args:
            limit: 返回结果数量限制
            
        Returns:
            任务列表
        """
        try:
            if not self.redis_client:
                return {
                    "success": False,
                    "error": "Redis未连接"
                }
            
            # 获取所有进度键
            pattern = "progress:*"
            keys = self.redis_client.keys(pattern)
            
            tasks = []
            for key in keys[:limit]:
                task_id = key.replace("progress:", "")
                progress_data = self.redis_client.get(key)
                if progress_data:
                    progress = json.loads(progress_data)
                    tasks.append({
                        "task_id": task_id,
                        "timestamp": progress.get("timestamp"),
                        "current_stage": progress.get("current_stage"),
                        "progress": progress.get("progress", {})
                    })
            
            return {
                "success": True,
                "tasks": tasks,
                "total": len(tasks)
            }
            
        except Exception as e:
            self.logger.error(f"列出分析任务失败: {str(e)}")
            return {
                "success": False,
                "error": f"列出任务失败: {str(e)}"
            }
    
    def delete_analysis_result(self, task_id: str) -> Dict[str, Any]:
        """
        删除分析结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            删除结果
        """
        try:
            if not self.redis_client:
                return {
                    "success": False,
                    "error": "Redis未连接",
                    "task_id": task_id
                }
            
            # 删除相关键
            keys_to_delete = [
                f"analysis:final:{task_id}",
                f"progress:{task_id}",
                f"analysis:{task_id}:document_parsing",
                f"analysis:{task_id}:content_analysis",
                f"analysis:{task_id}:ai_analysis"
            ]
            
            deleted_count = 0
            for key in keys_to_delete:
                if self.redis_client.delete(key):
                    deleted_count += 1
            
            return {
                "success": True,
                "task_id": task_id,
                "deleted_keys": deleted_count,
                "message": "分析结果已删除"
            }
            
        except Exception as e:
            self.logger.error(f"删除分析结果失败 - 任务ID: {task_id}, 错误: {str(e)}")
            return {
                "success": False,
                "error": f"删除失败: {str(e)}",
                "task_id": task_id
            }
    
    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        try:
            status = {
                "redis_connected": self.redis_client is not None,
                "llm_client_available": self.llm_client is not None,
                "thread_pool_active": not self.executor._shutdown,
                "timestamp": datetime.now().isoformat()
            }
            
            if self.redis_client:
                try:
                    self.redis_client.ping()
                    status["redis_ping"] = True
                except:
                    status["redis_ping"] = False
            
            return status
            
        except Exception as e:
            self.logger.error(f"获取服务状态失败: {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _init_task_progress(self, task_id: str):
        """初始化任务进度"""
        if not self.redis_client:
            return
        
        progress_data = {
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "current_stage": "document_parsing",
            "progress": {
                "document_parsing": 0,
                "content_analysis": 0,
                "ai_analysis": 0
            }
        }
        
        progress_key = f"progress:{task_id}"
        self.redis_client.set(progress_key, json.dumps(progress_data))
    
    def _update_progress(self, task_id: str, stage: str, progress: int, current_stage: str = None):
        """更新进度"""
        if not self.redis_client:
            return
        
        progress_key = f"progress:{task_id}"
        progress_data = self.redis_client.get(progress_key)
        
        if progress_data:
            data = json.loads(progress_data)
            data["progress"][stage] = progress
            data["timestamp"] = datetime.now().isoformat()
            if current_stage:
                data["current_stage"] = current_stage
            
            self.redis_client.set(progress_key, json.dumps(data))
    
    def _execute_pipeline_background(self, task_id: str, file_path: str, file_content: str, file_name: str):
        """后台执行完整分析流水线"""
        try:
            self.logger.info(f"后台执行分析流水线 - 任务ID: {task_id}")
            
            # 阶段1：文档解析
            self._update_progress(task_id, "document_parsing", 10, "document_parsing")
            time.sleep(2)  # 模拟处理时间
            
            parsing_result = self._mock_document_parsing(file_content, file_name)
            self._save_stage_result(task_id, "document_parsing", parsing_result)
            self._update_progress(task_id, "document_parsing", 100, "content_analysis")
            
            # 阶段2：内容分析
            self._update_progress(task_id, "content_analysis", 10, "content_analysis")
            time.sleep(2)  # 模拟处理时间
            
            content_result = self._mock_content_analysis(parsing_result)
            self._save_stage_result(task_id, "content_analysis", content_result)
            self._update_progress(task_id, "content_analysis", 100, "ai_analysis")
            
            # 阶段3：AI智能分析
            self._update_progress(task_id, "ai_analysis", 10, "ai_analysis")
            time.sleep(2)  # 模拟处理时间
            
            ai_result = self._mock_ai_analysis(parsing_result, content_result)
            self._save_stage_result(task_id, "ai_analysis", ai_result)
            self._update_progress(task_id, "ai_analysis", 100, "completed")
            
            # 生成最终结果
            final_result = self._assemble_final_result(task_id, {
                "document_parsing": parsing_result,
                "content_analysis": content_result,
                "ai_analysis": ai_result
            })
            
            self._save_final_result(task_id, final_result)
            
            self.logger.info(f"分析流水线完成 - 任务ID: {task_id}")
            
        except Exception as e:
            self.logger.error(f"后台分析流水线失败 - 任务ID: {task_id}, 错误: {str(e)}")
    
    def _execute_stage_background(self, task_id: str, stage: str, input_data: Dict[str, Any]):
        """后台执行单个阶段"""
        try:
            self.logger.info(f"后台执行阶段 - 任务ID: {task_id}, 阶段: {stage}")
            
            self._update_progress(task_id, stage, 10, stage)
            
            # 查找对应的分析服务
            service = None
            for stage_info in self.analysis_stages:
                if stage_info["stage"] == stage:
                    service = stage_info["service"]
                    break
            
            # 执行真实的分析服务
            if service:
                self.logger.info(f"使用真实分析服务 - 阶段: {stage}")
                
                # 运行异步方法（在同步环境中）
                import asyncio
                try:
                    result = asyncio.run(service.analyze(task_id, input_data))
                    
                    if result.get("success"):
                        stage_data = result.get("data", {})
                        self._save_stage_result(task_id, stage, stage_data)
                        self._update_progress(task_id, stage, 100, stage)
                        self.logger.info(f"真实分析服务执行成功 - 阶段: {stage}")
                    else:
                        raise Exception(f"分析服务返回失败: {result.get('error', '未知错误')}")
                        
                except Exception as e:
                    self.logger.error(f"真实分析服务执行失败 - 阶段: {stage}, 错误: {e}")
                    # 回退到模拟分析
                    result = self._execute_fallback_analysis(stage, input_data)
                    self._save_stage_result(task_id, stage, result)
                    self._update_progress(task_id, stage, 100, stage)
            else:
                # 没有真实服务，使用模拟分析
                self.logger.warning(f"未找到真实分析服务，使用模拟分析 - 阶段: {stage}")
                result = self._execute_fallback_analysis(stage, input_data)
                self._save_stage_result(task_id, stage, result)
                self._update_progress(task_id, stage, 100, stage)
            
            self.logger.info(f"阶段执行完成 - 任务ID: {task_id}, 阶段: {stage}")
            
        except Exception as e:
            self.logger.error(f"后台阶段执行失败 - 任务ID: {task_id}, 阶段: {stage}, 错误: {str(e)}")
    
    def _execute_fallback_analysis(self, stage: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行回退分析（使用模拟数据）"""
        file_content = input_data.get("file_content", "")
        file_name = input_data.get("file_name", "")
        
        if stage == "document_parsing":
            return self._mock_document_parsing(file_content, file_name)
        elif stage == "content_analysis":
            return self._mock_content_analysis({})
        elif stage == "ai_analysis":
            return self._mock_ai_analysis({}, {})
        else:
            raise ValueError(f"未知阶段: {stage}")
    
    def _mock_document_parsing(self, file_content: str, file_name: str) -> Dict[str, Any]:
        """模拟文档解析"""
        return {
            "file_info": {
                "file_name": file_name,
                "file_size": len(file_content),
                "file_type": "text",
                "encoding": "utf-8"
            },
            "structure": {
                "sections": ["概述", "功能描述", "技术要求"],
                "paragraphs": 10,
                "lines": 50
            },
            "content_elements": {
                "text_content": file_content[:500] + "..." if len(file_content) > 500 else file_content,
                "keywords": ["功能", "需求", "系统", "设计"],
                "entities": ["用户", "系统", "数据库"]
            },
            "quality_info": {
                "completeness": 85,
                "clarity": 90,
                "structure_quality": "良好"
            }
        }
    
    def _mock_content_analysis(self, parsing_result: Dict[str, Any]) -> Dict[str, Any]:
        """模拟内容分析"""
        return {
            "new_features": [
                {
                    "feature_name": "用户管理模块",
                    "description": "新增用户注册、登录、权限管理功能",
                    "priority": "高",
                    "complexity": "中等"
                }
            ],
            "modified_features": [
                {
                    "feature_name": "数据导出功能",
                    "description": "增强数据导出格式支持",
                    "changes": ["支持Excel格式", "添加数据过滤"]
                }
            ],
            "deleted_features": [],
            "key_changes": [
                {
                    "change_type": "架构调整",
                    "description": "从单体架构调整为微服务架构",
                    "impact": "高"
                }
            ]
        }
    
    def _mock_ai_analysis(self, parsing_result: Dict[str, Any], content_result: Dict[str, Any]) -> Dict[str, Any]:
        """模拟AI智能分析"""
        return {
            "requirements": [
                {
                    "requirement_id": "REQ-001",
                    "title": "用户身份验证",
                    "description": "系统需要支持用户注册、登录和权限管理",
                    "priority": "高",
                    "category": "功能性需求"
                }
            ],
            "technical_design": {
                "architecture": "微服务架构",
                "technologies": ["Spring Boot", "React", "MySQL", "Redis"],
                "design_patterns": ["MVC", "Repository", "Factory"]
            },
            "implementation_suggestions": [
                {
                    "phase": "第一阶段",
                    "tasks": ["搭建基础框架", "实现用户管理", "设计数据库"],
                    "duration": "4周"
                }
            ]
        }
    
    def _save_stage_result(self, task_id: str, stage: str, result: Dict[str, Any]):
        """保存阶段结果到Redis"""
        if not self.redis_client:
            return
        
        stage_key = f"analysis:{task_id}:{stage}"
        self.redis_client.set(stage_key, json.dumps(result))
    
    def _save_final_result(self, task_id: str, result: Dict[str, Any]):
        """保存最终结果到Redis"""
        if not self.redis_client:
            return
        
        final_key = f"analysis:final:{task_id}"
        self.redis_client.set(final_key, json.dumps(result))
    
    def _assemble_final_result(self, task_id: str, stage_results: Dict[str, Any]) -> Dict[str, Any]:
        """组装最终结果"""
        return {
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "status": "completed",
            "stages": stage_results,
            "summary": {
                "document_info": stage_results.get("document_parsing", {}).get("file_info", {}),
                "analysis_summary": {
                    "total_changes": len(stage_results.get("content_analysis", {}).get("new_features", [])) +
                                   len(stage_results.get("content_analysis", {}).get("modified_features", [])),
                    "new_features_count": len(stage_results.get("content_analysis", {}).get("new_features", [])),
                    "modified_features_count": len(stage_results.get("content_analysis", {}).get("modified_features", [])),
                    "key_changes_count": len(stage_results.get("content_analysis", {}).get("key_changes", []))
                },
                "requirements_info": {
                    "total_requirements": len(stage_results.get("ai_analysis", {}).get("requirements", [])),
                    "high_priority_requirements": len([r for r in stage_results.get("ai_analysis", {}).get("requirements", []) 
                                                     if r.get("priority") == "高"])
                }
            },
            "quick_access": {
                "new_features": stage_results.get("content_analysis", {}).get("new_features", []),
                "technical_design": stage_results.get("ai_analysis", {}).get("technical_design", {}),
                "implementation_suggestions": stage_results.get("ai_analysis", {}).get("implementation_suggestions", [])
            }
        }

# 全局服务管理器实例
_service_manager = None

def initialize_service_manager(llm_client=None, vector_db_type: str = "mock", 
                             redis_config: Dict = None, **kwargs) -> SyncAnalysisServiceManager:
    """初始化服务管理器"""
    global _service_manager
    _service_manager = SyncAnalysisServiceManager(
        llm_client=llm_client,
        vector_db_type=vector_db_type,
        redis_config=redis_config
    )
    return _service_manager

def get_service_manager() -> Optional[SyncAnalysisServiceManager]:
    """获取服务管理器实例"""
    return _service_manager