"""
AI智能分析服务 - 阶段3：AI智能分析
专注于需求提取、技术设计、实现建议和综合总结
"""

import json
import time
from typing import Dict, Any, List
from .base_service import BaseAnalysisService

class AIAnalyzerService(BaseAnalysisService):
    """AI智能分析服务类 - 阶段3：AI智能分析"""
    
    def __init__(self, llm_client=None, vector_db=None):
        super().__init__(llm_client, vector_db)
        self.stage_name = "ai_analysis"
    
    async def analyze(self, task_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行AI智能分析 - 第三阶段
        专注于需求理解、技术设计、实现建议和综合总结
        
        Args:
            task_id: 任务ID
            input_data: 包含文档解析和内容分析结果的数据
            
        Returns:
            AI分析结果字典
        """
        start_time = time.time()
        
        try:
            # 提取前两个阶段的结果
            document_parsing = input_data.get("document_parsing", {})
            content_analysis = input_data.get("content_analysis", {})
            
            # 获取基础数据
            document_content = document_parsing.get("content_elements", {}).get("text_content", "")
            new_features = content_analysis.get("new_features", [])
            modified_features = content_analysis.get("modified_features", [])
            deleted_features = content_analysis.get("deleted_features", [])
            key_changes = content_analysis.get("key_changes", [])
            
            self._log_analysis_start(task_id, "AI智能分析", len(document_content))
            
            # 1. 智能提取业务需求和用户故事
            requirements = await self.extract_requirements(document_parsing, content_analysis)
            
            # 2. 生成技术架构和设计方案
            technical_design = await self.generate_technical_design(
                document_parsing, content_analysis, requirements
            )
            
            # 3. 提供开发实现建议和最佳实践
            implementation_suggestions = await self.generate_implementation_suggestions(
                document_parsing, content_analysis, requirements, technical_design
            )
            
            # 4. 生成综合分析总结和风险评估
            analysis_summary = await self.generate_analysis_summary(
                document_parsing, content_analysis, requirements, technical_design, implementation_suggestions
            )
            
            # 合并AI智能分析结果
            ai_result = {
                "requirements": requirements,
                "technical_design": technical_design,
                "implementation_suggestions": implementation_suggestions,
                "analysis_summary": analysis_summary,
                "analysis_metadata": {
                    "stage": "ai_analysis",
                    "analysis_method": "ai_intelligent_analysis",
                    "analysis_time": time.time() - start_time,
                    "content_length": len(document_content),
                    "features_analyzed": {
                        "new_features": len(new_features),
                        "modified_features": len(modified_features),
                        "deleted_features": len(deleted_features),
                        "key_changes": len(key_changes)
                    }
                }
            }
            
            duration = time.time() - start_time
            self._log_analysis_complete(task_id, "AI智能分析", duration, len(str(ai_result)))
            
            return self._create_response(
                success=True,
                data=ai_result,
                metadata={"analysis_duration": duration, "stage": "ai_analysis"}
            )
            
        except Exception as e:
            self._log_error(task_id, "AI智能分析", e)
            return self._create_response(
                success=False,
                error=f"AI智能分析失败: {str(e)}",
                metadata={"stage": "ai_analysis"}
            )
    
    async def extract_requirements(self, document_parsing: Dict[str, Any], content_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """智能提取业务需求和用户故事"""
        try:
            system_prompt = """你是一个专业的需求分析专家，专门从文档中提取和整理业务需求。

基于文档解析结果和内容分析结果，请提取并整理所有业务需求：

1. 功能需求：具体的系统功能和特性
2. 非功能需求：性能、安全、可用性等
3. 用户故事：以用户为中心的需求描述
4. 业务规则：系统必须遵循的业务逻辑
5. 约束条件：技术、时间、资源等限制

对每个需求，请提供：
- 需求ID和类型
- 需求标题和详细描述
- 验收标准
- 优先级和依赖关系
- 预估工作量

返回JSON格式：
{
    "requirements": [
        {
            "requirement_id": "REQ-001",
            "type": "功能需求/非功能需求/用户故事/业务规则/约束条件",
            "category": "用户管理/数据处理/系统集成/界面交互",
            "title": "需求标题",
            "description": "详细描述",
            "acceptance_criteria": [
                "验收标准1",
                "验收标准2"
            ],
            "priority": "必须/重要/一般/可选",
            "estimated_effort": "工作量估算",
            "dependencies": ["依赖的需求ID"],
            "business_value": "业务价值描述",
            "user_story": "作为...我希望...以便于...",
            "source": "来源（新增功能/修改功能/业务规则）"
        }
    ]
}"""
            
            # 准备输入数据
            content_summary = {
                "new_features": content_analysis.get("new_features", []),
                "modified_features": content_analysis.get("modified_features", []),
                "deleted_features": content_analysis.get("deleted_features", []),
                "key_changes": content_analysis.get("key_changes", [])
            }
            
            user_prompt = f"""请基于以下文档分析结果，提取并整理业务需求：

内容分析结果：
{json.dumps(content_summary, ensure_ascii=False, indent=2)}

请按照指定的JSON格式返回需求分析结果。"""
            
            response = await self._call_llm(user_prompt, system_prompt, max_tokens=4000)
            if response:
                try:
                    result = json.loads(response)
                    return result.get("requirements", [])
                except json.JSONDecodeError:
                    return self._fallback_requirements_extraction(content_analysis)
            else:
                return self._fallback_requirements_extraction(content_analysis)
                
        except Exception as e:
            self.logger.error(f"需求提取失败: {str(e)}")
            return self._fallback_requirements_extraction(content_analysis)
    
    async def generate_technical_design(self, document_parsing: Dict[str, Any], 
                                       content_analysis: Dict[str, Any], 
                                       requirements: List[Dict[str, Any]]) -> str:
        """生成技术架构和设计方案"""
        try:
            system_prompt = """你是一个资深的技术架构师，请基于需求分析结果设计完整的技术方案。

请设计包含以下内容的技术架构方案：

1. 总体架构设计
   - 系统架构图描述
   - 技术栈选择
   - 部署架构

2. 技术选型
   - 前端技术栈
   - 后端技术栈
   - 数据库选择
   - 中间件和工具

3. 系统设计
   - 模块设计
   - 数据库设计要点
   - 接口设计原则
   - 安全设计

4. 性能设计
   - 性能指标
   - 缓存策略
   - 负载均衡

5. 部署方案
   - 环境规划
   - CI/CD流程
   - 监控方案

请以Markdown格式返回详细的技术设计文档。"""
            
            # 准备需求摘要
            requirements_summary = self._summarize_requirements(requirements)
            features_summary = {
                "new_features_count": len(content_analysis.get("new_features", [])),
                "modified_features_count": len(content_analysis.get("modified_features", [])),
                "key_changes_count": len(content_analysis.get("key_changes", [])),
                "complexity": content_analysis.get("analysis_summary", {}).get("change_complexity", "中等")
            }
            
            user_prompt = f"""请基于以下信息设计技术架构方案：

需求摘要：
{json.dumps(requirements_summary, ensure_ascii=False, indent=2)}

功能特性摘要：
{json.dumps(features_summary, ensure_ascii=False, indent=2)}

文档类型：{document_parsing.get("metadata", {}).get("category", "技术文档")}

请返回详细的技术设计文档（Markdown格式）。"""
            
            response = await self._call_llm(user_prompt, system_prompt, max_tokens=4000)
            if response:
                return response
            else:
                return self._fallback_technical_design(requirements, content_analysis)
                
        except Exception as e:
            self.logger.error(f"技术设计生成失败: {str(e)}")
            return self._fallback_technical_design(requirements, content_analysis)
    
    async def generate_implementation_suggestions(self, document_parsing: Dict[str, Any],
                                                content_analysis: Dict[str, Any],
                                                requirements: List[Dict[str, Any]],
                                                technical_design: str) -> str:
        """生成开发实现建议和最佳实践"""
        try:
            system_prompt = """你是一个经验丰富的项目经理和技术专家，请提供详细的实施建议。

请提供包含以下内容的实施建议：

1. 开发优先级规划
   - 第一阶段：核心功能
   - 第二阶段：重要功能
   - 第三阶段：增值功能

2. 开发团队建议
   - 团队规模和技能要求
   - 角色分工
   - 协作方式

3. 开发流程建议
   - 开发方法论选择
   - 迭代周期规划
   - 质量保证流程

4. 技术实施建议
   - 代码规范
   - 测试策略
   - 部署策略

5. 风险管控
   - 主要风险识别
   - 风险缓解措施
   - 应急预案

6. 项目管理建议
   - 里程碑规划
   - 进度跟踪
   - 沟通机制

请以Markdown格式返回详细的实施建议文档。"""
            
            # 准备上下文信息
            complexity_info = {
                "requirements_count": len(requirements),
                "high_priority_count": len([r for r in requirements if r.get("priority") == "必须"]),
                "change_complexity": content_analysis.get("analysis_summary", {}).get("change_complexity", "中等"),
                "estimated_effort": content_analysis.get("analysis_summary", {}).get("estimated_total_effort", "待评估")
            }
            
            user_prompt = f"""请基于以下项目信息提供实施建议：

项目复杂度信息：
{json.dumps(complexity_info, ensure_ascii=False, indent=2)}

主要需求类型：
{self._get_requirements_breakdown(requirements)}

文档质量评估：
{document_parsing.get("quality_info", {}).get("overall_score", 80)}/100

请返回详细的实施建议文档（Markdown格式）。"""
            
            response = await self._call_llm(user_prompt, system_prompt, max_tokens=4000)
            if response:
                return response
            else:
                return self._fallback_implementation_suggestions(requirements, content_analysis)
                
        except Exception as e:
            self.logger.error(f"实施建议生成失败: {str(e)}")
            return self._fallback_implementation_suggestions(requirements, content_analysis)
    
    async def generate_analysis_summary(self, document_parsing: Dict[str, Any],
                                       content_analysis: Dict[str, Any],
                                       requirements: List[Dict[str, Any]],
                                       technical_design: str,
                                       implementation_suggestions: str) -> str:
        """生成综合分析总结和风险评估"""
        try:
            system_prompt = """你是一个资深的项目分析专家，请基于完整的分析结果生成综合总结。

请生成包含以下内容的综合分析总结：

1. 项目概况
   - 项目类型和规模
   - 主要目标和价值
   - 关键特点

2. 主要发现
   - 核心功能点
   - 重要变更
   - 技术特色

3. 复杂度评估
   - 功能复杂度
   - 技术复杂度
   - 实施复杂度

4. 风险评估
   - 高风险项目
   - 中风险项目
   - 风险缓解建议

5. 投资收益分析
   - 预期收益
   - 投入成本
   - ROI评估

6. 总体建议
   - 是否建议实施
   - 关键成功因素
   - 注意事项

请以Markdown格式返回综合分析总结。"""
            
            # 准备完整的分析数据摘要
            analysis_data = {
                "document_info": {
                    "quality_score": document_parsing.get("quality_info", {}).get("overall_score", 80),
                    "structure_quality": document_parsing.get("structure", {}).get("structure_quality", "一般"),
                    "word_count": document_parsing.get("content_elements", {}).get("word_count", 0)
                },
                "content_changes": {
                    "new_features": len(content_analysis.get("new_features", [])),
                    "modified_features": len(content_analysis.get("modified_features", [])),
                    "deleted_features": len(content_analysis.get("deleted_features", [])),
                    "key_changes": len(content_analysis.get("key_changes", [])),
                    "complexity": content_analysis.get("analysis_summary", {}).get("change_complexity", "中等")
                },
                "requirements_info": {
                    "total_requirements": len(requirements),
                    "high_priority": len([r for r in requirements if r.get("priority") == "必须"]),
                    "functional_requirements": len([r for r in requirements if r.get("type") == "功能需求"]),
                    "non_functional_requirements": len([r for r in requirements if r.get("type") == "非功能需求"])
                }
            }
            
            user_prompt = f"""请基于以下完整分析数据生成综合总结：

分析数据摘要：
{json.dumps(analysis_data, ensure_ascii=False, indent=2)}

请返回详细的综合分析总结（Markdown格式）。"""
            
            response = await self._call_llm(user_prompt, system_prompt, max_tokens=3000)
            if response:
                return response
            else:
                return self._fallback_analysis_summary(document_parsing, content_analysis, requirements)
                
        except Exception as e:
            self.logger.error(f"综合总结生成失败: {str(e)}")
            return self._fallback_analysis_summary(document_parsing, content_analysis, requirements)
    
    # 辅助方法
    def _summarize_requirements(self, requirements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """总结需求信息"""
        return {
            "total_count": len(requirements),
            "functional_count": len([r for r in requirements if r.get("type") == "功能需求"]),
            "non_functional_count": len([r for r in requirements if r.get("type") == "非功能需求"]),
            "high_priority_count": len([r for r in requirements if r.get("priority") == "必须"]),
            "categories": list(set([r.get("category", "其他") for r in requirements]))
        }
    
    def _get_requirements_breakdown(self, requirements: List[Dict[str, Any]]) -> str:
        """获取需求分类统计"""
        categories = {}
        for req in requirements:
            category = req.get("category", "其他")
            categories[category] = categories.get(category, 0) + 1
        
        breakdown = []
        for category, count in categories.items():
            breakdown.append(f"{category}: {count}个")
        
        return ", ".join(breakdown)
    
    # 备选方法（当LLM调用失败时）
    def _fallback_requirements_extraction(self, content_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """备选需求提取方法"""
        requirements = []
        
        # 从新增功能提取需求
        for i, feature in enumerate(content_analysis.get("new_features", [])):
            requirements.append({
                "requirement_id": f"REQ-{str(i+1).zfill(3)}",
                "type": "功能需求",
                "category": "新功能",
                "title": feature.get("feature_name", f"新功能需求{i+1}"),
                "description": feature.get("description", "待详细分析"),
                "acceptance_criteria": feature.get("acceptance_criteria", ["待定义"]),
                "priority": feature.get("priority", "中等"),
                "estimated_effort": feature.get("estimated_effort", "待评估"),
                "dependencies": [],
                "business_value": feature.get("business_value", "待分析"),
                "user_story": f"作为用户，我希望{feature.get('feature_name', '新功能')}，以便于提升使用体验",
                "source": "新增功能"
            })
        
        return requirements
    
    def _fallback_technical_design(self, requirements: List[Dict], content_analysis: Dict) -> str:
        """备选技术设计方案"""
        return f"""# 技术架构设计方案

## 1. 总体架构
基于{len(requirements)}个需求，设计{content_analysis.get('analysis_summary', {}).get('change_complexity', '中等')}复杂度的系统架构。

## 2. 技术栈建议
- 前端：Vue 3 + TypeScript + Element Plus
- 后端：Spring Boot + MySQL + Redis
- 部署：Docker + Nginx

## 3. 开发建议
建议采用微服务架构，分{max(len(requirements)//5, 1)}个服务模块进行开发。

*注：此为简化版设计方案，建议进行详细的架构设计。*
"""
    
    def _fallback_implementation_suggestions(self, requirements: List[Dict], content_analysis: Dict) -> str:
        """备选实施建议"""
        complexity = content_analysis.get('analysis_summary', {}).get('change_complexity', '中等')
        estimated_effort = content_analysis.get('analysis_summary', {}).get('estimated_total_effort', '1-3个月')
        
        return f"""# 实施建议

## 1. 开发优先级
基于{len(requirements)}个需求，建议分3个阶段实施：
- 第一阶段：核心功能开发
- 第二阶段：扩展功能开发  
- 第三阶段：优化和完善

## 2. 项目规划
- 复杂度评估：{complexity}
- 预估工期：{estimated_effort}
- 团队规模：建议3-5人

## 3. 风险控制
- 定期进行技术评审
- 建立完善的测试体系
- 做好项目进度跟踪

*注：此为简化版实施建议，建议进行详细的项目规划。*
"""
    
    def _fallback_analysis_summary(self, document_parsing: Dict, content_analysis: Dict, requirements: List) -> str:
        """备选分析总结"""
        quality_score = document_parsing.get("quality_info", {}).get("overall_score", 80)
        total_changes = content_analysis.get("analysis_summary", {}).get("total_changes", 0)
        
        return f"""# 综合分析总结

## 项目概况
本次分析的文档质量评分为{quality_score}/100，共识别出{total_changes}项变更需求，{len(requirements)}个业务需求。

## 主要发现
- 文档结构：{document_parsing.get("structure", {}).get("structure_quality", "一般")}
- 变更复杂度：{content_analysis.get("analysis_summary", {}).get("change_complexity", "中等")}
- 实施难度：中等

## 总体建议
建议按计划实施，重点关注项目风险控制和质量保证。

*注：此为简化版分析总结，建议进行更详细的分析。*
""" 