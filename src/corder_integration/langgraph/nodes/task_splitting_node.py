#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务拆分节点 - 重构版本
实现滑动窗口机制和SQLite任务存储
"""

import logging
import json
import sqlite3
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
import os
import time

# 导入客户端
try:
    from src.utils.volcengine_client import get_volcengine_client
    VOLCENGINE_AVAILABLE = True
except ImportError:
    logging.warning("火山引擎客户端不可用")
    VOLCENGINE_AVAILABLE = False

logger = logging.getLogger(__name__)

class TaskSplittingPrompts:
    """任务拆分提示词管理器 - 简化版本"""
    
    def __init__(self):
        # 设置模板目录
        template_dir = os.path.join(
            os.path.dirname(__file__), 
            "..", 
            "prompts"
        )
        
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # 模板文件映射 - 完整映射
        self.template_files = {
            "design_analysis": "task_splitting/design_analysis_prompts.jinja2", 
            "service_boundary": "task_splitting/service_boundary_prompts.jinja2",
            "dependency_analysis": "task_splitting/dependency_analysis_prompts.jinja2",
            "task_scheduling": "task_splitting/task_scheduling_prompts.jinja2",
            "generate_sqlite_tasks": "task_splitting/generate_sqlite_tasks_prompts.jinja2"
        }
        
        self.templates = {}
        self._load_templates()
    
    def _load_templates(self):
        """加载模板文件"""
        for prompt_type, template_file in self.template_files.items():
            try:
                template = self.jinja_env.get_template(template_file)
                self.templates[prompt_type] = template
                logger.info(f"✅ 模板 {template_file} 加载成功")
            except TemplateNotFound:
                logger.warning(f"⚠️ 模板文件 {template_file} 未找到，使用内置模板")
                self.templates[prompt_type] = None
            except Exception as e:
                logger.error(f"❌ 加载模板 {template_file} 失败: {e}")
                self.templates[prompt_type] = None
    
    def get_prompt(self, prompt_type: str, **kwargs) -> str:
        """获取渲染后的提示词"""
        try:
            # 尝试从模板文件获取
            template = self.templates.get(prompt_type)
            if template:
                # 调用对应的宏
                macro_name = f"{prompt_type}_prompt"
                if hasattr(template.module, macro_name):
                    macro = getattr(template.module, macro_name)
                    return macro(**kwargs)
            
            # 使用内置默认提示词
            logger.warning(f"⚠️ 使用内置提示词: {prompt_type}")
            return self._get_builtin_prompt(prompt_type, **kwargs)
            
        except Exception as e:
            logger.error(f"❌ 渲染提示词失败: {e}")
            return self._get_builtin_prompt(prompt_type, **kwargs)
    
    def _get_builtin_prompt(self, prompt_type: str, **kwargs) -> str:
        """内置默认提示词"""
        builtin_templates = {
            "design_analysis": """你是系统架构师。分析设计文档，输出JSON格式结果。  
设计文档: {design_doc}
项目名称: {project_name}
输出格式: {{"architecture_style": "", "functional_modules": [], "summary": ""}}""",
            
            "service_boundary": """你是微服务专家。进行服务拆分，输出JSON格式结果。
设计概要: {design_summary}
架构概要: {architecture_summary}
输出格式: {{"identified_services": [], "summary": ""}}""",
            
            "dependency_analysis": """你是依赖分析专家。分析服务依赖，输出JSON格式结果。
服务概要: {services_summary}
输出格式: {{"service_dependencies": {{}}, "summary": ""}}""",
            
            "task_scheduling": """你是调度专家。制定执行计划，输出JSON格式结果。
服务概要: {services_summary}
依赖概要: {dependencies_summary}
输出格式: {{"execution_phases": [], "summary": ""}}""",
            
            "generate_sqlite_tasks": """你是任务管理专家。生成SQLite任务，输出JSON格式结果。
执行计划: {execution_plan}
服务概要: {services_summary}
基础项目路径: {base_project_path}

**路径一致性要求：**
- git_clone任务的local_path: {base_project_path}/服务目录名
- code_analysis任务的project_path: {base_project_path}/服务目录名
- api任务的project_path: {base_project_path}/服务目录名
- config任务的config_file: {base_project_path}/服务目录名/配置文件路径
- deployment任务的path: {base_project_path}/服务目录名
- **所有路径字段必须使用完全相同的基础路径格式**

