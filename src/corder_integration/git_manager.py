#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git管理器
负责Git分支管理、代码提交和推送操作
"""

import os
import re
import subprocess
import shutil
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from .config import get_coder_config, get_config_manager

logger = logging.getLogger(__name__)

class GitManager:
    """Git管理器"""
    
    def __init__(self):
        self.config = get_coder_config()
        self.config_manager = get_config_manager()
    
    def setup_project_environment(
        self, 
        project_name: str, 
        branch_name: str,
        remote_url: Optional[str] = None
    ) -> Dict[str, str]:
        """
        设置项目环境
        
        Args:
            project_name: 项目名称
            branch_name: 分支名称
            remote_url: 远程仓库URL（可选）
            
        Returns:
            环境设置结果
        """
        logger.info(f"开始设置项目环境: {project_name}")
        
        # 规范化项目名称，确保路径中不包含中文字符
        normalized_project_name = self._normalize_project_name_for_path(project_name)
        logger.info(f"项目名称规范化: '{project_name}' -> '{normalized_project_name}'")
        
        # 创建以规范化项目名称命名的项目路径
        base_project_path = self.config_manager.get_project_path()
        project_path = os.path.join(base_project_path, normalized_project_name)
        
        result = {
            "project_path": project_path,
            "branch_name": branch_name,
            "status": "success",
            "operations": []
        }
        
        try:
            # 1. 确保项目根目录存在
            os.makedirs(project_path, exist_ok=True)
            result["operations"].append(f"创建项目目录: {project_path}")
            
            # 2. 初始化或检查Git仓库（增强错误处理）
            try:
                if not self._is_git_repository(project_path):
                    # 初始化Git仓库
                    self._run_git_command(["git", "init"], project_path)
                    result["operations"].append("初始化Git仓库")
                    
                    # 设置默认分支为main
                    try:
                        self._run_git_command(["git", "branch", "-M", "main"], project_path)
                        result["operations"].append("设置默认分支为main")
                    except subprocess.CalledProcessError:
                        logger.warning("设置默认分支失败，使用当前分支")
                    
                    # 如果提供了远程URL，添加远程仓库
                    if remote_url:
                        self._run_git_command(
                            ["git", "remote", "add", "origin", remote_url], 
                            project_path
                        )
                        result["operations"].append(f"添加远程仓库: {remote_url}")
                else:
                    result["operations"].append("Git仓库已存在")
                    
                    # 确保远程仓库配置正确
                    if remote_url and not self._has_remote_origin(project_path):
                        try:
                            self._run_git_command(
                                ["git", "remote", "add", "origin", remote_url], 
                                project_path
                            )
                            result["operations"].append(f"添加远程仓库: {remote_url}")
                        except subprocess.CalledProcessError:
                            logger.warning("添加远程仓库失败，可能已存在")
                
                # 3. 拉取远程代码（如果有远程仓库）
                if self._has_remote_origin(project_path):
                    try:
                        # 首先拉取远程分支信息
                        self._run_git_command(["git", "fetch", "origin"], project_path)
                        result["operations"].append("获取远程分支信息")
                        
                        # 确保我们在main分支上
                        current_branch = self._get_current_branch(project_path)
                        if current_branch != "main":
                            try:
                                # 尝试切换到main分支
                                self._run_git_command(["git", "checkout", "main"], project_path)
                                result["operations"].append("切换到main分支")
                            except subprocess.CalledProcessError:
                                # 如果本地没有main分支，尝试从远程创建
                                try:
                                    self._run_git_command(["git", "checkout", "-b", "main", "origin/main"], project_path)
                                    result["operations"].append("从远程创建main分支")
                                except subprocess.CalledProcessError:
                                    logger.warning("远程main分支不存在，继续使用当前分支")
                        
                        # 如果成功切换到main，尝试拉取最新代码
                        current_branch = self._get_current_branch(project_path)
                        if current_branch == "main":
                            try:
                                self._run_git_command(["git", "pull", "origin", "main"], project_path)
                                result["operations"].append("从远程拉取main分支最新代码")
                            except subprocess.CalledProcessError as e:
                                logger.warning(f"拉取main分支失败: {e}")
                                result["operations"].append("拉取main分支失败，继续使用本地代码")
                        
                    except subprocess.CalledProcessError as e:
                        logger.warning(f"获取远程代码失败: {e}")
                        result["operations"].append("获取远程代码失败，继续使用本地代码")
                
                # 4. 切换或创建目标分支
                current_branch = self._get_current_branch(project_path)
                if current_branch != branch_name:
                    if self._branch_exists(project_path, branch_name):
                        # 分支存在，切换到该分支
                        self._run_git_command(["git", "checkout", branch_name], project_path)
                        result["operations"].append(f"切换到分支: {branch_name}")
                    else:
                        # 基于当前分支创建新分支
                        self._run_git_command(["git", "checkout", "-b", branch_name], project_path)
                        result["operations"].append(f"基于{current_branch}创建并切换到分支: {branch_name}")
                
            except Exception as git_error:
                logger.warning(f"Git设置失败: {git_error}")
                result["operations"].append(f"Git设置失败: {str(git_error)}")
                # Git失败不应该阻塞整个流程，继续创建目录结构
            
            # 5. 创建项目基础目录结构（无论git是否成功）
            self._create_basic_structure(project_path)
            result["operations"].append("创建基础目录结构")
            
            logger.info(f"项目环境设置完成: {project_path}")
            
        except Exception as e:
            logger.error(f"项目环境设置失败: {e}")
            result["status"] = "failed"
            result["error"] = str(e)
            # 即使设置失败，仍然返回项目路径，让代码生成可以继续
            logger.warning("环境设置失败，但代码生成将继续进行")
        
        return result
    
    def _is_git_repository(self, path: str) -> bool:
        """检查是否为Git仓库"""
        git_dir = os.path.join(path, '.git')
        return os.path.exists(git_dir)
    
    def _has_uncommitted_changes(self, path: str) -> bool:
        """检查是否有未提交的更改"""
        try:
            result = self._run_git_command(["git", "status", "--porcelain"], path)
            return bool(result.strip())
        except subprocess.CalledProcessError:
            return False
    
    def _get_current_branch(self, path: str) -> str:
        """获取当前分支名称"""
        try:
            result = self._run_git_command(["git", "branch", "--show-current"], path)
            return result.strip()
        except subprocess.CalledProcessError:
            return "main"  # 默认分支
    
    def _branch_exists(self, path: str, branch_name: str) -> bool:
        """检查分支是否存在"""
        try:
            result = self._run_git_command(["git", "branch", "--list", branch_name], path)
            return bool(result.strip())
        except subprocess.CalledProcessError:
            return False
    
    def _has_remote_origin(self, path: str) -> bool:
        """检查是否有远程origin"""
        try:
            result = self._run_git_command(["git", "remote", "get-url", "origin"], path)
            return bool(result.strip())
        except subprocess.CalledProcessError:
            return False
    
    def _normalize_project_name_for_path(self, project_name: str) -> str:
        """
        规范化项目名称，确保符合文件系统路径要求
        将中文、特殊字符转换为英文路径格式
        """
        if not project_name:
            return 'testproject'  # 默认项目名
        
        # 常见中文到英文的映射
        chinese_to_english = {
            '需求文档': 'requirements',
            '设计文档': 'design', 
            '链数优化': 'chain_optimization',
            '一局对接': 'business_integration',
            '用户管理': 'user_management',
            '产品管理': 'products_management',
            '订单管理': 'orders_management',
            '系统': 'system',
            '管理': 'management',
            '平台': 'platform',
            '项目': 'project',
            '应用': 'application',
            '服务': 'service',
            '模块': 'module',
            '组件': 'component',
            '对接': 'integration',
            '业务': 'business',
            '数据': 'data',
            '分析': 'analysis',
            '监控': 'monitor',
            '报告': 'report',
            '统计': 'statistics',
            '查询': 'query',
            '搜索': 'search',
            '导入': 'import',
            '导出': 'export',
            '配置': 'config',
            '设置': 'settings',
            '产品': 'products',
            '商品': 'products',
            '用户': 'users'
        }
        
        # 移除版本号信息（如V0, v1.0等）
        name = re.sub(r'[Vv]\d+(\.\d+)*', '', project_name).strip()
        
        # 先进行中文替换，并在替换时保持分隔符
        normalized_name = name
        for chinese, english in chinese_to_english.items():
            normalized_name = normalized_name.replace(chinese, f'_{english}_')
        
        # 处理特殊字符，将空格、连字符等转换为下划线
        normalized_name = re.sub(r'[\s\-\u4e00-\u9fff]', '_', normalized_name)
        
        # 移除其他特殊字符，只保留字母、数字、下划线
        normalized_name = re.sub(r'[^\w_]', '_', normalized_name)
        
        # 移除连续的下划线和连字符
        normalized_name = re.sub(r'[_\-]+', '_', normalized_name)
        
        # 移除前后的下划线
        normalized_name = normalized_name.strip('_')
        
        # 如果结果为空或太短，使用默认名称
        if not normalized_name or len(normalized_name) < 3:
            return 'testproject'
        
        # 确保以字母开头
        if not normalized_name[0].isalpha():
            normalized_name = 'project_' + normalized_name
        
        # 限制长度，但保持单词完整性
        if len(normalized_name) > 60:
            # 尝试在下划线处截断以保持单词完整性
            words = normalized_name.split('_')
            truncated = ''
            for word in words:
                new_length = len(truncated + '_' + word) if truncated else len(word)
                if new_length <= 60:
                    if truncated:
                        truncated += '_' + word
                    else:
                        truncated = word
                else:
                    break
            normalized_name = truncated if truncated else normalized_name[:60].rstrip('_')
        
        # 转换为小写
        normalized_name = normalized_name.lower()
        
        return normalized_name

    def _create_basic_structure(self, project_path: str):
        """创建基础目录结构"""
        directories = [
            "src/main/java",
            "src/main/resources",
            "src/test/java",
            "frontend/src/components",
            "frontend/src/views",
            "frontend/src/router",
            "frontend/src/utils",
            self.config.tasks_dir,
            self.config.test_project_dir,
            self.config.tech_stack_docs_dir
        ]
        
        for directory in directories:
            dir_path = os.path.join(project_path, directory)
            os.makedirs(dir_path, exist_ok=True)
            
            # 在空目录中创建.gitkeep文件
            gitkeep_file = os.path.join(dir_path, '.gitkeep')
            if not os.listdir(dir_path):
                Path(gitkeep_file).touch()
    
    def _run_git_command(self, command: List[str], cwd: str) -> str:
        """执行Git命令"""
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True,
                encoding='utf-8'
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Git命令执行失败: {' '.join(command)}")
            logger.error(f"错误输出: {e.stderr}")
            raise
    
    def _commit_changes(self, path: str, message: str):
        """提交更改"""
        self._run_git_command(["git", "add", "."], path)
        self._run_git_command(["git", "commit", "-m", message], path)
    
    def analyze_existing_structure(self, project_path: Optional[str] = None) -> Dict[str, any]:
        """
        分析现有项目结构
        
        Args:
            project_path: 项目路径，如果为None则使用配置的路径
            
        Returns:
            项目结构分析结果
        """
        if project_path is None:
            project_path = self.config_manager.get_project_path()
        
        analysis = {
            "project_exists": os.path.exists(project_path),
            "is_git_repo": False,
            "has_backend": False,
            "has_frontend": False,
            "backend_structure": {},
            "frontend_structure": {},
            "existing_files": [],
            "git_info": {}
        }
        
        if not analysis["project_exists"]:
            return analysis
        
        try:
            # 检查Git仓库信息
            if self._is_git_repository(project_path):
                analysis["is_git_repo"] = True
                analysis["git_info"] = {
                    "current_branch": self._get_current_branch(project_path),
                    "has_remote": self._has_remote_origin(project_path),
                    "uncommitted_changes": self._has_uncommitted_changes(project_path)
                }
            
            # 分析后端结构
            backend_indicators = ["pom.xml", "build.gradle", "src/main/java"]
            for indicator in backend_indicators:
                indicator_path = os.path.join(project_path, indicator)
                if os.path.exists(indicator_path):
                    analysis["has_backend"] = True
                    if indicator == "pom.xml":
                        analysis["backend_structure"]["build_tool"] = "maven"
                        analysis["backend_structure"]["config_file"] = indicator
                    elif indicator == "build.gradle":
                        analysis["backend_structure"]["build_tool"] = "gradle"
                        analysis["backend_structure"]["config_file"] = indicator
                    break
            
            # 分析前端结构
            frontend_indicators = ["package.json", "vue.config.js", "src/main.js", "frontend/package.json"]
            for indicator in frontend_indicators:
                indicator_path = os.path.join(project_path, indicator)
                if os.path.exists(indicator_path):
                    analysis["has_frontend"] = True
                    if "frontend/" in indicator:
                        analysis["frontend_structure"]["location"] = "frontend/"
                    else:
                        analysis["frontend_structure"]["location"] = "root"
                    analysis["frontend_structure"]["config_file"] = indicator
                    break
            
            # 收集现有文件信息
            for root, dirs, files in os.walk(project_path):
                # 跳过.git目录
                if '.git' in dirs:
                    dirs.remove('.git')
                
                for file in files:
                    if not file.startswith('.'):
                        rel_path = os.path.relpath(os.path.join(root, file), project_path)
                        analysis["existing_files"].append(rel_path)
            
            logger.info(f"项目结构分析完成: {project_path}")
            
        except Exception as e:
            logger.error(f"项目结构分析失败: {e}")
            analysis["error"] = str(e)
        
        return analysis
    
    def commit_and_push_code(
        self, 
        commit_message: str, 
        project_path: Optional[str] = None,
        push_to_remote: bool = True
    ) -> Dict[str, any]:
        """
        提交并推送代码
        
        Args:
            commit_message: 提交信息
            project_path: 项目路径
            push_to_remote: 是否推送到远程仓库
            
        Returns:
            操作结果
        """
        if project_path is None:
            project_path = self.config_manager.get_project_path()
        
        result = {
            "status": "success",
            "operations": [],
            "commit_id": "",
            "pushed": False
        }
        
        try:
            # 1. 检查是否有更改
            if not self._has_uncommitted_changes(project_path):
                logger.info("没有需要提交的更改")
                result["operations"].append("没有更改需要提交")
                return result
            
            # 2. 添加所有文件
            self._run_git_command(["git", "add", "."], project_path)
            result["operations"].append("添加所有更改的文件")
            
            # 3. 提交代码
            self._run_git_command(["git", "commit", "-m", commit_message], project_path)
            result["operations"].append(f"提交代码: {commit_message}")
            
            # 4. 获取提交ID
            commit_id = self._run_git_command(["git", "rev-parse", "HEAD"], project_path)
            result["commit_id"] = commit_id.strip()
            
            # 5. 推送到远程仓库（如果需要且存在远程仓库）
            if push_to_remote and self._has_remote_origin(project_path):
                try:
                    current_branch = self._get_current_branch(project_path)
                    self._run_git_command(["git", "push", "origin", current_branch], project_path)
                    result["pushed"] = True
                    result["operations"].append(f"推送到远程分支: {current_branch}")
                except subprocess.CalledProcessError as e:
                    logger.warning(f"推送失败: {e}")
                    result["operations"].append(f"推送失败: {e.stderr}")
            
            # 6. 记录推送时间
            result["timestamp"] = datetime.now().isoformat()
            
            logger.info(f"代码提交完成，提交ID: {result['commit_id'][:8]}")
            
        except Exception as e:
            logger.error(f"代码提交失败: {e}")
            result["status"] = "failed"
            result["error"] = str(e)
        
        return result
    
    def create_commit_message(self, commit_type: str, description: str) -> str:
        """
        创建规范的提交信息
        
        Args:
            commit_type: 提交类型 (feat, fix, test, docs等)
            description: 描述信息
            
        Returns:
            格式化的提交信息
        """
        prefix = self.config.git_commit_prefix.get(commit_type, commit_type)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        
        return f"[{prefix}] {description} - {timestamp}"
    
    def get_repository_status(self, project_path: Optional[str] = None) -> Dict[str, any]:
        """
        获取仓库状态
        
        Args:
            project_path: 项目路径
            
        Returns:
            仓库状态信息
        """
        if project_path is None:
            project_path = self.config_manager.get_project_path()
        
        status = {
            "is_git_repo": False,
            "current_branch": "",
            "has_uncommitted_changes": False,
            "ahead_commits": 0,
            "behind_commits": 0,
            "remote_url": "",
            "last_commit": {}
        }
        
        try:
            if not self._is_git_repository(project_path):
                return status
            
            status["is_git_repo"] = True
            status["current_branch"] = self._get_current_branch(project_path)
            status["has_uncommitted_changes"] = self._has_uncommitted_changes(project_path)
            
            # 获取远程URL
            if self._has_remote_origin(project_path):
                remote_url = self._run_git_command(["git", "remote", "get-url", "origin"], project_path)
                status["remote_url"] = remote_url.strip()
            
            # 获取最后一次提交信息
            try:
                commit_info = self._run_git_command(
                    ["git", "log", "-1", "--pretty=format:%H|%an|%ad|%s"], 
                    project_path
                )
                if commit_info:
                    parts = commit_info.split('|')
                    if len(parts) == 4:
                        status["last_commit"] = {
                            "id": parts[0][:8],
                            "author": parts[1],
                            "date": parts[2],
                            "message": parts[3]
                        }
            except subprocess.CalledProcessError:
                pass
            
            # 检查与远程的差异（如果有远程仓库）
            if status["remote_url"]:
                try:
                    # 获取远程分支信息
                    self._run_git_command(["git", "fetch", "origin"], project_path)
                    
                    # 检查本地领先多少提交
                    ahead_result = self._run_git_command(
                        ["git", "rev-list", "--count", f"origin/{status['current_branch']}..HEAD"], 
                        project_path
                    )
                    status["ahead_commits"] = int(ahead_result.strip()) if ahead_result.strip().isdigit() else 0
                    
                    # 检查本地落后多少提交
                    behind_result = self._run_git_command(
                        ["git", "rev-list", "--count", f"HEAD..origin/{status['current_branch']}"], 
                        project_path
                    )
                    status["behind_commits"] = int(behind_result.strip()) if behind_result.strip().isdigit() else 0
                    
                except subprocess.CalledProcessError:
                    # 远程分支可能不存在
                    pass
            
        except Exception as e:
            logger.error(f"获取仓库状态失败: {e}")
            status["error"] = str(e)
        
        return status 