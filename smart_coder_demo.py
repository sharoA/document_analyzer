#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能编码智能体使用示例
演示基于 LangGraph 的智能代码生成工作流
"""

import asyncio
import json
import sys
import os
from typing import Dict, Any

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from src.corder_integration.smart_coder_agent import SmartCoderAgent, LANGGRAPH_AVAILABLE
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已安装所有依赖，运行: python install_langgraph.py")
    sys.exit(1)

def compare_systems():
    """对比当前系统与智能编码智能体的差异"""
    print("📊 系统对比分析\n")
    
    comparison_data = {
        "特性": ["决策智能化", "错误处理", "质量保证", "可扩展性", "用户交互", "状态管理"],
        "当前系统": [
            "❌ 固定流程，缺乏智能决策",
            "⚠️ 基础错误处理，无重试机制", 
            "⚠️ 模板化生成，质量不稳定",
            "⚠️ 线性流程，难以扩展",
            "❌ 缺少人机交互",
            "⚠️ 简单状态机"
        ],
        "智能编码智能体": [
            "✅ AI驱动的智能决策和分支",
            "✅ 智能错误检测和自动修复",
            "✅ 多层次质量检查和优化",
            "✅ 图状态管理，高度可扩展",
            "✅ 支持人机协作和审批",
            "✅ 复杂图状态，支持循环优化"
        ]
    }
    
    # 打印对比表格
    print(f"{'特性':<12} | {'当前系统':<35} | {'智能编码智能体':<35}")
    print("-" * 90)
    
    for i, feature in enumerate(comparison_data["特性"]):
        current = comparison_data["当前系统"][i]
        smart = comparison_data["智能编码智能体"][i]
        print(f"{feature:<12} | {current:<35} | {smart:<35}")
    
    print("\n" + "="*90 + "\n")

async def demo_smart_workflow():
    """演示智能工作流"""
    print("🚀 智能编码智能体工作流演示\n")
    
    if not LANGGRAPH_AVAILABLE:
        print("❌ LangGraph 未安装，无法运行演示")
        print("请运行: python install_langgraph.py")
        return
    
    # 创建智能编码智能体
    try:
        agent = SmartCoderAgent()
        print("✅ 智能编码智能体初始化成功")
    except Exception as e:
        print(f"❌ 智能编码智能体初始化失败: {e}")
        return
    
    # 示例设计文档 - 复杂度适中的项目
    document_content = """
# 智能客服系统设计文档

## 项目概述
开发一个基于AI的智能客服系统，支持多渠道接入、智能问答、工单管理等功能。

## 技术要求
- 后端：Java 11 + Spring Boot 2.7 + Maven
- 前端：Vue 3 + TypeScript + Element Plus
- 数据库：MySQL 8.0 + Redis 6.0
- 消息队列：RabbitMQ
- AI接口：GPT-3.5-turbo
- 部署：Docker + Kubernetes

## 功能模块

### 1. 用户管理模块
- 用户注册/登录
- 权限管理（管理员、客服、用户）
- 用户配置管理

### 2. 智能问答模块
- 知识库管理
- 意图识别
- 智能回复生成
- 多轮对话管理

### 3. 会话管理模块  
- 多渠道接入（Web、微信、API）
- 会话状态管理
- 会话历史记录
- 实时消息推送

### 4. 工单系统模块
- 工单创建/分配
- 工单状态跟踪
- 工单优先级管理
- 自动升级机制

### 5. 数据分析模块
- 服务质量统计
- 用户满意度分析
- 客服工作量统计
- 智能报表生成

## API设计

### 用户相关API
- POST /api/auth/login - 用户登录
- POST /api/auth/logout - 用户登出
- GET /api/users/profile - 获取用户信息
- PUT /api/users/profile - 更新用户信息

### 对话相关API
- POST /api/chat/sessions - 创建会话
- GET /api/chat/sessions/{id} - 获取会话详情
- POST /api/chat/messages - 发送消息
- GET /api/chat/history - 获取历史记录

### 工单相关API
- POST /api/tickets - 创建工单
- GET /api/tickets - 获取工单列表
- PUT /api/tickets/{id} - 更新工单
- DELETE /api/tickets/{id} - 删除工单

### 知识库API
- POST /api/knowledge/articles - 创建知识条目
- GET /api/knowledge/search - 搜索知识库
- PUT /api/knowledge/articles/{id} - 更新条目

## 数据库设计

### 用户表 (users)
- id: bigint, 主键
- username: varchar(50), 用户名
- email: varchar(100), 邮箱
- role: enum('admin','agent','user'), 角色
- created_at: timestamp
- updated_at: timestamp

### 会话表 (chat_sessions)
- id: bigint, 主键
- user_id: bigint, 用户ID
- channel: enum('web','wechat','api'), 渠道
- status: enum('active','closed'), 状态
- created_at: timestamp

### 消息表 (messages)
- id: bigint, 主键
- session_id: bigint, 会话ID
- sender_type: enum('user','bot','agent'), 发送方
- content: text, 消息内容
- message_type: enum('text','image','file'), 消息类型
- created_at: timestamp