请输出JSON格式的任务列表：
{{
  "tasks": [
    {{
      "task_id": "task_001",
      "service_name": "服务名称",
      "task_type": "git_clone",
      "priority": 1,
      "dependencies": [],
      "estimated_duration": "10分钟",
      "description": "任务描述",
      "parameters": {{
        "git_url": "仓库地址",
        "local_path": "{base_project_path}/服务目录名"
      }}
    }},
    {{
      "task_id": "task_002",
      "service_name": "服务名称",
      "task_type": "code_analysis",
      "priority": 2,
      "dependencies": ["task_001"],
      "estimated_duration": "20分钟",
      "description": "代码分析任务描述",
      "parameters": {{
        "project_path": "{base_project_path}/服务目录名",
        "target_controller": "ControllerName",
        "target_api": "/api/path"
      }}
    }},
    {{
      "task_id": "task_003",
      "service_name": "服务名称",
      "task_type": "api",
      "priority": 3,
      "dependencies": ["task_002"],
      "estimated_duration": "30分钟",
      "description": "API任务描述",
      "parameters": {{
        "project_path": "{base_project_path}/服务目录名",
        "api_path": "/api/path",
        "http_method": "GET"
      }}
    }}
  ],
  "summary": "任务生成概要"
}}"""
        }
        
        template_str = builtin_templates.get(prompt_type, "")
        if template_str:
            return template_str.format(**kwargs)
        return ""

class SlidingWindowManager:
    """滑动窗口管理器 - 滑动窗口实现"""
    
    def __init__(self, max_window_size: int = 2500, overlap_size: int = 300):
        self.max_window_size = max_window_size
        self.overlap_size = overlap_size  # 窗口重叠大小
        self.context_history = []
        
    def add_context(self, context: str, context_type: str):
        """添加上下文信息"""
        self.context_history.append({
            "type": context_type,
            "content": context,
            "timestamp": datetime.now()
        })
        
        # 保持最近的5个上下文
        if len(self.context_history) > 5:
            self.context_history = self.context_history[-5:]
    
    def get_context_window(self) -> Optional[str]:
        """获取当前上下文窗口"""
        if not self.context_history:
            return None
        
        # 组合最近的上下文
        contexts = []
        for ctx in self.context_history[-3:]:  # 最近3个上下文
            contexts.append(f"[{ctx['type']}]: {ctx['content'][:300]}...")
        
        return "\n".join(contexts)
    
    def split_text_into_windows(self, text: str) -> List[Dict[str, Any]]:
        """将文本分割成滑动窗口片段"""
        if len(text) <= self.max_window_size:
            return [{
                "content": text,
                "window_id": 1,
                "is_complete": True,
                "start_pos": 0,
                "end_pos": len(text)
            }]
        
        windows = []
        start_pos = 0
        window_id = 1
        
        while start_pos < len(text):
            # 计算当前窗口的结束位置
            end_pos = min(start_pos + self.max_window_size, len(text))
            
            # 如果不是最后一个窗口，尝试在句号或换行符处切分
            if end_pos < len(text):
                # 向后查找合适的切分点（句号、换行符、中文句号）
                for i in range(end_pos - 100, end_pos):
                    if i > 0 and text[i] in '.。\n':
                        end_pos = i + 1
                        break
            
            window_content = text[start_pos:end_pos]
            windows.append({
                "content": window_content,
                "window_id": window_id,
                "is_complete": end_pos >= len(text),
                "start_pos": start_pos,
                "end_pos": end_pos,
                "total_windows": None  # 稍后填充
            })
            
            # 下一个窗口的起始位置（有重叠）
            if end_pos >= len(text):
                break
            start_pos = end_pos - self.overlap_size
            window_id += 1
        
        # 填充总窗口数
        for window in windows:
            window["total_windows"] = len(windows)
            
        logger.info(f"📄 文档分割完成：{len(text)} 字符 -> {len(windows)} 个窗口")
        return windows
    
    def merge_analysis_results(self, results: List[Dict[str, Any]], analysis_type: str) -> Dict[str, Any]:
        """合并多个窗口的分析结果"""
        if not results:
            return {"summary": f"{analysis_type}分析无结果", "merged": True}
        
        if len(results) == 1:
            return results[0]
        
        logger.info(f"🔄 合并 {len(results)} 个{analysis_type}分析结果...")
        
        # 根据分析类型进行不同的合并策略
        if analysis_type == "设计分析":
            return self._merge_design_analysis(results)
        elif analysis_type == "服务拆分":
            return self._merge_service_boundary(results)
        elif analysis_type == "依赖分析":
            return self._merge_dependency_analysis(results)
        elif analysis_type == "任务调度":
            return self._merge_task_scheduling(results)
        elif analysis_type == "任务生成":
            return self._merge_task_generation(results)
        else:
            return self._merge_generic(results, analysis_type)
    
    def _merge_design_analysis(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并设计分析结果"""
        merged = {
            "architecture_style": results[0].get("architecture_style", "微服务"),
            "technology_stack": [],
            "functional_modules": [],
            "system_components": [],
            "data_flow": [],
            "integration_points": [],
            "summary": ""
        }
        
        summaries = []
        for result in results:
            # 合并技术栈（去重）
            if result.get("technology_stack"):
                merged["technology_stack"].extend(result["technology_stack"])
            
            # 合并功能模块
            if result.get("functional_modules"):
                merged["functional_modules"].extend(result["functional_modules"])
            
            # 合并系统组件
            if result.get("system_components"):
                merged["system_components"].extend(result["system_components"])
                
            # 合并数据流
            if result.get("data_flow"):
                merged["data_flow"].extend(result["data_flow"])
                
            # 合并集成点
            if result.get("integration_points"):
                merged["integration_points"].extend(result["integration_points"])
            
            # 收集概要
            if result.get("summary"):
                summaries.append(result["summary"])
        
        # 去重
        merged["technology_stack"] = list(set(merged["technology_stack"]))
        merged["system_components"] = list(set(merged["system_components"]))
        merged["data_flow"] = list(set(merged["data_flow"]))
        merged["integration_points"] = list(set(merged["integration_points"]))
        
        # 合并概要
        merged["summary"] = " ".join(summaries)[:200] if summaries else "设计分析完成"
        
        return merged
    
    def _merge_service_boundary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并服务边界分析结果"""
        all_services = []
        summaries = []
        
        for result in results:
            if result.get("identified_services"):
                all_services.extend(result["identified_services"])
            if result.get("summary"):
                summaries.append(result["summary"])
        
        # 去重服务（基于name字段）
        unique_services = []
        seen_names = set()
        for service in all_services:
            name = service.get("name", "")
            if name and name not in seen_names:
                unique_services.append(service)
                seen_names.add(name)
        
        return {
            "identified_services": unique_services,
            "summary": " ".join(summaries)[:200] if summaries else "服务拆分完成"
        }
    
    def _merge_dependency_analysis(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并依赖分析结果"""
        merged_dependencies = {}
        summaries = []
        critical_paths = []
        
        for result in results:
            if result.get("service_dependencies"):
                merged_dependencies.update(result["service_dependencies"])
            if result.get("summary"):
                summaries.append(result["summary"])
            if result.get("critical_path"):
                critical_paths.extend(result["critical_path"])
        
        return {
            "service_dependencies": merged_dependencies,
            "critical_path": list(set(critical_paths)),
            "summary": " ".join(summaries)[:200] if summaries else "依赖分析完成"
        }
    
    def _merge_task_scheduling(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并任务调度结果"""
        all_phases = []
        all_parallel_groups = []
        execution_orders = []
        summaries = []
        
        for result in results:
            if result.get("execution_phases"):
                all_phases.extend(result["execution_phases"])
            if result.get("parallel_groups"):
                all_parallel_groups.extend(result["parallel_groups"])
            if result.get("execution_order"):
                execution_orders.extend(result["execution_order"])
            if result.get("summary"):
                summaries.append(result["summary"])
        
        return {
            "execution_phases": all_phases,
            "parallel_groups": all_parallel_groups,
            "execution_order": list(set(execution_orders)),
            "summary": " ".join(summaries)[:200] if summaries else "任务调度完成"
        }
    
    def _merge_task_generation(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并任务生成结果"""
        all_tasks = []
        summaries = []
        
        for result in results:
            if result.get("tasks"):
                all_tasks.extend(result["tasks"])
            if result.get("summary"):
                summaries.append(result["summary"])
        
        # 去重任务（基于task_id字段）
        unique_tasks = []
        seen_ids = set()
        for task in all_tasks:
            task_id = task.get("task_id", "")
            if task_id and task_id not in seen_ids:
                unique_tasks.append(task)
                seen_ids.add(task_id)
            elif not task_id:
                # 为没有ID的任务生成唯一ID
                import uuid
                task["task_id"] = f"task_{str(uuid.uuid4())[:8]}"
                unique_tasks.append(task)
        
        return {
            "tasks": unique_tasks,
            "total_tasks": len(unique_tasks),
            "summary": " ".join(summaries)[:200] if summaries else "任务生成完成"
        }
    
    def _merge_generic(self, results: List[Dict[str, Any]], analysis_type: str) -> Dict[str, Any]:
        """通用合并方法"""
        merged = {}
        summaries = []
        
        for result in results:
            for key, value in result.items():
                if key == "summary":
                    if value:
                        summaries.append(value)
                elif key not in merged:
                    merged[key] = value
                elif isinstance(value, list):
                    if isinstance(merged[key], list):
                        merged[key].extend(value)
                elif isinstance(value, dict):
                    if isinstance(merged[key], dict):
                        merged[key].update(value)
        
        merged["summary"] = " ".join(summaries)[:200] if summaries else f"{analysis_type}完成"
        return merged

class TaskStorageManager:
    """任务存储管理器 - 增强的SQLite数据库操作，支持Windows环境
    
    📝 注意：此数据库专门用于存储执行任务，与LangGraph检查点数据库(workflow_checkpoints.db)分离
    """
    
    def __init__(self, db_path: str = "coding_agent_workflow.db"):
        """初始化任务存储管理器
        
        Args:
            db_path: 任务数据库文件路径 (默认: coding_agent_workflow.db)
                    注意：与LangGraph检查点数据库分离，避免冲突
        """
        self.db_path = db_path
        self.max_retries = 3
        self.retry_delay = 1.0
        self._init_database()
    
    def _get_connection(self):
        """获取数据库连接，设置WAL模式和超时"""
        conn = sqlite3.connect(
            self.db_path, 
            timeout=30.0,  # 30秒超时
            isolation_level=None  # 自动提交模式
        )
        
        # 设置WAL模式和优化参数
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL") 
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=memory")
        conn.execute("PRAGMA mmap_size=268435456")  # 256MB
        
        return conn
    
    def _execute_with_retry(self, operation_func, *args, **kwargs):
        """带重试机制的数据库操作"""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                return operation_func(*args, **kwargs)
            except sqlite3.OperationalError as e:
                last_error = e
                if "database is locked" in str(e):
                    logger.warning(f"🔄 数据库锁定，第{attempt + 1}次重试...")
                    time.sleep(self.retry_delay * (2 ** attempt))  # 指数退避
                    continue
                else:
                    raise e
            except Exception as e:
                logger.error(f"❌ 数据库操作失败: {e}")
                raise e
        
        logger.error(f"❌ 数据库操作重试{self.max_retries}次后仍然失败")
        if last_error is not None:
            raise last_error
        else:
            raise RuntimeError(f"数据库操作重试{self.max_retries}次后失败")
    
    def force_unlock_database(self):
        """强制解锁数据库（Windows环境特殊处理）"""
        try:
            import os
            import time
            
            # 强制关闭所有WAL相关文件
            wal_file = f"{self.db_path}-wal"
            shm_file = f"{self.db_path}-shm"
            
            # 尝试删除WAL文件
            for file_path in [wal_file, shm_file]:
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        logger.info(f"✅ 删除WAL文件: {file_path}")
                    except PermissionError:
                        logger.warning(f"⚠️ 无法删除文件 {file_path}，可能被其他进程占用")
            
            # 执行VACUUM和优化
            try:
                with self._get_connection() as conn:
                    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                    conn.execute("VACUUM")
                logger.info("✅ 数据库WAL检查点和优化完成")
            except Exception as e:
                logger.warning(f"⚠️ WAL检查点操作失败: {e}")
                
        except Exception as e:
            logger.error(f"❌ 强制解锁失败: {e}")
    
    def reset_database(self):
        """重置数据库表结构"""
        def _reset_operation():
            # 先尝试强制解锁
            self.force_unlock_database()
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 删除旧表
                cursor.execute("DROP TABLE IF EXISTS execution_tasks")
                
                # 重新创建表
                cursor.execute("""
                    CREATE TABLE execution_tasks (
                        task_id TEXT PRIMARY KEY,
                        service_name TEXT NOT NULL,
                        task_type TEXT NOT NULL,  -- database|api|service|config|test|deployment
                        priority INTEGER DEFAULT 1,
                        status TEXT DEFAULT 'pending',
                        dependencies TEXT,  -- JSON array
                        estimated_duration TEXT,
                        description TEXT,
                        deliverables TEXT,  -- JSON array - 具体交付物
                        implementation_details TEXT,  -- 详细实现说明
                        completion_criteria TEXT,  -- 完成标准
                        parameters TEXT,     -- JSON object - 增强的参数
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                logger.info("✅ 数据库表结构重置完成")
        
        try:
            self._execute_with_retry(_reset_operation)
        except Exception as e:
            logger.error(f"❌ 数据库重置失败: {e}")
            # 尝试极端情况下的修复
            try:
                self.force_unlock_database()
                time.sleep(2)  # 等待2秒
                self._execute_with_retry(_reset_operation)
            except Exception as final_error:
                logger.error(f"❌ 最终数据库重置失败: {final_error}")
    
    def _init_database(self):
        """初始化数据库表"""
        def _init_operation():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 创建任务表 - 支持细粒度任务
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS execution_tasks (
                        task_id TEXT PRIMARY KEY,
                        service_name TEXT NOT NULL,
                        task_type TEXT NOT NULL,  -- database|api|service|config|test|deployment
                        priority INTEGER DEFAULT 1,
                        status TEXT DEFAULT 'pending',
                        dependencies TEXT,  -- JSON array
                        estimated_duration TEXT,
                        description TEXT,
                        deliverables TEXT,  -- JSON array - 具体交付物
                        implementation_details TEXT,  -- 详细实现说明
                        completion_criteria TEXT,  -- 完成标准
                        parameters TEXT,     -- JSON object - 增强的参数
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                logger.info("✅ 任务数据库初始化完成")
        
        try:
            self._execute_with_retry(_init_operation)
        except Exception as e:
            logger.error(f"❌ 数据库初始化失败: {e}")
            # 尝试强制解锁后重试
            self.force_unlock_database()
            time.sleep(1)
            try:
                self._execute_with_retry(_init_operation)
            except Exception as final_error:
                logger.error(f"❌ 最终数据库初始化失败: {final_error}")
    
    def save_tasks(self, tasks: List[Dict[str, Any]]) -> bool:
        """保存任务到数据库"""
        def _save_operation():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                for task in tasks:
                    cursor.execute("""
                        INSERT OR REPLACE INTO execution_tasks 
                        (task_id, service_name, task_type, priority, dependencies, 
                         estimated_duration, description, deliverables, 
                         implementation_details, completion_criteria, parameters)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        task.get('task_id', str(uuid.uuid4())),
                        task.get('service_name', ''),
                        task.get('task_type', 'code_generation'),
                        task.get('priority', 1),
                        json.dumps(task.get('dependencies', [])),
                        task.get('estimated_duration', '30分钟'),
                        task.get('description', ''),
                        json.dumps(task.get('deliverables', [])),
                        task.get('implementation_details', ''),
                        task.get('completion_criteria', ''),
                        json.dumps(task.get('parameters', {}))
                    ))
                
                logger.info(f"✅ 已保存 {len(tasks)} 个任务到数据库")
                return True
        
        try:
            return self._execute_with_retry(_save_operation)
        except Exception as e:
            logger.error(f"❌ 保存任务失败: {e}")
            return False
    
    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """获取待执行的任务"""
        def _get_operation():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT task_id, service_name, task_type, priority, dependencies,
                           estimated_duration, description, deliverables,
                           implementation_details, completion_criteria, parameters
                    FROM execution_tasks 
                    WHERE status = 'pending'
                    ORDER BY priority ASC, created_at ASC
                """)
                
                tasks = []
                for row in cursor.fetchall():
                    tasks.append({
                        'task_id': row[0],
                        'service_name': row[1],
                        'task_type': row[2],
                        'priority': row[3],
                        'dependencies': json.loads(row[4] or '[]'),
                        'estimated_duration': row[5],
                        'description': row[6],
                        'deliverables': json.loads(row[7] or '[]'),
                        'implementation_details': row[8],
                        'completion_criteria': row[9],
                        'parameters': json.loads(row[10] or '{}')
                    })
                
                return tasks
        
        try:
            return self._execute_with_retry(_get_operation)
        except Exception as e:
            logger.error(f"❌ 获取任务失败: {e}")
            return []

async def task_splitting_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    任务拆分节点 - 重构版本
    实现滑动窗口机制和SQLite任务存储
    """
    
    logger.info(f"🚀 开始执行任务拆分: {state['project_name']}")
    logger.info(f"📥 输入状态键: {list(state.keys())}")
    logger.info(f"📄 设计文档长度: {len(state.get('design_doc', ''))}")
    logger.info(f"🔄 当前阶段: {state.get('current_phase', 'unknown')}")
    
    # 🔧 计算项目路径，与git_management_node保持一致
    output_path = state.get('output_path', '/Users/renyu/Documents/create_project')
    project_name = state.get('project_name', 'unknown_project')
    base_project_path = f"{output_path}/{project_name}"
    logger.info(f"📁 计算的基础项目路径: {base_project_path}")
    
    # 初始化组件
    if not VOLCENGINE_AVAILABLE:
        logger.error("❌ 火山引擎客户端不可用")
        state["execution_errors"].append("火山引擎客户端不可用")
        return state
    
    client = get_volcengine_client()
    prompts = TaskSplittingPrompts()
    window_manager = SlidingWindowManager(max_window_size=2000)
    task_storage = TaskStorageManager()
    
    # 🔧 重置数据库表结构以支持新的任务字段
    task_storage.reset_database()
    
    try:
        # 🧠 步骤1：设计文档分析（使用真正的滑动窗口）
        logger.info("📋 步骤1：开始设计文档分析...")
        
        # 将设计文档分割成滑动窗口
        design_windows = window_manager.split_text_into_windows(state["design_doc"])
        logger.info(f"📄 设计文档分割成 {len(design_windows)} 个窗口")
        
        # 对每个窗口进行分析
        window_results = []
        for window in design_windows:
            total_windows = window.get('total_windows', len(design_windows))
            logger.info(f"📝 分析窗口 {window['window_id']}/{total_windows} (字符: {window['start_pos']}-{window['end_pos']})")
            
            design_analysis_prompt = prompts.get_prompt(
                "design_analysis", 
                design_doc=window["content"],
                project_name=state["project_name"],
                context_window=window_manager.get_context_window()
            )
            
            design_analysis_result = client.chat(
                messages=[
                    {"role": "system", "content": f"你是专业的系统架构师。正在分析第 {window['window_id']}/{total_windows} 个文档片段。"},
                    {"role": "user", "content": design_analysis_prompt}
                ],
                temperature=0.3
            )
            
            # 解析单个窗口的结果
            window_data = _extract_json_from_response(design_analysis_result)
            window_results.append(window_data)
            logger.info(f"✅ 窗口 {window['window_id']} 分析完成")
        
        # 合并所有窗口的分析结果
        design_analysis_data = window_manager.merge_analysis_results(window_results, "设计分析")
        logger.info(f"📊 合并后的设计分析结果: {design_analysis_data}")
        design_summary = design_analysis_data.get('summary', '设计分析完成')
        logger.info(f"📝 设计概要: {design_summary}")
        window_manager.add_context(design_summary, "设计分析")
        
        # 🏗️ 步骤2：技术架构分析
        logger.info("🏗️ 步骤2：开始技术架构分析...")
        
        # 基于设计概要进行更深入的技术架构分析
        architecture_summary = design_summary  # 直接使用步骤1的设计概要
        logger.info(f"📝 技术架构概要: {architecture_summary}")
        window_manager.add_context(architecture_summary, "技术架构")
        
        # 🔍 步骤3：服务边界识别
        logger.info("🔍 步骤3：开始服务边界识别...")
        logger.info(f"📝 输入 - 设计概要: {design_summary}")
        logger.info(f"📝 输入 - 架构概要: {architecture_summary}")
        
        service_prompt = prompts.get_prompt(
            "service_boundary",
            design_summary=design_summary,
            architecture_summary=architecture_summary,
            context_window=window_manager.get_context_window()
        )
        logger.info(f"📝 服务拆分提示词长度: {len(service_prompt)}")
        logger.debug(f"📝 服务拆分提示词内容: {service_prompt[:500]}...")
        
        service_result = client.chat(
            messages=[
                {"role": "system", "content": "你是微服务架构专家。"},
                {"role": "user", "content": service_prompt}
            ],
            temperature=0.2
        )
        logger.info(f"✅ 服务拆分LLM响应长度: {len(service_result)}")
        logger.debug(f"🔍 服务拆分原始响应: {service_result[:500]}...")
        
        # 解析服务识别结果
        try:
            service_data = _extract_json_from_response(service_result)
            logger.info(f"📊 服务拆分解析结果: {service_data}")
        except Exception as e:
            logger.error(f"❌ 服务拆分结果解析失败: {e}")
            # 使用默认服务列表
            service_data = {
                'identified_services': [
                    {'name': '用户服务', 'description': '负责用户管理'},
                    {'name': '业务服务', 'description': '负责核心业务逻辑'}
                ],
                'summary': '服务拆分基于默认配置完成'
            }
            logger.info(f"🔧 使用默认服务配置: {service_data}")
        
        identified_services = service_data.get('identified_services', [])
        
        # 如果服务列表为空，创建默认服务
        if not identified_services:
            logger.warning("⚠️ 未识别到任何服务，创建默认服务")
            identified_services = [
                {'name': '用户服务', 'description': '负责用户管理'},
                {'name': '业务服务', 'description': '负责核心业务逻辑'}
            ]
            
        logger.info(f"🎯 识别的服务列表: {identified_services}")
        logger.info(f"🔢 识别的服务数量: {len(identified_services)}")
        services_summary = service_data.get('summary', '服务拆分完成')
        logger.info(f"📝 服务拆分概要: {services_summary}")
        window_manager.add_context(services_summary, "服务拆分")
        
        # 🌐 步骤4：依赖分析
        logger.info("🌐 步骤4：开始依赖分析...")
        dependency_prompt = prompts.get_prompt(
            "dependency_analysis",
            services_summary=services_summary,
            architecture_summary=architecture_summary,
            context_window=window_manager.get_context_window()
        )
        logger.info(f"📝 依赖分析提示词长度: {len(dependency_prompt)}")
        
        dependency_result = client.chat(
            messages=[
                {"role": "system", "content": "你是微服务依赖分析专家。"},
                {"role": "user", "content": dependency_prompt}
            ],
            temperature=0.2
        )
        logger.info(f"✅ 依赖分析LLM响应长度: {len(dependency_result)}")
        
        # 解析依赖分析结果
        dependency_data = _extract_json_from_response(dependency_result)
        logger.info(f"📊 依赖分析解析结果: {dependency_data}")
        dependencies_summary = dependency_data.get('summary', '依赖分析完成')
        logger.info(f"📝 依赖分析概要: {dependencies_summary}")
        
        # 📅 步骤5：任务调度
        logger.info("📅 步骤5：开始制定执行计划...")
        scheduling_prompt = prompts.get_prompt(
            "task_scheduling",
            services_summary=services_summary,
            dependencies_summary=dependencies_summary,
            context_window=window_manager.get_context_window()
        )
        logger.info(f"📝 任务调度提示词长度: {len(scheduling_prompt)}")
        
        scheduling_result = client.chat(
            messages=[
                {"role": "system", "content": "你是项目调度专家。"},
                {"role": "user", "content": scheduling_prompt}
            ],
            temperature=0.2
        )
        logger.info(f"✅ 任务调度LLM响应长度: {len(scheduling_result)}")
        
        # 解析执行计划
        execution_data = _extract_json_from_response(scheduling_result)
        logger.info(f"📊 执行计划解析结果: {execution_data}")
        
        # 💾 步骤6：生成SQLite任务（使用滑动窗口处理长执行计划）
        logger.info("💾 步骤6：开始生成SQLite任务...")
        
        # 准备执行计划文本
        execution_plan_text = json.dumps(execution_data, ensure_ascii=False, indent=2)
        
        # 如果执行计划很长，使用滑动窗口处理
        if len(execution_plan_text) > 1800:
            logger.info(f"📄 执行计划较长({len(execution_plan_text)}字符)，使用滑动窗口处理")
            plan_windows = window_manager.split_text_into_windows(execution_plan_text)
            
            # 对每个窗口生成任务
            all_task_results = []
            for window in plan_windows:
                total_windows = window.get('total_windows', len(plan_windows))
                logger.info(f"📝 处理计划窗口 {window['window_id']}/{total_windows}")
                
                task_generation_prompt = prompts.get_prompt(
                    "generate_sqlite_tasks",
                    execution_plan=window["content"],
                    services_summary=services_summary,
                    context_window=window_manager.get_context_window(),
                    base_project_path=base_project_path
                )
                
                task_result = client.chat(
                    messages=[
                        {"role": "system", "content": f"你是任务管理专家。正在处理第 {window['window_id']}/{total_windows} 个执行计划片段。请严格按照模板格式生成任务，特别注意git_clone和api任务的路径一致性。"},
                        {"role": "user", "content": task_generation_prompt}
                    ],
                    temperature=0.1
                )
                
                window_task_data = _extract_json_from_response(task_result)
                all_task_results.append(window_task_data)
                logger.info(f"✅ 窗口 {window['window_id']} 任务生成完成")
            
            # 合并所有窗口的任务
            task_data = window_manager.merge_analysis_results(all_task_results, "任务生成")
        else:
            # 执行计划不长，直接处理
            logger.info(f"📄 执行计划适中({len(execution_plan_text)}字符)，直接处理")
            task_generation_prompt = prompts.get_prompt(
                "generate_sqlite_tasks",
                execution_plan=execution_plan_text,
                services_summary=services_summary,
                context_window=window_manager.get_context_window(),
                base_project_path=base_project_path
            )
            
            task_result = client.chat(
                messages=[
                    {"role": "system", "content": "你是任务管理专家。请严格按照模板格式生成任务，特别注意git_clone和api任务的路径一致性。"},
                    {"role": "user", "content": task_generation_prompt}
                ],
                temperature=0.1
            )
            
            task_data = _extract_json_from_response(task_result)
        
        logger.info(f"📊 任务生成解析结果: {task_data}")
        tasks = task_data.get('tasks', [])
        logger.info(f"🎯 生成的任务列表: {tasks}")
        logger.info(f"🔢 生成的任务数量: {len(tasks)}")
        
        # 保存任务到SQLite数据库
        if tasks:
            success = task_storage.save_tasks(tasks)
            if success:
                logger.info(f"✅ 已生成并保存 {len(tasks)} 个任务到数据库")
            else:
                logger.error("❌ 任务保存失败")
        else:
            logger.warning("⚠️ 没有生成任何任务")
        
        # 更新状态
        final_services = [service.get('name', f'服务{i+1}') for i, service in enumerate(identified_services)]
        logger.info(f"📤 最终服务列表: {final_services}")
        
        # 🔧 生成并行任务批次（为智能编码节点准备）
        parallel_tasks = [
            {
                "batch_id": "batch_1",
                "services": final_services,  # 简单起见，把所有服务放在一个批次
                "dependencies": []
            }
        ]
        logger.info(f"📤 生成并行任务批次: {parallel_tasks}")
        
        state.update({
            "identified_services": final_services,
            "service_dependencies": dependency_data.get('service_dependencies', {}),
            "task_execution_plan": execution_data,
            "parallel_tasks": parallel_tasks,  # 🔧 新增：为智能编码节点准备
            "generated_tasks": tasks,
            "current_phase": "intelligent_coding"  # 🔧 修改：设置为下一个阶段
        })
        
        logger.info(f"📤 输出状态键: {list(state.keys())}")
        logger.info(f"📤 输出 - 识别服务: {state['identified_services']}")
        logger.info(f"📤 输出 - 当前阶段: {state['current_phase']}")
        logger.info(f"✅ 任务拆分完成，识别 {len(identified_services)} 个服务，生成 {len(tasks)} 个任务")
        return state
        
    except Exception as e:
        logger.error(f"❌ 任务拆分失败: {e}")
        state["execution_errors"].append(f"任务拆分失败: {str(e)}")
        return state

def _extract_json_from_response(response_text: str) -> Dict[str, Any]:
    """从LLM响应中提取JSON数据"""
    try:
        # 尝试直接解析
        if response_text.strip().startswith('{'):
            return json.loads(response_text.strip())
        
        # 查找JSON代码块
        import re
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        
        # 查找第一个JSON对象
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        
        logger.warning("⚠️ 无法从响应中提取JSON，返回默认结构")
        return {"summary": "解析失败", "error": "JSON提取失败"}
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON解析失败: {e}")
        return {"summary": "JSON解析错误", "error": str(e)}
    except Exception as e:
        logger.error(f"❌ 响应解析失败: {e}")
        return {"summary": "响应解析失败", "error": str(e)} 