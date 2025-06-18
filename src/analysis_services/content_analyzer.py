"""
内容分析服务
使用大模型和向量数据库进行CRUD操作分析和业务需求识别
"""

import json
import time
import re
from typing import Dict, Any, List
from .base_service import BaseAnalysisService
from sentence_transformers import SentenceTransformer
from ..utils.weaviate_helper import get_weaviate_client

class ContentAnalyzerService(BaseAnalysisService):
    """内容分析服务类"""
    
    def __init__(self, llm_client=None, vector_db=None):
        super().__init__(llm_client, vector_db)
        # 初始化向量模型 - 使用bge-large-zh（1024维，中文优化）
        self.embedding_model = SentenceTransformer('BAAI/bge-large-zh')
        # 初始化Weaviate客户端
        self.weaviate_client = get_weaviate_client()
    
    async def analyze(self, task_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行内容分析
        
        Args:
            task_id: 任务ID
            input_data: 需求文档，转成的markdown模式
            
        Returns:
            内容分析结果字典
        """
        start_time = time.time()
        
        try:
            # 提取文件结果
            document_content = input_data.get("document_content", "")
            self.logger.info(f"内容分析开始document_content: {document_content}")
            self._log_analysis_start(task_id, "内容分析", len(document_content))
            
            # Step 1: 文档预处理
            structured_chunks = await self._preprocess_document(document_content)
            
            self.logger.info(f"文档预处理: {structured_chunks}")
            # Step 2: 与历史知识库内容对比
            history_comparison = await self._compare_with_history(structured_chunks)
            
            self.logger.info(f"历史比对结果: {history_comparison}")
            # Step 3: 大模型变更判断与结构化输出
            change_analysis = await self._analyze_changes(structured_chunks, history_comparison, document_content)
            
            self.logger.info(f"变更分析完成: {change_analysis}")
            
            # Step 3.5: 智能合并相似的变更项
            merged_change_analysis = await self._merge_similar_changes(change_analysis)
            
            self.logger.info(f"相似变更项合并完成: {merged_change_analysis}")
            
            # Step 4: 对变更项从原文档提取详细变更点
            enhanced_change_analysis = await self._extract_detailed_changes(merged_change_analysis, document_content)
            
            self.logger.info(f"详细变更内容提取完成: {enhanced_change_analysis}")
            
            # 清理结构化内容块，移除向量嵌入以减少输出大小
            cleaned_chunks = []
            for chunk in structured_chunks:
                cleaned_chunk = {
                    "section": chunk["section"],
                    "content": chunk["content"],
                    "level": chunk["level"],
                    "image_refs": chunk.get("image_refs", [])
                    # 不包含embedding向量
                }
                cleaned_chunks.append(cleaned_chunk)
            
            # 合并分析结果
            content_result = {
                "change_analysis": enhanced_change_analysis,
                "metadata": {
                    "analysis_method": "LLM+向量数据库分析+详细内容提取+智能合并",
                    "analysis_time": time.time() - start_time,
                    "content_length": len(document_content),
                    "chunks_count": len(structured_chunks)
                }
            }
            self.logger.info(f"内容分析结果: {content_result}")

            duration = time.time() - start_time
            self._log_analysis_complete(task_id, "内容分析", duration, len(str(content_result)))
            
            return self._create_response(
                success=True,
                data=content_result,
                metadata={"analysis_duration": duration}
            )
            
        except Exception as e:
            self._log_error(task_id, "内容分析", e)
            return self._create_response(
                success=False,
                error=f"内容分析失败: {str(e)}"
            )
    
    async def _preprocess_document(self, document_content: str) -> List[Dict[str, Any]]:
        """
        Step 1: 文档预处理
        将markdown文档拆解为结构化内容块
        
        Args:
            document_content: markdown格式的文档内容
            
        Returns:
            结构化内容块列表
        """
        structured_chunks = []
        
        # 按行分割文档
        lines = document_content.split('\n')
        current_section = ""
        current_content = []
        current_level = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 检测标题级别
            if line.startswith('#'):
                # 保存之前的内容块
                if current_section and current_content:
                    content_text = '\n'.join(current_content).strip()
                    if content_text:
                        # 生成向量嵌入
                        embedding = self.embedding_model.encode(f"{current_section}\n{content_text}").tolist()
                        
                        chunk = {
                            "section": current_section,
                            "content": content_text,
                            "level": current_level,
                            "embedding": embedding,
                            "image_refs": self._extract_image_refs(content_text)
                        }
                        structured_chunks.append(chunk)
                
                # 开始新的段落
                current_level = len(line) - len(line.lstrip('#'))
                current_section = line.lstrip('# ').strip()
                current_content = []
            else:
                # 普通内容行
                current_content.append(line)
        
        # 处理最后一个段落
        if current_section and current_content:
            content_text = '\n'.join(current_content).strip()
            if content_text:
                embedding = self.embedding_model.encode(f"{current_section}\n{content_text}").tolist()
                
                chunk = {
                    "section": current_section,
                    "content": content_text,
                    "level": current_level,
                    "embedding": embedding,
                    "image_refs": self._extract_image_refs(content_text)
                }
                structured_chunks.append(chunk)
        
        return structured_chunks
    
    def _extract_image_refs(self, content: str) -> List[str]:
        """提取内容中的图片引用"""
        image_refs = []
        # 匹配markdown图片语法: ![alt](path)
        image_pattern = re.compile(r'!\[.*?\]\((.*?)\)')
        matches = image_pattern.findall(content)
        image_refs.extend(matches)
        
        # 匹配其他可能的图片引用格式
        ref_pattern = re.compile(r'\[图片[：:]\s*(.*?)\]')
        matches = ref_pattern.findall(content)
        image_refs.extend(matches)
        
        return image_refs
    
    async def _compare_with_history(self, structured_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Step 2: 与历史知识库内容对比
        
        Args:
            structured_chunks: 结构化内容块
            
        Returns:
            历史对比结果，包含可读的历史文档信息
        """
        comparison_results = []
        deleted_items = []
        
        # Step 2-A: 历史内容匹配与相似度判断
        for chunk in structured_chunks:
            similar_history = await self._find_similar_history(chunk)
            
            if similar_history:
                max_similarity = max(item['similarity'] for item in similar_history)
                
                # 格式化历史匹配信息，确保返回可读内容而不是向量
                formatted_history = []
                for item in similar_history:
                    formatted_item = {
                        "title": item.get('title', ''),
                        "file_path": item.get('file_path', ''),
                        "content": item.get('content', ''),
                        "similarity": item.get('similarity', 0.0),
                        "search_method": item.get('search_method', '向量搜索')
                    }
                    # 移除embedding等非必要字段
                    formatted_history.append(formatted_item)
                
                if max_similarity >= 0.4:  # 相似度阈值
                    comparison_results.append({
                        "current_chunk": {
                            "section": chunk['section'],
                            "content": chunk['content'],
                            "level": chunk['level']
                            # 不包含embedding向量
                        },
                        "matched_history": formatted_history,
                        "change_type": "修改" if max_similarity < 0.9 else "相同",
                        "max_similarity": max_similarity
                    })
                else:
                    comparison_results.append({
                        "current_chunk": {
                            "section": chunk['section'],
                            "content": chunk['content'],
                            "level": chunk['level']
                        },
                        "matched_history": [],
                        "change_type": "新增",
                        "max_similarity": max_similarity
                    })
            else:
                comparison_results.append({
                    "current_chunk": {
                        "section": chunk['section'],
                        "content": chunk['content'],
                        "level": chunk['level']
                    },
                    "matched_history": [],
                    "change_type": "新增",
                    "max_similarity": 0.0
                })
        
        # Step 2-B: 识别删除项
        deleted_items = await self._identify_deleted_items(structured_chunks)
        
        return {
            "comparisons": comparison_results,
            "deleted_items": deleted_items,
            "summary": {
                "total_chunks": len(structured_chunks),
                "new_items": len([r for r in comparison_results if r["change_type"] == "新增"]),
                "modified_items": len([r for r in comparison_results if r["change_type"] == "修改"]),
                "same_items": len([r for r in comparison_results if r["change_type"] == "相同"]),
                "deleted_items": len(deleted_items)
            }
        }
    
    async def _find_similar_history(self, chunk: Dict[str, Any], top_k: int = 5) -> List[Dict[str, Any]]:
        """在历史知识库中查找相似内容"""
        try:
            collection = self.weaviate_client.collections.get("Document")
            
            # 使用向量搜索 - 需要处理向量格式差异
            query_vector = chunk['embedding']  # 1024维向量
            
            # 检查历史数据的向量格式
            # 先尝试获取一个示例来了解向量格式
            sample_response = collection.query.fetch_objects(limit=1, include_vector=True)
            
            if sample_response.objects and sample_response.objects[0].vector:
                sample_vector = sample_response.objects[0].vector
                
                # 检查向量格式
                if isinstance(sample_vector, dict) and 'default' in sample_vector:
                    # 如果历史数据使用 {'default': [vector]} 格式
                    actual_vector = sample_vector['default']
                    sample_dim = len(actual_vector)
                    
                    self.logger.info(f"历史数据向量维度: {sample_dim}, 当前分析向量维度: {len(query_vector)}")
                    
                    if sample_dim != len(query_vector):
                        # 维度不匹配，跳过向量搜索，使用关键词搜索替代
                        self.logger.info(f"向量维度不匹配 (历史: {sample_dim}, 当前: {len(query_vector)})，跳过向量搜索")
                        return await self._fallback_keyword_search(chunk, top_k)
                
                # 如果维度匹配，继续向量搜索
                response = collection.query.near_vector(
                    near_vector=query_vector,
                    limit=top_k,
                    return_metadata=['distance']
                )
            else:
                # 没有历史数据或没有向量，返回空结果
                return []
            
            similar_items = []
            for obj in response.objects:
                similarity = 1 - obj.metadata.distance  # 转换为相似度
                similar_items.append({
                    "content": obj.properties.get('content', ''),
                    "title": obj.properties.get('title', ''),
                    "file_path": obj.properties.get('file_path', ''),
                    "similarity": similarity
                })
            
            return similar_items
            
        except Exception as e:
            self.logger.error(f"历史内容搜索失败: {e}")
            # 降级到关键词搜索
            return await self._fallback_keyword_search(chunk, top_k)
    
    async def _fallback_keyword_search(self, chunk: Dict[str, Any], top_k: int = 5) -> List[Dict[str, Any]]:
        """当向量搜索失败时，使用关键词搜索作为降级方案"""
        try:
            collection = self.weaviate_client.collections.get("AnalyDesignDocuments")
            
            # 使用BM25关键词搜索
            search_text = f"{chunk['section']} {chunk['content']}"
            
            response = collection.query.bm25(
                query=search_text,
                limit=top_k,
                return_metadata=['score']
            )
            
            similar_items = []
            for obj in response.objects:
                # BM25得分转换为相似度（简单映射）
                similarity = min(obj.metadata.score / 10.0, 1.0) if obj.metadata.score else 0.1
                similar_items.append({
                    "content": obj.properties.get('content', ''),
                    "title": obj.properties.get('title', ''),
                    "file_path": obj.properties.get('file_path', ''),
                    "similarity": similarity,
                    "search_method": "BM25关键词搜索"
                })
            
            self.logger.info(f"使用关键词搜索找到 {len(similar_items)} 个相似项")
            return similar_items
            
        except Exception as e:
            self.logger.error(f"关键词搜索也失败: {e}")
            return []
    
    async def _identify_deleted_items(self, structured_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """识别删除项"""
        deleted_items = []
        
        # 在当前文档中搜索删除相关的关键词
        delete_keywords = [
            r"删除[了]?(.+?)功能",
            r"去除[了]?(.+?)接口",
            r"取消[了]?(.+?)服务",
            r"移除[了]?(.+)",
            r"不再(.+)",
            r"~~(.+?)~~"  # markdown删除线
        ]
        
        for chunk in structured_chunks:
            content = chunk['content']
            section = chunk['section']
            
            for pattern in delete_keywords:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    deleted_items.append({
                        "section": section,
                        "deleted_item": match.strip(),
                        "context": content,
                        "detection_method": "关键词匹配"
                    })
        
        return deleted_items
    
    async def _analyze_changes(self, structured_chunks: List[Dict[str, Any]], 
                             history_comparison: Dict[str, Any], document_content: str) -> Dict[str, Any]:
        """
        Step 3: 大模型变更判断与结构化输出
        
        Args:
            structured_chunks: 结构化内容块
            history_comparison: 历史对比结果
            document_content: 文档内容
            
        Returns:
            变更分析结果
        """
        change_analyses = []
        
        for comparison in history_comparison['comparisons']:
            if comparison['change_type'] in ['修改', '新增'] and comparison['matched_history']:
                # 对有历史匹配的内容进行详细分析
                analysis = await self._llm_change_analysis(comparison, document_content)
                if analysis:
                    change_analyses.append(analysis)
        
        # 对删除项进行分析
        deletion_analyses = []
        for deleted_item in history_comparison['deleted_items']:
            analysis = await self._llm_deletion_analysis(deleted_item, document_content)
            if analysis:
                deletion_analyses.append(analysis)
        
        return {
            "change_analyses": change_analyses,
            "deletion_analyses": deletion_analyses,
            "summary": {
                "total_changes": len(change_analyses),
                "total_deletions": len(deletion_analyses),
                "analysis_method": "LLM智能分析"
            }
        }
    
    async def _llm_change_analysis(self, comparison: Dict[str, Any], document_content: str) -> Dict[str, Any]:
        """使用LLM分析变更"""
        current_content = f"{comparison['current_chunk']['section']}\n{comparison['current_chunk']['content']}"
        self.logger.info(f"使用LLM分析变更: {current_content}")

        # 格式化历史内容信息，提供更丰富的上下文
        history_context = ""
        history_files = []
        self.logger.info(f"使用LLM的coparison: {comparison}")
        if comparison['matched_history']:
            history_items = []
            for idx, item in enumerate(comparison['matched_history'][:3]):  # 取前3个最相似的
                history_item = f"""
历史文档{idx+1}:
- 文件: {item.get('file_path', '未知文件')}
- 标题: {item.get('title', '未知标题')}
- 相似度: {item.get('similarity', 0):.2f}
- 内容: {item.get('content', '')}
"""
                history_items.append(history_item)
                history_files.append(item.get('file_path', ''))
            
            history_context = "\n".join(history_items)
        else:
            history_context = "无匹配的历史文档"
        
        system_prompt = """你是专业的需求文档变更分析专家。请仔细比较当前需求内容与历史需求内容，识别出具体的变更点，并按照指定的JSON格式输出分析结果。

分析要点：
1. 对比功能需求的差异
2. 识别新增、修改、删除的具体功能点
3. 分析业务逻辑的变化
4. 提供清晰的变更说明"""
        
        user_prompt = f"""
【完整文档内容】：
{document_content}

【当前版本需求内容】：
{current_content}

【历史版本需求内容】：
{history_context}

请仔细分析当前需求与历史需求的差异，结合完整文档内容的上下文，按照以下 JSON 格式输出分析结果：

{{
    "changeType": "新增 | 修改 | 删除",
    "changeReason": "详细说明变更的原因和判断依据",
    "changeItems": ["具体变更点1", "具体变更点2", "具体变更点3"],
    "version": {history_files[:1] if history_files else ["无历史版本"]}
}}

注意：
- 请结合完整文档内容理解当前需求的位置和作用
- changeItems应该包含具体的功能点变更描述
- changeReason要说明为什么判断为变更类型
- 如果是修改，请明确指出修改前后的差异
"""
        
        try:
            response = await self._call_llm(user_prompt, system_prompt, max_tokens=12000)
            if response:
                # 尝试解析JSON响应
                try:
                    # 先清理响应内容
                    cleaned_response = self._clean_json_response(response)
                    analysis_result = json.loads(cleaned_response)
                    return analysis_result
                except json.JSONDecodeError as e:
                    self.logger.warning(f"LLM响应JSON解析失败: {str(e)}")
                    self.logger.debug(f"原始响应前500字符: {response[:500]}")
                    
                    # 尝试修复常见的JSON格式问题
                    try:
                        fixed_response = self._fix_incomplete_json(response)
                        analysis_result = json.loads(fixed_response)
                        self.logger.info("成功修复并解析JSON响应")
                        return analysis_result
                    except:
                        self.logger.warning("JSON修复失败，返回格式化的原始响应")
                        # 如果JSON解析失败，返回格式化的原始响应
                        return {
                            "changeType": comparison['change_type'],
                            "changeReason": "LLM分析完成，但JSON格式解析失败",
                            "changeItems": [f"LLM原始分析: {response[:300]}{'...' if len(response) > 300 else ''}"],
                            "version": history_files[:1] if history_files else ["无历史版本"]
                        }
        except Exception as e:
            self.logger.error(f"LLM变更分析失败: {e}")
        
        return None
    
    def _clean_json_response(self, response: str) -> str:
        """
        清理LLM响应，提取JSON内容
        
        Args:
            response: LLM原始响应
            
        Returns:
            清理后的JSON字符串
        """
        # 移除代码块标记
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'\s*```$', '', response)
        response = re.sub(r'```.*$', '', response, flags=re.MULTILINE)
        
        # 移除额外的空白字符
        response = response.strip()
        
        # 查找JSON对象的开始和结束
        start_idx = response.find('{')
        if start_idx != -1:
            # 找到最后一个完整的大括号
            brace_count = 0
            end_idx = -1
            for i in range(start_idx, len(response)):
                if response[i] == '{':
                    brace_count += 1
                elif response[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i
                        break
            
            if end_idx != -1:
                response = response[start_idx:end_idx + 1]
        
        return response
    
    def _fix_incomplete_json(self, response: str) -> str:
        """
        尝试修复不完整的JSON响应
        
        Args:
            response: 可能不完整的JSON字符串
            
        Returns:
            修复后的JSON字符串
        """
        try:
            # 先清理响应
            cleaned = self._clean_json_response(response)
            
            # 统计括号和引号的数量
            open_braces = cleaned.count('{')
            close_braces = cleaned.count('}')
            open_brackets = cleaned.count('[')
            close_brackets = cleaned.count(']')
            
            # 修复缺失的结束括号
            while close_braces < open_braces:
                cleaned += '}'
                close_braces += 1
            
            while close_brackets < open_brackets:
                cleaned += ']'
                close_brackets += 1
            
            # 检查字符串是否正确闭合
            lines = cleaned.split('\n')
            fixed_lines = []
            
            for line in lines:
                # 检查是否有未闭合的字符串
                if line.count('"') % 2 == 1:
                    # 奇数个引号，可能缺少结束引号
                    if not line.rstrip().endswith('"') and not line.rstrip().endswith('",'):
                        line = line.rstrip() + '"'
                
                fixed_lines.append(line)
            
            fixed_response = '\n'.join(fixed_lines)
            
            # 确保最后的语法正确
            if not fixed_response.rstrip().endswith('}'):
                fixed_response = fixed_response.rstrip() + '}'
            
            return fixed_response
            
        except Exception as e:
            self.logger.error(f"JSON修复过程中出错: {e}")
            # 如果修复失败，返回一个基本的有效JSON
            return '{"error": "JSON格式修复失败"}'
    
    async def _llm_deletion_analysis(self, deleted_item: Dict[str, Any], document_content: str) -> Dict[str, Any]:
        """使用LLM分析删除项"""
        system_prompt = """你是一个专业的需求文档分析师，请分析文档中提到的删除项，并确认其历史存在性。"""
        
        user_prompt = f"""
【完整文档内容】：
{document_content}

【删除项信息】：
章节: {deleted_item['section']}
删除内容: {deleted_item['deleted_item']}
上下文: {deleted_item['context']}

请结合完整文档内容分析该删除项的合理性，并按照以下格式输出：

{{
    "changeType": "删除",
    "deletedItem": "{deleted_item['deleted_item']}",
    "section": "{deleted_item['section']}",
    "analysisResult": "删除原因和影响分析"
}}
"""
        
        try:
            response = await self._call_llm(user_prompt, system_prompt, max_tokens=12000)
            if response:
                try:
                    # 先清理响应内容
                    cleaned_response = self._clean_json_response(response)
                    analysis_result = json.loads(cleaned_response)
                    return analysis_result
                except json.JSONDecodeError:
                    # 尝试修复JSON格式
                    try:
                        fixed_response = self._fix_incomplete_json(response)
                        analysis_result = json.loads(fixed_response)
                        return analysis_result
                    except:
                        return {
                            "changeType": "删除",
                            "deletedItem": deleted_item['deleted_item'],
                            "section": deleted_item['section'],
                            "analysisResult": response[:200] + "..."
                        }
        except Exception as e:
            self.logger.error(f"LLM删除分析失败: {e}")
        
        return None
    
    async def _extract_detailed_changes(self, change_analysis: Dict[str, Any], document_content: str) -> Dict[str, Any]:
        """
        Step 4: 对变更项从原文档提取详细变更点
        处理整个变更分析结果，为每个变更项提取详细内容
        
        Args:
            change_analysis: Step3的完整分析结果
            document_content: 完整的当前文档内容
            
        Returns:
            增强后的完整变更分析结果，包含详细变更内容
        """
        try:
            enhanced_analysis = change_analysis.copy()
            
            # 处理change_analyses列表
            if 'change_analyses' in change_analysis and change_analysis['change_analyses']:
                enhanced_change_analyses = []
                for analysis in change_analysis['change_analyses']:
                    enhanced_analysis_item = await self._extract_single_change_details(analysis, document_content)
                    enhanced_change_analyses.append(enhanced_analysis_item)
                enhanced_analysis['change_analyses'] = enhanced_change_analyses
            
            # 处理deletion_analyses列表
            if 'deletion_analyses' in change_analysis and change_analysis['deletion_analyses']:
                enhanced_deletion_analyses = []
                for analysis in change_analysis['deletion_analyses']:
                    enhanced_analysis_item = await self._extract_single_change_details(analysis, document_content)
                    enhanced_deletion_analyses.append(enhanced_analysis_item)
                enhanced_analysis['deletion_analyses'] = enhanced_deletion_analyses
            
            # 更新summary信息
            if 'summary' in enhanced_analysis:
                enhanced_analysis['summary']['analysis_method'] = "LLM智能分析+详细内容提取"
            
            return enhanced_analysis
            
        except Exception as e:
            self.logger.error(f"详细变更内容提取失败: {e}")
            # 如果提取失败，返回原始分析结果并添加错误信息
            error_analysis = change_analysis.copy() if change_analysis else {}
            error_analysis['step4_error'] = f"详细内容提取失败: {str(e)}"
            return error_analysis
    
    async def _extract_single_change_details(self, change_analysis: Dict[str, Any], document_content: str) -> Dict[str, Any]:
        """
        对单个变更分析结果提取详细内容
        
        Args:
            change_analysis: 单个变更分析结果
            document_content: 完整的当前文档内容
            
        Returns:
            增强后的单个变更分析结果，包含详细变更内容
        """
        try:
            # 检查分析结果的结构
            if not change_analysis or not isinstance(change_analysis, dict):
                return change_analysis
            
            enhanced_analysis = change_analysis.copy()
            
            # 处理current_change列表（向后兼容）
            if 'current_change' in change_analysis and isinstance(change_analysis['current_change'], list):
                enhanced_changes = []
                
                for change_item in change_analysis['current_change']:
                    enhanced_change = change_item.copy()
                    
                    # 提取changeItems中的变更点详细内容
                    if 'changeItems' in change_item and change_item['changeItems']:
                        change_items = change_item['changeItems']
                        if isinstance(change_items, list):
                            change_items_text = ', '.join(change_items)
                        else:
                            change_items_text = str(change_items)
                        
                        # 使用LLM从原文档中提取详细内容
                        detailed_content = await self._llm_extract_details(change_items_text, document_content, change_item)
                        enhanced_change['changeDetails'] = detailed_content
                    else:
                        enhanced_change['changeDetails'] = "无具体变更项可提取"
                    
                    enhanced_changes.append(enhanced_change)
                
                enhanced_analysis['current_change'] = enhanced_changes
            
            # 处理新格式：直接的变更对象（有changeItems字段）
            elif 'changeItems' in change_analysis and change_analysis['changeItems']:
                change_items = change_analysis['changeItems']
                if isinstance(change_items, list):
                    change_items_text = ', '.join(change_items)
                else:
                    change_items_text = str(change_items)
                
                # 使用LLM从原文档中提取详细内容
                detailed_content = await self._llm_extract_details(change_items_text, document_content, change_analysis)
                enhanced_analysis['changeDetails'] = detailed_content
            
            # 处理其他可能的结构（如删除分析）
            elif 'changeType' in change_analysis:
                deleted_item = change_analysis.get('deletedItem', '')
                if deleted_item:
                    detailed_content = await self._llm_extract_details(deleted_item, document_content, change_analysis)
                    enhanced_analysis['changeDetails'] = detailed_content
                else:
                    enhanced_analysis['changeDetails'] = "无具体删除项可提取"
            
            return enhanced_analysis
            
        except Exception as e:
            self.logger.error(f"单个变更详细内容提取失败: {e}")
            # 如果提取失败，返回原始分析结果并添加错误信息
            enhanced_analysis = change_analysis.copy() if change_analysis else {}
            enhanced_analysis['changeDetails'] = f"详细内容提取失败: {str(e)}"
            return enhanced_analysis
    
    async def _llm_extract_details(self, change_items_text: str, document_content: str, change_context: Dict[str, Any]) -> str:
        """
        使用LLM从原文档中提取变更点的详细内容
        
        Args:
            change_items_text: 变更点文本
            document_content: 完整文档内容
            change_context: 变更上下文信息
            
        Returns:
            提取的详细内容
        """
        system_prompt = """你是一名专业的需求文档分析师，专门负责从需求文档中提取特定变更点的详细内容。

你的任务是：
1. 根据给定的变更点，在完整文档中查找相关的详细需求描述
2. 提取完整的字段定义、业务规则、涉及权限、技术规范等
3. 确保提取的内容具有完整性和准确性
4. 对于复杂变更，提供充分的上下文信息"""

        change_type = change_context.get('changeType', '未知')
        change_reason = change_context.get('changeReason', '')
        
        user_prompt = f"""
【变更类型】：{change_type}
【变更原因】：{change_reason}
【变更点】：{change_items_text}

【完整需求文档】：
{document_content}

请根据上述变更点，从完整需求文档中提取相关的详细内容，包括但不限于：
- 具体的功能描述
- 字段定义和数据结构
- 业务规则和逻辑
- 涉及权限
- 接口规范
- 流程说明
- 约束条件、限制

要求：
1. 提取的内容必须与变更点直接相关
2. 保持内容的完整性，不要截断重要信息
3. 如果涉及多个相关部分，请都包含进来
4. 用清晰的结构组织提取的内容
5. 如果找不到相关内容，请明确说明

请直接返回提取的详细内容，不需要JSON格式。
"""
        
        try:
            response = await self._call_llm(user_prompt, system_prompt, max_tokens=12000)
            if response and response.strip():
                return response.strip()
            else:
                return f"未能从文档中找到变更点「{change_items_text}」的详细内容"
                
        except Exception as e:
            self.logger.error(f"LLM详细内容提取失败: {e}")
            return f"详细内容提取过程中出现错误: {str(e)}"
    
    async def _merge_similar_changes(self, change_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 3.5: 智能合并相似的变更项
        
        Args:
            change_analysis: Step3的变更分析结果
            
        Returns:
            合并后的变更分析结果
        """
        try:
            merged_analysis = change_analysis.copy()
            
            # 处理change_analyses列表
            if 'change_analyses' in change_analysis and change_analysis['change_analyses']:
                original_changes = change_analysis['change_analyses']
                
                # 选择合并策略：可以根据配置选择不同策略
                merge_strategy = "llm_smart"  # 可选: "similarity", "keyword", "llm_smart", "rule_based"
                
                if merge_strategy == "llm_smart":
                    merged_changes = await self._llm_smart_merge(original_changes)
                elif merge_strategy == "similarity":
                    merged_changes = await self._similarity_based_merge(original_changes)
                elif merge_strategy == "keyword":
                    merged_changes = await self._keyword_based_merge(original_changes)
                else:
                    merged_changes = await self._rule_based_merge(original_changes)
                
                merged_analysis['change_analyses'] = merged_changes
                
                # 更新summary
                if 'summary' in merged_analysis:
                    merged_analysis['summary']['total_changes'] = len(merged_changes)
                    merged_analysis['summary']['merge_info'] = {
                        "original_count": len(original_changes),
                        "merged_count": len(merged_changes),
                        "reduction_ratio": round((len(original_changes) - len(merged_changes)) / len(original_changes) * 100, 2) if len(original_changes) > 0 else 0,
                        "strategy": merge_strategy
                    }
            
            return merged_analysis
            
        except Exception as e:
            self.logger.error(f"相似变更项合并失败: {e}")
            return change_analysis
    
    async def _llm_smart_merge(self, changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """方案1: 基于LLM的智能合并"""
        if len(changes) <= 1:
            return changes
        
        system_prompt = """你是一个专业的需求分析师，负责合并相似的变更项。

你的任务：
1. 识别功能相关、主题相似的变更项
2. 将相似的变更项合并成一个更完整的变更项
3. 保持变更项的完整性和准确性
4. 避免信息丢失"""
        
        changes_text = []
        for i, change in enumerate(changes):
            change_info = f"""变更项{i+1}:
- 类型: {change.get('changeType', '未知')}
- 原因: {change.get('changeReason', '未知')}
- 变更点: {change.get('changeItems', [])}
- 版本: {change.get('version', [])}
"""
            changes_text.append(change_info)
        
        user_prompt = f"""
请分析以下变更项，积极主动地将相似和相关的变更点进行合并，并去除重复的变更点所在json对象：

{chr(10).join(changes_text)}

【强制合并规则】：
1. **功能模块相关性合并**：涉及同一个功能模块（如"接口校验"、"链数额度"、"权限管理"等）的变更项必须合并
2. **业务关联性合并**：解决同一个业务问题或需求的变更项必须合并
3. **技术关联性合并**：对同一个技术组件（如API接口、数据库表、前端页面等）的变更项必须合并
4. **变更类型合并**：相同变更类型（新增/修改/删除）且内容相关的变更项应该合并
5. **关键词匹配合并**：变更项中包含相同关键词（如"校验"、"额度"、"接口"、"按钮"等）的变更项优先合并

【合并策略】：
- 优先合并具有多个相似关键词的变更项
- 将小的、分散的变更点整合成大的、完整的变更项
- 每个合并后的变更项应该代表一个完整的业务功能或技术组件的变更
- 目标是将变更项数量减少至少30%以上

【输出要求】：
- 合并后的changeItems应该包含所有原始变更点，按逻辑分组
- 合并后的changeReason应该综合说明所有变更原因，突出共同点
- version字段合并所有相关版本
- mergedFrom字段记录原始变更项编号

请返回JSON格式的合并结果。**必须返回数组格式，即使只有一个合并结果也要用数组包装**：
[
  {{
    "changeType": "合并后的变更类型",
    "changeReason": "合并后的综合变更原因",
    "changeItems": ["合并后的变更点1", "变更点2", ...],
    "version": ["相关版本1", "版本2", ...],
    "mergedFrom": [原始变更项编号列表],
    "mergeReason": "合并原因说明"
  }}
]

**重要提醒：**
1. 必须积极合并相关变更项，不要过于保守！
2. 返回结果必须是JSON数组格式，不要返回单个对象！
3. 即使所有变更项合并为一个，也要用 [{{...}}] 数组格式返回！
"""
        
        try:
            self.logger.info(f"LLM原始输入: {user_prompt}")
            response = await self._call_llm(user_prompt, system_prompt, max_tokens=12000)
            if response:
                self.logger.info(f"LLM原始响应: {response}")
                cleaned_response = self._clean_json_response(response)
                self.logger.info(f"LLM清理后响应: {cleaned_response[:500]}...")
                
                try:
                    merged_changes = json.loads(cleaned_response)
                    self.logger.info(f"JSON解析成功，类型: {type(merged_changes)}, 内容: {merged_changes}")
                except json.JSONDecodeError as json_error:
                    self.logger.error(f"JSON解析失败: {json_error}")
                    self.logger.error(f"尝试解析的内容: {cleaned_response}")
                    return changes
                
                # 处理LLM返回单个对象的情况
                if isinstance(merged_changes, dict):
                    # 如果返回的是单个合并对象，转换为数组
                    if 'changeType' in merged_changes and 'changeItems' in merged_changes:
                        merged_changes = [merged_changes]
                        self.logger.info(f"LLM返回单个合并对象，转换为数组: {merged_changes}")
                    else:
                        self.logger.warning("LLM返回的单个对象格式不正确，使用原始数据")
                        return changes
                
                # 验证合并结果
                if isinstance(merged_changes, list) and len(merged_changes) > 0 and len(merged_changes) <= len(changes):
                    # 验证每个合并项是否包含必要字段
                    valid_changes = []
                    for change in merged_changes:
                        if isinstance(change, dict) and 'changeType' in change and 'changeItems' in change:
                            valid_changes.append(change)
                    
                    if len(valid_changes) > 0:
                        self.logger.info(f"LLM智能合并成功: {len(changes)} -> {len(valid_changes)}")
                        return valid_changes
                    else:
                        self.logger.warning("LLM合并结果格式异常，使用原始数据")
                        return changes
                else:
                    self.logger.warning(f"LLM合并结果数量异常: 原始{len(changes)}项 -> 合并{len(merged_changes) if isinstance(merged_changes, list) else 'N/A'}项，使用原始数据")
                    return changes
        except json.JSONDecodeError as e:
            self.logger.error(f"LLM合并响应JSON解析失败: {e}")
            return changes
        except Exception as e:
            self.logger.error(f"LLM智能合并失败: {e}")
        
        return changes
    
    async def _similarity_based_merge(self, changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """方案2: 基于文本相似度的合并"""
        if len(changes) <= 1:
            return changes
        
        from difflib import SequenceMatcher
        
        merged_changes = []
        used_indices = set()
        
        for i, change in enumerate(changes):
            if i in used_indices:
                continue
                
            similar_group = [change]
            similar_indices = {i}
            
            change_text = f"{change.get('changeReason', '')} {' '.join(change.get('changeItems', []))}"
            
            for j, other_change in enumerate(changes[i+1:], i+1):
                if j in used_indices:
                    continue
                    
                other_text = f"{other_change.get('changeReason', '')} {' '.join(other_change.get('changeItems', []))}"
                similarity = SequenceMatcher(None, change_text, other_text).ratio()
                
                # 相似度阈值
                if similarity > 0.6:
                    similar_group.append(other_change)
                    similar_indices.add(j)
            
            used_indices.update(similar_indices)
            
            if len(similar_group) > 1:
                # 合并相似项
                merged_change = self._merge_change_group(similar_group)
                merged_changes.append(merged_change)
            else:
                merged_changes.append(change)
        
        self.logger.info(f"相似度合并: {len(changes)} -> {len(merged_changes)}")
        return merged_changes
    
    async def _keyword_based_merge(self, changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """方案3: 基于关键词的分组合并"""
        if len(changes) <= 1:
            return changes
        
        # 定义关键词组
        keyword_groups = {
            "数据库相关": ["数据库", "字段", "表", "索引", "查询", "存储"],
            "接口相关": ["接口", "API", "服务", "调用", "请求", "响应"],
            "功能模块": ["功能", "模块", "页面", "按钮", "操作"],
            "权限相关": ["权限", "认证", "授权", "角色", "用户"],
            "业务流程": ["流程", "步骤", "审批", "处理", "业务"]
        }
        
        grouped_changes = {}
        ungrouped_changes = []
        
        for change in changes:
            change_text = f"{change.get('changeReason', '')} {' '.join(change.get('changeItems', []))}"
            grouped = False
            
            for group_name, keywords in keyword_groups.items():
                if any(keyword in change_text for keyword in keywords):
                    if group_name not in grouped_changes:
                        grouped_changes[group_name] = []
                    grouped_changes[group_name].append(change)
                    grouped = True
                    break
            
            if not grouped:
                ungrouped_changes.append(change)
        
        merged_changes = []
        
        # 合并各个关键词组
        for group_name, group_changes in grouped_changes.items():
            if len(group_changes) > 1:
                merged_change = self._merge_change_group(group_changes)
                merged_change['groupType'] = group_name
                merged_changes.append(merged_change)
            else:
                merged_changes.extend(group_changes)
        
        # 添加未分组的变更
        merged_changes.extend(ungrouped_changes)
        
        self.logger.info(f"关键词合并: {len(changes)} -> {len(merged_changes)}")
        return merged_changes
    
    async def _rule_based_merge(self, changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """方案4: 基于规则的模式匹配合并"""
        if len(changes) <= 1:
            return changes
        
        merged_changes = []
        used_indices = set()
        
        # 规则1: 相同changeType的变更项可以考虑合并
        change_type_groups = {}
        for i, change in enumerate(changes):
            change_type = change.get('changeType', '未知')
            if change_type not in change_type_groups:
                change_type_groups[change_type] = []
            change_type_groups[change_type].append((i, change))
        
        for change_type, type_changes in change_type_groups.items():
            if len(type_changes) > 1:
                # 检查是否有共同的关键词
                all_items = []
                for _, change in type_changes:
                    all_items.extend(change.get('changeItems', []))
                
                # 如果有重复的关键词，说明可能相关
                item_text = ' '.join(all_items)
                common_keywords = self._extract_common_keywords(item_text)
                
                if len(common_keywords) > 0:
                    # 合并这组变更
                    group_changes = [change for _, change in type_changes]
                    merged_change = self._merge_change_group(group_changes)
                    merged_changes.append(merged_change)
                    used_indices.update(i for i, _ in type_changes)
                else:
                    # 不合并，分别添加
                    for i, change in type_changes:
                        if i not in used_indices:
                            merged_changes.append(change)
                            used_indices.add(i)
            else:
                i, change = type_changes[0]
                if i not in used_indices:
                    merged_changes.append(change)
                    used_indices.add(i)
        
        self.logger.info(f"规则合并: {len(changes)} -> {len(merged_changes)}")
        return merged_changes
    
    def _merge_change_group(self, changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并一组相似的变更项"""
        if not changes:
            return {}
        
        if len(changes) == 1:
            return changes[0]
        
        # 合并逻辑
        merged_change = {
            "changeType": changes[0].get('changeType', '未知'),
            "changeReason": self._merge_reasons([c.get('changeReason', '') for c in changes]),
            "changeItems": self._merge_items([c.get('changeItems', []) for c in changes]),
            "version": self._merge_versions([c.get('version', []) for c in changes]),
            "mergedCount": len(changes)
        }
        
        return merged_change
    
    def _merge_reasons(self, reasons: List[str]) -> str:
        """合并变更原因"""
        unique_reasons = []
        for reason in reasons:
            if reason and reason not in unique_reasons:
                unique_reasons.append(reason)
        
        if len(unique_reasons) == 1:
            return unique_reasons[0]
        else:
            return f"综合变更原因: {'; '.join(unique_reasons)}"
    
    def _merge_items(self, item_lists: List[List[str]]) -> List[str]:
        """合并变更项，去重但保持逻辑分组"""
        all_items = []
        for items in item_lists:
            all_items.extend(items)
        
        # 简单去重，保持顺序
        unique_items = []
        for item in all_items:
            if item not in unique_items:
                unique_items.append(item)
        
        return unique_items
    
    def _merge_versions(self, version_lists: List[List[str]]) -> List[str]:
        """合并版本信息"""
        all_versions = []
        for versions in version_lists:
            all_versions.extend(versions)
        
        unique_versions = list(set(all_versions))
        return unique_versions
    
    def _extract_common_keywords(self, text: str) -> List[str]:
        """提取常见关键词"""
        import re
        
        # 简单的关键词提取
        words = re.findall(r'[\u4e00-\u9fff]+', text)  # 提取中文词
        word_count = {}
        
        for word in words:
            if len(word) >= 2:  # 只考虑长度大于等于2的词
                word_count[word] = word_count.get(word, 0) + 1
        
        # 返回出现次数大于1的词
        common_keywords = [word for word, count in word_count.items() if count > 1]
        return common_keywords
   