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
            
            # Step 4: 智能合并相似的变更项
            merged_change_analysis = await self._merge_similar_changes(change_analysis)
            
            self.logger.info(f"相似变更项合并完成: {merged_change_analysis}")
            
            # Step 5: 对变更项从原文档提取详细变更点
            enhanced_change_analysis = await self._extract_detailed_changes(merged_change_analysis, document_content)
            
            # Step 6: 对生成的结果进行去重处理，若存在变更详情超过80%的，则进行合并，变更点完全一样的去处重复
            final_change_analysis = await self._deduplicate_and_sort_changes(enhanced_change_analysis)

            self.logger.info(f"去重排序完成: {final_change_analysis}")
            
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
                "change_analysis": final_change_analysis,
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
        清理LLM响应，提取JSON内容（支持数组和对象）
        
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
        
        # 优先查找JSON数组的开始和结束
        array_start = response.find('[')
        object_start = response.find('{')
        
        # 如果同时存在数组和对象，选择最先出现的
        if array_start != -1 and (object_start == -1 or array_start < object_start):
            # 处理JSON数组
            start_idx = array_start
            bracket_count = 0
            brace_count = 0
            end_idx = -1
            
            for i in range(start_idx, len(response)):
                if response[i] == '[':
                    bracket_count += 1
                elif response[i] == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        end_idx = i
                        break
                elif response[i] == '{':
                    brace_count += 1
                elif response[i] == '}':
                    brace_count -= 1
            
            if end_idx != -1:
                response = response[start_idx:end_idx + 1]
        elif object_start != -1:
            # 处理JSON对象
            start_idx = object_start
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
4. 如果在上一步及之前步骤提取的变更详情已经出现过相似内容，当前变更详情不要重复提取
5. 用清晰的结构组织提取的内容
6. 如果找不到相关内容，请明确说明
7. 如果是前端新增项，请将原文档中对应的页面截图路径附上

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
        
        # Step 1: 预处理 - 先修正变更类型
        preprocessed_changes = await self._preprocess_change_types(changes)
        
        system_prompt = """你是一个专业的需求分析师，负责合并相似的变更项。

你的任务：
1. 识别功能相关、主题相似的变更项
2. 将相似的变更项合并成一个更完整的变更项
3. 保持变更项的完整性和准确性
4. 避免信息丢失"""
        
        changes_text = []
        for i, change in enumerate(preprocessed_changes):  # 使用预处理后的数据
            change_info = f"""变更项{i+1}:
- 类型: {change.get('changeType', '未知')}
- 原因: {change.get('changeReason', '未知')}
- 变更点: {change.get('changeItems', [])}
- 版本: {change.get('version', [])}
"""
            changes_text.append(change_info)
        
        user_prompt = f"""
请分析以下变更项，按照变更类型和功能模块进行合理分类合并：

{chr(10).join(changes_text)}

【保守合并原则】：
1. **变更类型严格分离**：不同变更类型（新增/修改/删除）绝对不能合并
2. **功能子模块细分**：即使在同一功能模块内，也要按具体功能子模块进行细分
3. **重要功能保留**：重要的具体功能（如导出、查询、定时任务、筛选等）必须保留，不能被合并掉
4. **避免过度合并**：只有高度相似且重复的变更点才进行合并

【详细合并规则】：
- **接口校验相关**：只合并完全重复描述同一校验规则调整的变更点
- **操作功能相关**：按具体功能细分，如"功能重命名"、"新增按钮"、"新增字段"、"导出功能"、"定时任务"、"权限管理"、"数据升级"等应分别保留
- **页面功能相关**：查询、筛选、导出、汇总等具体功能应该分别保留
- **数据字段相关**：新增字段、字段类型等应该分别保留

【合并策略】：
- 只合并描述完全相同或高度重复的变更点
- 不同具体功能绝对不合并（如导出 ≠ 查询 ≠ 筛选）
- 保持功能的完整性和独立性
- 宁可多分几个变更项，也不要丢失重要功能细节

【输出要求】：
- 保持变更类型的纯粹性，不要混合不同类型
- 保留所有重要的具体功能，避免丢失功能细节
- 如果输入的变更点中包含多个功能，则需要将每个功能单独保留再合并
- changeReason应该说明具体的变更原因，不要过于笼统
- changeItems应该保留具体功能的独立性
- version字段合并相关版本
- mergedFrom字段记录原始变更项编号

请返回JSON格式的合并结果。**按功能子模块细分，保留重要功能细节**：
[
  {{
    "changeType": "具体的变更类型（新增/修改/删除）",
    "changeReason": "变更原因说明（说明为什么这些变更点可以在当前变更类型下",
    "changeItems": ["具体的变更点1", "变更点2", ...],
    "version": ["相关版本1", "版本2", ...],
    "mergedFrom": [原始变更项编号列表],
  }}
]

**重要提醒：**
1. 不同变更类型（新增/修改/删除）绝对不能合并！
2. 去除完全重复描述的变更点，但保留不同具体功能的变更点
3. 重要功能（导出、查询、筛选、汇总等）必须单独保留！
4. 返回结果必须是JSON数组格式！
5. 宁可多保留几个变更项，也不要丢失重要功能细节！
6. 每个结果项应该代表一个具体的功能变更，而不是大而全的合并！
"""
        
        try:
            self.logger.info(f"LLM原始输入: {user_prompt}")
            response = await self._call_llm(user_prompt, system_prompt, max_tokens=12000)
            if response:
                self.logger.info(f"LLM原始响应: {response}")
                cleaned_response = self._clean_json_response(response)
                self.logger.info(f"LLM清理后响应长度: {len(cleaned_response)}")
                self.logger.info(f"LLM清理后响应开头: {cleaned_response[:200]}...")
                if len(cleaned_response) > 500:
                    self.logger.info(f"LLM清理后响应结尾: ...{cleaned_response[-200:]}")
                
                try:
                    merged_changes = json.loads(cleaned_response)
                    self.logger.info(f"JSON解析成功，类型: {type(merged_changes)}, 内容: {merged_changes}")
                except json.JSONDecodeError as json_error:
                    self.logger.error(f"JSON解析失败: {json_error}")
                    self.logger.error(f"尝试解析的内容: {cleaned_response}")
                    return preprocessed_changes
                
                # 处理LLM返回单个对象的情况
                if isinstance(merged_changes, dict):
                    # 如果返回的是单个合并对象，转换为数组
                    if 'changeType' in merged_changes and 'changeItems' in merged_changes:
                        merged_changes = [merged_changes]
                        self.logger.info(f"LLM返回单个合并对象，转换为数组: {merged_changes}")
                    else:
                        self.logger.warning("LLM返回的单个对象格式不正确，使用预处理数据")
                        return preprocessed_changes
                
                # 验证合并结果 - 移除数量限制，允许分拆出更多变更项
                if isinstance(merged_changes, list) and len(merged_changes) > 0:
                    # 验证每个合并项是否包含必要字段
                    valid_changes = []
                    for change in merged_changes:
                        if isinstance(change, dict) and 'changeType' in change and 'changeItems' in change:
                            valid_changes.append(change)
                    
                    if len(valid_changes) > 0:
                        self.logger.info(f"LLM智能合并成功: {len(changes)} -> {len(valid_changes)}")
                        return valid_changes
                    else:
                        self.logger.warning("LLM合并结果格式异常，使用预处理数据")
                        return preprocessed_changes
                else:
                    self.logger.warning(f"LLM合并结果格式异常: 原始{len(changes)}项 -> 合并{len(merged_changes) if isinstance(merged_changes, list) else 'N/A'}项，使用预处理数据")
                    return preprocessed_changes
        except json.JSONDecodeError as e:
            self.logger.error(f"LLM合并响应JSON解析失败: {e}")
            return preprocessed_changes
        except Exception as e:
            self.logger.error(f"LLM智能合并失败: {e}")
        
        return preprocessed_changes
    
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
    
    async def _preprocess_change_types(self, changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        预处理变更类型，正确识别新增、修改、删除类型
        
        Args:
            changes: 原始变更项列表
            
        Returns:
            类型修正后的变更项列表
        """
        preprocessed_changes = []
        
        for change in changes:
            change_items = change.get('changeItems', [])
            
            # 分析变更项的内容，判断实际的变更类型
            new_items = []  # 新增功能项
            modify_items = []  # 修改功能项
            delete_items = []  # 删除功能项
            
            self.logger.info(f"正在分析变更项: {change.get('changeType', '未知')} - {change_items}")
            
            for item in change_items:
                change_type = self._analyze_single_change_item(item)
                
                if change_type == '新增':
                    new_items.append(item)
                elif change_type == '删除':
                    delete_items.append(item)
                else:  # 修改
                    modify_items.append(item)
                
                self.logger.info(f"  变更点分析: '{item[:50]}...' -> {change_type}")
            
            # 创建基础变更信息
            base_change = {
                'changeReason': change.get('changeReason', ''),
                'version': change.get('version', [])
            }
            
            # 根据分析结果创建变更项
            created_changes = []
            
            if new_items:
                new_change = base_change.copy()
                new_change.update({
                    'changeType': '新增',
                    'changeItems': new_items,
                    'changeReason': self._generate_change_reason('新增', base_change['changeReason'], new_items)
                })
                created_changes.append(new_change)
            
            if modify_items:
                modify_change = base_change.copy()
                modify_change.update({
                    'changeType': '修改',
                    'changeItems': modify_items,
                    'changeReason': self._generate_change_reason('修改', base_change['changeReason'], modify_items)
                })
                created_changes.append(modify_change)
            
            if delete_items:
                delete_change = base_change.copy()
                delete_change.update({
                    'changeType': '删除',
                    'changeItems': delete_items,
                    'changeReason': self._generate_change_reason('删除', base_change['changeReason'], delete_items)
                })
                created_changes.append(delete_change)
            
            # 如果没有任何变更项被归类，保留原变更项
            if not created_changes:
                original_change = change.copy()
                original_change['changeType'] = '修改'  # 默认为修改
                created_changes.append(original_change)
            
            preprocessed_changes.extend(created_changes)
            
            self.logger.info(f"  变更项拆分结果: 1 -> {len(created_changes)} 项")
        
        self.logger.info(f"变更类型预处理完成: {len(changes)} -> {len(preprocessed_changes)}")
        for i, change in enumerate(preprocessed_changes):
            self.logger.info(f"预处理后变更项{i+1}: {change.get('changeType')} - 包含{len(change.get('changeItems', []))}个变更点")
        
        return preprocessed_changes
    
    def _analyze_single_change_item(self, item: str) -> str:
        """
        分析单个变更项的类型
        
        Args:
            item: 单个变更描述
            
        Returns:
            变更类型: '新增', '修改', '删除'
        """
        item_text = item.strip()
        
        # 定义更精确的关键词匹配规则
        new_keywords = [
            '新增', '新建', '添加', '增加', '创建', '引入', 
            '支持', '提供', '实现', '设置',
            '新增功能', '新增按钮', '新增字段', '新增页面',
            '列表页', '详情页'  # 通常指新增页面
        ]
        
        delete_keywords = [
            '删除', '移除', '去除', '取消', '废弃', '停用',
            '不再', '禁用', '隐藏'
        ]
        
        modify_keywords = [
            '调整', '修改', '变更', '优化', '更新', '改为',
            '由.*变更为', '从.*调整为', '将.*修改为',
            '名称.*变更', '功能.*调整'
        ]
        
        # 优先级检查：先检查明确的新增标识
        for keyword in new_keywords:
            if keyword in item_text:
                # 进一步验证是否真的是新增
                if any(exclude in item_text for exclude in ['调整', '修改', '变更为', '改为']):
                    # 如果同时包含修改关键词，可能是修改现有功能
                    continue
                return '新增'
        
        # 检查删除关键词
        for keyword in delete_keywords:
            if keyword in item_text:
                return '删除'
        
        # 检查修改关键词
        import re
        for keyword in modify_keywords:
            if re.search(keyword, item_text):
                return '修改'
        
        # 特殊情况处理
        # 1. 功能名称变更通常是修改
        if re.search(r'名称.*(?:由|从).+(?:变更为|改为|调整为)', item_text):
            return '修改'
        
        # 2. 包含"新增"但也包含"在...下"可能是在现有功能下新增子功能
        if '新增' in item_text and any(phrase in item_text for phrase in ['在.*下', '功能下', '页面.*新增']):
            return '新增'
        
        # 3. 按钮、字段、页面相关的描述
        if any(element in item_text for element in ['按钮', '字段', '页面', '功能', '接口', '列表']):
            # 如果明确说是新增这些元素
            if any(action in item_text for action in ['新增', '添加', '创建']):
                return '新增'
            # 如果是调整现有元素
            elif any(action in item_text for action in ['调整', '修改', '变更', '优化']):
                return '修改'
        
        # 默认归类为修改（保守策略）
        return '修改'
    
    def _generate_change_reason(self, change_type: str, original_reason: str, items: List[str]) -> str:
        """
        生成更精确的变更原因
        
        Args:
            change_type: 变更类型
            original_reason: 原始变更原因
            items: 变更项列表
            
        Returns:
            生成的变更原因
        """
        # 简化处理：直接基于变更类型和数量生成通用描述
        if len(items) == 1:
            return f"{change_type}相关功能"
        else:
            return f"{change_type}多项相关功能"
    
    async def _deduplicate_and_sort_changes(self, change_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 6: 对变更分析结果进行去重和排序
        
        Args:
            change_analysis: Step5的变更分析结果
            
        Returns:
            去重排序后的变更分析结果
        """
        try:
            result = change_analysis.copy()
            
            # 处理change_analyses列表
            if 'change_analyses' in change_analysis and change_analysis['change_analyses']:
                # Step 1: 传统去重
                traditional_deduplicated = self._deduplicate_changes(change_analysis['change_analyses'])
                
                # Step 2: 大模型智能去重（识别不同变更模块中的相同功能）
                llm_deduplicated = await self._llm_intelligent_deduplicate(traditional_deduplicated)
                
                # Step 3: 排序
                sorted_changes = self._sort_changes(llm_deduplicated)
                result['change_analyses'] = sorted_changes
                
                self.logger.info(f"change_analyses智能去重排序: {len(change_analysis['change_analyses'])} -> {len(traditional_deduplicated)} -> {len(llm_deduplicated)} -> {len(sorted_changes)}")
            
            # 处理deletion_analyses列表
            if 'deletion_analyses' in change_analysis and change_analysis['deletion_analyses']:
                # Step 1: 传统去重
                traditional_deduplicated = self._deduplicate_changes(change_analysis['deletion_analyses'])
                
                # Step 2: 大模型智能去重
                llm_deduplicated = await self._llm_intelligent_deduplicate(traditional_deduplicated)
                
                # Step 3: 排序
                sorted_deletions = self._sort_changes(llm_deduplicated)
                result['deletion_analyses'] = sorted_deletions
                
                self.logger.info(f"deletion_analyses智能去重排序: {len(change_analysis['deletion_analyses'])} -> {len(traditional_deduplicated)} -> {len(llm_deduplicated)} -> {len(sorted_deletions)}")
            
            # 更新summary信息
            if 'summary' in result:
                result['summary']['analysis_method'] = "LLM+向量数据库分析+详细内容提取+智能合并+大模型智能去重+排序"
            
            # 添加去重元数据
            if 'metadata' not in result:
                result['metadata'] = {}
            result['metadata']['deduplication_applied'] = True
            result['metadata']['llm_deduplication_applied'] = True
            result['metadata']['deduplication_timestamp'] = time.time()
            
            return result
            
        except Exception as e:
            self.logger.error(f"去重排序失败: {e}")
            return change_analysis
    
    def _deduplicate_changes(self, changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        对变更项进行去重处理
        
        Args:
            changes: 变更项列表
            
        Returns:
            去重后的变更项列表
        """
        if len(changes) <= 1:
            return changes
        
        deduplicated = []
        used_indices = set()
        
        for i, change in enumerate(changes):
            if i in used_indices:
                continue
            
            # 查找相似的变更项
            similar_changes = [change]
            similar_indices = {i}
            
            for j, other_change in enumerate(changes[i+1:], i+1):
                if j in used_indices:
                    continue
                
                # 检查是否需要合并
                if self._should_merge_changes(change, other_change):
                    similar_changes.append(other_change)
                    similar_indices.add(j)
            
            used_indices.update(similar_indices)
            
            # 如果找到相似项，进行合并
            if len(similar_changes) > 1:
                merged_change = self._merge_similar_change_details(similar_changes)
                deduplicated.append(merged_change)
                self.logger.info(f"合并了 {len(similar_changes)} 个相似变更项")
            else:
                deduplicated.append(change)
        
        return deduplicated
    
    def _should_merge_changes(self, change1: Dict[str, Any], change2: Dict[str, Any]) -> bool:
        """
        判断两个变更项是否应该合并
        
        Args:
            change1: 变更项1
            change2: 变更项2
            
        Returns:
            是否应该合并
        """
        # 1. 变更类型必须相同
        if change1.get('changeType') != change2.get('changeType'):
            return False
        
        # 2. 检查变更点是否完全相同（去重）
        items1 = set(change1.get('changeItems', []))
        items2 = set(change2.get('changeItems', []))
        
        # 如果变更点完全相同，应该合并
        if items1 == items2:
            return True
        
        # 3. 检查变更点之间的高相似度（针对意思相同但表述略有不同的情况）
        items1_list = change1.get('changeItems', [])
        items2_list = change2.get('changeItems', [])
        
        # 如果两个变更项都只有一个changeItem，且高度相似，则合并
        if len(items1_list) == 1 and len(items2_list) == 1:
            item_similarity = self._calculate_text_similarity(items1_list[0], items2_list[0])
            if item_similarity >= 0.85:  # 85%相似度阈值，针对意思相同但表述略有不同的情况
                self.logger.info(f"发现高相似度变更点 (相似度: {item_similarity:.2f}): '{items1_list[0][:50]}...' vs '{items2_list[0][:50]}...'")
                return True
        
        # 4. 检查变更点列表的整体相似度
        if items1_list and items2_list:
            # 计算变更点列表的文本相似度
            text1 = ' '.join(items1_list)
            text2 = ' '.join(items2_list)
            items_similarity = self._calculate_text_similarity(text1, text2)
            if items_similarity >= 0.8:  # 80%相似度阈值
                self.logger.info(f"发现高相似度变更点列表 (相似度: {items_similarity:.2f})")
                return True
        
        # 5. 检查变更详情相似度（如果有changeDetails字段）
        details1 = change1.get('changeDetails', '')
        details2 = change2.get('changeDetails', '')
        
        if details1 and details2:
            similarity = self._calculate_text_similarity(details1, details2)
            if similarity >= 0.8:  # 80%相似度阈值
                self.logger.info(f"发现高相似度变更详情 (相似度: {similarity:.2f})")
                return True
        
        # 6. 检查变更原因相似度
        reason1 = change1.get('changeReason', '')
        reason2 = change2.get('changeReason', '')
        
        if reason1 and reason2:
            reason_similarity = self._calculate_text_similarity(reason1, reason2)
            if reason_similarity >= 0.9:  # 变更原因90%相似
                return True
        
        return False
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的相似度（针对中文文本优化）
        
        Args:
            text1: 文本1
            text2: 文本2
            
        Returns:
            相似度 (0-1)
        """
        from difflib import SequenceMatcher
        import re
        
        # 如果文本为空，返回0
        if not text1 or not text2:
            return 0.0
        
        # 去除多余空格和标点符号，保留核心内容
        clean_text1 = re.sub(r'[，。、；：！？\s]+', '', text1.strip())
        clean_text2 = re.sub(r'[，。、；：！？\s]+', '', text2.strip())
        
        # 方法1: 基础字符序列相似度
        basic_similarity = SequenceMatcher(None, clean_text1, clean_text2).ratio()
        
        # 方法2: 关键词匹配相似度（针对业务术语）
        # 提取关键业务词汇
        keywords1 = self._extract_business_keywords(text1)
        keywords2 = self._extract_business_keywords(text2)
        
        if keywords1 and keywords2:
            common_keywords = len(set(keywords1) & set(keywords2))
            total_keywords = len(set(keywords1) | set(keywords2))
            keyword_similarity = common_keywords / total_keywords if total_keywords > 0 else 0.0
        else:
            keyword_similarity = 0.0
        
        # 方法3: 语义相似度（检查核心概念）
        semantic_similarity = self._check_semantic_similarity(text1, text2)
        
        # 综合相似度计算（权重分配）
        final_similarity = (
            basic_similarity * 0.5 +      # 基础字符相似度权重50%
            keyword_similarity * 0.3 +    # 关键词相似度权重30%
            semantic_similarity * 0.2     # 语义相似度权重20%
        )
        
        self.logger.debug(f"相似度计算: 基础={basic_similarity:.3f}, 关键词={keyword_similarity:.3f}, 语义={semantic_similarity:.3f}, 综合={final_similarity:.3f}")
        
        return final_similarity
    
    def _extract_business_keywords(self, text: str) -> List[str]:
        """
        提取业务关键词
        
        Args:
            text: 输入文本
            
        Returns:
            关键词列表
        """
        import re
        
        # 定义业务关键词模式
        business_patterns = [
            r'确权业务申请',
            r'bizSerialNo',
            r'校验规则',
            r'业务编号',
            r'核心企业',
            r'内部系统',
            r'修改',
            r'推送',
            r'相同',
            r'允许',
            r'数据',
            r'接口',
            r'调整'
        ]
        
        keywords = []
        for pattern in business_patterns:
            if re.search(pattern, text):
                keywords.append(pattern)
        
        # 提取其他中文关键词（2-6个字符）
        chinese_words = re.findall(r'[\u4e00-\u9fff]{2,6}', text)
        keywords.extend(chinese_words)
        
        return list(set(keywords))  # 去重
    
    async def _llm_intelligent_deduplicate(self, changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        使用大模型进行智能去重，识别不同变更模块中的相同功能
        
        Args:
            changes: 已经过传统去重的变更项列表
            
        Returns:
            经过大模型智能去重的变更项列表
        """
        if len(changes) <= 1:
            return changes
        
        try:
            # 构建变更项摘要供大模型分析
            change_summaries = []
            for i, change in enumerate(changes):
                summary = {
                    'index': i,
                    'changeType': change.get('changeType', '未知'),
                    'changeReason': change.get('changeReason', ''),
                    'changeItems': change.get('changeItems', []),
                    'changeDetails': change.get('changeDetails', '')
                }
                change_summaries.append(summary)
            
            # 构建大模型提示词
            prompt = f"""
你是一个专业的文档变更分析专家。现在需要你分析以下{len(changes)}个变更项，识别其中功能相同但表述不同的项目并进行去重合并。

分析原则：
1. 识别语义相同但表述不同的变更项（如："调整了确权业务申请接口中关于bizSerialNo的校验规则，允许相同业务编号的数据在核心企业内部系统修改后重新推送" 和 "调整了确权业务申请接口中关于bizSerialNo的校验规则，允许相同业务编号的数据在核心企业内部系统修改后再次推送"）
2. 只有变更类型相同的项目才能合并
3. 合并时保留最完整、最准确的描述
4. 如果变更项描述的是不同的功能点，即使表述相似也不要合并

变更项列表：
{json.dumps(change_summaries, ensure_ascii=False, indent=2)}

请分析这些变更项，返回JSON格式的去重结果：
{{
  "merged_groups": [
    {{
      "merge_indices": [0, 3],  // 需要合并的变更项索引
      "reason": "这两个变更项都是关于同一个接口的相同校验规则调整，只是表述略有不同",
      "merged_changeReason": "合并后的变更原因",
      "merged_changeItems": ["合并后的变更点1", "合并后的变更点2"],
      "merged_changeDetails": "合并后的变更详情"
    }}
  ],
  "keep_separate": [1, 2, 4]  // 保持独立的变更项索引
}}

如果没有需要合并的项目，返回：
{{
  "merged_groups": [],
  "keep_separate": [0, 1, 2, ...]  // 所有索引
}}
"""

            # 调用大模型
            response = self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}], 
                temperature=0.1
            )  # 使用较低温度以获得更稳定的结果
            
            if not response:
                self.logger.warning("大模型智能去重失败，返回原始结果")
                return changes
            
            # 解析大模型响应
            response_text = response.strip()
            cleaned_response = self._clean_json_response(response_text)
            
            try:
                dedup_result = json.loads(cleaned_response)
            except json.JSONDecodeError as e:
                self.logger.error(f"大模型去重响应解析失败: {e}")
                return changes
            
            # 应用去重结果
            final_changes = []
            processed_indices = set()
            
            # 处理合并组
            for merge_group in dedup_result.get('merged_groups', []):
                merge_indices = merge_group.get('merge_indices', [])
                if len(merge_indices) < 2:
                    continue
                
                # 获取要合并的变更项
                changes_to_merge = [changes[i] for i in merge_indices if i < len(changes)]
                
                if changes_to_merge:
                    # 创建合并后的变更项
                    merged_change = self._create_llm_merged_change(changes_to_merge, merge_group)
                    final_changes.append(merged_change)
                    processed_indices.update(merge_indices)
                    
                    self.logger.info(f"大模型智能合并变更项 {merge_indices}: {merge_group.get('reason', '未知原因')}")
            
            # 添加保持独立的变更项
            for i, change in enumerate(changes):
                if i not in processed_indices:
                    final_changes.append(change)
            
            self.logger.info(f"大模型智能去重完成: {len(changes)} -> {len(final_changes)}")
            return final_changes
            
        except Exception as e:
            self.logger.error(f"大模型智能去重失败: {e}")
            return changes
    
    def _create_llm_merged_change(self, changes_to_merge: List[Dict[str, Any]], merge_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据大模型的合并建议创建合并后的变更项
        
        Args:
            changes_to_merge: 要合并的变更项列表
            merge_info: 大模型提供的合并信息
            
        Returns:
            合并后的变更项
        """
        base_change = changes_to_merge[0].copy()
        
        # 使用大模型建议的合并结果，如果没有则使用传统合并方法
        if 'merged_changeReason' in merge_info:
            base_change['changeReason'] = merge_info['merged_changeReason']
        
        if 'merged_changeItems' in merge_info:
            base_change['changeItems'] = merge_info['merged_changeItems']
        else:
            # 合并所有变更点
            all_items = []
            for change in changes_to_merge:
                all_items.extend(change.get('changeItems', []))
            base_change['changeItems'] = self._intelligent_dedup_items(all_items)
        
        if 'merged_changeDetails' in merge_info:
            base_change['changeDetails'] = merge_info['merged_changeDetails']
        else:
            # 选择最长的变更详情
            details_list = [change.get('changeDetails', '') for change in changes_to_merge]
            base_change['changeDetails'] = max(details_list, key=len) if details_list else ''
        
        # 合并版本信息
        all_versions = []
        for change in changes_to_merge:
            all_versions.extend(change.get('version', []))
        base_change['version'] = list(set(all_versions))
        
        # 添加合并信息
        base_change['mergedFrom'] = [
            f"变更项{i+1}" for i in range(len(changes_to_merge))
        ]
        base_change['mergeReason'] = merge_info.get('reason', '大模型智能合并')
        base_change['mergeMethod'] = 'llm_intelligent'
        base_change['mergedCount'] = len(changes_to_merge)
        
        return base_change
    
    def _check_semantic_similarity(self, text1: str, text2: str) -> float:
        """
        检查语义相似度
        
        Args:
            text1: 文本1
            text2: 文本2
            
        Returns:
            语义相似度 (0-1)
        """
        # 定义语义等价词组
        semantic_groups = [
            {'重新推送', '再次推送', '重推', '再推'},
            {'修改后', '修改后的', '修改之后'},
            {'允许', '支持', '可以'},
            {'相同', '同样', '相同的', '同一'},
            {'业务编号', '业务号', 'bizSerialNo'},
            {'校验规则', '验证规则', '校验'},
            {'核心企业内部系统', '核心企业系统', '内部系统'},
            {'调整了', '修改了', '变更了', '更新了'}
        ]
        
        # 检查两个文本是否包含语义等价的词组
        semantic_score = 0.0
        total_checks = 0
        
        for group in semantic_groups:
            found_in_text1 = any(word in text1 for word in group)
            found_in_text2 = any(word in text2 for word in group)
            
            if found_in_text1 or found_in_text2:
                total_checks += 1
                if found_in_text1 and found_in_text2:
                    semantic_score += 1.0
        
        return semantic_score / total_checks if total_checks > 0 else 0.0
    
    def _merge_similar_change_details(self, changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        合并相似的变更项详情
        
        Args:
            changes: 相似的变更项列表
            
        Returns:
            合并后的变更项
        """
        if len(changes) == 1:
            return changes[0]
        
        base_change = changes[0].copy()
        
        # 记录详细的合并信息用于调试
        self.logger.info(f"开始合并 {len(changes)} 个相似变更项:")
        for i, change in enumerate(changes):
            items = change.get('changeItems', [])
            self.logger.info(f"  变更项{i+1}: {change.get('changeType', '未知')} - {items}")
        
        # 合并变更点（去重但保留相似表述）
        all_items = []
        for change in changes:
            all_items.extend(change.get('changeItems', []))
        
        # 智能去重：保留最详细的表述
        unique_items = self._intelligent_dedup_items(all_items)
        base_change['changeItems'] = unique_items
        
        self.logger.info(f"  合并后变更点: {unique_items}")
        
        # 合并版本信息
        all_versions = []
        for change in changes:
            all_versions.extend(change.get('version', []))
        base_change['version'] = list(set(all_versions))
        
        # 合并mergedFrom信息（如果存在）
        all_merged_from = []
        for change in changes:
            if 'mergedFrom' in change:
                if isinstance(change['mergedFrom'], list):
                    all_merged_from.extend(change['mergedFrom'])
                else:
                    all_merged_from.append(change['mergedFrom'])
        if all_merged_from:
            base_change['mergedFrom'] = list(set(all_merged_from))
        
        # 合并变更详情（选择最长的或合并多个）
        all_details = []
        for change in changes:
            if 'changeDetails' in change and change['changeDetails']:
                all_details.append(change['changeDetails'])
        
        if len(all_details) > 1:
            # 如果有多个详情，选择最详细的一个
            base_change['changeDetails'] = max(all_details, key=len)
        elif len(all_details) == 1:
            base_change['changeDetails'] = all_details[0]
        
        # 添加合并标记
        base_change['mergedChangesCount'] = len(changes)
        base_change['originalItems'] = [change.get('changeItems', []) for change in changes]  # 保留原始信息用于调试
        
        self.logger.info(f"变更项合并完成: {len(changes)} -> 1")
        
        return base_change
    
    def _intelligent_dedup_items(self, items: List[str]) -> List[str]:
        """
        智能去重变更点，保留最详细的表述
        
        Args:
            items: 变更点列表
            
        Returns:
            去重后的变更点列表
        """
        if len(items) <= 1:
            return items
        
        unique_items = []
        used_indices = set()
        
        for i, item in enumerate(items):
            if i in used_indices:
                continue
            
            # 查找相似的项
            similar_group = [item]
            similar_indices = {i}
            
            for j, other_item in enumerate(items[i+1:], i+1):
                if j in used_indices:
                    continue
                
                similarity = self._calculate_text_similarity(item, other_item)
                if similarity >= 0.85:  # 高相似度阈值
                    similar_group.append(other_item)
                    similar_indices.add(j)
                    self.logger.info(f"发现相似变更点 (相似度: {similarity:.2f}): '{item[:30]}...' vs '{other_item[:30]}...'")
            
            used_indices.update(similar_indices)
            
            if len(similar_group) > 1:
                # 选择最详细的表述（通常是最长的）
                best_item = max(similar_group, key=len)
                unique_items.append(best_item)
                self.logger.info(f"相似变更点合并: 选择 '{best_item[:50]}...' 作为代表")
            else:
                unique_items.append(item)
        
        return unique_items
    
    def _sort_changes(self, changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        对变更项进行排序
        
        Args:
            changes: 变更项列表
            
        Returns:
            排序后的变更项列表
        """
        def sort_key(change):
            # 按照变更类型、变更原因、变更点数量、版本数量进行排序
            change_type = change.get('changeType', '')
            change_reason = change.get('changeReason', '')
            items_count = len(change.get('changeItems', []))
            version_count = len(change.get('version', []))
            
            # 变更类型排序：新增 -> 修改 -> 删除
            type_order = {'新增': 1, '修改': 2, '删除': 3}
            type_priority = type_order.get(change_type, 4)
            
            return (type_priority, change_reason, -items_count, -version_count)
        
        return sorted(changes, key=sort_key)
   