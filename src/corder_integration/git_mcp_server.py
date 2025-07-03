#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git MCP 服务器
基于 Model Context Protocol (MCP) 为大模型提供 Git 操作能力
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

from .git_function_calling import GitFunctionCalling

logger = logging.getLogger(__name__)

@dataclass
class MCPTool:
    """MCP 工具定义"""
    name: str
    description: str
    inputSchema: Dict[str, Any]

@dataclass 
class MCPMessage:
    """MCP 消息"""
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    method: Optional[str] = None
    params: Optional[Dict] = None
    result: Optional[Any] = None
    error: Optional[Dict] = None

class GitMCPServer:
    """Git MCP 服务器"""
    
    def __init__(self):
        self.git_tools = GitFunctionCalling()
        self.tools = self._init_tools()
        self.capabilities = {
            "tools": {
                "listChanged": False
            }
        }
    
    def _init_tools(self) -> List[MCPTool]:
        """初始化工具列表"""
        function_schemas = self.git_tools.get_function_schemas()
        tools = []
        
        for schema in function_schemas:
            tool = MCPTool(
                name=schema["name"],
                description=schema["description"],
                inputSchema=schema["parameters"]
            )
            tools.append(tool)
        
        return tools
    
    async def handle_request(self, message: Dict) -> Dict:
        """处理 MCP 请求"""
        try:
            method = message.get("method")
            params = message.get("params", {})
            request_id = message.get("id")
            
            if method == "initialize":
                return self._create_response(request_id, self._handle_initialize(params))
            elif method == "tools/list":
                return self._create_response(request_id, self._handle_list_tools())
            elif method == "tools/call":
                result = await self._handle_tool_call(params)
                return self._create_response(request_id, result)
            else:
                return self._create_error_response(request_id, -32601, f"未知方法: {method}")
                
        except Exception as e:
            logger.error(f"处理 MCP 请求失败: {e}")
            return self._create_error_response(
                message.get("id"), -32603, f"内部错误: {str(e)}"
            )
    
    def _handle_initialize(self, params: Dict) -> Dict:
        """处理初始化请求"""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": self.capabilities,
            "serverInfo": {
                "name": "git-mcp-server",
                "version": "1.0.0",
                "description": "Git 操作 MCP 服务器"
            }
        }
    
    def _handle_list_tools(self) -> Dict:
        """处理工具列表请求"""
        tools_data = []
        for tool in self.tools:
            tools_data.append({
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema
            })
        
        return {"tools": tools_data}
    
    async def _handle_tool_call(self, params: Dict) -> Dict:
        """处理工具调用请求"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not tool_name:
            raise ValueError("工具名称不能为空")
        
        # 检查工具是否存在
        tool_exists = any(tool.name == tool_name for tool in self.tools)
        if not tool_exists:
            raise ValueError(f"工具不存在: {tool_name}")
        
        # 执行工具
        result = self.git_tools.execute_function(tool_name, arguments)
        
        # 格式化返回结果
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, ensure_ascii=False, indent=2)
                }
            ]
        }
    
    def _create_response(self, request_id: Optional[Union[str, int]], result: Any) -> Dict:
        """创建成功响应"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
    
    def _create_error_response(
        self, 
        request_id: Optional[Union[str, int]], 
        code: int, 
        message: str
    ) -> Dict:
        """创建错误响应"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }


class GitMCPClient:
    """Git MCP 客户端（用于测试）"""
    
    def __init__(self, server: GitMCPServer):
        self.server = server
        self.request_id = 0
    
    def _next_id(self) -> int:
        """获取下一个请求 ID"""
        self.request_id += 1
        return self.request_id
    
    async def initialize(self) -> Dict:
        """初始化连接"""
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {
                    "name": "git-mcp-client",
                    "version": "1.0.0"
                }
            }
        }
        return await self.server.handle_request(request)
    
    async def list_tools(self) -> Dict:
        """获取工具列表"""
        request = {
            "jsonrpc": "2.0", 
            "id": self._next_id(),
            "method": "tools/list"
        }
        return await self.server.handle_request(request)
    
    async def call_tool(self, tool_name: str, arguments: Dict = None) -> Dict:
        """调用工具"""
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {}
            }
        }
        return await self.server.handle_request(request)


# 实际使用示例
async def demo_mcp_server():
    """演示 MCP 服务器使用"""
    print("=== Git MCP 服务器演示 ===\n")
    
    # 1. 创建服务器和客户端
    server = GitMCPServer()
    client = GitMCPClient(server)
    
    # 2. 初始化连接
    print("1. 初始化连接...")
    init_response = await client.initialize()
    print(f"初始化响应: {json.dumps(init_response, ensure_ascii=False, indent=2)}\n")
    
    # 3. 获取工具列表
    print("2. 获取可用工具...")
    tools_response = await client.list_tools()
    if tools_response.get("result"):
        tools = tools_response["result"]["tools"]
        print(f"可用工具数量: {len(tools)}")
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description']}")
    print()
    
    # 4. 调用工具 - 检查仓库状态
    print("3. 检查 Git 仓库状态...")
    status_response = await client.call_tool("git_check_repository_status")
    if status_response.get("result"):
        content = status_response["result"]["content"][0]["text"]
        print(f"仓库状态:\n{content}\n")
    
    # 5. 调用工具 - 分析项目结构
    print("4. 分析项目结构...")
    analysis_response = await client.call_tool("git_analyze_project_structure")
    if analysis_response.get("result"):
        content = analysis_response["result"]["content"][0]["text"]
        print(f"项目结构:\n{content}\n")
    
    # 6. 调用工具 - 创建提交信息
    print("5. 创建规范提交信息...")
    commit_response = await client.call_tool("git_create_commit_message", {
        "commit_type": "feat",
        "description": "添加 Git MCP 服务器支持"
    })
    if commit_response.get("result"):
        content = commit_response["result"]["content"][0]["text"]
        print(f"提交信息:\n{content}\n")


# Anthropic Claude Function Calling 格式支持
class GitClaudeFunctionCalling:
    """为 Anthropic Claude 提供的 Function Calling 格式"""
    
    def __init__(self):
        self.git_tools = GitFunctionCalling()
    
    def get_claude_tools(self) -> List[Dict]:
        """获取 Claude Function Calling 格式的工具定义"""
        function_schemas = self.git_tools.get_function_schemas()
        claude_tools = []
        
        for schema in function_schemas:
            claude_tool = {
                "name": schema["name"],
                "description": schema["description"],
                "input_schema": schema["parameters"]
            }
            claude_tools.append(claude_tool)
        
        return claude_tools
    
    def execute_tool(self, tool_name: str, tool_input: Dict) -> str:
        """执行工具并返回结果"""
        result = self.git_tools.execute_function(tool_name, tool_input)
        return json.dumps(result, ensure_ascii=False, indent=2)


# 命令行工具
async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Git MCP 服务器")
    parser.add_argument("--demo", action="store_true", help="运行演示")
    parser.add_argument("--list-tools", action="store_true", help="列出所有工具")
    parser.add_argument("--call-tool", help="调用指定工具")
    parser.add_argument("--tool-args", help="工具参数 (JSON 格式)")
    
    args = parser.parse_args()
    
    if args.demo:
        await demo_mcp_server()
    elif args.list_tools:
        git_tools = GitFunctionCalling()
        schemas = git_tools.get_function_schemas()
        print("=== 可用的 Git 工具 ===")
        for schema in schemas:
            print(f"{schema['name']}: {schema['description']}")
    elif args.call_tool:
        git_tools = GitFunctionCalling()
        tool_args = {}
        if args.tool_args:
            try:
                tool_args = json.loads(args.tool_args)
            except json.JSONDecodeError as e:
                print(f"工具参数 JSON 格式错误: {e}")
                return
        
        result = git_tools.execute_function(args.call_tool, tool_args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main()) 