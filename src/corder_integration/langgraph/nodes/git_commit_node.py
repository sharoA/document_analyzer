#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git提交节点 - 智能提交管理
"""

import asyncio
import json
import logging
import os
import subprocess
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

# 🔥 修改：使用火山引擎客户端替代OpenAI
try:
    from ....utils.volcengine_client import get_volcengine_client
    from ....resource.config import get_config
    VOLCENGINE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"火山引擎客户端不可用: {e}")
    VOLCENGINE_AVAILABLE = False

logger = logging.getLogger(__name__)

class GitCommitPrompts:
    """Git提交提示词管理器"""
    
    def __init__(self):
        self.prompts_dir = Path(__file__).parent.parent / "prompts"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.prompts_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        self._load_prompts()
    
    def _load_prompts(self):
        """加载提示词模板"""
        self.templates = {}
        self.default_templates = {}
        
        # 定义模板文件映射
        template_files = {
            "commit_message": "commit_message_prompts.jinja2",
            "pull_request": "pull_request_prompts.jinja2"
        }
        
        # 定义对应的默认模板文件映射
        default_template_files = {
            "commit_message": "default/commit_message_default_prompts.jinja2",
            "pull_request": "default/pull_request_default_prompts.jinja2"
        }
        
        # 逐个加载专门的模板文件
        for prompt_type, template_file in template_files.items():
            try:
                template = self.jinja_env.get_template(template_file)
                self.templates[prompt_type] = template
                logger.info(f"模板 {template_file} 加载成功")
            except Exception as e:
                logger.warning(f"加载模板 {template_file} 失败: {e}")
                self.templates[prompt_type] = None
        
        # 逐个加载对应的默认模板文件
        for prompt_type, default_template_file in default_template_files.items():
            try:
                default_template = self.jinja_env.get_template(default_template_file)
                self.default_templates[prompt_type] = default_template
                logger.info(f"默认模板 {default_template_file} 加载成功")
            except Exception as e:
                logger.warning(f"加载默认模板 {default_template_file} 失败: {e}")
                self.default_templates[prompt_type] = None
    
    def get_prompt(self, prompt_type: str, **kwargs) -> str:
        """获取渲染后的提示词"""
        try:
            # 首先尝试从专门的模板文件获取
            if prompt_type in self.templates and self.templates[prompt_type]:
                template = self.templates[prompt_type]
                if hasattr(template.module, f"{prompt_type}_prompt"):
                    macro = getattr(template.module, f"{prompt_type}_prompt")
                    return macro(**kwargs)
            
            # 其次尝试从对应的默认模板获取
            if prompt_type in self.default_templates and self.default_templates[prompt_type]:
                default_template = self.default_templates[prompt_type]
                if hasattr(default_template.module, f"{prompt_type}_prompt"):
                    macro = getattr(default_template.module, f"{prompt_type}_prompt")
                    return macro(**kwargs)
            
            # 最后使用内置默认提示词
            logger.warning(f"未找到提示词类型: {prompt_type}，使用内置默认提示词")
            return self._get_builtin_default_prompt(prompt_type, **kwargs)
            
        except Exception as e:
            logger.error(f"渲染提示词失败: {e}")
            return self._get_builtin_default_prompt(prompt_type, **kwargs)
    
    def _get_builtin_default_prompt(self, prompt_type: str, **kwargs) -> str:
        """获取内置默认提示词（最后备选方案）"""
        builtin_templates = {
            "commit_message": """
请为以下代码变更生成Git提交信息：

项目名称：{project_name}
完成的服务：{completed_services}

生成的功能：
- {service_count}个微服务
- API接口总数：{api_count}
- 数据库表数：{sql_count}

代码审查结果：{code_review_summary}
测试覆盖率：{test_coverage_summary}

请生成符合Conventional Commits规范的提交信息，格式如下：
feat: 实现电商系统核心微服务架构

