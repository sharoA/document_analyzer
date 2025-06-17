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
            change_analysis = await self._analyze_changes(structured_chunks, history_comparison)
            
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
                "change_analysis": change_analysis,
                "metadata": {
                    "analysis_method": "LLM+向量数据库分析",
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
                             history_comparison: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 3: 大模型变更判断与结构化输出
        
        Args:
            structured_chunks: 结构化内容块
            history_comparison: 历史对比结果
            
        Returns:
            变更分析结果
        """
        change_analyses = []
        
        for comparison in history_comparison['comparisons']:
            if comparison['change_type'] in ['修改', '新增'] and comparison['matched_history']:
                # 对有历史匹配的内容进行详细分析
                analysis = await self._llm_change_analysis(comparison)
                if analysis:
                    change_analyses.append(analysis)
        
        # 对删除项进行分析
        deletion_analyses = []
        for deleted_item in history_comparison['deleted_items']:
            analysis = await self._llm_deletion_analysis(deleted_item)
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
    
    async def _llm_change_analysis(self, comparison: Dict[str, Any]) -> Dict[str, Any]:
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
【当前版本需求内容】：
{current_content}

【历史版本需求内容】：
{history_context}

请仔细分析当前需求与历史需求的差异，按照以下 JSON 格式输出分析结果：

{{
    "current_change": [
        {{
            "changeType": "新增 | 修改 | 删除",
            "changeReason": "详细说明变更的原因和判断依据",
            "changeItems": ["具体变更点1", "具体变更点2", "具体变更点3"],
            "version": {history_files[:1] if history_files else ["无历史版本"]}
        }}
    ]
}}

注意：
- changeItems应该包含具体的功能点变更描述
- changeReason要说明为什么判断为变更类型
- 如果是修改，请明确指出修改前后的差异
"""
        
        try:
            response = await self._call_llm(user_prompt, system_prompt, max_tokens=2000)
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
                            "current_change": [{
                                "changeType": comparison['change_type'],
                                "changeReason": "LLM分析完成，但JSON格式解析失败",
                                "changeItems": [f"LLM原始分析: {response[:300]}{'...' if len(response) > 300 else ''}"],
                                "version": history_files[:1] if history_files else ["无历史版本"]
                            }]
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
    
    async def _llm_deletion_analysis(self, deleted_item: Dict[str, Any]) -> Dict[str, Any]:
        """使用LLM分析删除项"""
        system_prompt = """你是一个专业的需求文档分析师，请分析文档中提到的删除项，并确认其历史存在性。"""
        
        user_prompt = f"""
【删除项信息】：
章节: {deleted_item['section']}
删除内容: {deleted_item['deleted_item']}
上下文: {deleted_item['context']}

请分析该删除项的合理性，并按照以下格式输出：

{{
    "changeType": "删除",
    "deletedItem": "{deleted_item['deleted_item']}",
    "section": "{deleted_item['section']}",
    "analysisResult": "删除原因和影响分析"
}}
"""
        
        try:
            response = await self._call_llm(user_prompt, system_prompt, max_tokens=1000)
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
   