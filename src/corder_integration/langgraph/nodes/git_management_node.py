#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git管理节点 - 多仓库协调和分支管理
"""

import os
import json
import logging
import subprocess
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

async def git_management_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Git管理节点 - 环境准备和仓库管理
    """
    
    logger.info(f"开始执行Git管理: {state['project_name']}")
    
    try:
        # 🔍 从设计文档提取Git信息
        git_info = extract_git_info_from_design_doc(state["design_doc"])
        
        # 📁 设置工作目录 - 解决中文编码问题
        import urllib.parse
        import hashlib
        
        # 生成安全的目录名：使用项目名称的哈希值
        project_hash = hashlib.md5(state['project_name'].encode('utf-8')).hexdigest()[:8]
        safe_project_name = f"project_{project_hash}"
        workspace_path = f"./workspace/{safe_project_name}"
        
        logger.info(f"项目名称: {state['project_name']} -> 安全目录名: {safe_project_name}")
        os.makedirs(workspace_path, exist_ok=True)
        
        # 🌐 设置Git仓库
        if git_info.get("repo_url"):
            # 现有仓库：克隆并切换分支
            logger.info(f"克隆现有仓库: {git_info['repo_url']}")
            
            if not os.path.exists(os.path.join(workspace_path, ".git")):
                # 克隆仓库 - 带SSL错误处理
                success = False
                last_error = None
                
                # 尝试多种克隆方式
                clone_attempts = [
                    # 1. 正常克隆
                    ["git", "clone", git_info["repo_url"], workspace_path],
                    # 2. 禁用SSL验证（仅用于企业内部环境）
                    ["git", "-c", "http.sslVerify=false", "clone", git_info["repo_url"], workspace_path],
                    # 3. 使用不同的HTTP版本
                    ["git", "-c", "http.version=HTTP/1.1", "clone", git_info["repo_url"], workspace_path]
                ]
                
                for i, cmd in enumerate(clone_attempts, 1):
                    logger.info(f"克隆尝试 {i}/3: {' '.join(cmd[:3])}...")
                    result = subprocess.run(cmd, capture_output=True, text=True)
                
                    if result.returncode == 0:
                        success = True
                        logger.info(f"克隆成功 (尝试 {i})")
                        break
                    else:
                        last_error = result.stderr
                        logger.warning(f"克隆尝试 {i} 失败: {result.stderr[:200]}...")
                
                if not success:
                    logger.error(f"所有克隆尝试都失败，最后错误: {last_error}")
                    raise Exception(f"克隆仓库 失败: {last_error}")
            
            # 切换到工作目录
            abs_workspace_path = os.path.abspath(workspace_path)
            logger.info(f"切换到工作目录: {abs_workspace_path}")
            os.chdir(abs_workspace_path)
            
            # 创建并切换到目标分支
            try:
                # 尝试创建新分支
                subprocess.run([
                    "git", "checkout", "-b", state["target_branch"]
                ], check=True, capture_output=True, text=True)
                logger.info(f"创建新分支: {state['target_branch']}")
            except subprocess.CalledProcessError:
                # 如果分支已存在，直接切换
                subprocess.run([
                    "git", "checkout", state["target_branch"]
                ], check=True, capture_output=True, text=True)
                logger.info(f"切换到分支: {state['target_branch']}")
            
        else:   
            # 新仓库：初始化
            logger.info("初始化新的Git仓库")
            abs_workspace_path = os.path.abspath(workspace_path)
            logger.info(f"切换到工作目录: {abs_workspace_path}")
            os.chdir(abs_workspace_path)
            
            subprocess.run(["git", "init"], check=True, capture_output=True, text=True)
            subprocess.run([
                "git", "checkout", "-b", state["target_branch"]
            ], check=True, capture_output=True, text=True)
        
        # 📁 为每个微服务创建项目目录
        project_paths = {}
        abs_workspace_path = os.path.abspath(workspace_path)
        
        for service_name in state["identified_services"]:
            service_path = os.path.join(abs_workspace_path, service_name)
            os.makedirs(service_path, exist_ok=True)
            project_paths[service_name] = service_path
            logger.debug(f"创建服务目录: {service_path}")
        
        # 🔄 更新状态
        state["git_repo_url"] = git_info.get("repo_url")
        state["project_paths"] = project_paths
        state["repo_initialized"] = True
        state["current_phase"] = "intelligent_coding"
        
        logger.info(f"Git管理完成，工作目录: {workspace_path}")
        
        return state
        
    except Exception as e:
        logger.error(f"Git管理失败: {str(e)}")
        state["execution_errors"].append(f"Git管理失败: {str(e)}")
        state["repo_initialized"] = False
        state["retry_count"] += 1
        return state

def extract_git_info_from_design_doc(design_doc: str) -> Dict[str, Any]:
    """从设计文档中提取Git信息 - 增强版本"""
    
    git_info = {}
    
    # 简单的文本匹配来提取Git仓库URL
    import re
    
    # 定义多种Git URL模式
    git_patterns = [
        # GitHub HTTPS
        r'https://github\.com/[\w\-\.]+/[\w\-\.]+(?:\.git)?',
        # GitLab HTTPS (包括自建GitLab)
        r'https://gitlab\.(?:com|local|[\w\-\.]+)/[\w\-\.]+/[\w\-\.]+(?:\.git)?',
        # GitLab SSH
        r'git@gitlab\.(?:com|local|[\w\-\.]+):[\w\-\.]+/[\w\-\.]+(?:\.git)?',
        # GitHub SSH
        r'git@github\.com:[\w\-\.]+/[\w\-\.]+(?:\.git)?',
        # 通用Git HTTPS
        r'https://[\w\-\.]+/[\w\-\.]+/[\w\-\.]+(?:\.git)?',
        # 通用Git SSH
        r'git@[\w\-\.]+:[\w\-\.]+/[\w\-\.]+(?:\.git)?'
    ]
    
    # 按优先级匹配
    for pattern in git_patterns:
        matches = re.findall(pattern, design_doc, re.IGNORECASE)
        if matches:
            # 取第一个匹配的URL
            git_url = matches[0]
            # 确保以.git结尾
            if not git_url.endswith('.git'):
                git_url += '.git'
            git_info["repo_url"] = git_url
            break
    
    logger.info(f"提取到Git信息: {git_info}")
    
    return git_info 