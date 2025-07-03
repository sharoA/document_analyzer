#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git Function Calling 工具包装器
为大模型提供可直接调用的 Git 操作工具
"""

import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from .git_manager import GitManager
from .config import get_coder_config

logger = logging.getLogger(__name__)

class GitFunctionCalling:
    """Git Function Calling 工具包装器"""
    
    def __init__(self):
        self.git_manager = GitManager()
        self.config = get_coder_config()
    
    def get_function_schemas(self) -> List[Dict]:
        """获取所有可用的 Git 工具函数 Schema"""
        return [
            {
                "name": "git_check_repository_status",
                "description": "检查 Git 仓库状态，包括当前分支、未提交更改、远程状态等",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_path": {
                            "type": "string",
                            "description": "项目路径，如果不提供则使用默认路径"
                        }
                    }
                }
            },
            {
                "name": "git_analyze_project_structure",
                "description": "分析现有项目结构，检查后端、前端、Git 仓库等信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_path": {
                            "type": "string",
                            "description": "项目路径，如果不提供则使用默认路径"
                        }
                    }
                }
            },
            {
                "name": "git_setup_project_environment",
                "description": "设置项目环境，包括创建目录、初始化 Git 仓库、创建分支等",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_name": {
                            "type": "string",
                            "description": "项目名称",
                            "required": True
                        },
                        "branch_name": {
                            "type": "string", 
                            "description": "分支名称",
                            "required": True
                        },
                        "remote_url": {
                            "type": "string",
                            "description": "远程仓库 URL（可选）"
                        }
                    },
                    "required": ["project_name", "branch_name"]
                }
            },
            {
                "name": "git_commit_and_push",
                "description": "提交并推送代码到远程仓库",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "commit_message": {
                            "type": "string",
                            "description": "提交信息",
                            "required": True
                        },
                        "project_path": {
                            "type": "string",
                            "description": "项目路径，如果不提供则使用默认路径"
                        },
                        "push_to_remote": {
                            "type": "boolean",
                            "description": "是否推送到远程仓库，默认为 true"
                        }
                    },
                    "required": ["commit_message"]
                }
            },
            {
                "name": "git_create_commit_message",
                "description": "创建规范的 Git 提交信息",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "commit_type": {
                            "type": "string",
                            "description": "提交类型，如：feat（新功能）、fix（修复）、docs（文档）、test（测试）等",
                            "enum": ["feat", "fix", "docs", "style", "refactor", "test", "chore"],
                            "required": True
                        },
                        "description": {
                            "type": "string",
                            "description": "提交描述",
                            "required": True
                        }
                    },
                    "required": ["commit_type", "description"]
                }
            }
        ]
    
    def execute_function(self, function_name: str, parameters: Dict) -> Dict[str, Any]:
        """执行指定的函数"""
        try:
            if function_name == "git_check_repository_status":
                return self._check_repository_status(**parameters)
            elif function_name == "git_analyze_project_structure":
                return self._analyze_project_structure(**parameters)
            elif function_name == "git_setup_project_environment":
                return self._setup_project_environment(**parameters)
            elif function_name == "git_commit_and_push":
                return self._commit_and_push(**parameters)
            elif function_name == "git_create_commit_message":
                return self._create_commit_message(**parameters)
            else:
                return {
                    "success": False,
                    "error": f"未知的函数: {function_name}"
                }
        except Exception as e:
            logger.error(f"执行函数 {function_name} 失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _check_repository_status(self, project_path: Optional[str] = None) -> Dict[str, Any]:
        """检查仓库状态"""
        try:
            status = self.git_manager.get_repository_status(project_path)
            return {
                "success": True,
                "data": status,
                "message": "仓库状态检查完成"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"检查仓库状态失败: {e}"
            }
    
    def _analyze_project_structure(self, project_path: Optional[str] = None) -> Dict[str, Any]:
        """分析项目结构"""
        try:
            analysis = self.git_manager.analyze_existing_structure(project_path)
            return {
                "success": True,
                "data": analysis,
                "message": "项目结构分析完成"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"分析项目结构失败: {e}"
            }
    
    def _setup_project_environment(
        self, 
        project_name: str, 
        branch_name: str,
        remote_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """设置项目环境"""
        try:
            result = self.git_manager.setup_project_environment(
                project_name, branch_name, remote_url
            )
            return {
                "success": result["status"] == "success",
                "data": result,
                "message": f"项目环境设置{'成功' if result['status'] == 'success' else '失败'}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"设置项目环境失败: {e}"
            }
    
    def _commit_and_push(
        self, 
        commit_message: str,
        project_path: Optional[str] = None,
        push_to_remote: bool = True
    ) -> Dict[str, Any]:
        """提交并推送代码"""
        try:
            result = self.git_manager.commit_and_push_code(
                commit_message, project_path, push_to_remote
            )
            return {
                "success": result["status"] == "success",
                "data": result,
                "message": f"代码提交{'成功' if result['status'] == 'success' else '失败'}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"提交代码失败: {e}"
            }
    
    def _create_commit_message(self, commit_type: str, description: str) -> Dict[str, Any]:
        """创建提交信息"""
        try:
            message = self.git_manager.create_commit_message(commit_type, description)
            return {
                "success": True,
                "data": {"commit_message": message},
                "message": "提交信息创建成功"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"创建提交信息失败: {e}"
            }


# MCP 协议支持
class GitMCPServer:
    """Git MCP 服务器"""
    
    def __init__(self):
        self.git_tools = GitFunctionCalling()
    
    def get_mcp_tools(self) -> List[Dict]:
        """获取 MCP 工具定义"""
        function_schemas = self.git_tools.get_function_schemas()
        mcp_tools = []
        
        for schema in function_schemas:
            mcp_tool = {
                "name": schema["name"],
                "description": schema["description"],
                "inputSchema": schema["parameters"]
            }
            mcp_tools.append(mcp_tool)
        
        return mcp_tools
    
    async def handle_tool_call(self, tool_name: str, arguments: Dict) -> Dict:
        """处理工具调用"""
        result = self.git_tools.execute_function(tool_name, arguments)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, ensure_ascii=False, indent=2)
                }
            ]
        }


# 使用示例
def demo_function_calling():
    """演示 Function Calling 使用"""
    git_tools = GitFunctionCalling()
    
    # 1. 获取函数 Schema
    schemas = git_tools.get_function_schemas()
    print("=== 可用的 Git 工具函数 ===")
    for schema in schemas:
        print(f"- {schema['name']}: {schema['description']}")
    
    # 2. 执行检查仓库状态
    print("\n=== 检查仓库状态 ===")
    status_result = git_tools.execute_function("git_check_repository_status", {})
    print(json.dumps(status_result, ensure_ascii=False, indent=2))
    
    # 3. 分析项目结构
    print("\n=== 分析项目结构 ===")
    analysis_result = git_tools.execute_function("git_analyze_project_structure", {})
    print(json.dumps(analysis_result, ensure_ascii=False, indent=2))
    
    # 4. 创建提交信息
    print("\n=== 创建提交信息 ===")
    commit_msg_result = git_tools.execute_function("git_create_commit_message", {
        "commit_type": "feat",
        "description": "添加 Git Function Calling 支持"
    })
    print(json.dumps(commit_msg_result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    demo_function_calling() 