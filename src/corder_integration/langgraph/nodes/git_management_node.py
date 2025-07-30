#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git管理节点 - 支持从数据库领取和执行任务
"""

import asyncio
import logging
import os
import re
import subprocess
from typing import Dict, Any, List
from pathlib import Path
import json

# 导入任务管理工具
from ..task_manager import NodeTaskManager

logger = logging.getLogger(__name__)

class GitManagerAgent:
    """Git管理智能体 - 纯粹基于SQLite任务的工作模式"""
    
    def __init__(self):
        self.task_manager = NodeTaskManager()
        self.node_name = "git_management_node"
        self.supported_task_types = ["git_extraction", "git_clone"]
        # 🆕 统一的分支名称，在初始化时生成一次
        self._branch_name = None
    
    def _generate_unified_branch_name(self, project_name: str) -> str:
        """统一生成分支名称，确保整个生命周期使用相同的分支名"""
        if self._branch_name is None:
            from datetime import datetime
            import re
            
            # 生成日期时间格式：YYYYMMDDHHMM
            current_time = datetime.now().strftime("%Y%m%d%H%M")
            
            # 清理项目名称，只保留中文和英文字符
            clean_project_name = re.sub(r'[^\u4e00-\u9fa5a-zA-Z]', '', project_name)
            
            self._branch_name = f"D_{current_time}_{clean_project_name}"
            logger.info(f"🌿 生成统一分支名称: {self._branch_name}")
        
        return self._branch_name
    
    def extract_git_urls_from_text(self, text: str) -> List[Dict[str, str]]:
        """从文本中提取Git URL - 支持多种格式"""
        logger.info("🔍 开始从文本提取Git URL...")
        
        # Git URL 模式匹配 - 支持更多格式
        git_patterns = [
            r'https://github\.com/[\w\-\./]+\.git',
            r'git@github\.com:[\w\-\./]+\.git',
            r'https://gitlab\.com/[\w\-\./]+\.git',
            r'git@gitlab\.com:[\w\-\./]+\.git',
            # 🔧 支持本地GitLab实例
            r'https://gitlab\.local/[\w\-\./]+\.git',
            r'http://gitlab\.local/[\w\-\./]+\.git',
            r'git@gitlab\.local:[\w\-\./]+\.git',
            # 🔧 通用Git URL模式
            r'https?://[\w\-\.]+(?::\d+)?/[\w\-\./]+\.git',
            r'git@[\w\-\.]+:[\w\-\./]+\.git',
        ]
        
        extracted_repos = []
        
        for pattern in git_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                repo_name = match.split('/')[-1].replace('.git', '')
                # 避免重复添加相同的仓库
                if not any(repo['url'] == match for repo in extracted_repos):
                    extracted_repos.append({
                        'name': repo_name,
                        'url': match,
                        'type': 'git_repository'
                    })
                    logger.info(f"🔗 找到Git仓库: {match}")
        
        logger.info(f"✅ 提取到 {len(extracted_repos)} 个Git仓库")
        return extracted_repos
    
    def clone_repository(self, repo_url: str, target_dir: str, branch: str = "master") -> Dict[str, Any]:
        """克隆Git仓库到指定目录"""
        logger.info(f"📥 开始克隆仓库: {repo_url} -> {target_dir}")
        
        try:
            # 🆕 检查目标目录是否已存在
            if os.path.exists(target_dir):
                logger.warning(f"⚠️ 目标目录已存在，将清理后重新克隆: {target_dir}")
                import shutil
                try:
                    shutil.rmtree(target_dir)
                    logger.info(f"✅ 已清理旧目录: {target_dir}")
                except Exception as e:
                    logger.error(f"❌ 清理目录失败: {e}")
                    return {
                        'success': False,
                        'message': f'清理目录失败: {str(e)}'
                    }
            
            # 确保父目录存在
            Path(target_dir).parent.mkdir(parents=True, exist_ok=True)
            
            # 🔧 修复编码问题：指定UTF-8编码和错误处理
            clone_result = subprocess.run(
                ["git", "clone", repo_url, target_dir],
                capture_output=True,
                text=True,
                encoding='utf-8',  # 指定UTF-8编码
                errors='replace',  # 遇到无法解码的字符时替换为占位符
                timeout=300
            )
            
            if clone_result.returncode != 0:
                error_msg = clone_result.stderr or clone_result.stdout or "未知错误"
                logger.error(f"❌ 仓库克隆失败: {error_msg}")
                return {
                    'success': False,
                    'message': f'仓库克隆失败: {error_msg}',
                    'stderr': error_msg
                }
            
            # 创建新分支或切换到指定分支
            if os.path.exists(target_dir):
                original_cwd = os.getcwd()
                os.chdir(target_dir)
                
                try:
                    # 🆕 如果分支名包含 "D_" 前缀，说明是新分支，需要创建
                    if branch.startswith("D_"):
                        # 创建并切换到新分支
                        branch_result = subprocess.run(
                            ["git", "checkout", "-b", branch],
                            capture_output=True,
                            text=True,
                            encoding='utf-8',
                            errors='replace'
                        )
                        
                        if branch_result.returncode == 0:
                            logger.info(f"✅ 已创建并切换到新分支: {branch}")
                        else:
                            logger.warning(f"⚠️ 新分支创建失败，保持master分支: {branch_result.stderr}")
                    else:
                        # 🔧 切换到现有分支
                        branch_result = subprocess.run(
                            ["git", "checkout", branch],
                            capture_output=True,
                            text=True,
                            encoding='utf-8',
                            errors='replace'
                        )
                        
                        if branch_result.returncode == 0:
                            logger.info(f"✅ 已切换到分支: {branch}")
                        else:
                            logger.warning(f"⚠️ 分支切换失败，保持当前分支: {branch_result.stderr}")
                
                finally:
                    # 返回到原目录
                    os.chdir(original_cwd)
            
            logger.info(f"✅ 仓库克隆成功: {target_dir}")
            return {
                'success': True,
                'message': f'仓库克隆成功: {target_dir}',
                'local_path': target_dir,
                'repo_url': repo_url
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"❌ 仓库克隆超时: {repo_url}")
            return {
                'success': False,
                'message': '仓库克隆超时（300秒）'
            }
        except Exception as e:
            logger.error(f"❌ 仓库克隆异常: {e}")
            return {
                'success': False,
                'message': f'仓库克隆异常: {str(e)}'
            }
    
    def execute_task_from_database(self, project_task_id: str = None) -> List[Dict[str, Any]]:
        """从数据库领取并执行Git管理任务"""
        logger.info(f"🎯 {self.node_name} 开始执行任务...")
        if project_task_id:
            logger.info(f"🏷️ 过滤项目任务标识: {project_task_id}")
        
        execution_results = []
        
        # 🔧 修复：获取可执行的任务时传递项目标识
        available_tasks = self.task_manager.get_node_tasks(self.supported_task_types, project_task_id)
        
        if not available_tasks:
            logger.info("ℹ️ 没有可执行的Git管理任务")
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
                if task_type == "git_extraction":
                    result = self._execute_git_extraction_task(task)
                elif task_type == "git_clone":
                    result = self._execute_git_clone_task(task)
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
        
        logger.info(f"✅ Git管理任务执行完成，共处理 {len(execution_results)} 个任务")
        return execution_results
    
    def _execute_git_extraction_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行Git提取任务 - 从implementation_detail字段提取Git URL"""
        logger.info(f"🔍 执行Git提取任务: {task['task_id']}")
        
        # 🔧 从任务的implementation_detail字段获取Git URL信息
        implementation_detail = task.get('implementation_details', '')
        description = task.get('description', '')
        
        # 合并多个文本源进行URL提取
        text_sources = [implementation_detail, description]
        extracted_text = ' '.join(filter(None, text_sources))
        
        logger.info(f"📄 提取源文本: {extracted_text[:200]}...")
        
        if not extracted_text.strip():
            return {'success': False, 'message': '任务中没有可提取的Git URL信息'}
        
        # 提取Git URL
        extracted_repos = self.extract_git_urls_from_text(extracted_text)
        
        if not extracted_repos:
            logger.warning("⚠️ 未从任务中提取到任何Git仓库URL")
            return {
                'success': False, 
                'message': '未从任务中提取到Git仓库URL',
                'extracted_text': extracted_text[:500]  # 用于调试
            }
        
        return {
            'success': True,
            'message': f'成功提取 {len(extracted_repos)} 个Git仓库',
            'extracted_repositories': extracted_repos,
            'extraction_count': len(extracted_repos)
        }
    
    def _execute_git_clone_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行Git克隆任务"""
        logger.info(f"📥 执行Git克隆任务: {task['task_id']}")
        
        # 获取任务参数
        parameters = task.get('parameters', {})
        repo_url = parameters.get('repo_url', '')
        
        # 🔧 如果任务参数中没有repo_url，尝试从git_extraction任务结果中获取
        if not repo_url:
            logger.info("🔍 任务参数中无repo_url，尝试从git_extraction任务结果获取...")
            # ⭐️ 关键修复：传入当前项目的project_task_id
            project_task_id = task.get('project_task_id')
            extraction_results = self._get_git_extraction_results(project_task_id)
            
            if extraction_results:
                # 根据任务描述或ID匹配对应的仓库
                repo_info = self._match_repo_from_extraction(task, extraction_results)
                if repo_info:
                    repo_url = repo_info['url']
                    logger.info(f"✅ 从git_extraction结果获取到仓库地址: {repo_url}")
                else:
                    logger.warning(f"⚠️ 无法从git_extraction结果中匹配到仓库: {task.get('description', 'N/A')}")
            
            if not repo_url:
                return {
                    'success': False,
                    'message': 'repo_url参数缺失且无法从git_extraction结果中获取'
                }
        
        # 从任务中提取Git URL（备用方案）
        if not repo_url:
            task_text = f"{task.get('description', '')} {task.get('implementation_details', '')}"
            extracted_repos = self.extract_git_urls_from_text(task_text)
            
            if extracted_repos:
                repo_url = extracted_repos[0]['url']
                logger.info(f"✅ 从任务详情提取到仓库地址: {repo_url}")
            else:
                return {
                    'success': False,
                    'message': 'repo_url参数缺失且无法从任务详情中提取'
                }
        
        # 确定本地目标目录
        target_dir = parameters.get('target_dir', '')
        if not target_dir:
            # 自动生成目标目录
            repo_name = repo_url.split('/')[-1].replace('.git', '')
            output_path = parameters.get('output_path', '/Users/renyu/Documents/create_project')
            project_name = parameters.get('project_name', 'default_project')
            target_dir = f"{output_path}/{project_name}/{repo_name}"
        
        # 🆕 使用统一的分支名称生成方法 - 优先使用已获取的project_name
        new_branch = self._generate_unified_branch_name(project_name)
        
        # 执行克隆并创建新分支
        clone_result = self.clone_repository(repo_url, target_dir, new_branch)
        
        if clone_result['success']:
            # 🔧 修复路径映射：实际的项目根目录就是target_dir，不需要再加repo_name
            actual_project_path = target_dir
            return {
                'success': True,
                'message': f'仓库克隆成功: {actual_project_path}',
                'repo_url': repo_url,
                'local_path': actual_project_path,
                'repo_name': repo_url.split('/')[-1].replace('.git', '')
            }
        else:
            return {
                'success': False,
                'message': f'仓库克隆失败: {clone_result["message"]}'
            }
    
    def _get_git_extraction_results(self, project_task_id: str) -> List[Dict[str, Any]]:
        """获取指定项目已完成的git_extraction任务结果"""
        if not project_task_id:
            logger.warning("⚠️ project_task_id未提供，无法获取git_extraction结果")
            return []
            
        try:
            conn = self.task_manager._get_connection()
            cursor = conn.cursor()
            
            # ⭐️ 关键修复：按 project_task_id 过滤
            cursor.execute("""
                SELECT task_id, parameters 
                FROM execution_tasks 
                WHERE task_type = 'git_extraction' 
                AND status = 'completed'
                AND project_task_id = ?
                AND parameters IS NOT NULL
            """, (project_task_id,))
            
            extraction_tasks = cursor.fetchall()
            conn.close()
            
            extracted_repos = []
            for task_id, params_json in extraction_tasks:
                try:
                    # 结果现在存储在parameters字段中
                    params = json.loads(params_json)
                    if params.get('success') and 'extracted_repositories' in params:
                        extracted_repos.extend(params['extracted_repositories'])
                        logger.info(f"📋 从任务 {task_id} 的parameters中获取到 {len(params['extracted_repositories'])} 个仓库")
                except json.JSONDecodeError:
                    logger.warning(f"⚠️ 无法解析任务 {task_id} 的parameters字段")
            
            return extracted_repos
            
        except Exception as e:
            logger.error(f"❌ 获取git_extraction结果失败: {e}")
            return []
    
    def _match_repo_from_extraction(self, clone_task: Dict[str, Any], extracted_repos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """从提取结果中匹配对应的仓库"""
        task_desc = clone_task.get('description', '').lower()
        task_details = clone_task.get('implementation_details', '').lower()
        task_text = f"{task_desc} {task_details}"
        
        # 尝试通过关键词匹配
        for repo in extracted_repos:
            repo_name = repo.get('name', '').lower()
            repo_url = repo.get('url', '').lower()
            
            # 检查任务描述中是否包含仓库名称的关键词
            if repo_name in task_text or any(part in task_text for part in repo_name.split('-')):
                logger.info(f"✅ 通过名称匹配找到仓库: {repo['name']}")
                return repo
                
            # 检查URL匹配
            if repo_url in task_text:
                logger.info(f"✅ 通过URL匹配找到仓库: {repo['url']}")
                return repo
        
        # 如果只有一个仓库，直接返回
        if len(extracted_repos) == 1:
            logger.info(f"✅ 只有一个提取的仓库，直接使用: {extracted_repos[0]['name']}")
            return extracted_repos[0]
        
        # 如果有多个仓库，按索引分配（简单策略）
        task_id = clone_task.get('task_id', '')
        if task_id.endswith('_002') and len(extracted_repos) >= 1:
            return extracted_repos[0]
        elif task_id.endswith('_003') and len(extracted_repos) >= 2:
            return extracted_repos[1]
        
        logger.warning(f"⚠️ 无法匹配仓库，任务: {task_desc}")
        return None


async def git_management_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Git管理节点 - 纯粹基于SQLite任务的工作模式"""
    logger.info("🚀 Git管理节点开始执行...")
    
    try:
        git_agent = GitManagerAgent()
        
        # 🔧 纯粹从SQLite执行任务，不依赖状态传递
        task_results = git_agent.execute_task_from_database()
        
        # 分析执行结果
        successful_extractions = []
        successful_clones = []
        
        for result in task_results:
            if result['task_type'] == 'git_extraction' and result['result'].get('success'):
                extracted_repos = result['result'].get('extracted_repositories', [])
                successful_extractions.extend(extracted_repos)
            elif result['task_type'] == 'git_clone' and result['result'].get('success'):
                successful_clones.append(result['result'])
        
        # 🔧 如果有成功的提取任务，自动生成克隆任务
        auto_cloned_repos = []
        if successful_extractions:
            logger.info(f"🚀 基于提取结果自动克隆 {len(successful_extractions)} 个仓库...")
            
            # 从状态获取输出路径和项目名称
            output_path = state.get('output_path', '/Users/renyu/Documents/create_project')
            project_name = state.get('project_name', 'unknown_project')
            
            # 获取未完成的git_clone任务，准备标记为完成
            pending_clone_tasks = git_agent.task_manager.get_node_tasks(['git_clone'])
            
            for i, repo in enumerate(successful_extractions):
                repo_url = repo['url']
                repo_name = repo['name']
                target_dir = f"{output_path}/{project_name}/{repo_name}"
                
                # 🆕 使用统一的分支名称生成方法
                new_branch = git_agent._generate_unified_branch_name(project_name)
                
                logger.info(f"📥 自动克隆仓库: {repo_url} -> {target_dir}")
                clone_result = git_agent.clone_repository(repo_url, target_dir, new_branch)
                
                if clone_result['success']:
                    auto_cloned_repos.append({
                        'repo_name': repo_name,
                        'repo_url': repo_url,
                        'local_path': target_dir,
                        'status': 'auto_cloned'
                    })
                    logger.info(f"✅ 自动克隆成功: {repo_name}")
                    
                    # 🔧 自动标记对应的数据库任务为完成
                    if i < len(pending_clone_tasks):
                        task = pending_clone_tasks[i]
                        task_id = task['task_id']
                        
                        # 标记任务为完成
                        result_data = {
                            'success': True,
                            'message': f'通过自动克隆完成: {target_dir}',
                            'repo_url': repo_url,
                            'local_path': target_dir,
                            'repo_name': repo_name,
                            'completion_method': 'auto_clone'
                        }
                        
                        # 更新任务状态为completed，结果存储在parameters中
                        conn = git_agent.task_manager._get_connection()
                        cursor = conn.cursor()
                        cursor.execute('''
                            UPDATE execution_tasks 
                            SET status = 'completed', 
                                parameters = ?,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE task_id = ?
                        ''', (json.dumps(result_data), task_id))
                        conn.close()
                        logger.info(f"✅ 已标记任务 {task_id} 为完成状态")
                else:
                    logger.error(f"❌ 自动克隆失败: {repo_name} - {clone_result['message']}")
        
        # 合并所有克隆的仓库
        all_cloned_repos = auto_cloned_repos + [
            {
                'repo_name': result['result']['repo_url'].split('/')[-1].replace('.git', ''),
                'repo_url': result['result']['repo_url'],
                'local_path': result['result']['local_path'],
                'status': 'task_cloned'
            }
            for result in task_results 
            if result['task_type'] == 'git_clone' and result['result'].get('success')
        ]
        
        # 🔧 构建项目路径映射
        project_paths = {}
        for repo in all_cloned_repos:
            service_name = repo['repo_name'].replace('-', '_')
            project_paths[service_name] = repo['local_path']
        
        # 🔧 更新状态
        updated_state = {
            'git_operations': task_results,
            'git_extraction_completed': True,
            'repo_initialized': len(all_cloned_repos) > 0,  # 🔧 基于实际克隆结果
            'cloned_repositories': all_cloned_repos,
            'project_paths': project_paths,
            'git_summary': {
                'extracted_repos': len(successful_extractions),
                'cloned_repos': len(all_cloned_repos),
                'database_tasks_processed': len(task_results)
            }
        }
        
        logger.info(f"✅ Git管理节点完成 - 提取: {len(successful_extractions)} 个仓库, "
                   f"克隆: {len(all_cloned_repos)} 个仓库, "
                   f"仓库初始化状态: {updated_state['repo_initialized']}")
        
        return updated_state
        
    except Exception as e:
        logger.error(f"❌ Git管理节点执行失败: {e}")
        return {
            'git_operations': [],
            'repo_initialized': False,  # 🔧 失败时标记为未初始化
            'error': f'Git管理节点执行失败: {str(e)}',
            'git_summary': {
                'extracted_repos': 0,
                'cloned_repos': 0,
                'database_tasks_processed': 0
            }
        } 