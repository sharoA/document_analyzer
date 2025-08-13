#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git提交节点 - 支持从数据库领取和执行任务
"""

import asyncio
import logging
import json
import os
import subprocess
from typing import Dict, Any, List
from pathlib import Path
import yaml

# 导入任务管理工具
from ..task_manager import NodeTaskManager

logger = logging.getLogger(__name__)

class GitCommitAgent:
    """Git提交智能体 - 支持任务领取和状态更新"""
    
    def __init__(self):
        self.task_manager = NodeTaskManager()
        self.node_name = "git_commit_node"
        self.supported_task_types = ["deployment"]
    
    def execute_task_from_database(self, project_task_id: str = None) -> List[Dict[str, Any]]:
        """从数据库领取并执行Git提交任务"""
        logger.info(f"🎯 {self.node_name} 开始执行任务...")
        if project_task_id:
            logger.info(f"🏷️ 过滤项目任务标识: {project_task_id}")
        
        execution_results = []
        
        # 🔧 修复：获取可执行的任务时传递项目标识
        available_tasks = self.task_manager.get_node_tasks(self.supported_task_types, project_task_id)
        
        if not available_tasks:
            logger.info("ℹ️ 没有可执行的Git提交任务")
            return []
        
        logger.info(f"📋 找到 {len(available_tasks)} 个可执行任务")
        
        for task in available_tasks:
            task_id = task['task_id']
            task_type = task['task_type']
            
            logger.info(f"🚀 开始执行任务: {task_id} ({task_type})")
            
            # 领取任务
            if not self.task_manager.claim_task(task_id, self.node_name):
                logger.warning(f"⚠️ 任务 {task_id} 领取失败，跳过")
                continue
            
            try:
                # 执行任务
                if task_type == "deployment":
                    result = self._execute_deployment_task(task)
                else:
                    logger.warning(f"⚠️ 未支持的任务类型: {task_type}")
                    result = {'success': False, 'message': f'未支持的任务类型: {task_type}'}
                
                # 更新任务状态
                if result.get('success'):
                    self.task_manager.update_task_status(task_id, 'completed', result)
                    logger.info(f"✅ 任务 {task_id} 执行成功")
                else:
                    self.task_manager.update_task_status(task_id, 'failed', result)
                    logger.error(f"❌ 任务 {task_id} 执行失败: {result.get('message')}")
                
                execution_results.append({
                    'task_id': task_id,
                    'task_type': task_type,
                    'result': result
                })
                
            except Exception as e:
                logger.error(f"❌ 任务 {task_id} 执行异常: {e}")
                error_result = {'success': False, 'message': f'执行异常: {str(e)}'}
                self.task_manager.update_task_status(task_id, 'failed', error_result)
                
                execution_results.append({
                    'task_id': task_id,
                    'task_type': task_type,
                    'result': error_result
                })
        
        logger.info(f"✅ Git提交任务执行完成，共处理 {len(execution_results)} 个任务")
        return execution_results
    
    def _execute_deployment_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行部署任务"""
        logger.info(f"🚀 执行部署任务: {task['task_id']}")
        
        # 获取任务参数
        parameters = task.get('parameters', {})
        service_name = task.get('service_name', 'unknown_service')
        
        # 🔧 修复：执行真正的Git提交而不是模拟
        git_commit_result = self._execute_real_git_commit(task, parameters)
        
        return {
            'success': git_commit_result.get('success', False),
            'message': f'{service_name}服务Git提交' + ('成功' if git_commit_result.get('success') else '失败'),
            'git_commit_result': git_commit_result,
            'service_name': service_name
        }
    
    def _execute_real_git_commit(self, task: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行真正的Git提交操作"""
        service_name = task.get('service_name', 'unknown_service')
        logger.info(f"📝 执行{service_name}服务的真实Git提交流程")
        
        # 从参数中获取仓库信息
        repositories = parameters.get('repositories', [])
        if not repositories:
            logger.warning("⚠️ 未找到仓库信息，无法执行Git提交")
            return {
                'success': False,
                'error': '未找到仓库信息',
                'commit_status': 'failed'
            }
        
        git_results = []
        overall_success = True
        
        for repo_info in repositories:
            if isinstance(repo_info, dict):
                repo_path = repo_info.get('path', '')
                changes_desc = repo_info.get('changes', f'新增{service_name}相关功能')
            else:
                # 向后兼容：如果是字符串，直接作为路径
                repo_path = str(repo_info)
                changes_desc = f'新增{service_name}相关功能'
            
            if not repo_path or not os.path.exists(repo_path):
                logger.warning(f"⚠️ 仓库路径不存在: {repo_path}")
                git_results.append({
                    'repo_path': repo_path,
                    'success': False,
                    'error': '仓库路径不存在'
                })
                overall_success = False
                continue
            
            # 执行真正的Git操作
            repo_result = self._execute_git_operations(repo_path, changes_desc, service_name)
            git_results.append(repo_result)
            
            if not repo_result.get('success'):
                overall_success = False
        
        return {
            'success': overall_success,
            'commit_status': 'success' if overall_success else 'failed',
            'git_results': git_results,
            'total_repositories': len(repositories)
        }
    
    def _execute_git_operations(self, repo_path: str, changes_desc: str, service_name: str) -> Dict[str, Any]:
        """在指定仓库中执行Git操作"""
        logger.info(f"🔧 在仓库 {repo_path} 中执行Git操作")
        
        try:
            # 切换到仓库目录
            original_cwd = os.getcwd()
            os.chdir(repo_path)
            
            # 检查是否是Git仓库
            if not os.path.exists('.git'):
                logger.error(f"❌ {repo_path} 不是一个Git仓库")
                return {
                    'repo_path': repo_path,
                    'success': False,
                    'error': '不是Git仓库'
                }
            
            git_operations = []
            
            # 1. git add .
            logger.info("📁 执行 git add .")
            add_result = subprocess.run(['git', 'add', '.'], 
                                      capture_output=True, text=True, cwd=repo_path)
            git_operations.append({
                'operation': 'git add .',
                'success': add_result.returncode == 0,
                'stdout': add_result.stdout,
                'stderr': add_result.stderr
            })
            
            if add_result.returncode != 0:
                logger.error(f"❌ git add 失败: {add_result.stderr}")
                return {
                    'repo_path': repo_path,
                    'success': False,
                    'error': f'git add 失败: {add_result.stderr}',
                    'operations': git_operations
                }
            
            # 2. 检查是否有更改
            status_result = subprocess.run(['git', 'status', '--porcelain'], 
                                         capture_output=True, text=True, cwd=repo_path)
            
            if not status_result.stdout.strip():
                logger.info("ℹ️ 没有检测到文件更改，跳过提交")
                return {
                    'repo_path': repo_path,
                    'success': True,
                    'message': '没有文件更改，跳过提交',
                    'operations': git_operations
                }
            
            # 3. git commit
            commit_message = f"feat: {changes_desc}\n\n🤖 已经按设计文档生成对应初始代码\n\nCo-Authored-By: coder <coder@yljr.com>"
            
            logger.info(f"💾 执行 git commit")
            commit_result = subprocess.run(['git', 'commit', '-m', commit_message], 
                                         capture_output=True, text=True, cwd=repo_path)
            git_operations.append({
                'operation': 'git commit',
                'success': commit_result.returncode == 0,
                'stdout': commit_result.stdout,
                'stderr': commit_result.stderr,
                'commit_message': commit_message
            })
            
            if commit_result.returncode != 0:
                logger.error(f"❌ git commit 失败: {commit_result.stderr}")
                return {
                    'repo_path': repo_path,
                    'success': False,
                    'error': f'git commit 失败: {commit_result.stderr}',
                    'operations': git_operations
                }
            
            # 提取commit hash
            commit_hash = None
            if 'commit' in commit_result.stdout.lower():
                import re
                hash_match = re.search(r'commit ([a-f0-9]+)', commit_result.stdout)
                if hash_match:
                    commit_hash = hash_match.group(1)
            
            # 4. git push - 智能处理上游分支设置
            logger.info("🚀 执行 git push")
            
            # 首先尝试普通的git push
            push_result = subprocess.run(['git', 'push'], 
                                       capture_output=True, text=True, cwd=repo_path)
            
            # 如果失败且错误信息包含"no upstream branch"，则设置上游分支
            if push_result.returncode != 0 and "no upstream branch" in push_result.stderr:
                logger.info("🔧 检测到新分支，设置上游分支并推送")
                
                # 获取当前分支名
                branch_result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
                                             capture_output=True, text=True, cwd=repo_path)
                
                if branch_result.returncode == 0:
                    current_branch = branch_result.stdout.strip()
                    logger.info(f"📋 当前分支: {current_branch}")
                    
                    # 使用 --set-upstream 推送
                    push_upstream_result = subprocess.run(
                        ['git', 'push', '--set-upstream', 'origin', current_branch], 
                        capture_output=True, text=True, cwd=repo_path
                    )
                    
                    git_operations.append({
                        'operation': f'git push --set-upstream origin {current_branch}',
                        'success': push_upstream_result.returncode == 0,
                        'stdout': push_upstream_result.stdout,
                        'stderr': push_upstream_result.stderr
                    })
                    
                    push_success = push_upstream_result.returncode == 0
                    if push_success:
                        logger.info("✅ 上游分支设置成功，git push 完成")
                    else:
                        logger.error(f"❌ 设置上游分支后 git push 仍然失败: {push_upstream_result.stderr}")
                else:
                    logger.error(f"❌ 获取当前分支名失败: {branch_result.stderr}")
                    push_success = False
            else:
                # 记录普通push的结果
                git_operations.append({
                    'operation': 'git push',
                    'success': push_result.returncode == 0,
                    'stdout': push_result.stdout,
                    'stderr': push_result.stderr
                })
                
                push_success = push_result.returncode == 0
                if push_success:
                    logger.info("✅ git push 成功")
                else:
                    logger.error(f"❌ git push 失败: {push_result.stderr}")
            
            # 如果push仍然失败，但commit成功了，记录这种情况
            if not push_success:
                logger.warning("⚠️ git push 失败，但commit可能已经成功")
            
            return {
                'repo_path': repo_path,
                'success': push_success,  # 只有push成功才算完全成功
                'commit_hash': commit_hash,
                'operations': git_operations,
                'message': 'Git操作完成' if push_success else 'Commit成功但Push失败'
            }
            
        except Exception as e:
            logger.error(f"❌ Git操作执行异常: {e}")
            return {
                'repo_path': repo_path,
                'success': False,
                'error': f'Git操作异常: {str(e)}'
            }
        finally:
            # 恢复原始工作目录
            try:
                os.chdir(original_cwd)
            except Exception as e:
                logger.warning(f"⚠️ 恢复工作目录失败: {e}")

async def git_commit_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Git提交节点 - 支持任务驱动的Git操作和部署"""
    logger.info("🚀 Git提交节点开始执行...")
    
    try:
        commit_agent = GitCommitAgent()
        
        # 🆕 获取项目任务标识
        project_task_id = state.get('project_task_id')
        if project_task_id:
            logger.info(f"🏷️ Git提交节点获取项目标识: {project_task_id}")
        
        # 🔧 修复：执行数据库中的任务时传递项目标识
        task_results = commit_agent.execute_task_from_database(project_task_id)
        
        # 将任务执行结果添加到状态中
        commit_operations = state.get('commit_operations', [])
        commit_operations.extend(task_results)
        
        # 处理传统的Git提交（向后兼容）
        tested_services = state.get('tested_services', [])
        if tested_services and not any(r['task_type'] == 'deployment' for r in task_results):
            logger.info("🔍 执行传统Git提交流程（向后兼容）")
            for service_name in tested_services:
                # 模拟传统的Git提交
                commit_operations.append({
                    'task_type': 'legacy_commit',
                    'result': {
                        'success': True,
                        'service_name': service_name,
                        'commit_hash': f'legacy_commit_{service_name}',
                        'deployed': True
                    }
                })
        
        # 更新状态
        updated_state = {
            'commit_operations': commit_operations,
            'git_commit_completed': True
        }
        
        # 收集部署结果
        deployed_services = []
        all_deployments_successful = True
        
        for op in commit_operations:
            result = op.get('result', {})
            if result.get('service_name'):
                service_name = result['service_name']
                if service_name not in deployed_services:
                    deployed_services.append(service_name)
                
                # 检查部署是否成功
                deployment_success = result.get('success', True)
                if not deployment_success:
                    all_deployments_successful = False
        
        if deployed_services:
            updated_state['deployed_services'] = deployed_services
            updated_state['all_deployments_successful'] = all_deployments_successful
        
        # 如果所有部署都成功，标记工作流完成
        if all_deployments_successful and deployed_services:
            updated_state['workflow_completed'] = True
            updated_state['final_status'] = 'success'
        
        logger.info(f"✅ Git提交节点完成，处理了 {len(task_results)} 个任务")
        return updated_state
        
    except Exception as e:
        logger.error(f"❌ Git提交节点执行失败: {e}")
        return {
            'commit_operations': state.get('commit_operations', []),
            'error': f'Git提交节点执行失败: {str(e)}'
        }