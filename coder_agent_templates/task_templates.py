#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务模版定义
包含各种任务的模版和配置
"""

from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class TaskTemplate:
    """任务模版"""
    id: str
    name: str
    description: str
    type: str
    estimated_hours: float
    dependencies: List[str]
    assigned_module: str
    template_content: str = ""

# 预定义的任务模版
TASK_TEMPLATES = {
    "backend_setup": TaskTemplate(
        id="backend_setup",
        name="后端项目初始化",
        description="创建Spring Boot项目结构，配置Maven依赖",
        type="backend",
        estimated_hours=1.0,
        dependencies=[],
        assigned_module="code_generator",
        template_content="""
# 后端项目初始化任务

## 任务目标
- 创建标准的Spring Boot项目结构
- 配置Maven依赖
- 设置基础配置文件

## 生成内容
1. pom.xml - Maven项目配置
2. application.properties - 应用配置
3. 项目目录结构
4. 基础配置类

## 技术要求
- Java 8
- Spring Boot 2.7.x
- Maven 3.6+
"""
    ),
    
    "frontend_setup": TaskTemplate(
        id="frontend_setup", 
        name="前端项目初始化",
        description="创建Vue2项目结构，配置Webpack",
        type="frontend",
        estimated_hours=1.0,
        dependencies=[],
        assigned_module="code_generator",
        template_content="""
# 前端项目初始化任务

## 任务目标
- 创建Vue2项目结构
- 配置Webpack构建工具
- 设置开发和生产环境

## 生成内容
1. package.json - 项目依赖配置
2. webpack配置文件
3. Vue项目目录结构
4. 基础组件和路由

## 技术要求
- Vue.js 2.x
- Webpack 4.x
- Element UI
"""
    ),
    
    "api_implementation": TaskTemplate(
        id="api_implementation",
        name="API接口实现", 
        description="根据接口设计实现RESTful API",
        type="backend",
        estimated_hours=2.0,
        dependencies=["backend_setup"],
        assigned_module="code_generator",
        template_content="""
# API接口实现任务

## 任务目标
- 实现RESTful API接口
- 实现统一异常处理

## 生成内容
1. Controller类 - 接口控制器
2. DTO类 - 数据传输对象
3. 异常处理类

## 设计原则
- RESTful设计规范
- 统一响应格式
- 完善的错误处理
"""
    ),
    
    "database_layer": TaskTemplate(
        id="database_layer",
        name="数据库层实现",
        description="实现数据访问层，包括Entity和Repository",
        type="database", 
        estimated_hours=1.5,
        dependencies=["backend_setup"],
        assigned_module="code_generator",
        template_content="""
# 数据库层实现任务

## 任务目标
- 创建JPA Entity类
- 实现Repository接口
- 配置数据库连接

## 生成内容
1. Entity类 - 数据实体
2. Repository接口 - 数据访问
3. MyBatis Mapper文件
4. 数据库配置

## 技术要求
- JPA规范
- MyBatis集成
- 数据库事务管理
"""
    ),
    
    "unit_testing": TaskTemplate(
        id="unit_testing",
        name="单元测试编写",
        description="为业务逻辑编写JUnit单元测试",
        type="test",
        estimated_hours=2.0,
        dependencies=["api_implementation", "database_layer"],
        assigned_module="test_generator",
        template_content="""
# 单元测试编写任务

## 任务目标
- 编写完整的单元测试
- 确保代码覆盖率达标
- 设置测试数据和Mock

## 生成内容
1. Service层测试
2. Controller层测试
3. Repository层测试
4. 测试配置文件

## 测试要求
- JUnit 5框架
- Mockito模拟
- 覆盖率>80%
"""
    )
}

def get_task_template(template_id: str) -> TaskTemplate:
    """获取任务模版"""
    return TASK_TEMPLATES.get(template_id)

def list_task_templates() -> List[TaskTemplate]:
    """获取所有任务模版"""
    return list(TASK_TEMPLATES.values())

def get_templates_by_type(task_type: str) -> List[TaskTemplate]:
    """根据类型获取任务模版"""
    return [template for template in TASK_TEMPLATES.values() if template.type == task_type] 