- 新增用户服务：用户注册、登录、信息管理
- 新增产品服务：产品展示、库存管理
- 新增订单服务：订单创建、支付处理
- 实现服务间Feign调用
- 添加完整的单元测试，覆盖率85%+

只返回commit message文本，不要其他内容。
""",
            "pull_request": """
请为以下代码变更生成Pull Request描述：

项目：{project_name}
分支：{target_branch}
提交哈希：{commit_hash}

实现的服务：{completed_services}
代码质量：{code_quality_summary}
测试覆盖率：{test_coverage_summary}

请生成一个专业的PR描述，包含：
1. 变更概述
2. 实现的功能列表
3. 技术栈和架构
4. 测试情况
5. 部署说明

只返回PR描述文本。
"""
        }
        
        template_str = builtin_templates.get(prompt_type, "")
        if template_str:
            return template_str.format(**kwargs)
        return ""

async def git_commit_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Git提交节点 - 代码提交和推送
    """
    
    logger.info(f"开始执行Git提交: {state['project_name']}")
    
    client = get_volcengine_client()
    prompts = GitCommitPrompts()
    
    try:
        commit_results = {}
        
        # 🎯 生成提交信息
        commit_message = await generate_commit_message(state, client, prompts)
        
        # 📁 切换到工作目录
        workspace_path = f"./workspace/{state['project_name']}"
        original_cwd = os.getcwd()
        
        try:
            os.chdir(workspace_path)
            
            # 📝 添加所有文件到Git
            logger.info("添加文件到Git...")
            subprocess.run(["git", "add", "."], check=True, capture_output=True, text=True)
            
            # 📊 检查是否有变更
            status_result = subprocess.run(
                ["git", "status", "--porcelain"], 
                capture_output=True, text=True
            )
            
            if not status_result.stdout.strip():
                logger.info("没有需要提交的变更")
                state["commit_hashes"] = {}
                state["push_results"] = {}
                state["current_phase"] = "completed"
                return state
            
            # 🔧 配置Git用户信息（如果需要）
            try:
                subprocess.run([
                    "git", "config", "user.name", "Coding Agent"
                ], check=True, capture_output=True, text=True)
                subprocess.run([
                    "git", "config", "user.email", "coding-agent@company.com"
                ], check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError:
                pass  # 用户信息可能已经配置
            
            # 💾 提交代码
            logger.info(f"提交代码: {commit_message}")
            commit_result = subprocess.run([
                "git", "commit", "-m", commit_message
            ], capture_output=True, text=True)
            
            if commit_result.returncode == 0:
                # 获取提交哈希
                hash_result = subprocess.run([
                    "git", "rev-parse", "HEAD"
                ], capture_output=True, text=True)
                commit_hash = hash_result.stdout.strip() if hash_result.returncode == 0 else "unknown"
                
                commit_results["commit_hash"] = commit_hash
                commit_results["commit_success"] = True
                
                logger.info(f"提交成功，哈希: {commit_hash}")
                
                # 🚀 推送到远程仓库（如果配置了）
                if state.get("git_repo_url"):
                    logger.info("推送到远程仓库...")
                    
                    try:
                        push_result = subprocess.run([
                            "git", "push", "origin", state["target_branch"]
                        ], capture_output=True, text=True, timeout=60)
                        
                        if push_result.returncode == 0:
                            commit_results["push_success"] = True
                            logger.info("推送成功")
                            
                            # 🔗 生成PR（如果需要）
                            pr_url = await generate_pull_request_info(state, client, prompts, commit_hash)
                            commit_results["pr_url"] = pr_url
                            
                        else:
                            commit_results["push_success"] = False
                            commit_results["push_error"] = push_result.stderr
                            logger.warning(f"推送失败: {push_result.stderr}")
                    
                    except subprocess.TimeoutExpired:
                        commit_results["push_success"] = False
                        commit_results["push_error"] = "推送超时"
                        logger.warning("推送超时")
                
                else:
                    commit_results["push_success"] = True  # 本地仓库，无需推送
                    logger.info("本地仓库，无需推送")
            
            else:
                commit_results["commit_success"] = False
                commit_results["commit_error"] = commit_result.stderr
                logger.error(f"提交失败: {commit_result.stderr}")
        
        finally:
            # 恢复原始工作目录
            os.chdir(original_cwd)
        
        # 🔄 更新状态
        for service in state["completed_services"]:
            state["commit_hashes"][service] = commit_results.get("commit_hash", "")
            state["push_results"][service] = commit_results.get("push_success", False)
            if commit_results.get("pr_url"):
                state["pr_urls"][service] = commit_results["pr_url"]
        
        state["current_phase"] = "completed"
        
        logger.info(f"Git提交完成: {commit_results}")
        
        return state
        
    except Exception as e:
        logger.error(f"Git提交失败: {str(e)}")
        state["execution_errors"].append(f"Git提交失败: {str(e)}")
        state["current_phase"] = "error"
        return state

async def generate_commit_message(state: Dict[str, Any], client, prompts: GitCommitPrompts) -> str:
    """生成提交信息"""
    
    logger.info("生成Git提交信息")
    
    try:
        commit_generation = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system", 
                    "content": "你是一个Git提交信息专家，擅长编写清晰、规范的commit message。"
                },
                {
                    "role": "user", 
                    "content": prompts.get_prompt("commit_message",
                                                  project_name=state['project_name'],
                                                  completed_services=state['completed_services'],
                                                  generated_apis=state['generated_apis'],
                                                  generated_sql=state['generated_sql'],
                                                  code_review_results=state.get('code_review_results', {}),
                                                  test_coverage=state.get('test_coverage', {}))
                }
            ],
            temperature=0.3
        )
        
        commit_message = commit_generation.choices[0].message.content.strip()
        
        # 确保提交信息不超过72个字符每行
        lines = commit_message.split('\n')
        if lines and len(lines[0]) > 72:
            lines[0] = lines[0][:69] + "..."
        
        return '\n'.join(lines)
        
    except Exception as e:
        logger.error(f"生成提交信息失败: {e}")
        # 返回默认提交信息
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        return f"feat: 实现{state['project_name']}微服务系统 ({timestamp})"

