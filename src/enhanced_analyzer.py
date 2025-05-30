from typing import List, Dict, Any, Optional
from langchain_community.llms import DeepSeek
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from .config import settings
from .database_analyzer import DatabaseAnalyzer
from .vector_store import VectorStore
import json
import os

class EnhancedRequirementAnalyzer:
    def __init__(self):
        self.llm = DeepSeek(api_key=settings.DEEPSEEK_API_KEY)
        self.db_analyzer = DatabaseAnalyzer()
        self.vector_store = VectorStore()
        self._setup_chains()
        self._load_templates()
    
    def _load_templates(self):
        """加载设计文档模板"""
        self.templates = {}
        template_folder = settings.TEMPLATE_FOLDER
        
        if os.path.exists(template_folder):
            for template_file in [
                settings.BACKEND_DESIGN_TEMPLATE,
                settings.FRONTEND_DESIGN_TEMPLATE,
                settings.API_DESIGN_TEMPLATE
            ]:
                template_path = os.path.join(template_folder, template_file)
                if os.path.exists(template_path):
                    with open(template_path, 'r', encoding='utf-8') as f:
                        self.templates[template_file] = f.read()
    
    def _setup_chains(self):
        """设置各种分析链"""
        
        # 业务关键词提取模板（结合历史文档和数据库）
        keyword_template = """
        基于以下信息提取业务关键词：
        
        当前需求文档：
        {content}
        
        相似历史文档：
        {similar_docs}
        
        数据库表结构摘要：
        {db_summary}
        
        请分析并返回JSON格式，包含：
        - business_keywords: 业务关键词列表
        - technical_keywords: 技术关键词列表
        - entities: 业务实体列表
        - relationships: 实体关系
        - data_requirements: 数据需求列表
        """
        self.keyword_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate(
                input_variables=["content", "similar_docs", "db_summary"],
                template=keyword_template
            )
        )
        
        # 问题检查模板（结合数据库字段检查）
        issue_template = """
        分析需求文档中的问题，特别关注数据可用性：
        
        需求文档：
        {content}
        
        提取的关键词：
        {keywords}
        
        数据库字段可用性检查：
        {field_availability}
        
        相关数据库表：
        {related_tables}
        
        请检查以下问题并返回JSON格式：
        - requirement_issues: 需求不明确的问题
        - data_issues: 数据缺失或不匹配的问题
        - technical_issues: 技术实现问题
        - business_logic_issues: 业务逻辑问题
        - suggestions: 改进建议
        """
        self.issue_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate(
                input_variables=["content", "keywords", "field_availability", "related_tables"],
                template=issue_template
            )
        )
        
        # API设计分析模板
        api_design_template = """
        基于需求文档分析需要开发的API接口：
        
        需求文档：
        {content}
        
        业务关键词：
        {keywords}
        
        相关数据库表：
        {related_tables}
        
        请分析并返回JSON格式：
        - apis: [
            {{
                "name": "接口名称",
                "method": "HTTP方法",
                "path": "接口路径",
                "description": "接口描述",
                "request_params": ["参数列表"],
                "response_fields": ["返回字段"],
                "required_data": ["需要的数据字段"],
                "database_tables": ["涉及的数据库表"],
                "business_logic": "业务逻辑描述"
            }}
        ]
        """
        self.api_design_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate(
                input_variables=["content", "keywords", "related_tables"],
                template=api_design_template
            )
        )
        
        # 后端设计文档生成模板
        backend_design_template = """
        基于以下信息生成后端详细设计文档：
        
        需求文档：
        {content}
        
        API设计：
        {api_design}
        
        数据库分析：
        {db_analysis}
        
        问题分析：
        {issues}
        
        设计文档模板：
        {template}
        
        请生成完整的后端详细设计文档，包括：
        1. 系统架构设计
        2. 数据库设计
        3. API接口设计
        4. 业务逻辑设计
        5. 安全性设计
        6. 性能优化方案
        """
        self.backend_design_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate(
                input_variables=["content", "api_design", "db_analysis", "issues", "template"],
                template=backend_design_template
            )
        )
        
        # 前端设计文档生成模板
        frontend_design_template = """
        基于需求文档和截图分析生成前端详细设计文档：
        
        需求文档：
        {content}
        
        截图OCR文本：
        {ocr_text}
        
        API设计：
        {api_design}
        
        设计文档模板：
        {template}
        
        请生成完整的前端详细设计文档，包括：
        1. 页面结构设计
        2. 组件设计
        3. 交互设计
        4. 数据流设计
        5. 样式设计
        6. 响应式设计
        """
        self.frontend_design_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate(
                input_variables=["content", "ocr_text", "api_design", "template"],
                template=frontend_design_template
            )
        )
    
    def analyze_requirements(self, content: str, images: List[str] = None) -> Dict[str, Any]:
        """综合分析需求文档"""
        # 1. 搜索相似历史文档
        similar_docs = self.vector_store.search_similar(content, limit=3)
        similar_content = "\n".join([doc.get("content", "")[:500] for doc in similar_docs])
        
        # 2. 获取数据库摘要
        db_summary = self.db_analyzer.generate_database_summary()
        
        # 3. 提取关键词
        keywords_result = self.keyword_chain.run(
            content=content,
            similar_docs=similar_content,
            db_summary=db_summary
        )
        keywords = self._parse_json_result(keywords_result)
        
        # 4. 搜索相关数据库表
        business_keywords = keywords.get("business_keywords", [])
        related_tables = self.db_analyzer.search_related_tables(business_keywords)
        
        # 5. 检查字段可用性
        data_requirements = keywords.get("data_requirements", [])
        field_availability = self.db_analyzer.check_field_availability(data_requirements)
        
        # 6. 问题检查
        issues_result = self.issue_chain.run(
            content=content,
            keywords=json.dumps(keywords, ensure_ascii=False),
            field_availability=json.dumps(field_availability, ensure_ascii=False),
            related_tables=json.dumps(related_tables, ensure_ascii=False)
        )
        issues = self._parse_json_result(issues_result)
        
        # 7. API设计分析
        api_design_result = self.api_design_chain.run(
            content=content,
            keywords=json.dumps(keywords, ensure_ascii=False),
            related_tables=json.dumps(related_tables, ensure_ascii=False)
        )
        api_design = self._parse_json_result(api_design_result)
        
        return {
            "keywords": keywords,
            "related_tables": related_tables,
            "field_availability": field_availability,
            "issues": issues,
            "api_design": api_design,
            "similar_docs": similar_docs
        }
    
    def generate_backend_design(self, analysis_result: Dict[str, Any], content: str) -> str:
        """生成后端设计文档"""
        template = self.templates.get(settings.BACKEND_DESIGN_TEMPLATE, "")
        
        return self.backend_design_chain.run(
            content=content,
            api_design=json.dumps(analysis_result["api_design"], ensure_ascii=False),
            db_analysis=json.dumps(analysis_result["related_tables"], ensure_ascii=False),
            issues=json.dumps(analysis_result["issues"], ensure_ascii=False),
            template=template
        )
    
    def generate_frontend_design(self, analysis_result: Dict[str, Any], content: str, ocr_text: str = "") -> str:
        """生成前端设计文档"""
        template = self.templates.get(settings.FRONTEND_DESIGN_TEMPLATE, "")
        
        return self.frontend_design_chain.run(
            content=content,
            ocr_text=ocr_text,
            api_design=json.dumps(analysis_result["api_design"], ensure_ascii=False),
            template=template
        )
    
    def _parse_json_result(self, result: str) -> Dict[str, Any]:
        """解析JSON结果"""
        try:
            # 尝试直接解析
            return json.loads(result)
        except:
            try:
                # 尝试提取JSON部分
                start = result.find('{')
                end = result.rfind('}') + 1
                if start != -1 and end != 0:
                    return json.loads(result[start:end])
            except:
                pass
        return {} 