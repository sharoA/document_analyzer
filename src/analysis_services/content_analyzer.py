"""
内容分析服务
使用大模型和向量数据库进行CRUD操作分析和业务需求识别
"""

import json
import time
import re
from typing import Dict, Any, List
from .base_service import BaseAnalysisService

class ContentAnalyzerService(BaseAnalysisService):
    """内容分析服务类"""
    
    async def analyze(self, task_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行内容分析
        
        Args:
            task_id: 任务ID
            input_data: 包含文档解析结果的数据
            
        Returns:
            内容分析结果字典
        """
        start_time = time.time()
        
        try:
            # 提取解析结果
            parsing_result = input_data.get("parsing_result", {})
            document_content = input_data.get("document_content", "")
            
            self._log_analysis_start(task_id, "内容分析", len(document_content))
            
            # 基础内容分析
            basic_analysis = await self._basic_content_analysis(parsing_result, document_content)
            
            # CRUD操作识别
            crud_analysis = await self._crud_operation_analysis(document_content, parsing_result)
            
            # 向量数据库相似性分析
            similarity_analysis = await self._vector_similarity_analysis(document_content)
            
            # 业务需求分析
            business_analysis = await self._business_requirement_analysis(document_content, parsing_result)
            
            # 技术复杂度评估
            complexity_analysis = await self._complexity_assessment(crud_analysis, business_analysis)
            
            # 合并分析结果
            content_result = {
                "basic_analysis": basic_analysis,
                "crud_analysis": crud_analysis,
                "similarity_analysis": similarity_analysis,
                "business_analysis": business_analysis,
                "complexity_analysis": complexity_analysis,
                "metadata": {
                    "analysis_method": "LLM+向量数据库分析",
                    "analysis_time": time.time() - start_time,
                    "content_length": len(document_content)
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
    
    async def _basic_content_analysis(self, parsing_result: Dict[str, Any], content: str) -> Dict[str, Any]:
        """基础内容分析"""
        basic_info = parsing_result.get("basic_info", {})
        llm_analysis = parsing_result.get("llm_analysis", {})
        
        return {
            "content_type": llm_analysis.get("document_type", "未知"),
            "language": basic_info.get("language", "未知"),
            "word_count": basic_info.get("word_count", 0),
            "character_count": basic_info.get("character_count", 0),
            "summary": llm_analysis.get("summary", ""),
            "key_points": llm_analysis.get("key_points", []),
            "structure_analysis": llm_analysis.get("structure", {}),
            "entities": llm_analysis.get("entities", {})
        }
    
    async def _crud_operation_analysis(self, content: str, parsing_result: Dict[str, Any]) -> Dict[str, Any]:
        """CRUD操作分析"""
        # 使用大模型进行CRUD操作识别
        system_prompt = """你是一个专业的业务分析师，专门识别文档中的CRUD操作需求。

请分析文档内容，识别所有可能的数据操作需求：
1. Create（创建）：新增、添加、创建、注册等操作
2. Read（查询）：查看、搜索、获取、列表、详情等操作  
3. Update（更新）：修改、编辑、更新、变更等操作
4. Delete（删除）：删除、移除、取消等操作

对每个识别的操作，请提供：
- 操作类型（C/R/U/D）
- 操作对象（数据实体）
- 操作描述
- 业务场景
- 复杂度评估（简单/中等/复杂）

返回JSON格式：
{
    "crud_operations": [
        {
            "type": "Create/Read/Update/Delete",
            "entity": "数据实体名称",
            "description": "操作描述",
            "scenario": "业务场景",
            "complexity": "简单/中等/复杂",
            "keywords": ["关键词1", "关键词2"]
        }
    ],
    "summary": {
        "total_operations": 数量,
        "create_count": 数量,
        "read_count": 数量,
        "update_count": 数量,
        "delete_count": 数量
    }
}"""
        
        user_prompt = f"""请分析以下文档内容，识别其中的CRUD操作需求：

文档内容：
{content[:2000]}

请按照指定的JSON格式返回分析结果。"""
        
        try:
            response = await self._call_llm(user_prompt, system_prompt, max_tokens=2000)
            if response:
                try:
                    crud_result = json.loads(response)
                    # 添加关键词匹配验证
                    crud_result["keyword_validation"] = self._validate_crud_keywords(content)
                    return crud_result
                except json.JSONDecodeError:
                    # 如果JSON解析失败，使用关键词匹配作为备选
                    return self._fallback_crud_analysis(content)
            else:
                return self._fallback_crud_analysis(content)
        except Exception as e:
            self.logger.error(f"CRUD分析失败: {str(e)}")
            return self._fallback_crud_analysis(content)
    
    def _validate_crud_keywords(self, content: str) -> Dict[str, List[str]]:
        """验证CRUD关键词"""
        crud_keywords = {
            "create": ["创建", "新增", "添加", "注册", "建立", "生成", "create", "add", "insert", "register"],
            "read": ["查询", "查看", "搜索", "获取", "列表", "详情", "read", "get", "search", "list", "view"],
            "update": ["修改", "编辑", "更新", "变更", "调整", "update", "edit", "modify", "change"],
            "delete": ["删除", "移除", "取消", "清除", "delete", "remove", "cancel", "clear"]
        }
        
        found_keywords = {}
        content_lower = content.lower()
        
        for operation, keywords in crud_keywords.items():
            found = []
            for keyword in keywords:
                if keyword in content_lower:
                    found.append(keyword)
            if found:
                found_keywords[operation] = found
        
        return found_keywords
    
    def _fallback_crud_analysis(self, content: str) -> Dict[str, Any]:
        """备选CRUD分析方法"""
        keyword_validation = self._validate_crud_keywords(content)
        
        crud_operations = []
        for operation, keywords in keyword_validation.items():
            for keyword in keywords:
                crud_operations.append({
                    "type": operation.capitalize(),
                    "entity": "未指定",
                    "description": f"检测到{operation}操作关键词: {keyword}",
                    "scenario": "基于关键词匹配",
                    "complexity": "中等",
                    "keywords": [keyword]
                })
        
        return {
            "crud_operations": crud_operations,
            "summary": {
                "total_operations": len(crud_operations),
                "create_count": len(keyword_validation.get("create", [])),
                "read_count": len(keyword_validation.get("read", [])),
                "update_count": len(keyword_validation.get("update", [])),
                "delete_count": len(keyword_validation.get("delete", []))
            },
            "keyword_validation": keyword_validation,
            "analysis_method": "关键词匹配"
        }
    
    async def _vector_similarity_analysis(self, content: str) -> Dict[str, Any]:
        """向量数据库相似性分析"""
        try:
            # 提取关键句子进行向量搜索
            sentences = self._extract_key_sentences(content)
            similarity_results = []
            
            for sentence in sentences[:5]:  # 限制搜索数量
                similar_docs = await self._vector_search(sentence, top_k=3)
                if similar_docs:
                    similarity_results.append({
                        "query": sentence,
                        "similar_documents": similar_docs
                    })
            
            return {
                "similarity_results": similarity_results,
                "total_queries": len(sentences),
                "found_similarities": len(similarity_results),
                "analysis_method": "向量相似性搜索"
            }
            
        except Exception as e:
            self.logger.error(f"向量相似性分析失败: {str(e)}")
            return {
                "similarity_results": [],
                "error": f"向量分析失败: {str(e)}",
                "analysis_method": "向量相似性搜索"
            }
    
    def _extract_key_sentences(self, content: str) -> List[str]:
        """提取关键句子"""
        sentences = re.split(r'[。！？\n]', content)
        key_sentences = []
        
        # 筛选包含重要关键词的句子
        important_keywords = [
            "需求", "功能", "系统", "接口", "数据", "用户", "管理", "查询", "创建", "删除", "修改",
            "requirement", "function", "system", "interface", "data", "user", "manage"
        ]
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10 and any(keyword in sentence for keyword in important_keywords):
                key_sentences.append(sentence)
        
        return key_sentences[:10]  # 返回前10个关键句子
    
    async def _business_requirement_analysis(self, content: str, parsing_result: Dict[str, Any]) -> Dict[str, Any]:
        """业务需求分析"""
        system_prompt = """你是一个专业的业务分析师，请分析文档中的业务需求。

请识别以下内容：
1. 核心业务流程
2. 用户角色和权限
3. 数据实体和关系
4. 业务规则和约束
5. 非功能性需求（性能、安全等）

返回JSON格式：
{
    "business_processes": ["流程1", "流程2"],
    "user_roles": ["角色1", "角色2"],
    "data_entities": ["实体1", "实体2"],
    "business_rules": ["规则1", "规则2"],
    "non_functional_requirements": {
        "performance": ["性能要求"],
        "security": ["安全要求"],
        "usability": ["可用性要求"]
    },
    "priority": "高/中/低"
}"""
        
        user_prompt = f"""请分析以下文档的业务需求：

{content[:2000]}

请按照指定的JSON格式返回分析结果。"""
        
        try:
            response = await self._call_llm(user_prompt, system_prompt, max_tokens=1500)
            if response:
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    return {"raw_response": response, "parse_error": "JSON解析失败"}
            else:
                return {"error": "LLM响应为空"}
        except Exception as e:
            return {"error": f"业务需求分析失败: {str(e)}"}
    
    async def _complexity_assessment(self, crud_analysis: Dict[str, Any], 
                                   business_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """技术复杂度评估"""
        crud_count = crud_analysis.get("summary", {}).get("total_operations", 0)
        business_processes = len(business_analysis.get("business_processes", []))
        data_entities = len(business_analysis.get("data_entities", []))
        
        # 复杂度评分
        complexity_score = 0
        complexity_score += crud_count * 2  # CRUD操作权重
        complexity_score += business_processes * 3  # 业务流程权重
        complexity_score += data_entities * 2  # 数据实体权重
        
        # 复杂度等级
        if complexity_score <= 10:
            complexity_level = "简单"
            estimated_days = "1-3天"
        elif complexity_score <= 25:
            complexity_level = "中等"
            estimated_days = "1-2周"
        else:
            complexity_level = "复杂"
            estimated_days = "2-4周"
        
        return {
            "complexity_score": complexity_score,
            "complexity_level": complexity_level,
            "estimated_development_time": estimated_days,
            "factors": {
                "crud_operations": crud_count,
                "business_processes": business_processes,
                "data_entities": data_entities
            },
            "recommendations": self._get_complexity_recommendations(complexity_level)
        }
    
    def _get_complexity_recommendations(self, complexity_level: str) -> List[str]:
        """获取复杂度建议"""
        recommendations = {
            "简单": [
                "可以使用快速开发框架",
                "建议采用敏捷开发模式",
                "重点关注代码质量和测试覆盖"
            ],
            "中等": [
                "建议进行详细的技术设计",
                "考虑使用微服务架构",
                "需要完善的测试策略",
                "建议分阶段开发和部署"
            ],
            "复杂": [
                "必须进行详细的架构设计",
                "建议使用领域驱动设计(DDD)",
                "需要完整的CI/CD流程",
                "建议组建专门的开发团队",
                "需要详细的项目管理和风险控制"
            ]
        }
        
        return recommendations.get(complexity_level, []) 