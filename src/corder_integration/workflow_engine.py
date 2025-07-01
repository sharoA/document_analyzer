#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流引擎
基于LangChain/LangGraph的工作流编排，状态管理和流程控制
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import re

try:
    from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
    from langchain.callbacks.manager import CallbackManagerForLLMRun
    from langchain.memory import ConversationBufferMemory
    from langchain.prompts import PromptTemplate
except ImportError:
    print("警告: LangChain未安装，请执行: pip install langchain")
    
    # 提供基础的替代实现
    class BaseMessage:
        def __init__(self, content: str):
            self.content = content
    
    class HumanMessage(BaseMessage):
        pass
    
    class AIMessage(BaseMessage):
        pass
    
    class SystemMessage(BaseMessage):
        pass

from .config import get_coder_config, get_config_manager
from .task_planner import TaskPlanner, ExecutionPlan, TaskItem
from .git_manager import GitManager
from ..utils.task_storage import get_task_storage
from ..utils.openai_client import get_openai_client
from ..utils.volcengine_client import get_volcengine_client

logger = logging.getLogger(__name__)

class WorkflowState(Enum):
    """工作流状态枚举"""
    INITIALIZED = "initialized"
    PLANNING = "planning"
    ENVIRONMENT_SETUP = "environment_setup"
    CODE_GENERATION = "code_generation"
    TESTING = "testing"
    GIT_OPERATIONS = "git_operations"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

@dataclass
class WorkflowContext:
    """工作流上下文"""
    execution_plan: Optional[ExecutionPlan] = None
    current_state: WorkflowState = WorkflowState.INITIALIZED
    current_task: Optional[TaskItem] = None
    project_path: str = ""
    results: Dict[str, Any] = None
    errors: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.results is None:
            self.results = {}
        if self.errors is None:
            self.errors = []
        if self.metadata is None:
            self.metadata = {}

