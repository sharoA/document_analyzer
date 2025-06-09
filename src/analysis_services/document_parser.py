"""
文档解析服务
使用大模型进行智能文档解析和结构化信息提取
"""

import json
import time
from typing import Dict, Any, List
from .base_service import BaseAnalysisService

class DocumentParserService(BaseAnalysisService):
    """文档解析服务类"""
    
    async def analyze(self, task_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行文档解析分析
        
        Args:
            task_id: 任务ID
            input_data: 包含文件内容、文件类型等信息
            
        Returns:
            解析结果字典
        """
        start_time = time.time()
        
        try:
            # 提取输入数据
            file_content = input_data.get("file_content", "")
            file_type = input_data.get("file_type", "")
            file_name = input_data.get("file_name", "")
            
            self._log_analysis_start(task_id, "文档解析", len(file_content))
            
            # 基础信息提取
            basic_info = self._extract_basic_info(file_content, file_type)
            
            # 使用大模型进行智能解析
            llm_analysis = await self._llm_document_analysis(file_content, file_type, file_name)
            
            # 结构化信息提取
            structured_info = await self._extract_structured_info(file_content, file_type)
            
            # 合并解析结果
            parsing_result = {
                "text_content": file_content,
                "basic_info": basic_info,
                "llm_analysis": llm_analysis,
                "structured_info": structured_info,
                "metadata": {
                    "parsing_method": "LLM智能解析",
                    "file_type": file_type,
                    "file_name": file_name,
                    "content_length": len(file_content),
                    "parsing_time": time.time() - start_time
                }
            }
            
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
    
    def _extract_basic_info(self, content: str, file_type: str) -> Dict[str, Any]:
        """提取基础信息"""
        lines = content.split('\n')
        words = content.split()
        
        return {
            "character_count": len(content),
            "word_count": len(words),
            "line_count": len(lines),
            "paragraph_count": len([line for line in lines if line.strip()]),
            "file_type": file_type,
            "encoding": "utf-8",
            "language": self._detect_language(content)
        }
    
    def _detect_language(self, content: str) -> str:
        """简单的语言检测"""
        chinese_chars = sum(1 for char in content if '\u4e00' <= char <= '\u9fff')
        english_chars = sum(1 for char in content if char.isalpha() and ord(char) < 128)
        
        if chinese_chars > english_chars:
            return "中文"
        elif english_chars > 0:
            return "英文"
        else:
            return "未知"
    
    async def _llm_document_analysis(self, content: str, file_type: str, file_name: str) -> Dict[str, Any]:
        """使用大模型进行文档分析"""
        system_prompt = """你是一个专业的文档分析专家。请分析给定的文档内容，提取关键信息并返回JSON格式的结果。

请分析以下方面：
1. 文档类型和用途
2. 主要内容摘要
3. 关键信息点
4. 文档结构分析
5. 重要实体识别（人名、地名、组织、时间等）
6. 技术要求或业务需求（如果有）

返回格式：
{
    "document_type": "文档类型",
    "purpose": "文档用途",
    "summary": "内容摘要",
    "key_points": ["关键点1", "关键点2"],
    "structure": {
        "sections": ["章节1", "章节2"],
        "has_tables": true/false,
        "has_images": true/false,
        "has_code": true/false
    },
    "entities": {
        "persons": ["人名"],
        "organizations": ["组织名"],
        "locations": ["地名"],
        "dates": ["时间"]
    },
    "requirements": {
        "technical": ["技术要求"],
        "business": ["业务需求"],
        "functional": ["功能需求"]
    }
}"""
        
        user_prompt = f"""请分析以下文档：

文件名：{file_name}
文件类型：{file_type}
文档内容：
{content[:3000]}  # 限制内容长度避免token超限

请按照指定的JSON格式返回分析结果。"""
        
        try:
            response = await self._call_llm(user_prompt, system_prompt, max_tokens=2000)
            if response:
                # 尝试解析JSON
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    # 如果JSON解析失败，返回原始响应
                    return {"raw_response": response, "parse_error": "JSON解析失败"}
            else:
                return {"error": "LLM响应为空"}
        except Exception as e:
            return {"error": f"LLM分析失败: {str(e)}"}
    
    async def _extract_structured_info(self, content: str, file_type: str) -> Dict[str, Any]:
        """提取结构化信息"""
        structured_info = {
            "headers": [],
            "tables": [],
            "lists": [],
            "code_blocks": [],
            "links": [],
            "special_formats": []
        }
        
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # 检测标题
            if line.startswith('#') or (line and i > 0 and lines[i-1].strip() == ''):
                if any(keyword in line.lower() for keyword in ['章', '节', '部分', 'chapter', 'section']):
                    structured_info["headers"].append({
                        "level": line.count('#') if line.startswith('#') else 1,
                        "text": line.lstrip('#').strip(),
                        "line_number": i + 1
                    })
            
            # 检测列表
            if line.startswith(('- ', '* ', '+ ')) or (line and line[0].isdigit() and '. ' in line):
                structured_info["lists"].append({
                    "type": "ordered" if line[0].isdigit() else "unordered",
                    "text": line,
                    "line_number": i + 1
                })
            
            # 检测代码块
            if line.startswith('```') or line.startswith('    ') and line.strip():
                structured_info["code_blocks"].append({
                    "text": line,
                    "line_number": i + 1
                })
            
            # 检测链接
            if 'http' in line or 'www.' in line:
                structured_info["links"].append({
                    "text": line,
                    "line_number": i + 1
                })
        
        return structured_info 