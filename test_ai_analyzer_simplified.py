#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试简化版AI分析器的输出结果
"""

import asyncio
import json
import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.analysis_services.ai_analyzer import AIAnalyzerService

# 模拟LLM客户端
class MockLLMClient:
    def chat(self, messages, max_tokens=4000):
        # 返回一个简单的设计文档
        return """设计文档 - 测试项目V0.1
1. 系统架构设计
1.1 项目介绍
这是一个测试项目，用于验证AI分析器的输出格式。
建设目标及路线。优化系统架构，提升开发效率。

1.2 功能需求说明
1.2.1 核心功能优化
调整说明:本期对核心功能进行优化调整。

1.3 总体架构
采用微服务架构模式，实现松耦合、高可扩展的系统设计：
- 涉及2个后端服务：
1. 用户服务：user-service
2. 业务服务：business-service

1.4 技术栈选型
- 后端框架：Spring Boot 2.7.x + Spring Cloud 2021.x
- 数据访问：MyBatis Plus 3.5.x
- 数据库：MySQL 8.0
- 缓存：Redis 6.0

2. 服务设计
2.1 用户服务 (user-service)
职责：用户管理、权限控制

2.1.1 核心模块：
- 用户管理模块

2.1.2 API设计：
2.1.2.1 新增接口：
uri : GET /api/v1/users
method: GET
description:获取用户列表

2.1.3 数据库表设计：
CREATE TABLE users (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(50) UNIQUE NOT NULL
);

2.1.4 本次项目依赖服务：
依赖服务名称：无

3 执行要求
3.1 涉及服务范围
本次涉及的服务范围：
1. 用户服务：user-service，git地址：http://localhost:30000/ls/user-service.git

3.2 涉及数据库范围
本次涉及的数据库范围：
3.2.1 用户数据库：MySQL

3.3 涉及接口范围
本次新增接口，已经按服务范围进行划分，详见设计文档2服务设计部分。"""

# 模拟向量数据库
class MockVectorDB:
    pass

async def test_ai_analyzer():
    """测试AI分析器"""
    
    # 模拟输入数据
    input_data = {
        "content_analysis": {
            "data": {
                "change_analysis": {
                    "change_analyses": [
                        {
                            "changeType": "新增",
                            "componentName": "用户管理功能",
                            "description": "新增用户列表查询功能"
                        }
                    ]
                }
            }
        },
        "parsing_result": {
            "data": {
                "fileFormat": {
                    "fileName": "test_requirements.docx",
                    "primaryType": "需求文档",
                    "technicalDetails": {"charCount": 1000},
                    "basicInfo": {"language": "中文"}
                },
                "documentStructure": {
                    "contentSummary": {
                        "abstract": "这是一个用户管理系统的需求文档",
                        "functionCount": 3,
                        "functionName": ["用户注册", "用户登录", "用户列表"],
                        "apiCount": 2,
                        "apiName": ["POST /users", "GET /users"]
                    },
                    "contentKeyWord": {
                        "primaryKeywords": ["用户管理", "权限控制", "接口设计"],
                        "semanticClusters": ["用户服务", "认证授权"]
                    }
                }
            }
        }
    }
    
    # 创建AI分析器
    analyzer = AIAnalyzerService(
        llm_client=MockLLMClient(),
        vector_db=MockVectorDB()
    )
    
    # 执行分析
    try:
        result = await analyzer.analyze(
            task_id="test_001",
            input_data=input_data
        )
        
        print("=== AI分析器测试结果 ===")
        print(f"成功状态: {result.get('success')}")
        print(f"分析方法: {result.get('metadata', {}).get('analysis_method')}")
        print(f"框架信息: {result.get('metadata', {}).get('framework')}")
        print(f"Markdown生成: {result.get('metadata', {}).get('markdown_generated')}")
        
        # 检查数据结构
        data = result.get('data', {})
        print(f"\n=== 数据结构检查 ===")
        print(f"包含markdown_content: {'markdown_content' in data}")
        print(f"包含generation_metadata: {'generation_metadata' in data}")
        print(f"包含design_data: {'design_data' in data}")
        print(f"包含architecture_diagram: {'architecture_diagram' in data}")
        
        # 显示markdown内容的前500字符
        markdown_content = data.get('markdown_content', '')
        print(f"\n=== Markdown内容预览 ===")
        print(f"长度: {len(markdown_content)} 字符")
        if markdown_content:
            preview = markdown_content[:500] + "..." if len(markdown_content) > 500 else markdown_content
            print(f"内容预览:\n{preview}")
        
        # 保存完整结果到文件
        with open(f"{project_root}/test_result_simplified.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n=== 完整结果已保存到 test_result_simplified.json ===")
        
        return result
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(test_ai_analyzer())