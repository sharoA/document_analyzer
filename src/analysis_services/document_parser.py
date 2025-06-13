"""
文档解析服务
基于document_analyze.md规范，使用大模型进行6阶段智能文档解析
"""
import logging
import json
import time
from typing import Dict, Any, List
from .base_service import BaseAnalysisService

# 创建logger实例
logger = logging.getLogger(__name__)

def clean_llm_response(response: str) -> str:
    """清理LLM响应中的markdown代码块标记"""
    if not response:
        return response
    
    # 去掉开头和结尾的markdown代码块标记
    response = response.strip()
    
    # 去掉 ```json 开头
    if response.startswith('```json'):
        response = response[7:].strip()
    elif response.startswith('```'):
        response = response[3:].strip()
    
    # 去掉 ``` 结尾
    if response.endswith('```'):
        response = response[:-3].strip()
    
    return response

class DocumentParserService(BaseAnalysisService):
    """文档解析服务类 - 实现6阶段解析流程"""
    
    async def analyze(self, task_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行文档解析分析 - 6阶段流程
        
        Args:
            task_id: 任务ID
            input_data: 包含文件内容、文件类型等信息
            
        Returns:
            符合document_analyze.md规范的解析结果
        """
        start_time = time.time()
        
        try:
            # 提取输入数据
            file_content = input_data.get("file_content", "")
            file_type = input_data.get("file_type", "")
            file_name = input_data.get("file_name", "")
            file_size = len(file_content.encode('utf-8'))
            
            self._log_analysis_start(task_id, "文档解析", len(file_content))
            
            # 阶段1: 格式识别
            file_format = await self._stage1_format_recognition(file_name, file_size, file_type, file_content)
            
            # 阶段2: 生成摘要及内容
            document_structure = await self._stage2_structure_analysis(file_content)
       
            # 构建符合规范的最终结果
            parsing_result = {
                "fileFormat": file_format,
                "documentStructure": document_structure,
                "notes": {"model": self._get_model_name()}
                
            }
            # 打印解析结果
            self.logger.info(f"文档解析结果: {parsing_result}")
            
            duration = time.time() - start_time
            self._log_analysis_complete(task_id, "文档解析", duration, len(str(parsing_result)))
            
            return self._create_response(
                success=True,
                data=parsing_result,
                metadata={"analysis_duration": duration}
            )
            
        except Exception as e:
            self._log_error(task_id, "文档解析", e)
            return self._create_response(
                success=False,
                error=f"文档解析失败: {str(e)}"
            )
    
    async def _stage1_format_recognition(self, file_name: str, file_size: int, file_type: str, content: str) -> Dict[str, Any]:
        """阶段1: 格式识别"""
        
        # 提取文件扩展名
        file_extension = file_name.split('.')[-1] if '.' in file_name else 'unknown'
         # 提取文件名
        file_first_name = file_name.split('.')[0] if '.' in file_name else file_name

        # 基础信息统计
        lines = content.split('\n')
        words = content.split()
        empty_lines = sum(1 for line in lines if not line.strip())
        
        # 语言检测
        chinese_chars = sum(1 for char in content if '\u4e00' <= char <= '\u9fff')
        english_chars = sum(1 for char in content if char.isalpha() and ord(char) < 128)
        language = "中文" if chinese_chars > english_chars else "英文" if english_chars > 0 else "unknown"
        
        # 格式置信度评估
        confidence = 0.9
        if file_extension in ['md', 'txt', 'doc', 'docx', 'pdf']:
            confidence = 0.95
        elif file_type and 'text' in file_type:
            confidence = 0.85
        
        return {
            "primaryType": self._determine_primary_type(file_extension, content),
            "subType": file_extension,
            "encoding": "utf-8",
            "confidence": confidence,
             "fileName": file_first_name,
            "basicInfo": {
                "fileSize": file_size,
                "estimatedPages": max(1, len(lines) // 50),  # 估算页数
                "language": language,
                "charset": "utf-8" 
            },
            "technicalDetails": {
                "lineCount": len(lines),
                "wordCount": len(words),
                "charCount": len(content),
                "emptyLines": empty_lines
            }
        }
    
    async def _stage2_structure_analysis(self, content: str) -> Dict[str, Any]:
        """阶段2: 结构解析"""
        
        system_prompt = """你是专业的文档结构分析专家。请分析文档的逻辑结构和物理结构。"""
        
        # 安全地处理文档内容，避免格式化冲突
        safe_content = content[:12000].replace('{', '{{').replace('}', '}}')
        user_prompt = f"""请分析以下文档的结构并返回JSON格式：

文档内容：
{safe_content}

请按以下格式返回：
{{
  "contentSummary": {{
    "abstract": "摘要",
    "functionCount": "功能数量",
    "functionName": ["功能名称列表"],
    "apiCount": "API数量", 
    "apiName": ["授信审批流程优化","授信审批流程优化"],
    "dbChangeCount": "数据库变更数量",
    "dbChangeName": ["数据库变更名称列表"],
    "mqCount": "MQ数量",
    "mqName": ["MQ名称列表"],
    "timerCount": "定时任务数量",
    "timerName": ["定时任务名称列表"]
  }},

  "contentKeyWord": {{
    "keywords": ["关键词列表"],
    "primaryKeywords": [
        {{
            "keyword": "关键词",  
            "frequency": "出现频次",  
            "importance": "重要性分数（0-1)", 
            "positions": ["出现位置列表"],  
            "context": ["上下文片段"]  
        }}
    ],
    "phrases": [
              {{
                  "phrase": "短语", 
                  "frequency": "频次",   
                  "significance": "重要性"
              }}
          ],
    "semanticClusters": [
        {{
            "clusterName": "语义簇名称",  
            "keywords": ["相关关键词"],   
            "coherenceScore": "连贯性分数"
        }}
    ]
  }},
  "metadata": {{
    "userRole": ["用户角色，如果文档中没有默认所有人可操作"], 
    "targetAudience": ["目标受众"]
  }}
}}"""
        
        try:
            # 安全的日志记录，避免格式化错误
            content_preview = content[:5000].replace('{', '{{').replace('}', '}}')
            logger.info(f"开始调用LLM进行结构分析，内容长度: {len(content)}, 预览: {content_preview}")
            response = await self._call_llm(user_prompt, system_prompt, max_tokens=16384)
            if response:
                logger.info("LLM结构分析成功,开始解析JSON响应")
                # 安全的响应日志记录
                response_preview = response[:5000].replace('{', '{{').replace('}', '}}')
                logger.info(f"LLM响应预览: {response_preview}")
                cleaned_response = clean_llm_response(response)
                result = json.loads(cleaned_response)
                logger.info(f"JSON解析成功,结果包含 {len(result)} 个顶级键")
                return result
        except Exception as e:
            # 安全地记录错误，避免格式化问题
            error_msg = str(e).replace('{', '{{').replace('}', '}}')
            logger.error(f"结构分析失败，错误: {error_msg}")
            # 降级到基础结构分析
            return self._basic_structure_analysis(content)
        
        return self._basic_structure_analysis(content)
    
    async def _stage3_content_extraction(self, content: str) -> Dict[str, Any]:
        """阶段3: 内容元素提取"""
        
        system_prompt = """你是专业的文档内容提取专家。请全面提取文档中的各类内容元素。"""
        
        # 安全地处理文档内容，避免格式化冲突
        safe_content = content[:2500].replace('{', '{{').replace('}', '}}')
        user_prompt = f"""请提取以下文档的内容元素并返回JSON格式：

文档内容：
{safe_content}

请按以下格式返回：
{{
  "textContent": {{
    "paragraphs": "段落数量",
    "sentences": "句子数量",
    "textBlocks": [
      {{
        "type": "paragraph/quote/note",
        "content": "内容片段",
        "location": "位置信息",
        "formatting": "格式信息"
      }}
    ]
  }},
  "structuredContent": {{
    "tables": [
      {{
        "caption": "表格标题",
        "rows": "行数",
        "columns": "列数",
        "headers": ["列标题"],
        "location": "位置信息",
        "dataType": "数据类型"
      }}
    ],
    "lists": [
      {{
        "type": "ordered/unordered",
        "items": ["列表项"],
        "nested": "是否嵌套",
        "location": "位置信息"
      }}
    ]
  }},
  "mediaContent": {{
    "images": [
      {{
        "altText": "替代文本",
        "caption": "图片说明",
        "location": "位置信息",
        "type": "图片类型"
      }}
    ],
    "links": [
      {{
        "text": "链接文本",
        "url": "链接地址",
        "type": "internal/external",
        "location": "位置信息"
      }}
    ]
  }},
  "codeContent": {{
    "inlineCode": "行内代码数量",
    "codeBlocks": [
      {{
        "language": "编程语言",
        "lines": "代码行数",
        "content": "代码内容(前100字符)",
        "location": "位置信息"
      }}
    ]
  }}
}}"""
        
        try:
            response = await self._call_llm(user_prompt, system_prompt, max_tokens=16384)
            if response:
                cleaned_response = clean_llm_response(response)
                return json.loads(cleaned_response)
        except Exception as e:
            # 安全地记录错误，避免格式化问题
            error_msg = str(e).replace('{', '{{').replace('}', '}}')
            logger.error(f"内容提取失败，错误: {error_msg}")
            # 降级到基础内容提取
            return self._basic_content_extraction(content)
        
        return self._basic_content_extraction(content)
    
    async def _stage4_quality_analysis(self, content: str) -> Dict[str, Any]:
        """阶段4: 质量分析"""
        
        system_prompt = """你是专业的文档质量分析专家。请从可读性、完整性、格式一致性等维度评估文档质量。"""
        
        # 安全地处理文档内容，避免格式化冲突
        safe_content = content[:2000].replace('{', '{{').replace('}', '}}')
        user_prompt = f"""请分析以下文档的质量并返回JSON格式：

文档内容：
{safe_content}

请按以下格式返回：
{{
  "readability": {{
    "score": "可读性评分(1-10)",
    "factors": {{
      "languageClarity": "语言清晰度(1-5)",
      "structureClarity": "结构清晰度(1-5)",
      "terminologyConsistency": "术语一致性(1-5)",
      "sentenceComplexity": "句子复杂度评估"
    }},
    "issues": ["具体的可读性问题"],
    "suggestions": ["改进建议"]
  }},
  "completeness": {{
    "score": "完整性评分(1-10)",
    "assessment": {{
      "contentCoverage": "内容覆盖度",
      "logicalFlow": "逻辑流畅性",
      "missingElements": ["缺失的重要元素"],
      "redundantContent": ["冗余内容识别"]
    }}
  }},
  "formatConsistency": {{
    "score": "格式一致性评分(1-10)",
    "issues": {{
      "headingInconsistency": "标题格式不一致",
      "listFormatting": "列表格式问题",
      "codeFormatting": "代码格式问题",
      "linkFormatting": "链接格式问题"
    }}
  }},
  "overallQuality": {{
    "score": "综合质量评分(1-10)",
    "grade": "质量等级(Excellent/Good/Fair/Poor)",
    "strengths": ["文档优点"],
    "weaknesses": ["需要改进的方面"],
    "recommendations": ["具体改进建议"]
  }}
}}"""
        
        try:
            response = await self._call_llm(user_prompt, system_prompt, max_tokens=16384)
            if response:
                cleaned_response = clean_llm_response(response)
                return json.loads(cleaned_response)
        except Exception as e:
            # 安全地记录错误，避免格式化问题
            error_msg = str(e).replace('{', '{{').replace('}', '}}')
            logger.error(f"质量分析失败，错误: {error_msg}")
            # 降级到基础质量分析
            return self._basic_quality_analysis(content)
        
        return self._basic_quality_analysis(content)
    
    async def _stage5_metadata_extraction(self, content: str) -> Dict[str, Any]:
        """阶段5: 元数据提取"""
        
        system_prompt = """你是专业的文档元数据提取专家。请从文档内容中提取各类元数据信息。"""
        
        # 安全地处理文档内容，避免格式化冲突
        safe_content = content[:2000].replace('{', '{{').replace('}', '}}')
        user_prompt = f"""请提取以下文档的元数据并返回JSON格式：

文档内容：
{safe_content}

请按以下格式返回：
{{
  "documentInfo": {{
    "title": "文档标题",
    "subtitle": "副标题",
    "documentType": "文档类型(需求文档/设计文档/用户手册等)",
    "subject": "主题领域",
    "description": "文档描述"
  }},
  "authorshipInfo": {{
    "author": "作者信息",
    "organization": "所属组织",
    "contact": "联系方式",
    "contributors": ["贡献者列表"]
  }},
  "versionInfo": {{
    "version": "版本号",
    "releaseDate": "发布日期",
    "lastModified": "最后修改时间",
    "changeLog": ["版本变更记录"],
    "status": "文档状态"
  }},
  "projectInfo": {{
    "projectName": "项目名称",
    "projectPhase": "项目阶段",
    "targetAudience": "目标受众",
    "confidentialityLevel": "保密级别"
  }},
  "technicalInfo": {{
    "dependencies": ["依赖项"],
    "platforms": ["目标平台"],
    "technologies": ["涉及技术"],
    "standards": ["遵循标准"]
  }}
}}"""
        
        try:
            response = await self._call_llm(user_prompt, system_prompt, max_tokens=16384)
            if response:
                cleaned_response = clean_llm_response(response)
                return json.loads(cleaned_response)
        except Exception as e:
            # 安全地记录错误，避免格式化问题
            error_msg = str(e).replace('{', '{{').replace('}', '}}')
            logger.error(f"元数据提取失败，错误: {error_msg}")
            # 降级到基础元数据提取
            return self._basic_metadata_extraction(content)
        
        return self._basic_metadata_extraction(content)
    
    async def _stage6_summary_keywords(self, content: str) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """阶段6: 摘要和关键词生成"""
        
        system_prompt = """你是专业的文档摘要和关键词生成专家。请基于文档内容生成高质量的摘要和关键词。"""
        
        # 安全地处理文档内容，避免格式化冲突
        safe_content = content[:3000].replace('{', '{{').replace('}', '}}')
        user_prompt = f"""请为以下文档生成摘要和关键词并返回JSON格式：

文档内容：
{safe_content}

请按以下格式返回：
{{
  "contentSummary": {{
    "executiveSummary": "执行摘要(100-150字)",
    "detailedSummary": "详细摘要(300-500字)",
    "keyPoints": [
      "关键要点1",
      "关键要点2",
      "关键要点3"
    ],
    "mainTopics": [
      {{
        "topic": "主题名称",
        "description": "主题描述",
        "importance": "重要程度(1-5)"
      }}
    ]
  }},
  "keywords": {{
    "primaryKeywords": ["核心关键词(5-8个)"],
    "secondaryKeywords": ["次要关键词(8-12个)"],
    "technicalTerms": ["技术术语"],
    "domainSpecific": ["领域特定词汇"],
    "phrases": ["重要短语"]
  }},
  "insights": {{
    "documentPurpose": "文档目的",
    "targetOutcome": "预期成果",
    "actionItems": ["行动项"],
    "decisions": ["决策点"],
    "assumptions": ["假设条件"]
  }}
}}"""
        
        try:
            response = await self._call_llm(user_prompt, system_prompt, max_tokens=16384)
            if response:
                cleaned_response = clean_llm_response(response)
                result = json.loads(cleaned_response)
                return result.get("contentSummary", {}), result.get("keywords", {})
        except Exception as e:
            # 安全地记录错误，避免格式化问题
            error_msg = str(e).replace('{', '{{').replace('}', '}}')
            logger.error(f"摘要关键词生成失败，错误: {error_msg}")
            # 降级to基础摘要关键词生成
            return self._basic_summary_keywords(content)
        
        return self._basic_summary_keywords(content)
    
    # ============ 降级处理方法 ============
    
    def _determine_primary_type(self, extension: str, content: str) -> str:
        """确定文档主要类型"""
        extension_map = {
            'md': 'markdown',
            'txt': 'text',
            'doc': 'word',
            'docx': 'word',
            'pdf': 'pdf',
            'html': 'html',
            'htm': 'html'
        }
        
        if extension.lower() in extension_map:
            return extension_map[extension.lower()]
        
        # 基于内容判断
        if content.startswith('#') or '##' in content:
            return 'markdown'
        elif '<html' in content.lower() or '<div' in content.lower():
            return 'html'
        else:
            return 'text'
    
    def _basic_structure_analysis(self, content: str) -> Dict[str, Any]:
        """基础结构分析（降级方案）"""
        lines = content.split('\n')
        sections = []
        has_title = False
        max_depth = 0
        
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                max_depth = max(max_depth, level)
                if level == 1:
                    has_title = True
                sections.append({
                    "level": level,
                    "title": line.lstrip('#').strip(),
                    "startLine": i + 1,
                    "endLine": i + 1,
                    "subsections": 0
                })
        
        return {
            "hierarchy": {
                "hasTitle": has_title,
                "maxDepth": max_depth,
                "sections": sections
            },
            "navigation": {
                "hasTOC": "目录" in content or "Table of Contents" in content,
                "tocLocation": "unknown",
                "pageNumbers": False,
                "crossReferences": 0
            },
            "organization": {
                "structureType": "hierarchical" if sections else "linear",
                "coherence": 4,
                "completeness": 4
            }
        }
    
    def _basic_content_extraction(self, content: str) -> Dict[str, Any]:
        """基础内容提取（降级方案）"""
        lines = content.split('\n')
        paragraphs = [line for line in lines if line.strip() and not line.startswith('#')]
        
        lists = []
        code_blocks = []
        links = []
        
        for i, line in enumerate(lines):
            if line.strip().startswith(('- ', '* ', '+ ')) or (line.strip() and line.strip()[0].isdigit() and '. ' in line):
                lists.append({
                    "type": "ordered" if line.strip()[0].isdigit() else "unordered",
                    "items": [line.strip()],
                    "nested": False,
                    "location": f"line {i+1}"
                })
            
            if line.strip().startswith('```') or line.startswith('    '):
                code_blocks.append({
                    "language": "unknown",
                    "lines": 1,
                    "content": line[:100],
                    "location": f"line {i+1}"
                })
            
            if 'http' in line or 'www.' in line:
                links.append({
                    "text": line.strip(),
                    "url": "extracted_from_content",
                    "type": "external",
                    "location": f"line {i+1}"
                })
        
        return {
            "textContent": {
                "paragraphs": len(paragraphs),
                "sentences": len([s for p in paragraphs for s in p.split('.') if s.strip()]),
                "textBlocks": [{"type": "paragraph", "content": p[:200], "location": "auto", "formatting": "plain"} for p in paragraphs[:5]]
            },
            "structuredContent": {
                "tables": [],
                "lists": lists
            },
            "mediaContent": {
                "images": [],
                "links": links
            },
            "codeContent": {
                "inlineCode": content.count('`'),
                "codeBlocks": code_blocks
            }
        }
    
    def _basic_quality_analysis(self, content: str) -> Dict[str, Any]:
        """基础质量分析（降级方案）"""
        words = content.split()
        sentences = content.split('.')
        avg_words_per_sentence = len(words) / max(len(sentences), 1)
        
        # 简单的质量评估
        readability_score = 8 if avg_words_per_sentence < 20 else 6 if avg_words_per_sentence < 30 else 4
        
        return {
            "readability": {
                "score": readability_score,
                "factors": {
                    "languageClarity": 4,
                    "structureClarity": 4,
                    "terminologyConsistency": 4,
                    "sentenceComplexity": "中等"
                },
                "issues": ["句子长度适中" if avg_words_per_sentence < 25 else "部分句子较长"],
                "suggestions": ["保持现有写作风格"]
            },
            "completeness": {
                "score": 7,
                "assessment": {
                    "contentCoverage": "良好",
                    "logicalFlow": "合理",
                    "missingElements": [],
                    "redundantContent": []
                }
            },
            "formatConsistency": {
                "score": 8,
                "issues": {
                    "headingInconsistency": False,
                    "listFormatting": False,
                    "codeFormatting": False,
                    "linkFormatting": False
                }
            },
            "overallQuality": {
                "score": 7,
                "grade": "Good",
                "strengths": ["内容丰富", "结构清晰"],
                "weaknesses": ["可进一步优化"],
                "recommendations": ["增加更多具体示例"]
            }
        }
    
    def _basic_metadata_extraction(self, content: str) -> Dict[str, Any]:
        """基础元数据提取（降级方案）"""
        lines = content.split('\n')
        title = "unknown"
        
        # 尝试从第一行获取标题
        for line in lines:
            line = line.strip()
            if line:
                if line.startswith('#'):
                    title = line.lstrip('#').strip()
                else:
                    title = line
                break
        
        return {
            "documentInfo": {
                "title": title,
                "subtitle": "not_specified",
                "documentType": "文档",
                "subject": "unknown",
                "description": content[:200] + "..." if len(content) > 200 else content
            },
            "authorshipInfo": {
                "author": "not_specified",
                "organization": "not_specified",
                "contact": "not_specified",
                "contributors": []
            },
            "versionInfo": {
                "version": "not_specified",
                "releaseDate": "not_specified",
                "lastModified": "not_specified",
                "changeLog": [],
                "status": "unknown"
            },
            "projectInfo": {
                "projectName": "not_specified",
                "projectPhase": "not_specified",
                "targetAudience": "not_specified",
                "confidentialityLevel": "not_specified"
            },
            "technicalInfo": {
                "dependencies": [],
                "platforms": [],
                "technologies": [],
                "standards": []
            }
        }
    
    def _basic_summary_keywords(self, content: str) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """基础摘要关键词生成（降级方案）"""
        words = content.split()
        sentences = content.split('.')
        
        # 生成简单摘要
        summary = content[:300] + "..." if len(content) > 300 else content
        
        # 提取高频词作为关键词
        word_freq = {}
        for word in words:
            word = word.strip('.,!?;:').lower()
            if len(word) > 2 and word.isalpha():
                word_freq[word] = word_freq.get(word, 0) + 1
        
        primary_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:6]
        primary_keywords = [word for word, freq in primary_keywords]
        
        content_summary = {
            "executiveSummary": summary[:150],
            "detailedSummary": summary,
            "keyPoints": sentences[:3],
            "mainTopics": [
                {
                    "topic": "主要内容",
                    "description": "文档主要讨论内容",
                    "importance": 5
                }
            ]
        }
        
        keywords = {
            "primaryKeywords": primary_keywords,
            "secondaryKeywords": primary_keywords[6:12] if len(primary_keywords) > 6 else [],
            "technicalTerms": [],
            "domainSpecific": [],
            "phrases": []
        }
        
        return content_summary, keywords 
    
    def _get_model_name(self) -> str:
        """获取当前使用的模型名称"""
        if not self.llm_client:
            return "no_llm_client"
        
        # 尝试从不同的客户端类型获取模型名称
        if hasattr(self.llm_client, 'config') and hasattr(self.llm_client.config, 'model_id'):
            return self.llm_client.config.model_id
        elif hasattr(self.llm_client, 'model'):
            return self.llm_client.model
        elif hasattr(self.llm_client, 'model_name'):
            return self.llm_client.model_name
        else:
            return "unknown_model"