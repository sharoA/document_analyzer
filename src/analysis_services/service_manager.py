"""
分析服务管理器
统一管理三阶段文档分析：文档解析、内容分析、AI智能分析
"""

import json
import logging
import asyncio
import time
import requests
from typing import Dict, Any, Optional
from datetime import datetime

# 导入Redis客户端
try:
    import redis
    redis_available = True
except ImportError:
    redis_available = False

# 导入WebSocket客户端
try:
    import socketio
    websocket_available = True
except ImportError:
    websocket_available = False

from .document_parser import DocumentParserService
from .content_analyzer import ContentAnalyzerService
from .ai_analyzer import AIAnalyzerService
from .vector_database import VectorDatabaseFactory, initialize_sample_data

class AnalysisServiceManager:
    """分析服务管理器 - 支持新三阶段架构"""
    
    def __init__(self, llm_client=None, vector_db_type: str = "mock", redis_config: Dict = None, **vector_db_kwargs):
        """
        初始化服务管理器
        
        Args:
            llm_client: 大语言模型客户端
            vector_db_type: 向量数据库类型 ("mock" 或 "chroma")
            redis_config: Redis配置
            **vector_db_kwargs: 向量数据库初始化参数
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
        
        # 初始化向量数据库
        try:
            self.vector_db = VectorDatabaseFactory.create_database(vector_db_type, **vector_db_kwargs)
            self.logger.info(f"初始化向量数据库: {vector_db_type}")
        except Exception as e:
            self.logger.error(f"向量数据库初始化失败: {str(e)}")
            # 使用模拟数据库作为备选
            self.vector_db = VectorDatabaseFactory.create_database("mock")
        
        # 初始化三个分析服务（适配新架构）
        self.document_parser = DocumentParserService(llm_client=llm_client, vector_db=self.vector_db)
        self.content_analyzer = ContentAnalyzerService(llm_client=llm_client, vector_db=self.vector_db)
        self.ai_analyzer = AIAnalyzerService(llm_client=llm_client, vector_db=self.vector_db)
        
        # 分析阶段定义
        self.analysis_stages = [
            {"stage": "document_parsing", "name": "文档解析", "service": self.document_parser},
            {"stage": "content_analysis", "name": "内容分析", "service": self.content_analyzer},
            {"stage": "ai_analysis", "name": "AI智能分析", "service": self.ai_analyzer}
        ]
        
        # 初始化WebSocket客户端用于推送进度
        self.websocket_client = None
        if websocket_available:
            try:
                self.websocket_client = socketio.SimpleClient(logger=False, engineio_logger=False)
                self.websocket_client.connect('http://localhost:8081', wait_timeout=5)
                self.logger.info("WebSocket客户端连接成功")
                
                # 测试连接
                self.websocket_client.emit('test_connection', {'test': True})
                self.logger.info("WebSocket客户端测试发送成功")
            except Exception as e:
                self.logger.error(f"WebSocket客户端连接失败: {e}")
                self.websocket_client = None
        
        self.logger.info("分析服务管理器初始化完成")
    
    def _emit_progress_update(self, task_id: str, stage: str, progress: int, status: str = "running"):
        """发送进度更新到WebSocket"""
        if not self.websocket_client:
            self.logger.warning(f"WebSocket客户端未连接，无法发送进度更新 - 任务: {task_id}, 阶段: {stage}")
            return
            
        try:
            progress_data = {
                "task_id": task_id,
                "stage": stage,
                "progress": progress,
                "status": status,
                "timestamp": datetime.now().isoformat()
            }
            
            self.websocket_client.emit('analysis_progress', progress_data)
            self.logger.info(f"✅ 发送进度更新成功 - 任务: {task_id}, 阶段: {stage}, 进度: {progress}%, 状态: {status}")
        except Exception as e:
            self.logger.error(f"❌ 发送进度更新失败: {e} - 任务: {task_id}, 阶段: {stage}")
    
    def _emit_stage_completed(self, task_id: str, stage: str, result: Dict[str, Any]):
        """发送阶段完成通知到WebSocket"""
        if not self.websocket_client:
            return
            
        try:
            completion_data = {
                "task_id": task_id,
                "stage": stage,
                "status": "completed",
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
            self.websocket_client.emit('stage_completed', completion_data)
            self.logger.info(f"发送阶段完成通知 - 任务: {task_id}, 阶段: {stage}")
        except Exception as e:
            self.logger.warning(f"发送阶段完成通知失败: {e}")
    
    def _emit_analysis_completed(self, task_id: str, results: Dict[str, Any]):
        """发送分析完成通知到WebSocket"""
        if not self.websocket_client:
            return
            
        try:
            completion_data = {
                "task_id": task_id,
                "status": "completed",
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
            
            self.websocket_client.emit('analysis_completed', completion_data)
            self.logger.info(f"发送分析完成通知 - 任务: {task_id}")
        except Exception as e:
            self.logger.warning(f"发送分析完成通知失败: {e}")
    
    def initialize(self):
        """初始化服务（加载示例数据等）"""
        try:
            initialize_sample_data(self.vector_db)
            self.logger.info("服务初始化完成")
        except Exception as e:
            self.logger.error(f"服务初始化失败: {str(e)}")
    
    def full_analysis_pipeline(self, task_id: str, file_path: str, file_content: str, 
                                   file_name: str, store_to_redis: bool = True) -> Dict[str, Any]:
        """
        执行完整的三阶段分析流水线
        
        Args:
            task_id: 任务ID
            file_path: 文件路径
            file_content: 文件内容
            file_name: 文件名
            store_to_redis: 是否存储到Redis
            
        Returns:
            完整的分析结果
        """
        self.logger.info(f"开始完整分析流水线 - 任务ID: {task_id}")
        
        try:
            results = {}
            
            # 阶段1：文档解析
            self._emit_progress_update(task_id, "document_parsing", 0, "started")
            
            stage1_input = {
                "file_path": file_path,
                "file_content": file_content,
                "file_name": file_name
            }
            
            # 推送进度：开始解析
            self._emit_progress_update(task_id, "document_parsing", 20, "running")
            
            parsing_result = self.document_parser.analyze(task_id, stage1_input)
            
            if not parsing_result.get("success"):
                return self._create_error_response(task_id, "document_parsing", parsing_result.get("error"))
            
            results["document_parsing"] = parsing_result.get("data", {})
            
            # 推送进度：文档解析完成
            self._emit_progress_update(task_id, "document_parsing", 100, "completed")
            self._emit_stage_completed(task_id, "document_parsing", results["document_parsing"])
            
            # 存储阶段1结果到Redis
            if store_to_redis:
                self._save_stage_result(task_id, "document_parsing", results["document_parsing"])
            
            # 阶段2：内容分析
            self._emit_progress_update(task_id, "content_analysis", 0, "started")
            
            stage2_input = {
                "document_parsing": results["document_parsing"]
            }
            
            # 推送进度：开始内容分析
            self._emit_progress_update(task_id, "content_analysis", 30, "running")
            
            content_result = self.content_analyzer.analyze(task_id, stage2_input)
            
            if not content_result.get("success"):
                return self._create_error_response(task_id, "content_analysis", content_result.get("error"))
            
            results["content_analysis"] = content_result.get("data", {})
            
            # 推送进度：内容分析完成
            self._emit_progress_update(task_id, "content_analysis", 100, "completed")
            self._emit_stage_completed(task_id, "content_analysis", results["content_analysis"])
            
            # 存储阶段2结果到Redis
            if store_to_redis:
                self._save_stage_result(task_id, "content_analysis", results["content_analysis"])
            
            # 阶段3：AI智能分析
            self._emit_progress_update(task_id, "ai_analysis", 0, "started")
            
            stage3_input = {
                "document_parsing": results["document_parsing"],
                "content_analysis": results["content_analysis"]
            }
            
            # 推送进度：开始AI分析
            self._emit_progress_update(task_id, "ai_analysis", 40, "running")
            
            ai_result = self.ai_analyzer.analyze(task_id, stage3_input)
            
            if not ai_result.get("success"):
                return self._create_error_response(task_id, "ai_analysis", ai_result.get("error"))
            
            results["ai_analysis"] = ai_result.get("data", {})
            
            # 推送进度：AI分析完成
            self._emit_progress_update(task_id, "ai_analysis", 100, "completed")
            self._emit_stage_completed(task_id, "ai_analysis", results["ai_analysis"])
            
            # 存储阶段3结果到Redis
            if store_to_redis:
                self._save_stage_result(task_id, "ai_analysis", results["ai_analysis"])
            
            # 生成最终结果
            final_result = self._assemble_final_result(task_id, results)
            
            # 存储最终结果到Redis
            if store_to_redis:
                self._save_final_result(task_id, final_result)
            
            # 推送最终完成通知
            self._emit_analysis_completed(task_id, final_result)
            
            self.logger.info(f"完整分析流水线完成 - 任务ID: {task_id}")
            return final_result
            
        except Exception as e:
            self.logger.error(f"分析流水线失败 - 任务ID: {task_id}, 错误: {str(e)}")
            return self._create_error_response(task_id, "pipeline", str(e))
    
    async def execute_single_stage(self, task_id: str, stage: str, input_data: Dict[str, Any], 
                                 store_to_redis: bool = True) -> Dict[str, Any]:
        """
        执行单个分析阶段
        
        Args:
            task_id: 任务ID
            stage: 阶段名称 (document_parsing, content_analysis, ai_analysis)
            input_data: 输入数据
            store_to_redis: 是否存储到Redis
            
        Returns:
            阶段分析结果
        """
        self.logger.info(f"执行单个阶段 - 任务ID: {task_id}, 阶段: {stage}")
        
        try:
            # 查找对应的服务
            service = None
            for stage_info in self.analysis_stages:
                if stage_info["stage"] == stage:
                    service = stage_info["service"]
                    break
            
            if not service:
                return {
                    "success": False,
                    "error": f"未知的分析阶段: {stage}",
                    "task_id": task_id,
                    "stage": stage
                }
            
            # 执行分析
            result = await service.analyze(task_id, input_data)
            
            # 存储结果到Redis
            if result.get("success") and store_to_redis:
                self._save_stage_result(task_id, stage, result.get("data", {}))
            
            return result
            
        except Exception as e:
            self.logger.error(f"单阶段分析失败 - 任务ID: {task_id}, 阶段: {stage}, 错误: {str(e)}")
            return {
                "success": False,
                "error": f"阶段{stage}执行失败: {str(e)}",
                "task_id": task_id,
                "stage": stage
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
                if not include_stages:
                    # 只返回摘要信息
                    return {
                        "success": True,
                        "task_id": task_id,
                        "timestamp": result.get("timestamp"),
                        "summary": result.get("summary", {})
                    }
                return {
                    "success": True,
                    "data": result
                }
            
            # 如果没有最终结果，尝试获取各阶段结果
            stage_results = {}
            for stage_info in self.analysis_stages:
                stage = stage_info["stage"]
                stage_key = f"analysis:{task_id}:{stage}"
                stage_result = self.redis_client.get(stage_key)
                if stage_result:
                    stage_results[stage] = json.loads(stage_result)
            
            if stage_results:
                return {
                    "success": True,
                    "task_id": task_id,
                    "partial_results": stage_results,
                    "status": "in_progress"
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
            
            # 获取所有最终结果键
            final_keys = self.redis_client.keys("analysis:final:*")
            
            tasks = []
            for key in final_keys[:limit]:
                task_id = key.split(":")[-1]
                result_data = self.redis_client.get(key)
                if result_data:
                    result = json.loads(result_data)
                    tasks.append({
                        "task_id": task_id,
                        "timestamp": result.get("timestamp"),
                        "summary": result.get("summary", {})
                    })
            
            return {
                "success": True,
                "tasks": sorted(tasks, key=lambda x: x.get("timestamp", ""), reverse=True),
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
            
            # 删除所有相关键
            keys_to_delete = []
            
            # 最终结果键
            keys_to_delete.append(f"analysis:final:{task_id}")
            
            # 各阶段结果键
            for stage_info in self.analysis_stages:
                keys_to_delete.append(f"analysis:{task_id}:{stage_info['stage']}")
            
            deleted_count = 0
            for key in keys_to_delete:
                if self.redis_client.delete(key):
                    deleted_count += 1
            
            return {
                "success": True,
                "task_id": task_id,
                "deleted_keys": deleted_count,
                "message": f"已删除任务 {task_id} 的 {deleted_count} 个结果"
            }
            
        except Exception as e:
            self.logger.error(f"删除分析结果失败 - 任务ID: {task_id}, 错误: {str(e)}")
            return {
                "success": False,
                "error": f"删除失败: {str(e)}",
                "task_id": task_id
            }
    
    def _save_stage_result(self, task_id: str, stage: str, result: Dict[str, Any]):
        """保存阶段结果到Redis"""
        if not self.redis_client:
            return
            
        try:
            key = f"analysis:{task_id}:{stage}"
            self.redis_client.setex(key, 3600 * 24, json.dumps(result, ensure_ascii=False))
            self.logger.info(f"阶段结果已保存 - Task: {task_id}, Stage: {stage}")
        except Exception as e:
            self.logger.error(f"保存阶段结果失败: {e}")
    
    def _save_final_result(self, task_id: str, result: Dict[str, Any]):
        """保存最终结果到Redis"""
        if not self.redis_client:
            return
            
        try:
            key = f"analysis:final:{task_id}"
            self.redis_client.setex(key, 3600 * 24 * 7, json.dumps(result, ensure_ascii=False))
            self.logger.info(f"最终结果已保存 - Task: {task_id}")
        except Exception as e:
            self.logger.error(f"保存最终结果失败: {e}")
    
    def _assemble_final_result(self, task_id: str, stage_results: Dict[str, Any]) -> Dict[str, Any]:
        """组装最终分析结果"""
        try:
            # 提取各阶段的关键信息
            document_parsing = stage_results.get("document_parsing", {})
            content_analysis = stage_results.get("content_analysis", {})
            ai_analysis = stage_results.get("ai_analysis", {})
            
            # 生成综合摘要
            summary = {
                "task_id": task_id,
                "timestamp": datetime.now().isoformat(),
                "document_info": {
                    "file_type": document_parsing.get("file_info", {}).get("file_type", "unknown"),
                    "file_size": document_parsing.get("file_info", {}).get("file_size", 0),
                    "quality_score": document_parsing.get("quality_info", {}).get("overall_score", 0),
                    "structure_quality": document_parsing.get("structure", {}).get("structure_quality", "unknown")
                },
                "analysis_summary": {
                    "total_changes": content_analysis.get("analysis_summary", {}).get("total_changes", 0),
                    "new_features_count": content_analysis.get("analysis_summary", {}).get("new_features_count", 0),
                    "modified_features_count": content_analysis.get("analysis_summary", {}).get("modified_features_count", 0),
                    "key_changes_count": content_analysis.get("analysis_summary", {}).get("key_changes_count", 0),
                    "change_complexity": content_analysis.get("analysis_summary", {}).get("change_complexity", "unknown")
                },
                "requirements_info": {
                    "total_requirements": len(ai_analysis.get("requirements", [])),
                    "high_priority_requirements": len([r for r in ai_analysis.get("requirements", []) if r.get("priority") == "必须"]),
                    "estimated_effort": content_analysis.get("analysis_summary", {}).get("estimated_total_effort", "unknown")
                }
            }
            
            # 组装完整结果
            final_result = {
                "task_id": task_id,
                "timestamp": datetime.now().isoformat(),
                "status": "completed",
                "summary": summary,
                "stages": stage_results,
                "quick_access": {
                    "requirements": ai_analysis.get("requirements", []),
                    "new_features": content_analysis.get("new_features", []),
                    "technical_design": ai_analysis.get("technical_design", ""),
                    "implementation_suggestions": ai_analysis.get("implementation_suggestions", ""),
                    "analysis_summary": ai_analysis.get("analysis_summary", "")
                }
            }
            
            return {
                "success": True,
                "data": final_result
            }
            
        except Exception as e:
            self.logger.error(f"组装最终结果失败: {str(e)}")
            return {
                "success": False,
                "error": f"组装结果失败: {str(e)}",
                "task_id": task_id
            }
    
    def _create_error_response(self, task_id: str, stage: str, error: str) -> Dict[str, Any]:
        """创建错误响应"""
        return {
            "success": False,
            "error": error,
            "task_id": task_id,
            "failed_stage": stage,
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        try:
            status = {
                "service_manager": "running",
                "services": {
                    "document_parser": "available",
                    "content_analyzer": "available", 
                    "ai_analyzer": "available"
                },
                "integrations": {
                    "llm_client": "connected" if self.llm_client else "disconnected",
                    "vector_db": "connected" if self.vector_db else "disconnected",
                    "redis": "connected" if self.redis_client else "disconnected"
            },
                "analysis_stages": [stage["name"] for stage in self.analysis_stages],
                "capabilities": {
                    "full_pipeline": True,
                    "single_stage": True,
                    "result_storage": bool(self.redis_client),
                    "result_retrieval": bool(self.redis_client)
                }
            }
            
            return {
                "success": True,
                "status": status
            }
            
        except Exception as e:
            self.logger.error(f"获取服务状态失败: {str(e)}")
            return {
                "success": False,
                "error": f"获取状态失败: {str(e)}"
        }
    
    async def cleanup(self):
        """清理资源"""
        try:
            self.logger.info("开始清理服务管理器资源...")
            
            # 关闭Redis连接
            if self.redis_client:
                self.redis_client.close()
                
            self.logger.info("服务管理器资源清理完成")
        except Exception as e:
            self.logger.error(f"清理资源时出错: {e}")

# 全局服务管理器实例
_service_manager_instance = None

def get_service_manager() -> Optional[AnalysisServiceManager]:
    """获取全局服务管理器实例"""
    global _service_manager_instance
    return _service_manager_instance

def initialize_service_manager(llm_client=None, vector_db_type: str = "mock", 
                             redis_config: Dict = None, **kwargs) -> AnalysisServiceManager:
    """
    初始化全局服务管理器
    
    Args:
        llm_client: 大语言模型客户端
        vector_db_type: 向量数据库类型
        redis_config: Redis配置
        **kwargs: 其他参数
        
    Returns:
        服务管理器实例
    """
    global _service_manager_instance
    
    _service_manager_instance = AnalysisServiceManager(
        llm_client=llm_client,
        vector_db_type=vector_db_type,
        redis_config=redis_config,
        **kwargs
    )
    
    return _service_manager_instance

async def initialize_services(llm_client=None, vector_db_type: str = "mock", 
                            redis_config: Dict = None, **kwargs):
    """异步初始化服务"""
    manager = initialize_service_manager(llm_client, vector_db_type, redis_config, **kwargs)
    await manager.initialize()
    return manager 