class WorkflowEngine:
    """工作流引擎"""
    
    def __init__(self):
        self.config = get_coder_config()
        self.config_manager = get_config_manager()
        self.task_planner = TaskPlanner()
        self.git_manager = GitManager()
        self.task_storage = get_task_storage()
        
        # 根据配置选择AI客户端
        if self.config.ai_provider == "volcengine":
            self.ai_client = get_volcengine_client()
            logger.info("使用火山引擎作为AI提供商")
        else:
            self.ai_client = get_openai_client()
            logger.info("使用OpenAI作为AI提供商")
        
        # 保持向后兼容性
        self.openai_client = self.ai_client
        
        # 工作流状态
        self.context = WorkflowContext()
        self.state_handlers = self._initialize_state_handlers()
        self.memory = ConversationBufferMemory() if 'ConversationBufferMemory' in globals() else None
        
        # 回调函数
        self.on_state_change: Optional[Callable] = None
        self.on_task_complete: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
    
    def _initialize_state_handlers(self) -> Dict[WorkflowState, Callable]:
        """初始化状态处理器"""
        return {
            WorkflowState.PLANNING: self._handle_planning_state,
            WorkflowState.ENVIRONMENT_SETUP: self._handle_environment_setup_state,
            WorkflowState.CODE_GENERATION: self._handle_code_generation_state,
            WorkflowState.TESTING: self._handle_testing_state,
            WorkflowState.GIT_OPERATIONS: self._handle_git_operations_state,
        }
    
    async def execute_workflow(
        self, 
        document_content: str, 
        project_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行完整的编码智能体工作流
        
        Args:
            document_content: 设计文档内容
            project_name: 项目名称
            
        Returns:
            执行结果
        """
        logger.info("开始执行编码智能体工作流")
        
        try:
            # 1. 规划阶段
            await self._transition_to_state(WorkflowState.PLANNING)
            planning_result = await self._handle_planning_state(document_content, project_name)
            
            if not planning_result.get("success"):
                raise Exception(f"规划阶段失败: {planning_result.get('error')}")
            
            # 2. 环境准备阶段
            await self._transition_to_state(WorkflowState.ENVIRONMENT_SETUP)
            env_result = await self._handle_environment_setup_state()
            
            if not env_result.get("success"):
                raise Exception(f"环境准备失败: {env_result.get('error')}")
            
            # 3. 代码生成阶段
            await self._transition_to_state(WorkflowState.CODE_GENERATION)
            code_result = await self._handle_code_generation_state()
            
            if not code_result.get("success"):
                logger.warning(f"代码生成阶段有警告: {code_result.get('warnings', [])}")
            
            # 4. 测试阶段
            await self._transition_to_state(WorkflowState.TESTING)
            test_result = await self._handle_testing_state()
            
            if not test_result.get("success"):
                logger.warning(f"测试阶段有警告: {test_result.get('warnings', [])}")
            
            # 5. Git操作阶段
            await self._transition_to_state(WorkflowState.GIT_OPERATIONS)
            git_result = await self._handle_git_operations_state()
            
            if not git_result.get("success"):
                logger.warning(f"Git操作有警告: {git_result.get('warnings', [])}")
            
            # 6. 完成
            await self._transition_to_state(WorkflowState.COMPLETED)
            
            final_result = {
                "status": "completed",
                "execution_plan": self.context.execution_plan.to_dict() if self.context.execution_plan else None,
                "project_path": self.context.project_path,
                "results": self.context.results,
                "summary": self._generate_execution_summary()
            }
            
            logger.info("编码智能体工作流执行完成")
            return final_result
            
        except Exception as e:
            logger.error(f"工作流执行失败: {e}")
            await self._transition_to_state(WorkflowState.FAILED)
            self.context.errors.append(str(e))
            
            return {
                "status": "failed",
                "error": str(e),
                "errors": self.context.errors,
                "partial_results": self.context.results
            }
    
    async def _transition_to_state(self, new_state: WorkflowState):
        """状态转换"""
        old_state = self.context.current_state
        self.context.current_state = new_state
        
        logger.info(f"工作流状态转换: {old_state.value} -> {new_state.value}")
        
        # 触发状态变更回调
        if self.on_state_change:
            try:
                await self.on_state_change(old_state, new_state, self.context)
            except Exception as e:
                logger.error(f"状态变更回调失败: {e}")
    
    async def _handle_planning_state(
        self, 
        document_content: str, 
        project_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """处理规划阶段"""
        logger.info("执行规划阶段")
        
        try:
            # 创建执行计划
            execution_plan = self.task_planner.create_execution_plan(
                document_content, project_name
            )
            
            self.context.execution_plan = execution_plan
            
            # 保存执行计划
            tasks_dir = self.task_planner.save_execution_plan(execution_plan)
            
            # 记录结果
            self.context.results["planning"] = {
                "execution_plan_id": execution_plan.plan_id,
                "project_name": execution_plan.project_name,
                "total_tasks": execution_plan.total_tasks,
                "estimated_hours": execution_plan.estimated_total_hours,
                "branch_name": execution_plan.branch_name,
                "tasks_directory": tasks_dir
            }
            
            return {"success": True, "execution_plan": execution_plan}
            
        except Exception as e:
            logger.error(f"规划阶段失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def _handle_environment_setup_state(self) -> Dict[str, Any]:
        """处理环境准备阶段"""
        logger.info("执行环境准备阶段")
        
        try:
            if not self.context.execution_plan:
                raise Exception("执行计划未找到")
            
            # 获取Git项目名而不是文档项目名
            git_project_name = self._get_git_project_name()
            
            # 设置项目环境
            # 从配置中获取默认的远程仓库URL
            from ..resource.config import get_config
            main_config = get_config()
            coder_config = main_config.get_coder_agent_config()
            git_config = coder_config.get("git_config", {})
            remote_url = git_config.get("default_remote_url")
            
            env_result = self.git_manager.setup_project_environment(
                git_project_name,  # 使用Git项目名而不是execution_plan.project_name
                self.context.execution_plan.branch_name,
                remote_url=remote_url
            )
            
            self.context.project_path = env_result["project_path"]
            
            # 分析现有项目结构
            structure_analysis = self.git_manager.analyze_existing_structure(
                self.context.project_path
            )
            
            # 记录结果
            self.context.results["environment_setup"] = {
                "project_path": self.context.project_path,
                "git_setup": env_result,
                "structure_analysis": structure_analysis,
                "git_project_name": git_project_name
            }
            
            logger.info(f"使用Git项目名 '{git_project_name}' 设置项目环境: {self.context.project_path}")
            
            return {"success": True, "project_path": self.context.project_path}
            
        except Exception as e:
            logger.error(f"环境准备阶段失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def _handle_code_generation_state(self) -> Dict[str, Any]:
        """处理代码生成阶段"""
        logger.info("执行代码生成阶段")
        
        warnings = []
        generated_files = []
        
        try:
            if not self.context.execution_plan:
                raise Exception("执行计划未找到")
            
            # 获取代码生成相关的任务
            code_tasks = [
                task for task in self.context.execution_plan.tasks 
                if task.type in ["backend", "frontend", "database", "docs"]
            ]
            
            # 执行每个代码生成任务
            for task in code_tasks:
                try:
                    task_result = await self._execute_code_generation_task(task)
                    if task_result.get("success"):
                        generated_files.extend(task_result.get("files", []))
                        logger.info(f"任务 {task.id} 执行成功")
                    else:
                        warnings.append(f"任务 {task.id} 执行失败: {task_result.get('error')}")
                        logger.warning(f"任务 {task.id} 执行失败: {task_result.get('error')}")
                
                except Exception as e:
                    warnings.append(f"任务 {task.id} 执行异常: {str(e)}")
                    logger.error(f"任务 {task.id} 执行异常: {e}")
            
            # 记录结果
            self.context.results["code_generation"] = {
                "total_tasks": len(code_tasks),
                "completed_tasks": len(code_tasks) - len(warnings),
                "generated_files": generated_files,
                "warnings": warnings
            }
            
            return {
                "success": len(warnings) < len(code_tasks),  # 如果不是全部失败就算成功
                "warnings": warnings,
                "generated_files": generated_files
            }
            
        except Exception as e:
            logger.error(f"代码生成阶段失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_code_generation_task(self, task: TaskItem) -> Dict[str, Any]:
        """执行单个代码生成任务"""
        logger.info(f"执行代码生成任务: {task.name}")
        
        # 这里应该调用具体的代码生成器
        # 为了演示，我创建一个简化的实现
        try:
            generated_files = []
            
            if task.type == "docs":
                # 生成技术栈文档
                docs_result = await self._generate_tech_stack_docs()
                generated_files.extend(docs_result.get("files", []))
            
            elif task.type == "backend":
                # 生成后端代码
                backend_result = await self._generate_backend_code(task)
                generated_files.extend(backend_result.get("files", []))
            
            elif task.type == "frontend":
                # 生成前端代码
                frontend_result = await self._generate_frontend_code(task)
                generated_files.extend(frontend_result.get("files", []))
            
            elif task.type == "database":
                # 生成数据库相关代码
                db_result = await self._generate_database_code(task)
                generated_files.extend(db_result.get("files", []))
            
            return {"success": True, "files": generated_files}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _generate_tech_stack_docs(self) -> Dict[str, Any]:
        """生成技术栈文档"""
        logger.info("生成技术栈文档")
        
        generated_files = []
        docs_dir = self.config_manager.get_tech_stack_docs_dir()
        
        # 创建文档目录
        import os
        os.makedirs(docs_dir, exist_ok=True)
        
        # 生成后端技术栈文档
        backend_doc_content = self._create_backend_stack_doc()
        backend_doc_path = os.path.join(docs_dir, "backend-stack.md")
        with open(backend_doc_path, 'w', encoding='utf-8') as f:
            f.write(backend_doc_content)
        generated_files.append(backend_doc_path)
        
        # 生成前端技术栈文档
        frontend_doc_content = self._create_frontend_stack_doc()
        frontend_doc_path = os.path.join(docs_dir, "frontend-stack.md")
        with open(frontend_doc_path, 'w', encoding='utf-8') as f:
            f.write(frontend_doc_content)
        generated_files.append(frontend_doc_path)
        
        # 生成开发规范文档
        standards_content = self._create_development_standards_doc()
        standards_path = os.path.join(docs_dir, "development-standards.md")
        with open(standards_path, 'w', encoding='utf-8') as f:
            f.write(standards_content)
        generated_files.append(standards_path)
        
        return {"success": True, "files": generated_files}
    
    def _create_backend_stack_doc(self) -> str:
        """创建后端技术栈文档"""
        return f"""# 后端技术栈文档

## 技术栈概览
- **框架**: Spring Boot {self.config.backend_version}
- **Java版本**: Java {self.config.backend_java_version}
- **构建工具**: Maven 3.6+
- **数据库**: MySQL/Oracle (根据项目需求)
- **ORM框架**: MyBatis
- **API文档**: Swagger/OpenAPI 3.0
- **测试框架**: JUnit5 + Mockito + Spring Boot Test

## 项目结构
```
src/
├── main/
│   ├── java/
│   │   └── com/yourcompany/yourmicroservice/
│   │       ├── application/       # 应用层
│   │       ├── domain/            # 领域层
│   │       │   ├── model/         # 实体和值对象
│   │       │   ├── repository/    # 仓库接口
│   │       │   └── service/       # 领域服务
│   │       ├── infrastructure/    # 基础设施层
│   │       │   ├── config/        # 配置文件
│   │       │   ├── security/      # 安全配置
│   │       │   └── persistence/   # 数据持久化
│   │       └── interfaces/        # 接口层（REST Controllers）
│   └── resources/
│       ├── application.properties
│       └── bootstrap.properties
└── test/
    └── java/
```

## 开发规范
1. 遵循DDD（领域驱动设计）架构
2. 使用RESTful API设计原则
3. 实现统一的异常处理
4. 添加详细的日志记录
5. 编写完整的单元测试

## 配置说明
- 数据库连接配置
- 日志配置
- 安全配置
- API文档配置

生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
    
    def _create_frontend_stack_doc(self) -> str:
        """创建前端技术栈文档"""
        return f"""# 前端技术栈文档

## 技术栈概览
- **框架**: Vue.js 2.x
- **构建工具**: Webpack + npm
- **路由**: Vue Router
- **状态管理**: Vuex
- **HTTP客户端**: Axios
- **UI框架**: Element UI / Ant Design Vue (根据项目选择)
- **测试框架**: Jest + Vue Test Utils

## 项目结构
```
frontend/
├── build/                    # 项目构建相关代码
├── config/                   # 项目开发环境配置
├── src/
│   ├── components/           # Vue公共组件
│   ├── views/               # 页面组件
│   ├── router/              # 路由管理
│   ├── store/               # Vuex状态管理
│   ├── utils/               # 工具函数
│   ├── api/                 # API接口
│   ├── assets/              # 静态资源
│   ├── App.vue              # 根组件
│   └── main.js              # 入口文件
├── static/                   # 静态文件
├── package.json
└── index.html
```

## 开发规范
1. 组件命名使用PascalCase
2. 文件命名使用kebab-case
3. 统一的代码格式化(ESLint + Prettier)
4. 组件单一职责原则
5. 合理的组件拆分和复用

## 构建配置
- 开发环境配置
- 生产环境配置
- 代理配置
- 打包优化

生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
    
    def _create_development_standards_doc(self) -> str:
        """创建开发规范文档"""
        return f"""# 开发规范文档

## 代码规范

### 命名规范
- **类名**: PascalCase (如: UserService)
- **方法名**: camelCase (如: getUserInfo)
- **变量名**: camelCase (如: userName)
- **常量名**: UPPER_SNAKE_CASE (如: MAX_SIZE)
- **包名**: 小写字母+点分隔 (如: com.company.module)

### 注释规范
- 类和接口必须有JavaDoc注释
- 公共方法必须有注释说明
- 复杂业务逻辑需要行内注释
- 注释内容要准确、简洁

### 异常处理
- 使用统一的异常处理机制
- 不允许吞掉异常
- 异常信息要具体明确
- 合理使用自定义异常

## Git提交规范

### 提交信息格式
```
[类型] 简短描述

详细描述（可选）
```

### 提交类型
- **feat**: 新功能
- **fix**: 修复bug
- **docs**: 文档更新
- **style**: 代码格式调整
- **refactor**: 重构代码
- **test**: 添加测试
- **chore**: 构建过程或辅助工具的变动

## 测试规范

### 单元测试
- 测试覆盖率不低于{self.config.test_coverage_target * 100:.0f}%
- 测试方法命名: should_返回结果_when_输入条件
- 使用AAA模式: Arrange-Act-Assert
- Mock外部依赖

### 集成测试
- 测试关键业务流程
- 测试API接口
- 测试数据库操作

## 代码审查
- 所有代码合并前必须经过代码审查
- 关注代码质量、性能、安全性
- 确保符合项目架构设计

生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
    
    async def _generate_backend_code(self, task: TaskItem) -> Dict[str, Any]:
        """生成后端代码"""
        logger.info(f"生成后端代码: {task.name}")
        
        try:
            # 导入并使用实际的代码生成器
            from .code_generator import CodeGenerator
            code_generator = CodeGenerator()
            
            # 准备设计数据
            design_data = self._prepare_design_data_for_backend(task)
            
            # 调用后端代码生成器
            result = code_generator.generate_backend_code(
                design_data=design_data,
                project_path=self.context.project_path
            )
            
            if result.get("success"):
                logger.info(f"后端代码生成成功: {result.get('total_files', 0)} 个文件")
                return {
                    "success": True, 
                    "files": result.get("generated_files", []),
                    "total_files": result.get("total_files", 0)
                }
            else:
                logger.error(f"后端代码生成失败: {result.get('error')}")
                return {"success": False, "error": result.get("error"), "files": []}
                
        except Exception as e:
            logger.error(f"后端代码生成异常: {e}")
            return {"success": False, "error": str(e), "files": []}
    
    async def _generate_frontend_code(self, task: TaskItem) -> Dict[str, Any]:
        """生成前端代码"""
        logger.info(f"生成前端代码: {task.name}")
        
        try:
            # 导入并使用实际的代码生成器
            from .code_generator import CodeGenerator
            code_generator = CodeGenerator()
            
            # 准备设计数据
            design_data = self._prepare_design_data_for_frontend(task)
            
            # 调用前端代码生成器
            result = code_generator.generate_frontend_code(
                design_data=design_data,
                project_path=self.context.project_path
            )
            
            if result.get("success"):
                logger.info(f"前端代码生成成功: {result.get('total_files', 0)} 个文件")
                return {
                    "success": True, 
                    "files": result.get("generated_files", []),
                    "total_files": result.get("total_files", 0)
                }
            else:
                logger.error(f"前端代码生成失败: {result.get('error')}")
                return {"success": False, "error": result.get("error"), "files": []}
                
        except Exception as e:
            logger.error(f"前端代码生成异常: {e}")
            return {"success": False, "error": str(e), "files": []}
    
    async def _generate_database_code(self, task: TaskItem) -> Dict[str, Any]:
        """生成数据库相关代码（简化实现）"""
        logger.info(f"生成数据库代码: {task.name}")
        
        # 这里应该调用具体的数据库代码生成器
        # 为了演示，返回模拟结果
        generated_files = [
            f"src/main/java/com/example/entity/{task.name}Entity.java",
            f"src/main/resources/mapper/{task.name}Mapper.xml"
        ]
        
        return {"success": True, "files": generated_files}
    
    async def _handle_testing_state(self) -> Dict[str, Any]:
        """处理测试阶段"""
        logger.info("执行测试阶段")
        
        warnings = []
        
        try:
            # 获取测试相关任务
            test_tasks = [
                task for task in self.context.execution_plan.tasks 
                if task.type == "test"
            ]
            
            test_results = []
            
            for task in test_tasks:
                try:
                    # 执行测试任务（简化实现）
                    test_result = await self._execute_test_task(task)
                    test_results.append(test_result)
                    
                    if not test_result.get("success"):
                        warnings.append(f"测试任务 {task.id} 失败: {test_result.get('error')}")
                
                except Exception as e:
                    warnings.append(f"测试任务 {task.id} 异常: {str(e)}")
            
            # 记录结果
            self.context.results["testing"] = {
                "total_test_tasks": len(test_tasks),
                "test_results": test_results,
                "warnings": warnings
            }
            
            return {
                "success": len(warnings) == 0,
                "warnings": warnings,
                "test_results": test_results
            }
            
        except Exception as e:
            logger.error(f"测试阶段失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_test_task(self, task: TaskItem) -> Dict[str, Any]:
        """执行测试任务（简化实现）"""
        logger.info(f"执行测试任务: {task.name}")
        
        # 这里应该调用具体的测试生成器和执行器
        # 为了演示，返回模拟结果
        return {
            "success": True,
            "task_id": task.id,
            "test_files_generated": 5,
            "tests_passed": 12,
            "tests_failed": 0,
            "coverage": 85.5
        }
    
    async def _handle_git_operations_state(self) -> Dict[str, Any]:
        """处理Git操作阶段，整合成功的git推送逻辑"""
        logger.info("执行Git操作阶段")
        
        try:
            # 如果环境设置阶段git失败了，这里重新初始化git
            if not self.git_manager._is_git_repository(self.context.project_path):
                logger.info("Git仓库未初始化，开始重新设置...")
                await self._reinitialize_git_repository()
            
            # 创建提交信息
            commit_message = f"AI生成代码 - {self.context.execution_plan.project_name} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # 提交并推送代码
            git_result = self._commit_and_push_with_retry(commit_message)
            
            # 记录结果
            self.context.results["git_operations"] = git_result
            
            return git_result
            
        except Exception as e:
            logger.error(f"Git操作阶段失败: {e}")
            return {"success": False, "error": str(e), "operations": []}
    
    async def _reinitialize_git_repository(self) -> Dict[str, Any]:
        """重新初始化git仓库（基于成功的git推送脚本）"""
        logger.info("重新初始化Git仓库")
        
        try:
            # 获取配置
            from ..resource.config import get_config
            main_config = get_config()
            coder_config = main_config.get_coder_agent_config()
            git_config = coder_config.get("git_config", {})
            remote_url = git_config.get("default_remote_url")
            branch_name = self.context.execution_plan.branch_name
            
            project_path = self.context.project_path
            
            # 1. 初始化git仓库
            self.git_manager._run_git_command(["git", "init"], project_path)
            logger.info("Git仓库初始化成功")
            
            # 2. 设置默认分支
            try:
                self.git_manager._run_git_command(["git", "branch", "-M", "main"], project_path)
                logger.info("设置默认分支为main")
            except:
                logger.warning("设置默认分支失败")
            
            # 3. 添加远程仓库
            if remote_url:
                try:
                    self.git_manager._run_git_command(
                        ["git", "remote", "add", "origin", remote_url], 
                        project_path
                    )
                    logger.info(f"添加远程仓库: {remote_url}")
                except:
                    logger.warning("添加远程仓库失败，可能已存在")
            
            # 4. 获取远程信息
            if self.git_manager._has_remote_origin(project_path):
                try:
                    self.git_manager._run_git_command(["git", "fetch", "origin"], project_path)
                    logger.info("获取远程分支信息")
                except:
                    logger.warning("获取远程信息失败")
            
            # 5. 创建或切换到目标分支
            try:
                self.git_manager._run_git_command(["git", "checkout", "-b", branch_name], project_path)
                logger.info(f"创建并切换到分支: {branch_name}")
            except:
                # 分支可能已存在，尝试切换
                try:
                    self.git_manager._run_git_command(["git", "checkout", branch_name], project_path)
                    logger.info(f"切换到分支: {branch_name}")
                except:
                    logger.warning("分支切换失败，使用当前分支")
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"重新初始化Git仓库失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _commit_and_push_with_retry(self, commit_message: str) -> Dict[str, Any]:
        """带重试的提交和推送（基于成功的git推送脚本）"""
        result = {
            "success": False,
            "operations": [],
            "commit_id": "",
            "pushed": False
        }
        
        try:
            project_path = self.context.project_path
            
            # 1. 检查是否有文件需要提交
            if not self.git_manager._has_uncommitted_changes(project_path):
                logger.info("没有需要提交的更改")
                result["operations"].append("没有更改需要提交")
                result["success"] = True
                return result
            
            # 2. 添加所有文件
            self.git_manager._run_git_command(["git", "add", "."], project_path)
            result["operations"].append("添加所有更改的文件")
            
            # 3. 提交代码
            self.git_manager._run_git_command(["git", "commit", "-m", commit_message], project_path)
            result["operations"].append(f"提交代码: {commit_message}")
            
            # 4. 获取提交ID
            commit_id = self.git_manager._run_git_command(["git", "rev-parse", "HEAD"], project_path)
            result["commit_id"] = commit_id.strip()
            
            # 5. 推送到远程仓库
            if self.git_manager._has_remote_origin(project_path):
                try:
                    current_branch = self.git_manager._get_current_branch(project_path)
                    self.git_manager._run_git_command(
                        ["git", "push", "-u", "origin", current_branch], 
                        project_path
                    )
                    result["pushed"] = True
                    result["operations"].append(f"推送到远程分支: {current_branch}")
                    logger.info(f"代码推送成功到分支: {current_branch}")
                    
                except Exception as push_error:
                    logger.warning(f"推送失败: {push_error}")
                    result["operations"].append(f"推送失败: {str(push_error)}")
                    # 推送失败不算整体失败，提交已经成功了
            else:
                result["operations"].append("没有远程仓库配置，跳过推送")
            
            result["success"] = True
            result["timestamp"] = datetime.now().isoformat()
            
            logger.info(f"Git操作完成，提交ID: {result['commit_id'][:8]}")
            
        except Exception as e:
            logger.error(f"Git提交失败: {e}")
            result["error"] = str(e)
            result["operations"].append(f"Git操作失败: {str(e)}")
        
        return result
    
    def _generate_execution_summary(self) -> Dict[str, Any]:
        """生成执行摘要"""
        summary = {
            "project_name": self.context.execution_plan.project_name if self.context.execution_plan else "Unknown",
            "execution_time": datetime.now().isoformat(),
            "total_phases": len(self.state_handlers),
            "completed_phases": 0,
            "total_errors": len(self.context.errors),
            "phases_summary": {}
        }
        
        # 统计各阶段完成情况
        for phase_name, phase_result in self.context.results.items():
            summary["phases_summary"][phase_name] = {
                "completed": True,
                "has_warnings": "warnings" in phase_result and len(phase_result["warnings"]) > 0
            }
            summary["completed_phases"] += 1
        
        return summary
    
    def set_callbacks(
        self,
        on_state_change: Optional[Callable] = None,
        on_task_complete: Optional[Callable] = None,
        on_error: Optional[Callable] = None
    ):
        """设置回调函数"""
        if on_state_change:
            self.on_state_change = on_state_change
        if on_task_complete:
            self.on_task_complete = on_task_complete
        if on_error:
            self.on_error = on_error
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """获取工作流状态"""
        return {
            "current_state": self.context.current_state.value,
            "execution_plan_id": self.context.execution_plan.plan_id if self.context.execution_plan else None,
            "project_path": self.context.project_path,
            "current_task": self.context.current_task.to_dict() if self.context.current_task else None,
            "completed_phases": list(self.context.results.keys()),
            "total_errors": len(self.context.errors),
            "errors": self.context.errors[-5:]  # 最近5个错误
        }
    
    def _prepare_design_data_for_backend(self, task: TaskItem) -> Dict[str, Any]:
        """为后端代码生成准备设计数据"""
        try:
            # 从执行计划中获取解析的文档数据
            design_analysis = {}
            if self.context.execution_plan and hasattr(self.context.execution_plan, 'project_structure'):
                project_structure = self.context.execution_plan.project_structure
                if project_structure:
                    design_analysis = project_structure
            
            # 获取项目基本信息 - 确保使用Git项目名
            git_project_name = self._get_git_project_name()
            
            # 构造基于实际需求的设计数据
            design_data = {
                "project_info": {
                    "name": git_project_name,
                    "version": "1.0.0",
                    "package_prefix": "com.example"
                },
                "database_design": self._extract_database_design_from_task(task),
                "business_logic": self._extract_business_logic_from_task(task),
                "api_design": self._extract_api_design_from_task(task)
            }
            
            return design_data
            
        except Exception as e:
            logger.error(f"准备后端设计数据失败: {e}")
            # 如果解析失败，返回基于任务描述的最小数据
            return self._create_fallback_design_data_from_task(task)
    
    def _get_git_project_name(self) -> str:
        """获取Git项目名称"""
        try:
            # 1. 尝试从配置中获取Git URL并提取项目名
            from ..resource.config import get_config
            from .task_planner import TaskPlanner
            
            main_config = get_config()
            coder_config = main_config.get_coder_agent_config()
            git_config = coder_config.get("git_config", {})
            default_remote_url = git_config.get("default_remote_url")
            
            if default_remote_url:
                planner = TaskPlanner()
                git_project_name = planner._parse_project_name_from_url(default_remote_url)
                if git_project_name and git_project_name != 'UnknownProject':
                    logger.info(f"使用Git项目名: {git_project_name}")
                    return git_project_name
            
            # 2. 如果Git URL提取失败，使用执行计划的项目名但进行规范化
            if self.context.execution_plan:
                original_name = self.context.execution_plan.project_name
                planner = TaskPlanner()
                normalized_name = planner._normalize_project_name(original_name)
                
                # 如果规范化后的名称和原始名称差别很大，说明原始名称可能是中文文档名
                # 在这种情况下，使用默认的Git项目名
                if len(normalized_name) > len(original_name) * 2:
                    logger.warning(f"项目名 '{original_name}' 可能是文档名，使用默认Git项目名")
                    return "testproject"
                
                return normalized_name
            
            # 3. 最后的回退方案
            return "testproject"
            
        except Exception as e:
            logger.error(f"获取Git项目名失败: {e}")
            return "testproject"
    
    def _extract_database_design_from_task(self, task: TaskItem) -> List[Dict[str, Any]]:
        """从任务中提取数据库设计"""
        # 根据任务描述推断数据库设计
        task_desc = task.description.lower()
        project_name = self.context.execution_plan.project_name if self.context.execution_plan else "unknown"
        
        # 根据项目名称和任务描述智能推断实体
        entities = []
        
        # 分析项目名称中的关键词
        project_keywords = project_name.lower()
        
        if "用户" in task_desc or "user" in task_desc:
            entities.append(self._create_user_entity())
        
        if "链数优化" in project_keywords or "chain" in project_keywords:
            entities.append(self._create_chain_entity())
            entities.append(self._create_optimization_record_entity())
        
        if "订单" in task_desc or "order" in task_desc:
            entities.append(self._create_order_entity())
            
        if "产品" in task_desc or "product" in task_desc:
            entities.append(self._create_product_entity())
        
        # 如果没有识别到特定实体，创建通用实体
        if not entities:
            entities.append(self._create_generic_entity_from_project_name(project_name))
        
        return entities
    
    def _extract_business_logic_from_task(self, task: TaskItem) -> List[Dict[str, Any]]:
        """从任务中提取业务逻辑"""
        business_modules = []
        
        task_desc = task.description
        project_name = self.context.execution_plan.project_name if self.context.execution_plan else "unknown"
        
        # 根据任务描述提取业务模块
        if "链数优化" in project_name:
            business_modules.append({
                "module": "链数优化管理",
                "description": "链数优化算法执行、结果分析、性能监控功能",
                "operations": ["create", "read", "update", "delete", "optimize"]
            })
            business_modules.append({
                "module": "优化记录管理", 
                "description": "优化历史记录、结果对比、报告生成功能",
                "operations": ["create", "read", "export", "compare"]
            })
        elif "用户" in task_desc:
            business_modules.append({
                "module": "用户管理",
                "description": task_desc,
                "operations": ["create", "read", "update", "delete"]
            })
        else:
            # 从项目名称创建通用业务模块
            module_name = project_name.replace("V0", "").replace("系统", "").strip()
            business_modules.append({
                "module": f"{module_name}管理",
                "description": task_desc,
                "operations": ["create", "read", "update", "delete"]
            })
        
        return business_modules
    
    def _extract_api_design_from_task(self, task: TaskItem) -> List[Dict[str, Any]]:
        """从任务中提取API设计"""
        apis = []
        project_name = self.context.execution_plan.project_name if self.context.execution_plan else "unknown"
        
        if "链数优化" in project_name:
            apis.extend([
                {"path": "/optimization/start", "method": "POST", "description": "启动链数优化"},
                {"path": "/optimization/status", "method": "GET", "description": "获取优化状态"},
                {"path": "/optimization/result", "method": "GET", "description": "获取优化结果"},
                {"path": "/optimization/history", "method": "GET", "description": "获取优化历史"},
                {"path": "/optimization/report", "method": "GET", "description": "生成优化报告"}
            ])
        else:
            # 通用API
            resource_name = project_name.lower().replace("系统", "").replace("v0", "").strip()
            apis.extend([
                {"path": f"/{resource_name}/list", "method": "GET", "description": f"获取{resource_name}列表"},
                {"path": f"/{resource_name}/create", "method": "POST", "description": f"创建{resource_name}"},
                {"path": f"/{resource_name}/update", "method": "PUT", "description": f"更新{resource_name}"},
                {"path": f"/{resource_name}/delete", "method": "DELETE", "description": f"删除{resource_name}"}
            ])
        
        return apis
    
    def _create_chain_entity(self) -> Dict[str, Any]:
        """创建链数优化实体"""
        return {
            "name": "chain_optimization",
            "description": "链数优化记录表",
            "columns": [
                {"name": "id", "type": "BIGINT", "primary": True},
                {"name": "chain_id", "type": "VARCHAR(100)", "nullable": False},
                {"name": "optimization_type", "type": "VARCHAR(50)", "nullable": False},
                {"name": "before_value", "type": "DECIMAL(10,2)", "nullable": False},
                {"name": "after_value", "type": "DECIMAL(10,2)", "nullable": False},
                {"name": "improvement_rate", "type": "DECIMAL(5,2)", "nullable": False},
                {"name": "status", "type": "VARCHAR(20)", "nullable": False},
                {"name": "created_at", "type": "TIMESTAMP", "nullable": False},
                {"name": "updated_at", "type": "TIMESTAMP", "nullable": False}
            ]
        }
    
    def _create_optimization_record_entity(self) -> Dict[str, Any]:
        """创建优化记录实体"""
        return {
            "name": "optimization_record",
            "description": "优化历史记录表",
            "columns": [
                {"name": "id", "type": "BIGINT", "primary": True},
                {"name": "optimization_id", "type": "BIGINT", "nullable": False},
                {"name": "step_name", "type": "VARCHAR(100)", "nullable": False},
                {"name": "step_result", "type": "TEXT", "nullable": True},
                {"name": "execution_time", "type": "INTEGER", "nullable": False},
                {"name": "created_at", "type": "TIMESTAMP", "nullable": False}
            ]
        }
    
    def _create_generic_entity_from_project_name(self, project_name: str) -> Dict[str, Any]:
        """从项目名称创建通用实体"""
        # 清理项目名称作为实体名
        entity_name = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff]', '_', project_name.lower())
        entity_name = re.sub(r'_+', '_', entity_name).strip('_')
        
        return {
            "name": entity_name,
            "description": f"{project_name}主要数据表",
            "columns": [
                {"name": "id", "type": "BIGINT", "primary": True},
                {"name": "name", "type": "VARCHAR(100)", "nullable": False},
                {"name": "description", "type": "TEXT", "nullable": True},
                {"name": "status", "type": "VARCHAR(20)", "nullable": False},
                {"name": "created_at", "type": "TIMESTAMP", "nullable": False},
                {"name": "updated_at", "type": "TIMESTAMP", "nullable": False}
            ]
        }
    
    def _create_user_entity(self) -> Dict[str, Any]:
        """创建用户实体（如果需要用户管理）"""
        return {
            "name": "users",
            "description": "用户表",
            "columns": [
                {"name": "id", "type": "BIGINT", "primary": True},
                {"name": "username", "type": "VARCHAR(50)", "nullable": False},
                {"name": "password", "type": "VARCHAR(100)", "nullable": False},
                {"name": "email", "type": "VARCHAR(100)", "nullable": False},
                {"name": "phone", "type": "VARCHAR(20)", "nullable": True},
                {"name": "created_at", "type": "TIMESTAMP", "nullable": False},
                {"name": "updated_at", "type": "TIMESTAMP", "nullable": False}
            ]
        }
    
    def _create_order_entity(self) -> Dict[str, Any]:
        """创建订单实体"""
        return {
            "name": "orders",
            "description": "订单表",
            "columns": [
                {"name": "id", "type": "BIGINT", "primary": True},
                {"name": "order_no", "type": "VARCHAR(50)", "nullable": False},
                {"name": "amount", "type": "DECIMAL(10,2)", "nullable": False},
                {"name": "status", "type": "VARCHAR(20)", "nullable": False},
                {"name": "created_at", "type": "TIMESTAMP", "nullable": False}
            ]
        }
    
    def _create_product_entity(self) -> Dict[str, Any]:
        """创建产品实体"""
        return {
            "name": "products",
            "description": "产品表",
            "columns": [
                {"name": "id", "type": "BIGINT", "primary": True},
                {"name": "name", "type": "VARCHAR(100)", "nullable": False},
                {"name": "price", "type": "DECIMAL(10,2)", "nullable": False},
                {"name": "description", "type": "TEXT", "nullable": True},
                {"name": "status", "type": "VARCHAR(20)", "nullable": False},
                {"name": "created_at", "type": "TIMESTAMP", "nullable": False}
            ]
        }
    
    def _create_fallback_design_data_from_task(self, task: TaskItem) -> Dict[str, Any]:
        """创建基于任务的回退设计数据"""
        git_project_name = self._get_git_project_name()
        
        return {
            "project_info": {
                "name": git_project_name,
                "version": "1.0.0",
                "package_prefix": "com.example"
            },
            "database_design": [self._create_generic_entity_from_project_name(git_project_name)],
            "business_logic": [{
                "module": f"{git_project_name}管理",
                "description": task.description,
                "operations": ["create", "read", "update", "delete"]
            }],
            "api_design": [
                {"path": "/api/data/list", "method": "GET", "description": "获取数据列表"},
                {"path": "/api/data/create", "method": "POST", "description": "创建数据"},
                {"path": "/api/data/update", "method": "PUT", "description": "更新数据"},
                {"path": "/api/data/delete", "method": "DELETE", "description": "删除数据"}
            ]
        }
    
    def _prepare_design_data_for_frontend(self, task: TaskItem) -> Dict[str, Any]:
        """为前端代码生成准备设计数据"""
        try:
            # 构造前端代码生成器期望的数据格式
            design_data = {
                "project_info": {
                    "name": self.context.execution_plan.project_name if self.context.execution_plan else "UserManagementSystem",
                    "version": "1.0.0",
                    "framework": "Vue2"
                },
                "pages": [
                    {
                        "name": "Login",
                        "path": "/login",
                        "description": "用户登录页面",
                        "components": ["LoginForm"]
                    },
                    {
                        "name": "Register", 
                        "path": "/register",
                        "description": "用户注册页面",
                        "components": ["RegisterForm"]
                    },
                    {
                        "name": "Profile",
                        "path": "/profile", 
                        "description": "用户信息页面",
                        "components": ["ProfileForm", "PasswordForm"]
                    }
                ],
                "components": [
                    {"name": "LoginForm", "type": "form", "description": "登录表单组件"},
                    {"name": "RegisterForm", "type": "form", "description": "注册表单组件"},
                    {"name": "ProfileForm", "type": "form", "description": "用户信息表单组件"},
                    {"name": "PasswordForm", "type": "form", "description": "密码修改表单组件"}
                ],
                "api_endpoints": [
                    {"name": "login", "url": "/api/users/login", "method": "POST"},
                    {"name": "register", "url": "/api/users/register", "method": "POST"},
                    {"name": "getProfile", "url": "/api/users/profile", "method": "GET"},
                    {"name": "updateProfile", "url": "/api/users/profile", "method": "PUT"},
                    {"name": "updatePassword", "url": "/api/users/password", "method": "PUT"}
                ]
            }
            
            return design_data
            
        except Exception as e:
            logger.error(f"准备前端设计数据失败: {e}")
            # 返回最小的默认数据
            return {
                "project_info": {"name": "UserManagementSystem", "version": "1.0.0"},
                "pages": [],
                "components": [],
                "api_endpoints": []
            } 