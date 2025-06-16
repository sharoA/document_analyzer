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
            
            self._log_analysis_start(task_id, "内容分析", len(document_content))
            
            # Step 1: 文档预处理
            structured_chunks = await self._preprocess_document(document_content)
            
            # Step 2: 与历史知识库内容对比
            history_comparison = await self._compare_with_history(structured_chunks)
            
            # Step 3: 大模型变更判断与结构化输出
            change_analysis = await self._analyze_changes(structured_chunks, history_comparison)
            
            # 合并分析结果
            content_result = {
                "structured_chunks": structured_chunks,
                "history_comparison": history_comparison,
                "change_analysis": change_analysis,
                "metadata": {
                    "analysis_method": "LLM+向量数据库分析",
                    "analysis_time": time.time() - start_time,
                    "content_length": len(document_content),
                    "chunks_count": len(structured_chunks)
                }
            }
            
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
            历史对比结果
        """
        comparison_results = []
        deleted_items = []
        
        # Step 2-A: 历史内容匹配与相似度判断
        for chunk in structured_chunks:
            similar_history = await self._find_similar_history(chunk)
            
            if similar_history:
                max_similarity = max(item['similarity'] for item in similar_history)
                if max_similarity >= 0.4:  # 相似度阈值
                    comparison_results.append({
                        "current_chunk": chunk,
                        "matched_history": similar_history,
                        "change_type": "修改" if max_similarity < 0.9 else "相同",
                        "max_similarity": max_similarity
                    })
                else:
                    comparison_results.append({
                        "current_chunk": chunk,
                        "matched_history": [],
                        "change_type": "新增",
                        "max_similarity": max_similarity
                    })
            else:
                comparison_results.append({
                    "current_chunk": chunk,
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
                "deleted_items": len(deleted_items)
            }
        }
    
    async def _find_similar_history(self, chunk: Dict[str, Any], top_k: int = 5) -> List[Dict[str, Any]]:
        """在历史知识库中查找相似内容"""
        try:
            collection = self.weaviate_client.collections.get("AnalyDesignDocuments")
            
            # 使用向量搜索 - 需要处理向量格式差异
            query_vector = chunk['embedding']  # 384维向量
            
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
                    
                    if sample_dim == 768 and len(query_vector) == 384:
                        # 维度不匹配，跳过向量搜索，使用关键词搜索替代
                        self.logger.warning("向量维度不匹配，跳过向量搜索")
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
        
        if comparison['matched_history']:
            history_content = comparison['matched_history'][0]['content']
            history_title = comparison['matched_history'][0]['title']
            history_file = comparison['matched_history'][0]['file_path']
        else:
            history_content = ""
            history_title = ""
            history_file = ""
        
        system_prompt = """你是一个专业的需求文档分析师，请分析当前版本与历史版本内容的差异，并按照指定格式输出结果。"""
        
        user_prompt = f"""
【当前版本内容】：
{current_content}

【历史版本内容】：
标题: {history_title}
文件: {history_file}
内容: {history_content}

请按照以下 JSON 格式输出分析结果：

{{
    "current_change": [
        {{
            "changeType": "新增 | 修改 | 删除",
            "changeReason": "简要说明判断依据",
            "changeItems": ["变更点1", "变更点2"],
            "version": ["{history_file}"]
        }}
    ]
}}
"""
        
        try:
            response = await self._call_llm(user_prompt, system_prompt, max_tokens=2000)
            if response:
                # 尝试解析JSON响应
                try:
                    analysis_result = json.loads(response)
                    return analysis_result
                except json.JSONDecodeError:
                    # 如果JSON解析失败，返回原始响应
                    return {
                        "current_change": [{
                            "changeType": comparison['change_type'],
                            "changeReason": "LLM分析结果解析失败",
                            "changeItems": [response[:200] + "..."],
                            "version": [history_file]
                        }]
                    }
        except Exception as e:
            self.logger.error(f"LLM变更分析失败: {e}")
        
        return None
    
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
                    analysis_result = json.loads(response)
                    return analysis_result
                except json.JSONDecodeError:
                    return {
                        "changeType": "删除",
                        "deletedItem": deleted_item['deleted_item'],
                        "section": deleted_item['section'],
                        "analysisResult": response[:200] + "..."
                    }
        except Exception as e:
            self.logger.error(f"LLM删除分析失败: {e}")
        
        return None
   