#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能文档分析API接口
基于Redis存储和HTTP轮询的分析系统
"""

import json
import time
import uuid
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

# 导入配置和服务
from ..resource.config import get_config
from ..utils.volcengine_client import VolcengineClient, VolcengineConfig
from ..analysis_services import AnalysisServiceManager
from ..utils.redis_util import get_redis_manager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DocumentAnalysisAPI:
    """文档分析API类"""
    
    def __init__(self):
        """初始化API服务"""
        self.config = get_config()
        self.logger = logger
        
        # 初始化Redis管理器
        self.redis_manager = get_redis_manager()
        
        # 初始化火山引擎客户端
        self._init_volcengine_client()
        
        # 初始化分析服务管理器
        self._init_analysis_service()
        
        # 创建Flask应用
        self.app = self._create_flask_app()
        
        # 线程池用于后台分析
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        # 支持的文件格式
        self.ALLOWED_EXTENSIONS = {
            'pdf', 'docx', 'doc', 'xlsx', 'xls', 
            'pptx', 'ppt', 'md', 'txt'
        }
        
        # 分析阶段定义
        self.ANALYSIS_STAGES = [
            {'stage': 'document_parsing', 'name': '文档解析'},
            {'stage': 'content_analysis', 'name': '内容分析'},
            {'stage': 'ai_analysis', 'name': 'AI智能分析'}
        ]
    
    def _init_volcengine_client(self):
        """初始化火山引擎客户端"""
        try:
            volcengine_config = self.config.get_volcengine_config()
            volcano_config = VolcengineConfig(
                api_key=volcengine_config.get('api_key', ''),
                model_id=volcengine_config.get('model', 'doubao-pro-4k'),
                base_url=volcengine_config.get('endpoint', 'https://ark.cn-beijing.volces.com/api/v3'),
                temperature=volcengine_config.get('temperature', 0.7),
                max_tokens=volcengine_config.get('max_tokens', 4000)
            )
            self.volcano_client = VolcengineClient(volcano_config)
            self.logger.info("火山引擎客户端初始化成功")
        except Exception as e:
            self.logger.error(f"火山引擎客户端初始化失败: {e}")
            self.volcano_client = None
    
    def _init_analysis_service(self):
        """初始化分析服务管理器"""
        try:
            self.analysis_manager = AnalysisServiceManager(
                llm_client=self.volcano_client,
                vector_db_type="mock"
            )
            self.logger.info("分析服务管理器初始化成功")
        except Exception as e:
            self.logger.error(f"分析服务管理器初始化失败: {e}")
            self.analysis_manager = None
    
    def _create_flask_app(self):
        """创建Flask应用"""
        app = Flask(__name__)
        
        # 配置CORS
        CORS(app, 
             origins=["http://localhost:3000", "http://127.0.0.1:3000"],
             methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             allow_headers=["Content-Type", "Authorization"],
             supports_credentials=True)
        
        # 注册路由
        self._register_routes(app)
        
        return app
    
    def _register_routes(self, app):
        """注册API路由"""
        
        @app.route('/api/analysis', methods=['POST'])
        def start_analysis():
            """启动文档分析（上传+分析）"""
            return self._start_analysis()
        
        @app.route('/api/analysis/<task_id>', methods=['GET'])
        def get_analysis_progress(task_id):
            """获取分析进度"""
            return self._get_analysis_progress(task_id)
        
        @app.route('/api/analysis/<task_id>/result', methods=['GET'])
        def get_analysis_result(task_id):
            """获取分析结果（Markdown格式）"""
            return self._get_analysis_result(task_id)
        
        @app.route('/api/analysis/<task_id>', methods=['DELETE'])
        def cancel_analysis(task_id):
            """取消分析任务"""
            return self._cancel_analysis(task_id)
        
        @app.route('/api/health', methods=['GET'])
        def health_check():
            """健康检查"""
            return self._health_check()
        
        @app.route('/api/chat', methods=['POST'])
        def chat():
            """聊天接口"""
            return self._chat()
    
    def _start_analysis(self):
        """启动分析"""
        try:
            # 检查文件上传
            if 'file' not in request.files:
                return jsonify({
                    'status': 'error',
                    'error_code': 'NO_FILE',
                    'error_message': '未找到上传文件',
                    'retry_able': False
                }), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({
                    'status': 'error',
                    'error_code': 'EMPTY_FILENAME',
                    'error_message': '文件名不能为空',
                    'retry_able': False
                }), 400
            
            # 验证文件格式
            filename = secure_filename(file.filename)
            file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            
            if file_ext not in self.ALLOWED_EXTENSIONS:
                return jsonify({
                    'status': 'error',
                    'error_code': 'UNSUPPORTED_FORMAT',
                    'error_message': f'不支持的文件格式: {file_ext}',
                    'retry_able': False,
                    'suggestions': [f'支持的格式: {", ".join(self.ALLOWED_EXTENSIONS)}']
                }), 400
            
            # 验证文件大小
            file_content = file.read()
            file_size = len(file_content)
            max_size = self.config.config.get('file_upload', {}).get('max_size', 50 * 1024 * 1024)
            
            if file_size > max_size:
                return jsonify({
                    'status': 'error',
                    'error_code': 'FILE_TOO_LARGE',
                    'error_message': f'文件大小超过限制: {file_size / 1024 / 1024:.1f}MB',
                    'retry_able': False,
                    'suggestions': [f'最大文件大小: {max_size / 1024 / 1024:.0f}MB']
                }), 400
            
            # 生成任务ID
            task_id = str(uuid.uuid4())
            
            # 保存文件
            upload_dir = self.config.config.get('directories', {}).get('uploads', 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, f"{task_id}_{filename}")
            
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # 保存基本信息到Redis
            basic_info = {
                'task_id': task_id,
                'filename': filename,
                'filesize': f"{file_size / 1024 / 1024:.2f}MB",
                'file_type': file_ext,
                'upload_time': datetime.now().isoformat(),
                'status': 'uploaded',
                'created_at': datetime.now().isoformat()
            }
            
            self.redis_manager.set(f"analysis:{task_id}:basic_info", basic_info, ttl=24 * 3600)
            
            # 初始化进度信息
            progress_info = {
                'task_id': task_id,
                'status': 'started',
                'current_stage': None,
                'stages': {
                    'document_parsing': {'status': 'pending', 'progress': 0, 'message': '等待开始'},
                    'content_analysis': {'status': 'pending', 'progress': 0, 'message': '等待开始'},
                    'ai_analysis': {'status': 'pending', 'progress': 0, 'message': '等待开始'}
                },
                'overall_progress': 0,
                'updated_at': datetime.now().isoformat()
            }
            
            self.redis_manager.set(f"analysis:{task_id}:progress", progress_info, ttl=24 * 3600)
            
            # 启动后台分析任务
            self.executor.submit(self._run_full_analysis, task_id, file_path, file_content.decode('utf-8', errors='ignore'), filename)
            
            return jsonify({
                'status': 'started',
                'task_id': task_id,
                'message': '分析已启动',
                'basic_info': basic_info
            })
            
        except Exception as e:
            self.logger.error(f"启动分析失败: {e}")
            return jsonify({
                'status': 'error',
                'error_code': 'INTERNAL_ERROR',
                'error_message': '服务器内部错误',
                'retry_able': True
            }), 500
    
    def _run_full_analysis(self, task_id: str, file_path: str, file_content: str, filename: str):
        """后台运行完整分析"""
        try:
            self.logger.info(f"开始后台分析任务: {task_id}")
            
            if not self.analysis_manager:
                raise Exception("分析服务管理器未初始化")
            
            # 执行三阶段分析
            for i, stage_info in enumerate(self.ANALYSIS_STAGES):
                stage = stage_info['stage']
                stage_name = stage_info['name']
                
                try:
                    # 更新当前阶段状态
                    self._update_stage_progress(task_id, stage, 'running', 0, f'开始{stage_name}...')
                    
                    # 准备输入数据
                    if stage == 'document_parsing':
                        # 第一阶段：文档解析
                        input_data = {
                            "file_path": file_path,
                            "file_content": file_content,
                            "file_name": filename
                        }
                    else:
                        # 后续阶段：从Redis获取前一阶段结果
                        prev_stage = self.ANALYSIS_STAGES[i-1]['stage']
                        prev_result = self.redis_manager.get(f"analysis:{task_id}:{prev_stage}")
                        if not prev_result:
                            raise Exception(f"无法获取前一阶段结果: {prev_stage}")
                        input_data = prev_result
                    
                    # 执行分析
                    stage_result = None
                    if stage == 'document_parsing':
                        stage_result = self.analysis_manager.document_parser.analyze(task_id, input_data)
                    elif stage == 'content_analysis':
                        stage_result = self.analysis_manager.content_analyzer.analyze(task_id, input_data)
                    elif stage == 'ai_analysis':
                        stage_result = self.analysis_manager.ai_analyzer.analyze(task_id, input_data)
                    
                    # 保存阶段结果到Redis
                    self.redis_manager.set(f"analysis:{task_id}:{stage}", stage_result, ttl=24 * 3600)
                    
                    # 更新阶段完成状态
                    self._update_stage_progress(task_id, stage, 'completed', 100, f'{stage_name}完成')
                    
                    self.logger.info(f"阶段完成: {task_id} - {stage}")
                    
                except Exception as e:
                    self.logger.error(f"阶段执行失败 {task_id} - {stage}: {e}")
                    self._update_stage_progress(task_id, stage, 'error', 0, f'{stage_name}失败: {str(e)}')
                    return
            
            # 组装最终结果
            final_result = self._assemble_final_result(task_id)
            
            # 保存最终结果
            self.redis_manager.set(f"analysis:{task_id}:result", final_result, ttl=24 * 3600)
            
            # 更新整体状态为完成
            self._update_overall_progress(task_id, 'completed', 100, '分析完成')
            
            self.logger.info(f"分析任务完成: {task_id}")
            
        except Exception as e:
            self.logger.error(f"分析任务失败 {task_id}: {e}")
            self._update_overall_progress(task_id, 'error', 0, f'分析失败: {str(e)}')
    
    def _update_stage_progress(self, task_id: str, stage: str, status: str, progress: int, message: str):
        """更新阶段进度"""
        try:
            progress_info = self.redis_manager.get(f"analysis:{task_id}:progress", default={})
            
            if 'stages' not in progress_info:
                progress_info['stages'] = {}
            
            progress_info['stages'][stage] = {
                'status': status,
                'progress': progress,
                'message': message,
                'updated_at': datetime.now().isoformat()
            }
            
            progress_info['current_stage'] = stage if status == 'running' else None
            progress_info['updated_at'] = datetime.now().isoformat()
            
            # 计算整体进度
            completed_stages = sum(1 for s in progress_info['stages'].values() if s['status'] == 'completed')
            progress_info['overall_progress'] = int((completed_stages / len(self.ANALYSIS_STAGES)) * 100)
            
            self.redis_manager.set(f"analysis:{task_id}:progress", progress_info, ttl=24 * 3600)
            
        except Exception as e:
            self.logger.error(f"更新阶段进度失败: {e}")
    
    def _update_overall_progress(self, task_id: str, status: str, progress: int, message: str):
        """更新整体进度"""
        try:
            progress_info = self.redis_manager.get(f"analysis:{task_id}:progress", default={})
            
            progress_info.update({
                'status': status,
                'overall_progress': progress,
                'message': message,
                'updated_at': datetime.now().isoformat()
            })
            
            self.redis_manager.set(f"analysis:{task_id}:progress", progress_info, ttl=24 * 3600)
            
        except Exception as e:
            self.logger.error(f"更新整体进度失败: {e}")
    
    def _assemble_final_result(self, task_id: str) -> Dict[str, Any]:
        """组装最终结果"""
        try:
            # 获取基本信息
            basic_info = self.redis_manager.get(f"analysis:{task_id}:basic_info", default={})
            
            # 获取各阶段结果
            document_parsing = self.redis_manager.get(f"analysis:{task_id}:document_parsing", default={})
            content_analysis = self.redis_manager.get(f"analysis:{task_id}:content_analysis", default={})
            ai_analysis = self.redis_manager.get(f"analysis:{task_id}:ai_analysis", default={})
            
            # 组装完整结果
            final_result = {
                "task_id": task_id,
                "status": "completed",
                "created_at": basic_info.get('created_at'),
                "completed_at": datetime.now().isoformat(),
                "basic_info": basic_info,
                "document_parsing": document_parsing,
                "content_analysis": content_analysis,
                "ai_analysis": ai_analysis,
                "analysis_summary": self._generate_analysis_summary(document_parsing, content_analysis, ai_analysis)
            }
            
            return final_result
            
        except Exception as e:
            self.logger.error(f"组装最终结果失败: {e}")
            return {"error": str(e)}
    
    def _generate_analysis_summary(self, doc_parsing: Dict, content_analysis: Dict, ai_analysis: Dict) -> str:
        """生成分析总结"""
        try:
            summary_parts = []
            
            # 文档基本信息
            if doc_parsing.get('file_info'):
                file_info = doc_parsing['file_info']
                summary_parts.append(f"文档类型: {file_info.get('file_type', 'unknown')}")
                if file_info.get('page_count'):
                    summary_parts.append(f"页数: {file_info['page_count']}")
            
            # 内容分析摘要
            if content_analysis.get('key_changes'):
                changes_count = len(content_analysis['key_changes'])
                summary_parts.append(f"识别到 {changes_count} 个关键变更")
            
            # AI分析摘要
            if ai_analysis.get('requirements'):
                req_count = len(ai_analysis['requirements'])
                summary_parts.append(f"提取了 {req_count} 个需求")
            
            return "、".join(summary_parts) if summary_parts else "分析完成"
            
        except Exception as e:
            return f"生成摘要失败: {str(e)}"
    
    def _get_analysis_progress(self, task_id: str):
        """获取分析进度"""
        try:
            # 获取基本信息
            basic_info = self.redis_manager.get(f"analysis:{task_id}:basic_info")
            if not basic_info:
                return jsonify({
                    'status': 'error',
                    'error_code': 'TASK_NOT_FOUND',
                    'error_message': '任务不存在'
                }), 404
            
            # 获取进度信息
            progress_info = self.redis_manager.get(f"analysis:{task_id}:progress", default={
                'status': 'pending',
                'overall_progress': 0,
                'stages': {},
                'message': '等待开始'
            })
            
            response = {
                'task_id': task_id,
                'basic_info': basic_info,
                'progress': progress_info
            }
            
            # 如果分析完成，添加结果预览
            if progress_info.get('status') == 'completed':
                result = self.redis_manager.get(f"analysis:{task_id}:result")
                if result:
                    response['result_available'] = True
                    response['summary'] = result.get('analysis_summary', '分析完成')
            
            return jsonify(response)
            
        except Exception as e:
            self.logger.error(f"获取分析进度失败: {e}")
            return jsonify({
                'status': 'error',
                'error_code': 'INTERNAL_ERROR',
                'error_message': '服务器内部错误'
            }), 500
    
    def _get_analysis_result(self, task_id: str):
        """获取分析结果（Markdown格式）"""
        try:
            # 检查任务是否存在
            basic_info = self.redis_manager.get(f"analysis:{task_id}:basic_info")
            if not basic_info:
                return jsonify({
                    'status': 'error',
                    'error_code': 'TASK_NOT_FOUND',
                    'error_message': '任务不存在'
                }), 404
            
            # 获取分析结果
            result = self.redis_manager.get(f"analysis:{task_id}:result")
            if not result:
                return jsonify({
                    'status': 'error',
                    'error_code': 'RESULT_NOT_READY',
                    'error_message': '分析结果尚未准备就绪'
                }), 404
            
            # 转换为Markdown格式
            markdown_content = self._convert_to_markdown(result)
            
            return jsonify({
                'status': 'success',
                'task_id': task_id,
                'format': 'markdown',
                'content': markdown_content,
                'raw_data': result  # 同时提供原始JSON数据
            })
            
        except Exception as e:
            self.logger.error(f"获取分析结果失败: {e}")
            return jsonify({
                'status': 'error',
                'error_code': 'INTERNAL_ERROR',
                'error_message': '服务器内部错误'
            }), 500
    
    def _convert_to_markdown(self, result: Dict[str, Any]) -> str:
        """将JSON结果转换为Markdown格式"""
        try:
            markdown_lines = []
            
            # 标题
            basic_info = result.get('basic_info', {})
            filename = basic_info.get('filename', '未知文件')
            markdown_lines.append(f"# 文档分析报告 - {filename}")
            markdown_lines.append("")
            
            # 基本信息
            markdown_lines.append("## 📋 基本信息")
            markdown_lines.append(f"- **文件名**: {filename}")
            markdown_lines.append(f"- **文件大小**: {basic_info.get('filesize', '未知')}")
            markdown_lines.append(f"- **文件类型**: {basic_info.get('file_type', '未知')}")
            markdown_lines.append(f"- **上传时间**: {basic_info.get('upload_time', '未知')}")
            markdown_lines.append(f"- **分析完成时间**: {result.get('completed_at', '未知')}")
            markdown_lines.append("")
            
            # 文档解析结果
            doc_parsing = result.get('document_parsing', {})
            if doc_parsing:
                markdown_lines.append("## 📖 文档解析")
                
                # 文件信息
                file_info = doc_parsing.get('file_info', {})
                if file_info:
                    markdown_lines.append("### 文件信息")
                    for key, value in file_info.items():
                        markdown_lines.append(f"- **{key}**: {value}")
                    markdown_lines.append("")
                
                # 文档结构
                structure = doc_parsing.get('structure', {})
                if structure:
                    markdown_lines.append("### 文档结构")
                    if structure.get('title'):
                        markdown_lines.append(f"- **标题**: {structure['title']}")
                    if structure.get('sections'):
                        markdown_lines.append("- **章节结构**:")
                        for section in structure['sections'][:5]:  # 限制显示前5个章节
                            markdown_lines.append(f"  - {section.get('title', '未知章节')}")
                    markdown_lines.append("")
            
            # 内容分析结果
            content_analysis = result.get('content_analysis', {})
            if content_analysis:
                markdown_lines.append("## 🔍 内容分析")
                
                # 新增功能
                new_features = content_analysis.get('new_features', [])
                if new_features:
                    markdown_lines.append("### 新增功能")
                    for feature in new_features[:3]:  # 限制显示前3个
                        markdown_lines.append(f"- **{feature.get('feature_name', '未知功能')}**: {feature.get('description', '无描述')}")
                    markdown_lines.append("")
                
                # 关键变更
                key_changes = content_analysis.get('key_changes', [])
                if key_changes:
                    markdown_lines.append("### 关键变更")
                    for change in key_changes[:3]:  # 限制显示前3个
                        markdown_lines.append(f"- **{change.get('title', '未知变更')}**: {change.get('impact', '无影响描述')}")
                    markdown_lines.append("")
            
            # AI智能分析结果
            ai_analysis = result.get('ai_analysis', {})
            if ai_analysis:
                markdown_lines.append("## 🤖 AI智能分析")
                
                # 需求提取
                requirements = ai_analysis.get('requirements', [])
                if requirements:
                    markdown_lines.append("### 需求提取")
                    for req in requirements[:5]:  # 限制显示前5个
                        markdown_lines.append(f"- **{req.get('title', '未知需求')}**: {req.get('description', '无描述')}")
                    markdown_lines.append("")
                
                # 技术设计
                tech_design = ai_analysis.get('technical_design', '')
                if tech_design:
                    markdown_lines.append("### 技术设计")
                    markdown_lines.append(tech_design[:500] + "..." if len(tech_design) > 500 else tech_design)
                    markdown_lines.append("")
                
                # 实现建议
                implementation = ai_analysis.get('implementation_suggestions', '')
                if implementation:
                    markdown_lines.append("### 实现建议")
                    markdown_lines.append(implementation[:500] + "..." if len(implementation) > 500 else implementation)
                    markdown_lines.append("")
            
            # 分析总结
            summary = result.get('analysis_summary', '')
            if summary:
                markdown_lines.append("## 📊 分析总结")
                markdown_lines.append(summary)
                markdown_lines.append("")
            
            # 生成时间戳
            markdown_lines.append("---")
            markdown_lines.append(f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
            
            return "\n".join(markdown_lines)
            
        except Exception as e:
            self.logger.error(f"转换Markdown失败: {e}")
            return f"# 转换错误\n\n转换Markdown格式时发生错误: {str(e)}"
    
    def _cancel_analysis(self, task_id: str):
        """取消分析任务"""
        try:
            # 检查任务是否存在
            basic_info = self.redis_manager.get(f"analysis:{task_id}:basic_info")
            if not basic_info:
                return jsonify({
                    'status': 'error',
                    'error_code': 'TASK_NOT_FOUND',
                    'error_message': '任务不存在'
                }), 404
            
            # 更新状态为已取消
            self._update_overall_progress(task_id, 'cancelled', 0, '任务已取消')
            
            return jsonify({
                'status': 'success',
                'message': '任务已取消'
            })
            
        except Exception as e:
            self.logger.error(f"取消分析任务失败: {e}")
            return jsonify({
                'status': 'error',
                'error_message': '服务器内部错误'
            }), 500
    
    def _health_check(self):
        """健康检查"""
        status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'services': {
                'redis': self.redis_manager.test_connection(),
                'volcengine': self.volcano_client is not None,
                'analysis_manager': self.analysis_manager is not None
            }
        }
        
        return jsonify(status)
    
    def run(self, host='0.0.0.0', port=8082, debug=False):
        """运行API服务"""
        self.logger.info(f"启动文档分析API服务: http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

# 创建API实例
api = DocumentAnalysisAPI()

def create_app():
    """创建Flask应用（用于外部调用）"""
    return api.app

if __name__ == '__main__':
    api.run(debug=True) 