async def generate_pull_request_info(state: Dict[str, Any], client, prompts: GitCommitPrompts, commit_hash: str) -> str:
    """生成Pull Request信息"""
    
    logger.info("生成Pull Request信息")
    
    try:
        pr_generation = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system", 
                    "content": "你是一个代码评审专家，擅长编写详细的Pull Request描述。"
                },
                {
                    "role": "user", 
                    "content": prompts.get_prompt("pull_request",
                                                  project_name=state['project_name'],
                                                  target_branch=state['target_branch'],
                                                  commit_hash=commit_hash,
                                                  completed_services=state['completed_services'],
                                                  code_review_results=state.get('code_review_results', {}),
                                                  test_coverage=state.get('test_coverage', {}))
                }
            ],
            temperature=0.3
        )
        
        pr_description = pr_generation.choices[0].message.content.strip()
        
        # 生成PR URL（实际项目中需要调用Git平台API）
        if state.get("git_repo_url"):
            repo_url = state["git_repo_url"]
            if "github.com" in repo_url:
                pr_url = f"{repo_url}/compare/main...{state['target_branch']}"
            elif "gitlab.com" in repo_url:
                pr_url = f"{repo_url}/-/merge_requests/new?source_branch={state['target_branch']}"
            else:
                pr_url = f"{repo_url}/pull-request/new"
            
            logger.info(f"生成的PR URL: {pr_url}")
            return pr_url
        
        return ""
        
    except Exception as e:
        logger.error(f"生成PR信息失败: {e}")
        return "" 