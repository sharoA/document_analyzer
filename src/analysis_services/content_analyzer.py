"""
内容分析服务 - 阶段2：内容分析
专注于功能变更识别：新增功能、修改功能、删除功能、关键变更提取
"""

import json
import time
import re
from typing import Dict, Any, List
from .base_service import BaseAnalysisService

class ContentAnalyzerService(BaseAnalysisService):
    """内容分析服务类 - 阶段2：内容分析"""
    
    def __init__(self, llm_client=None, vector_db=None):
        super().__init__(llm_client, vector_db)
        self.stage_name = "content_analysis"
    
    async def analyze(self, task_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行内容分析 - 第二阶段
        专注于功能变更识别和关键信息提取
        
        Args:
            task_id: 任务ID
            input_data: 包含文档解析结果的数据
            
        Returns:
            内容分析结果字典
        """
        start_time = time.time()
        
        try:
            # 提取文档解析结果
            document_parsing = input_data.get("document_parsing", {})
            document_content = document_parsing.get("content_elements", {}).get("text_content", "")
            file_info = document_parsing.get("file_info", {})
            
            self._log_analysis_start(task_id, "内容分析", len(document_content))
            
            # 1. 分析新增功能
            new_features = await self.analyze_new_features(document_content, document_parsing)
            
            # 2. 分析修改功能
            modified_features = await self.analyze_modified_features(document_content, document_parsing)
            
            # 3. 分析删除功能
            deleted_features = await self.analyze_deleted_features(document_content, document_parsing)
            
            # 4. 提取关键变更
            key_changes = await self.extract_key_changes(document_content, document_parsing)
            
            # 合并内容分析结果
            content_result = {
                "new_features": new_features,
                "modified_features": modified_features,
                "deleted_features": deleted_features,
                "key_changes": key_changes,
                "analysis_summary": self._generate_content_summary(
                    new_features, modified_features, deleted_features, key_changes
                ),
                "analysis_metadata": {
                    "stage": "content_analysis",
                    "analysis_method": "enhanced_content_analyzer",
                    "analysis_time": time.time() - start_time,
                    "content_length": len(document_content)
                }
            }
            
            duration = time.time() - start_time
            self._log_analysis_complete(task_id, "内容分析", duration, len(str(content_result)))
            
            return self._create_response(
                success=True,
                data=content_result,
                metadata={"analysis_duration": duration, "stage": "content_analysis"}
            )
            
        except Exception as e:
            self._log_error(task_id, "内容分析", e)
            return self._create_response(
                success=False,
                error=f"内容分析失败: {str(e)}",
                metadata={"stage": "content_analysis"}
            )
    
    async def analyze_new_features(self, content: str, document_parsing: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分析新增功能"""
        try:
            # 使用LLM识别新增功能
            system_prompt = """你是一个专业的需求分析专家，专门识别文档中的新增功能需求。

请仔细分析文档内容，识别所有新增的功能特性：
1. 明确标注为"新增"、"增加"、"添加"的功能
2. 文档中描述的新功能模块
3. 新的业务流程或操作
4. 新的界面或交互功能

对每个新增功能，请提供：
- 功能ID
- 功能名称
- 详细描述
- 优先级（高/中/低）
- 复杂度评估（简单/中等/复杂）
- 预估工作量
- 所在位置（章节/页码）

返回JSON格式：
{
    "new_features": [
        {
            "feature_id": "F001",
            "feature_name": "功能名称",
            "description": "详细描述",
            "priority": "高/中/低",
            "complexity": "简单/中等/复杂",
            "estimated_effort": "预估工作量",
            "location": "所在位置",
            "business_value": "业务价值",
            "dependencies": ["依赖项"],
            "acceptance_criteria": ["验收标准"]
        }
    ]
}"""
            
            user_prompt = f"""请分析以下文档内容，识别其中的新增功能需求：

文档内容：
{content[:3000]}  # 限制长度

请按照指定的JSON格式返回分析结果。"""
        
            response = await self._call_llm(user_prompt, system_prompt, max_tokens=2500)
            if response:
                try:
                    result = json.loads(response)
                    return result.get("new_features", [])
                except json.JSONDecodeError:
                    # 备选方案：关键词匹配
                    return self._fallback_new_features_analysis(content)
            else:
                return self._fallback_new_features_analysis(content)
                
        except Exception as e:
            self.logger.error(f"新增功能分析失败: {str(e)}")
            return self._fallback_new_features_analysis(content)
    
    async def analyze_modified_features(self, content: str, document_parsing: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分析修改功能"""
        try:
            system_prompt = """你是一个专业的需求分析专家，专门识别文档中的功能修改需求。

请仔细分析文档内容，识别所有修改的功能特性：
1. 明确标注为"修改"、"变更"、"优化"的功能
2. 对现有功能的改进或调整
3. 业务流程的变化
4. 界面或交互的调整

对每个修改功能，请提供：
- 功能ID
- 功能名称  
- 修改类型（功能增强/业务调整/界面优化/性能优化）
- 修改描述
- 影响级别（高/中/低）
- 所在位置

返回JSON格式：
{
    "modified_features": [
        {
            "feature_id": "M001",
            "feature_name": "功能名称",
            "change_type": "功能增强/业务调整/界面优化/性能优化",
            "description": "修改描述",
            "original_behavior": "原有行为",
            "new_behavior": "新行为",
            "impact_level": "高/中/低",
            "location": "所在位置",
            "impact_analysis": "影响分析",
            "migration_required": true/false
        }
    ]
}"""
            
            user_prompt = f"""请分析以下文档内容，识别其中的功能修改需求：

文档内容：
{content[:3000]}

请按照指定的JSON格式返回分析结果。"""
            
            response = await self._call_llm(user_prompt, system_prompt, max_tokens=2500)
            if response:
                try:
                    result = json.loads(response)
                    return result.get("modified_features", [])
                except json.JSONDecodeError:
                    return self._fallback_modified_features_analysis(content)
            else:
                return self._fallback_modified_features_analysis(content)
                
        except Exception as e:
            self.logger.error(f"修改功能分析失败: {str(e)}")
            return self._fallback_modified_features_analysis(content)
    
    async def analyze_deleted_features(self, content: str, document_parsing: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分析删除功能"""
        try:
            system_prompt = """你是一个专业的需求分析专家，专门识别文档中的功能删除需求。

请仔细分析文档内容，识别所有删除或废弃的功能：
1. 明确标注为"删除"、"移除"、"废弃"的功能
2. 不再需要的功能模块
3. 被替代的旧功能
4. 停止维护的特性

对每个删除功能，请提供：
- 功能ID
- 功能名称
- 删除原因
- 替代方案
- 所在位置

返回JSON格式：
{
    "deleted_features": [
        {
            "feature_id": "D001",
            "feature_name": "功能名称",
            "description": "功能描述",
            "deletion_reason": "删除原因",
            "replacement": "替代方案",
            "location": "所在位置",
            "impact_analysis": "影响分析",
            "cleanup_required": true/false,
            "data_migration": "数据迁移说明"
        }
    ]
}"""
            
            user_prompt = f"""请分析以下文档内容，识别其中的功能删除需求：

文档内容：
{content[:3000]}

请按照指定的JSON格式返回分析结果。"""
            
            response = await self._call_llm(user_prompt, system_prompt, max_tokens=2500)
            if response:
                try:
                    result = json.loads(response)
                    return result.get("deleted_features", [])
                except json.JSONDecodeError:
                    return self._fallback_deleted_features_analysis(content)
            else:
                return self._fallback_deleted_features_analysis(content)
            
        except Exception as e:
            self.logger.error(f"删除功能分析失败: {str(e)}")
            return self._fallback_deleted_features_analysis(content)
    
    async def extract_key_changes(self, content: str, document_parsing: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取关键变更"""
        try:
            system_prompt = """你是一个专业的变更管理专家，专门识别文档中的关键变更点。

请仔细分析文档内容，识别所有重要的变更：
1. 架构层面的重大变更
2. 业务流程的重要调整
3. 技术栈的改变
4. 数据模型的变更
5. 接口的重大调整

对每个关键变更，请提供：
- 变更ID
- 变更类型
- 变更标题
- 影响程度
- 实施时间线
- 风险评估

返回JSON格式：
{
    "key_changes": [
        {
            "change_id": "C001",
            "change_type": "架构变更/业务流程/技术栈/数据模型/接口调整",
            "title": "变更标题",
            "description": "详细描述",
            "impact": "重大/中等/轻微",
            "timeline": "时间线",
            "risks": ["风险1", "风险2"],
            "benefits": ["收益1", "收益2"],
            "stakeholders": ["相关方"],
            "location": "所在位置"
        }
    ]
}"""
            
            user_prompt = f"""请分析以下文档内容，识别其中的关键变更：

文档内容：
{content[:3000]}

请按照指定的JSON格式返回分析结果。"""
        
            response = await self._call_llm(user_prompt, system_prompt, max_tokens=2500)
            if response:
                try:
                    result = json.loads(response)
                    return result.get("key_changes", [])
                except json.JSONDecodeError:
                    return self._fallback_key_changes_analysis(content)
            else:
                return self._fallback_key_changes_analysis(content)
                
        except Exception as e:
            self.logger.error(f"关键变更分析失败: {str(e)}")
            return self._fallback_key_changes_analysis(content)
    
    # 备选分析方法（基于关键词匹配）
    def _fallback_new_features_analysis(self, content: str) -> List[Dict[str, Any]]:
        """备选新增功能分析"""
        new_keywords = ["新增", "增加", "添加", "新功能", "新特性", "新建", "创建", "引入"]
        features = []
        
        for i, keyword in enumerate(new_keywords):
            if keyword in content:
                features.append({
                    "feature_id": f"F{str(i+1).zfill(3)}",
                    "feature_name": f"检测到的新增功能{i+1}",
                    "description": f"基于关键词'{keyword}'识别的新增功能",
                    "priority": "中",
                    "complexity": "中等",
                    "estimated_effort": "待评估",
                    "location": "基于关键词匹配",
                    "business_value": "待分析",
                    "dependencies": [],
                    "acceptance_criteria": []
                })
        
        return features
    
    def _fallback_modified_features_analysis(self, content: str) -> List[Dict[str, Any]]:
        """备选修改功能分析"""
        modify_keywords = ["修改", "变更", "调整", "优化", "改进", "更新", "升级"]
        features = []
        
        for i, keyword in enumerate(modify_keywords):
            if keyword in content:
                features.append({
                    "feature_id": f"M{str(i+1).zfill(3)}",
                    "feature_name": f"检测到的修改功能{i+1}",
                    "change_type": "功能调整",
                    "description": f"基于关键词'{keyword}'识别的修改功能",
                    "original_behavior": "待分析",
                    "new_behavior": "待分析",
                    "impact_level": "中",
                    "location": "基于关键词匹配",
                    "impact_analysis": "待详细分析",
                    "migration_required": False
                })
        
        return features
    
    def _fallback_deleted_features_analysis(self, content: str) -> List[Dict[str, Any]]:
        """备选删除功能分析"""
        delete_keywords = ["删除", "移除", "废弃", "取消", "停用", "下线"]
        features = []
        
        for i, keyword in enumerate(delete_keywords):
            if keyword in content:
                features.append({
                    "feature_id": f"D{str(i+1).zfill(3)}",
                    "feature_name": f"检测到的删除功能{i+1}",
                    "description": f"基于关键词'{keyword}'识别的删除功能",
                    "deletion_reason": "待分析",
                    "replacement": "暂无",
                    "location": "基于关键词匹配",
                    "impact_analysis": "待详细分析",
                    "cleanup_required": True,
                    "data_migration": "待评估"
                })
        
        return features
    
    def _fallback_key_changes_analysis(self, content: str) -> List[Dict[str, Any]]:
        """备选关键变更分析"""
        change_keywords = ["重大变更", "架构调整", "技术升级", "流程改进", "系统重构"]
        changes = []
        
        for i, keyword in enumerate(change_keywords):
            if keyword in content:
                changes.append({
                    "change_id": f"C{str(i+1).zfill(3)}",
                    "change_type": "系统变更",
                    "title": f"检测到的关键变更{i+1}",
                    "description": f"基于关键词'{keyword}'识别的关键变更",
                    "impact": "中等",
                    "timeline": "待确定",
                    "risks": ["待识别"],
                    "benefits": ["待分析"],
                    "stakeholders": ["项目团队"],
                    "location": "基于关键词匹配"
                })
        
        return changes
    
    def _generate_content_summary(self, new_features: List, modified_features: List, 
                                 deleted_features: List, key_changes: List) -> Dict[str, Any]:
        """生成内容分析摘要"""
        return {
            "total_changes": len(new_features) + len(modified_features) + len(deleted_features) + len(key_changes),
            "new_features_count": len(new_features),
            "modified_features_count": len(modified_features),
            "deleted_features_count": len(deleted_features),
            "key_changes_count": len(key_changes),
            "change_complexity": self._assess_change_complexity(
                new_features, modified_features, deleted_features, key_changes
            ),
            "high_priority_count": self._count_high_priority_items(
                new_features, modified_features, key_changes
            ),
            "estimated_total_effort": self._estimate_total_effort(
                new_features, modified_features, deleted_features
            )
        }
    
    def _assess_change_complexity(self, new_features: List, modified_features: List,
                                 deleted_features: List, key_changes: List) -> str:
        """评估变更复杂度"""
        total_items = len(new_features) + len(modified_features) + len(deleted_features) + len(key_changes)
        
        if total_items > 20:
            return "非常复杂"
        elif total_items > 10:
            return "复杂"
        elif total_items > 5:
            return "中等"
        else:
            return "简单"
    
    def _count_high_priority_items(self, new_features: List, modified_features: List, key_changes: List) -> int:
        """统计高优先级项目数量"""
        high_priority_count = 0
        
        for feature in new_features:
            if feature.get("priority") == "高":
                high_priority_count += 1
        
        for feature in modified_features:
            if feature.get("impact_level") == "高":
                high_priority_count += 1
        
        for change in key_changes:
            if change.get("impact") == "重大":
                high_priority_count += 1
        
        return high_priority_count
    
    def _estimate_total_effort(self, new_features: List, modified_features: List, deleted_features: List) -> str:
        """估算总工作量"""
        # 简化的工作量估算
        total_items = len(new_features) + len(modified_features) + len(deleted_features)
        
        if total_items > 15:
            return "6个月+"
        elif total_items > 10:
            return "3-6个月"
        elif total_items > 5:
            return "1-3个月"
        else:
            return "1个月内" 