### 工单表 (tickets)
- id: bigint, 主键
- user_id: bigint, 用户ID
- title: varchar(200), 标题
- description: text, 描述
- priority: enum('low','medium','high','urgent'), 优先级
- status: enum('open','processing','resolved','closed'), 状态
- assigned_to: bigint, 分配给
- created_at: timestamp
- updated_at: timestamp

### 知识库表 (knowledge_articles)
- id: bigint, 主键
- title: varchar(200), 标题
- content: text, 内容
- category: varchar(100), 分类
- tags: json, 标签
- status: enum('draft','published'), 状态
- created_at: timestamp
- updated_at: timestamp

## 非功能需求
- 性能：支持1000并发用户，响应时间<200ms
- 可用性：99.9%可用性，支持故障自动恢复
- 安全性：数据加密传输，用户认证授权
- 可扩展性：微服务架构，支持水平扩展

## 部署要求
- 使用Docker容器化部署
- Kubernetes集群管理
- CI/CD流水线自动部署
- 监控和日志收集
"""
    
    print("📄 示例文档内容:")
    print("- 项目：智能客服系统")
    print("- 复杂度：中高级")
    print("- 模块：5个主要功能模块")
    print("- API：15+ 个接口")
    print("- 数据表：5个核心表")
    print("- 技术栈：现代化微服务架构\n")
    
    try:
        # 执行智能工作流
        print("🔄 启动智能工作流...")
        result = await agent.execute_smart_workflow(
            document_content=document_content,
            project_name="smart-customer-service",
            config={
                "max_retries": 3,
                "quality_threshold": 0.7,
                "enable_optimization": True
            }
        )
        
        # 显示执行结果
        print("\n📊 执行结果分析:")
        print(f"状态: {result.get('status', '未知')}")
        print(f"质量评分: {result.get('quality_score', 0):.2f}")
        
        if result.get('tech_stack'):
            print(f"\n🛠️ 智能选择的技术栈:")
            tech_stack = result['tech_stack']
            for key, value in tech_stack.items():
                if key != 'reasoning':
                    print(f"  {key}: {value}")
            
            if 'reasoning' in tech_stack:
                print(f"\n💡 选择理由: {tech_stack['reasoning']}")
        
        if result.get('architecture'):
            print(f"\n🏗️ 系统架构设计:")
            arch = result['architecture']
            if 'layers' in arch:
                print("  分层架构:")
                for layer, desc in arch['layers'].items():
                    print(f"    {layer}: {desc}")
        
        if result.get('errors'):
            print(f"\n⚠️ 警告信息:")
            for error in result['errors']:
                print(f"  - {error}")
        
        print(f"\n📁 项目路径: {result.get('project_path', '未生成')}")
        print(f"📄 生成文件数量: {len(result.get('generated_files', []))}")
        
        return result
        
    except Exception as e:
        print(f"❌ 智能工作流执行失败: {e}")
        return None

def show_workflow_advantages():
    """展示智能工作流的优势"""
    print("🌟 智能编码智能体的核心优势\n")
    
    advantages = [
        {
            "title": "🧠 智能决策能力",
            "description": "基于文档分析自动选择最适合的技术栈和架构模式",
            "example": "自动识别项目复杂度，选择微服务vs单体架构"
        },
        {
            "title": "🔄 自适应工作流",
            "description": "支持条件分支、循环优化，根据质量检查结果动态调整",
            "example": "代码质量不达标时自动触发优化循环"
        },
        {
            "title": "🔍 多层质量保证",
            "description": "文档质量评估、代码质量检查、测试验证多重保障",
            "example": "低质量文档自动收集补充信息"
        },
        {
            "title": "⚡ 智能错误处理",
            "description": "自动检测错误、智能重试、自我修复能力",
            "example": "编译错误时自动分析并修复代码"
        },
        {
            "title": "🎯 个性化策略",
            "description": "根据项目特点制定专属的代码生成策略",
            "example": "API优先vs数据模型优先的生成顺序"
        },
        {
            "title": "📈 持续学习",
            "description": "基于执行历史和反馈持续优化工作流",
            "example": "记录成功模式，提高后续项目质量"
        }
    ]
    
    for i, advantage in enumerate(advantages, 1):
        print(f"{i}. {advantage['title']}")
        print(f"   描述: {advantage['description']}")
        print(f"   示例: {advantage['example']}\n")

async def main():
    """主演示流程"""
    print("🎬 智能编码智能体完整演示\n")
    print("="*60)
    
    # 1. 系统对比
    compare_systems()
    
    # 2. 优势展示
    show_workflow_advantages()
    
    # 3. 实际演示
    result = await demo_smart_workflow()
    
    # 4. 总结
    print("\n" + "="*60)
    print("📝 演示总结:")
    
    if result:
        print("✅ 智能编码智能体成功完成了复杂项目的分析和规划")
        print("🎯 相比传统方法，提供了更智能、更可靠的代码生成体验")
        print("🚀 支持复杂的决策逻辑和自适应优化")
    else:
        print("⚠️ 演示执行遇到问题，但架构设计已经完成")
        print("💡 安装完整依赖后可以体验完整功能")
    
    print("\n🎉 欢迎使用智能编码智能体！")
    print("📚 更多信息请查看 smart_coder_agent.py 源码")

if __name__ == "__main__":
    asyncio.run(main()) 