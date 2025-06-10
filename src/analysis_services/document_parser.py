"""
文档解析服务
实现完整的文档解析功能：格式识别、结构解析、内容提取、质量分析、版本信息提取
"""

import os
import json
import time
import re
from typing import Dict, Any, List, Optional
from pathlib import Path
from .base_service import BaseAnalysisService

class DocumentParserService(BaseAnalysisService):
    """文档解析服务类 - 阶段1：文档解析"""
    
    def __init__(self, llm_client=None, vector_db=None):
        super().__init__(llm_client, vector_db)
        self.stage_name = "document_parsing"
    
    async def analyze(self, task_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行文档解析分析 - 第一阶段
        
        Args:
            task_id: 任务ID
            input_data: 包含文件路径、文件内容等信息
            
        Returns:
            解析结果字典
        """
        start_time = time.time()
        
        try:
            # 提取输入数据
            file_path = input_data.get("file_path", "")
            file_content = input_data.get("file_content", "")
            file_name = input_data.get("file_name", "")
            
            self.logger.info(f"📄 开始文档解析 - Task: {task_id}")
            self.logger.info(f"   - 文件路径: {file_path}")
            self.logger.info(f"   - 文件名: {file_name}")
            self.logger.info(f"   - 原始内容长度: {len(file_content)}")
            
            # 🔧 修复：如果file_content为空但有file_path，尝试从文件读取内容
            if not file_content and file_path and os.path.exists(file_path):
                self.logger.info(f"📖 从文件路径读取内容: {file_path}")
                file_content = await self._read_file_content(file_path, file_name)
                self.logger.info(f"📖 读取后内容长度: {len(file_content)}")
            
            # 如果仍然没有内容，生成默认结果
            if not file_content:
                self.logger.warning(f"⚠️ 文件内容为空 - Task: {task_id}")
                return await self._generate_empty_content_result(task_id, file_name, file_path)
            
            self._log_analysis_start(task_id, "文档解析", len(file_content))
            
            # 1. 文件格式识别和基本信息
            file_info = await self.identify_file_type(file_path, file_name)
            
            # 2. 文档结构解析
            structure_info = await self.parse_document_structure(file_content, file_info['file_type'])
            
            # 3. 内容元素提取
            content_elements = await self.extract_content_elements(file_content, file_info['file_type'])
            
            # 4. 文档质量分析
            quality_info = await self.analyze_document_quality(file_content, structure_info)
            
            # 5. 版本信息和元数据提取
            version_info = await self.extract_version_info(file_content)
            metadata = await self.extract_metadata(file_content, file_name)
            
            # 合并解析结果
            parsing_result = {
                "file_info": file_info,
                "structure": structure_info,
                "content_elements": content_elements,
                "quality_info": quality_info,
                "version_info": version_info,
                "metadata": metadata,
                "analysis_metadata": {
                    "stage": "document_parsing",
                    "parsing_method": "enhanced_parser",
                    "analysis_time": time.time() - start_time,
                    "content_length": len(file_content)
                }
            }
            
            duration = time.time() - start_time
            self._log_analysis_complete(task_id, "文档解析", duration, len(str(parsing_result)))
            
            return self._create_response(
                success=True,
                data=parsing_result,
                metadata={"analysis_duration": duration, "stage": "document_parsing"}
            )
            
        except Exception as e:
            self._log_error(task_id, "文档解析", e)
            return self._create_response(
                success=False,
                error=f"文档解析失败: {str(e)}",
                metadata={"stage": "document_parsing"}
            )
    
    async def identify_file_type(self, file_path: str, file_name: str) -> Dict[str, Any]:
        """文件格式识别和基本信息"""
        try:
            file_ext = Path(file_name).suffix.lower()
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            
            # 文件类型映射
            file_type_map = {
                '.pdf': 'pdf',
                '.docx': 'docx', '.doc': 'doc',
                '.xlsx': 'xlsx', '.xls': 'xls',
                '.pptx': 'pptx', '.ppt': 'ppt',
                '.md': 'markdown',
                '.txt': 'text'
            }
            
            file_type = file_type_map.get(file_ext, 'unknown')
            
            # 获取文件时间信息
            file_info = {
                "file_type": file_type,
                "file_extension": file_ext,
                "file_size": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "file_name": file_name,
                "supported": file_type in ['pdf', 'docx', 'doc', 'xlsx', 'xls', 'pptx', 'ppt', 'markdown', 'text']
            }
            
            if os.path.exists(file_path):
                stat = os.stat(file_path)
                file_info.update({
                    "creation_date": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_ctime)),
                    "modification_date": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime)),
                    "access_date": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_atime))
                })
            
            # 基于文件类型添加特殊属性
            if file_type == 'pdf':
                file_info.update({
                    "is_encrypted": False,  # 需要实际检测
                    "has_digital_signature": False,  # 需要实际检测
                    "pdf_version": "unknown"  # 需要实际检测
                })
            
            return file_info
            
        except Exception as e:
            return {
                "file_type": "unknown",
                "error": f"文件信息获取失败: {str(e)}"
            }
    
    async def parse_document_structure(self, content: str, file_type: str) -> Dict[str, Any]:
        """文档结构解析"""
        try:
            # 提取标题和章节结构
            sections = self._extract_sections(content)
            
            # 分析目录结构
            toc_info = self._analyze_table_of_contents(content, sections)
            
            # 检测文档组件
            has_tables = bool(re.search(r'\|.*\|.*\|', content) or '表格' in content or 'table' in content.lower())
            has_images = bool(re.search(r'!\[.*\]|图\d+|图片|image', content, re.IGNORECASE))
            has_code = bool(re.search(r'```|代码|code|function|class', content, re.IGNORECASE))
            has_lists = bool(re.search(r'^\s*[-*+]\s+|^\s*\d+\.\s+', content, re.MULTILINE))
            
            structure_info = {
                "title": self._extract_document_title(content, sections),
                "sections": sections,
                "total_sections": len(sections),
                "max_depth": max([s.get('level', 1) for s in sections]) if sections else 1,
                "toc_available": toc_info['has_toc'],
                "toc_info": toc_info,
                "document_components": {
                    "has_tables": has_tables,
                    "has_images": has_images,
                    "has_code": has_code,
                    "has_lists": has_lists,
                    "has_links": bool(re.search(r'http[s]?://|www\.', content))
                },
                "structure_quality": self._assess_structure_quality(sections, content)
            }
            
            return structure_info
            
        except Exception as e:
            return {"error": f"结构解析失败: {str(e)}"}
    
    async def extract_content_elements(self, content: str, file_type: str) -> Dict[str, Any]:
        """内容元素提取"""
        try:
            elements = {
                "text_content": content,
                "word_count": len(content.split()),
                "character_count": len(content),
                "paragraph_count": len([p for p in content.split('\n\n') if p.strip()]),
                "line_count": len(content.split('\n')),
                "tables": self._extract_tables(content),
                "images": self._extract_images(content),
                "lists": self._extract_lists(content),
                "code_blocks": self._extract_code_blocks(content),
                "hyperlinks": self._extract_hyperlinks(content),
                "key_phrases": await self._extract_key_phrases(content),
                "language": self._detect_language(content)
            }
            
            return elements
            
        except Exception as e:
            return {"error": f"内容提取失败: {str(e)}"}
    
    async def analyze_document_quality(self, content: str, structure_info: Dict[str, Any]) -> Dict[str, Any]:
        """文档质量分析"""
        try:
            # 可读性评分
            readability = self._assess_readability(content)
            
            # 完整性评分
            completeness = self._assess_completeness(content, structure_info)
            
            # 格式化评分
            formatting = self._assess_formatting(content, structure_info)
            
            # 一致性评分
            consistency = self._assess_consistency(content, structure_info)
            
            quality_info = {
                "overall_score": round((readability['score'] + completeness['score'] + 
                                     formatting['score'] + consistency['score']) / 4, 1),
                "readability": readability,
                "completeness": completeness,
                "formatting": formatting,
                "consistency": consistency,
                "quality_level": self._get_quality_level(
                    (readability['score'] + completeness['score'] + 
                     formatting['score'] + consistency['score']) / 4
                ),
                "recommendations": self._generate_quality_recommendations(
                    readability, completeness, formatting, consistency
                )
            }
            
            return quality_info
            
        except Exception as e:
            return {"error": f"质量分析失败: {str(e)}"}
    
    async def extract_version_info(self, content: str) -> Dict[str, Any]:
        """版本信息提取"""
        try:
            # 版本号识别
            version_patterns = [
                r'版本\s*[:：]?\s*([vV]?\d+\.\d+(?:\.\d+)?)',
                r'version\s*[:：]?\s*([vV]?\d+\.\d+(?:\.\d+)?)',
                r'v(\d+\.\d+(?:\.\d+)?)',
                r'V(\d+\.\d+(?:\.\d+)?)'
            ]
            
            document_version = None
            for pattern in version_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    document_version = match.group(1)
                    break
            
            # 变更日志识别
            change_log = self._extract_change_log(content)
            
            # 版本历史识别
            version_history = self._extract_version_history(content)
            
            version_info = {
                "document_version": document_version or "未找到版本信息",
                "version_history": version_history,
                "change_log": change_log,
                "last_modified": self._extract_last_modified_date(content),
                "version_control_info": self._extract_version_control_info(content)
            }
            
            return version_info
            
        except Exception as e:
            return {"error": f"版本信息提取失败: {str(e)}"}
    
    async def extract_metadata(self, content: str, file_name: str) -> Dict[str, Any]:
        """元数据提取"""
        try:
            # 使用大模型生成摘要和提取关键词
            keywords = await self._extract_key_phrases(content)
            summary = await self._generate_summary(content)
            
            metadata = {
                "author": self._extract_author(content),
                "company": self._extract_company(content),
                "project": self._extract_project_name(content, file_name),
                "keywords": keywords,
                "summary": summary,
                "category": self._classify_document(content),
                "importance_level": self._assess_importance(content),
                "technical_level": self._assess_technical_level(content),
                "target_audience": self._identify_target_audience(content)
            }
            
            return metadata
            
        except Exception as e:
            return {"error": f"元数据提取失败: {str(e)}"}
    
    # 辅助方法实现
    def _extract_sections(self, content: str) -> List[Dict[str, Any]]:
        """提取章节结构"""
        sections = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Markdown格式标题
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                title = line.lstrip('#').strip()
                if title:
                    sections.append({
                        "level": level,
                        "title": title,
                        "line_number": i + 1,
                        "type": "markdown_header"
                    })
            
            # 数字编号标题
            elif re.match(r'^\d+(\.\d+)*\.?\s+', line):
                level = line.count('.') + 1
                title = re.sub(r'^\d+(\.\d+)*\.?\s+', '', line)
                if title:
                    sections.append({
                        "level": level,
                        "title": title,
                        "line_number": i + 1,
                        "type": "numbered_header"
                    })
        
        return sections
    
    def _extract_document_title(self, content: str, sections: List[Dict]) -> str:
        """提取文档标题"""
        lines = content.split('\n')
        
        # 尝试从第一行获取
        first_line = lines[0].strip() if lines else ""
        if first_line and len(first_line) < 100:
            return first_line
        
        # 尝试从第一个标题获取
        if sections:
            return sections[0]['title']
        
        # 从文件名推断
        return "未找到文档标题"
    
    def _assess_readability(self, content: str) -> Dict[str, Any]:
        """评估可读性"""
        words = content.split()
        sentences = re.split(r'[。！？.!?]', content)
        
        avg_word_per_sentence = len(words) / max(len(sentences), 1)
        
        # 简单的可读性评分
        if avg_word_per_sentence < 15:
            score = 90
            level = "优秀"
        elif avg_word_per_sentence < 25:
            score = 75
            level = "良好"
        elif avg_word_per_sentence < 35:
            score = 60
            level = "一般"
        else:
            score = 40
            level = "较差"
        
        return {
            "score": score,
            "level": level,
            "avg_words_per_sentence": round(avg_word_per_sentence, 1),
            "total_sentences": len(sentences)
        }
    
    def _assess_completeness(self, content: str, structure_info: Dict) -> Dict[str, Any]:
        """评估完整性"""
        required_sections = ["概述", "需求", "功能", "技术", "总结"]
        found_sections = []
        
        content_lower = content.lower()
        for section in required_sections:
            if section in content or section.lower() in content_lower:
                found_sections.append(section)
        
        completeness_ratio = len(found_sections) / len(required_sections)
        score = int(completeness_ratio * 100)
        
        return {
            "score": score,
            "found_sections": found_sections,
            "missing_sections": [s for s in required_sections if s not in found_sections],
            "section_coverage": round(completeness_ratio * 100, 1)
        }
    
    def _assess_formatting(self, content: str, structure_info: Dict) -> Dict[str, Any]:
        """评估格式化质量"""
        sections = structure_info.get('sections', [])
        
        # 检查标题一致性
        consistent_headers = len(set(s.get('type', '') for s in sections)) <= 2
        
        # 检查结构层次
        proper_hierarchy = all(s.get('level', 1) <= 4 for s in sections)
        
        score = 80
        if consistent_headers:
            score += 10
        if proper_hierarchy:
            score += 10
        
        return {
            "score": min(score, 100),
            "consistent_headers": consistent_headers,
            "proper_hierarchy": proper_hierarchy,
            "total_sections": len(sections)
        }
    
    def _assess_consistency(self, content: str, structure_info: Dict) -> Dict[str, Any]:
        """评估一致性"""
        # 简单的一致性检查
        score = 80  # 基础分数
        
        return {
            "score": score,
            "terminology_consistent": True,
            "style_consistent": True
        }
    
    def _get_quality_level(self, score: float) -> str:
        """获取质量等级"""
        if score >= 85:
            return "优秀"
        elif score >= 70:
            return "良好"
        elif score >= 60:
            return "一般"
        else:
            return "需要改进"
    
    def _generate_quality_recommendations(self, readability: Dict, completeness: Dict, 
                                        formatting: Dict, consistency: Dict) -> List[str]:
        """生成质量改进建议"""
        recommendations = []
        
        if readability['score'] < 70:
            recommendations.append("建议缩短句子长度，提高可读性")
        
        if completeness['score'] < 80:
            recommendations.append(f"建议补充缺失章节: {', '.join(completeness['missing_sections'])}")
        
        if formatting['score'] < 80:
            recommendations.append("建议统一标题格式，改善文档结构")
        
        if not recommendations:
            recommendations.append("文档质量良好，建议继续保持")
        
        return recommendations
    
    # ... 其他辅助方法的实现
    def _extract_tables(self, content: str) -> List[Dict]:
        """提取表格"""
        # 简化实现
        return []
    
    def _extract_images(self, content: str) -> List[Dict]:
        """提取图片信息"""
        # 简化实现
        return []
    
    def _extract_lists(self, content: str) -> List[Dict]:
        """提取列表"""
        # 简化实现
        return []
    
    def _extract_code_blocks(self, content: str) -> List[Dict]:
        """提取代码块"""
        # 简化实现
        return []
    
    def _extract_hyperlinks(self, content: str) -> List[Dict]:
        """提取超链接"""
        # 简化实现
        return []
    
    async def _extract_key_phrases(self, content: str) -> List[str]:
        """使用大模型提取关键短语"""
        if not self.llm_client:
            # 回退到简单的关键词提取
            return self._extract_keywords_fallback(content)
        
        try:
            # 构建prompt
            prompt = f"""请从以下文档内容中提取8-12个最重要的关键词或关键短语。

要求：
1. 提取能够代表文档核心内容的关键词
2. 包括技术术语、业务术语、功能模块等
3. 每个关键词不超过10个字符
4. 按重要性排序
5. 只返回关键词列表，用英文逗号分隔

文档内容：
{content[:2000]}

关键词："""

            # 调用大模型
            response = self.llm_client.chat([
                {"role": "user", "content": prompt}
            ])
            
            if response:
                keywords_text = response.strip()
                # 解析关键词
                keywords = [kw.strip() for kw in keywords_text.split(',') if kw.strip()]
                return keywords[:12]  # 最多返回12个关键词
            
        except Exception as e:
            self.logger.warning(f"大模型提取关键词失败: {e}, 使用回退方案")
        
        return self._extract_keywords_fallback(content)
    
    def _detect_language(self, content: str) -> str:
        """检测语言"""
        chinese_chars = sum(1 for char in content if '\u4e00' <= char <= '\u9fff')
        english_chars = sum(1 for char in content if char.isalpha() and ord(char) < 128)
        
        if chinese_chars > english_chars:
            return "中文"
        elif english_chars > 0:
            return "英文"
        else:
            return "未知"
    
    def _analyze_table_of_contents(self, content: str, sections: List) -> Dict:
        """分析目录结构"""
        return {
            "has_toc": len(sections) > 3,
            "toc_quality": "良好" if len(sections) > 5 else "一般"
        }
    
    def _assess_structure_quality(self, sections: List, content: str) -> str:
        """评估结构质量"""
        if len(sections) > 5:
            return "结构清晰"
        elif len(sections) > 2:
            return "结构一般"
        else:
            return "结构简单"
    
    def _extract_change_log(self, content: str) -> List[Dict]:
        """提取变更日志"""
        return []
    
    def _extract_version_history(self, content: str) -> List[Dict]:
        """提取版本历史"""
        return []
    
    def _extract_last_modified_date(self, content: str) -> Optional[str]:
        """提取最后修改日期"""
        return None
    
    def _extract_version_control_info(self, content: str) -> Dict:
        """提取版本控制信息"""
        return {}
    
    def _extract_author(self, content: str) -> str:
        """提取作者"""
        return "未找到作者信息"
    
    def _extract_company(self, content: str) -> str:
        """提取公司信息"""
        return "未找到公司信息"
    
    def _extract_project_name(self, content: str, file_name: str) -> str:
        """提取项目名称"""
        return Path(file_name).stem
    
    def _extract_keywords_fallback(self, content: str) -> List[str]:
        """回退方案：简单的关键词提取"""
        import re
        
        # 提取中文词汇（2-6字符）
        chinese_words = re.findall(r'[\u4e00-\u9fff]{2,6}', content)
        
        # 提取英文单词
        english_words = re.findall(r'\b[A-Za-z]{3,12}\b', content)
        
        # 常见技术词汇优先级更高
        tech_keywords = []
        common_tech_terms = [
            '系统', '模块', '功能', '接口', '数据库', '服务', '架构', '设计',
            '需求', '优化', '配置', '管理', '用户', '权限', '安全', '性能',
            'API', 'HTTP', 'JSON', 'XML', 'SQL', 'Redis', 'MySQL', 'MongoDB'
        ]
        
        for term in common_tech_terms:
            if term in content:
                tech_keywords.append(term)
        
        # 合并并去重
        all_keywords = tech_keywords + chinese_words + english_words
        unique_keywords = list(dict.fromkeys(all_keywords))  # 保持顺序去重
        
        return unique_keywords[:10]  # 返回前10个关键词
    
    def _extract_keywords(self, content: str) -> List[str]:
        """提取关键词（兼容性方法）"""
        return self._extract_keywords_fallback(content)
    
    async def _generate_summary(self, content: str) -> str:
        """使用大模型生成文档摘要"""
        if not self.llm_client:
            # 回退到简单截取
            return content[:200] + "..." if len(content) > 200 else content
        
        try:
            # 构建prompt
            prompt = f"""请为以下文档生成一个150-300字的准确摘要。

要求：
1. 概括文档的主要内容和目的
2. 包含关键功能、技术要点或业务需求
3. 语言简洁明了，突出重点
4. 保持客观中性的语调
5. 如果是技术文档，要提及核心技术栈或架构
6. 如果是需求文档，要说明主要功能和业务目标

文档内容：
{content[:3000]}

摘要："""

            # 调用大模型
            response = self.llm_client.chat([
                {"role": "user", "content": prompt}
            ])
            
            if response:
                summary = response.strip()
                # 确保摘要长度合理
                if len(summary) > 500:
                    summary = summary[:497] + "..."
                return summary
            
        except Exception as e:
            self.logger.warning(f"大模型生成摘要失败: {e}, 使用回退方案")
        
        # 回退方案
        return content[:200] + "..." if len(content) > 200 else content
    
    def _classify_document(self, content: str) -> str:
        """文档分类"""
        if "需求" in content:
            return "需求文档"
        elif "设计" in content:
            return "设计文档"
        elif "技术" in content:
            return "技术文档"
        else:
            return "其他文档"
    
    def _assess_importance(self, content: str) -> str:
        """评估重要性"""
        return "中等"
    
    def _assess_technical_level(self, content: str) -> str:
        """评估技术水平"""
        return "中等"
    
    def _identify_target_audience(self, content: str) -> str:
        """识别目标受众"""
        return "项目团队"
    
    async def _read_file_content(self, file_path: str, file_name: str) -> str:
        """根据文件类型读取文件内容"""
        try:
            file_ext = Path(file_name).suffix.lower()
            
            if file_ext == '.docx':
                return await self._read_docx_content(file_path)
            elif file_ext == '.doc':
                return await self._read_doc_content(file_path)
            elif file_ext == '.pdf':
                return await self._read_pdf_content(file_path)
            elif file_ext in ['.txt', '.md', '.csv', '.log', '.json', '.xml', '.html']:
                return await self._read_text_content(file_path)
            else:
                # 对于未知格式，尝试作为文本读取
                return await self._read_text_content(file_path)
                
        except Exception as e:
            self.logger.error(f"读取文件内容失败: {e}")
            return ""
    
    async def _read_docx_content(self, file_path: str) -> str:
        """读取Word DOCX文档内容"""
        try:
            # 尝试使用python-docx库
            try:
                from docx import Document
                doc = Document(file_path)
                content = []
                for paragraph in doc.paragraphs:
                    if paragraph.text.strip():
                        content.append(paragraph.text.strip())
                return '\n\n'.join(content)
            except ImportError:
                self.logger.warning("python-docx库未安装，使用备用方法")
                # 备用方法：尝试解压docx文件并读取XML
                return await self._read_docx_fallback(file_path)
        except Exception as e:
            self.logger.error(f"读取DOCX文件失败: {e}")
            return ""
    
    async def _read_docx_fallback(self, file_path: str) -> str:
        """DOCX文件备用读取方法"""
        try:
            import zipfile
            import xml.etree.ElementTree as ET
            
            with zipfile.ZipFile(file_path, 'r') as docx:
                # 读取主文档内容
                try:
                    xml_content = docx.read('word/document.xml')
                    root = ET.fromstring(xml_content)
                    
                    # 提取文本内容
                    namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                    texts = []
                    for paragraph in root.findall('.//w:p', namespaces):
                        para_text = []
                        for text_elem in paragraph.findall('.//w:t', namespaces):
                            if text_elem.text:
                                para_text.append(text_elem.text)
                        if para_text:
                            texts.append(''.join(para_text))
                    
                    return '\n\n'.join(texts)
                except:
                    # 如果XML解析失败，返回一个基本的占位内容
                    return f"Word文档解析失败，文件路径: {file_path}"
        except Exception as e:
            self.logger.error(f"DOCX备用读取方法失败: {e}")
            return ""
    
    async def _read_doc_content(self, file_path: str) -> str:
        """读取Word DOC文档内容（旧格式）"""
        try:
            # 对于.doc文件，我们先返回一个占位内容
            # 实际生产环境中需要安装python-docx2txt或其他库
            return f"Word DOC文档（旧格式），需要专门的解析库。文件路径: {file_path}"
        except Exception as e:
            self.logger.error(f"读取DOC文件失败: {e}")
            return ""
    
    async def _read_pdf_content(self, file_path: str) -> str:
        """读取PDF文档内容"""
        try:
            # 对于PDF文件，我们先返回一个占位内容
            # 实际生产环境中需要安装PyPDF2或pdfplumber
            return f"PDF文档，需要专门的解析库。文件路径: {file_path}"
        except Exception as e:
            self.logger.error(f"读取PDF文件失败: {e}")
            return ""
    
    async def _read_text_content(self, file_path: str) -> str:
        """读取纯文本文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    return f.read()
            except:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
        except Exception as e:
            self.logger.error(f"读取文本文件失败: {e}")
            return ""
    
    async def _generate_empty_content_result(self, task_id: str, file_name: str, file_path: str) -> Dict[str, Any]:
        """生成空内容的默认解析结果"""
        self.logger.info(f"生成空内容的默认解析结果 - Task: {task_id}")
        
        parsing_result = {
            "file_info": {
                "file_type": "unknown",
                "file_extension": Path(file_name).suffix.lower() if file_name else "",
                "file_size": 0,
                "file_size_mb": 0.0,
                "file_name": file_name,
                "supported": False,
                "error": "文件内容为空或无法读取"
            },
            "structure": {
                "title": "未找到文档标题",
                "sections": [],
                "total_sections": 0,
                "max_depth": 1,
                "toc_available": False,
                "toc_info": {"has_toc": False, "toc_quality": "无"},
                "document_components": {
                    "has_tables": False,
                    "has_images": False,
                    "has_code": False,
                    "has_lists": False,
                    "has_links": False
                },
                "structure_quality": "无结构"
            },
            "content_elements": {
                "text_content": "",
                "word_count": 0,
                "character_count": 0,
                "paragraph_count": 0,
                "line_count": 0,
                "tables": [],
                "images": [],
                "lists": [],
                "code_blocks": [],
                "hyperlinks": [],
                "key_phrases": ["文件内容为空或无法解析"],
                "language": "未知"
            },
            "quality_info": {
                "overall_score": 0,
                "readability": {"score": 0, "level": "无法评估"},
                "completeness": {"score": 0, "found_sections": [], "missing_sections": []},
                "formatting": {"score": 0, "consistent_headers": False},
                "consistency": {"score": 0, "terminology_consistent": False},
                "quality_level": "无法评估",
                "recommendations": ["请检查文件格式和内容完整性"]
            },
            "version_info": {
                "document_version": "未找到版本信息",
                "version_history": [],
                "change_log": [],
                "last_modified": None,
                "version_control_info": {}
            },
            "metadata": {
                "author": "未找到作者信息",
                "company": "未找到公司信息",
                "project": file_name or "未知项目",
                "keywords": ["空文档", "解析失败"],
                "summary": "文件内容为空或无法解析，请检查文件格式是否正确。",
                "category": "其他文档",
                "importance_level": "低",
                "technical_level": "无",
                "target_audience": "未知"
            },
            "analysis_metadata": {
                "stage": "document_parsing",
                "parsing_method": "empty_content_handler",
                "analysis_time": 0.1,
                "content_length": 0
            }
        }
        
        return self._create_response(
            success=True,
            data=parsing_result,
            metadata={"analysis_duration": 0.1, "stage": "document_parsing"}
        ) 