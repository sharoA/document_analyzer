#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库初始化脚本 - Weaviate 版本
将D:\knowledge_base\链数_LS\需求文档\LS-1(YS-72)_需求文档-链数一期V1.8.docx内容转换为向量并存储到 Weaviate 中
使用 LangChain 框架进行 RAG
"""


import os
import re
import uuid
import json
import logging
import hashlib
import shutil
import base64
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from io import BytesIO


# 文件处理相关
try:
    import docx2txt
    DOCX2TXT_AVAILABLE = True
except ImportError:
    DOCX2TXT_AVAILABLE = False

try:
    import mammoth
    MAMMOTH_AVAILABLE = True
except ImportError:
    MAMMOTH_AVAILABLE = False

# 向量化和嵌入
from sentence_transformers import SentenceTransformer

# Weaviate 和 LangChain
import weaviate
import weaviate.classes as wvc
from weaviate.auth import AuthApiKey
from langchain_community.vectorstores import Weaviate as LangChainWeaviate
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

# 项目配置和 Redis
try:
    from ..resource.config import get_config
    from .redis_util import get_redis_manager
    from .weaviate_helper import get_weaviate_client
except ImportError:
    import sys
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, project_root)
    from src.resource.config import get_config
    from src.utils.redis_util import get_redis_manager
    from src.utils.weaviate_helper import get_weaviate_client

# 已在上面定义了相关的导入检查


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class KnowledgeBaseInitializer:
    """知识库初始化器"""
    
    def __init__(self, knowledge_base_path: str = "D:\\knowledge_base"):
        """
        初始化知识库处理器
        
        Args:
            knowledge_base_path: 知识库根目录路径
        """
        # 初始化LLM客户端以使用_call_llm方法
        self.llm_client = None
        self._initialize_llm_client()
        
        self.knowledge_base_path = Path(knowledge_base_path)
        self.weaviate_client = None
        self.redis_manager = None
        self.embeddings_model = None
        self.langchain_embeddings = None
        self.langchain_vectorstore = None
        self.text_splitter = None

        
        # 支持的文件类型
        self.supported_extensions = {'.docx'}
        
        # 图片输出目录 - 按要求设置为指定路径
        self.image_output_dir = self.knowledge_base_path / "链数_LS" / "需求文档" / "需求文档图片"
        
        # 初始化组件
        self._initialize_components()
    
    def _initialize_llm_client(self):
        """初始化LLM客户端"""
        try:
            from ..utils.volcengine_client import VolcengineClient
            config = get_config()
            volcengine_config = config.get_volcengine_config()
            self.llm_client = VolcengineClient(volcengine_config)
            logger.info("✅ LLM客户端初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ LLM客户端初始化失败: {e}")
            self.llm_client = None
    
    def _call_llm(self, prompt: str, system_prompt: str = None, max_tokens: int = 4000) -> Optional[str]:
        """
        调用LLM进行分析
        
        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            max_tokens: 最大token数
            
        Returns:
            模型响应文本
        """
        if not self.llm_client:
            logger.warning("LLM客户端未初始化")
            return None
        
        try:
            response = self.llm_client.chat(
                messages=[
                    {"role": "system", "content": system_prompt or "你是一个专业的文档分析助手"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens
            )
            return response
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            return None
    
    def _initialize_components(self):
        """初始化各种组件"""
        try:
            # 初始化 Weaviate 客户端
            self.weaviate_client = get_weaviate_client()
            logger.info("✅ Weaviate 客户端初始化成功")
            
            # 初始化 Redis 管理器
            self.redis_manager = get_redis_manager()
            logger.info("✅ Redis 管理器初始化成功")
            
            # 初始化嵌入模型 - 使用bge-large-zh（1024维，中文优化）
            self.embeddings_model = SentenceTransformer('BAAI/bge-large-zh')
            logger.info("✅ 嵌入模型加载成功 (bge-large-zh, 1024维，中文优化)")
            
            # 初始化 LangChain 嵌入模型
            self.langchain_embeddings = SentenceTransformerEmbeddings(
                model_name='BAAI/bge-large-zh'
            )
            logger.info("✅ LangChain 嵌入模型初始化成功")
            
            # 初始化文本分割器
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50,
                length_function=len,
                separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""]
            )
            logger.info("✅ 文本分割器初始化成功")
            
            # 创建图片输出目录
            self.image_output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ 图片输出目录创建成功: {self.image_output_dir}")
            
            logger.info("✅ 组件初始化完成")
            
        except Exception as e:
            logger.error(f"❌ 组件初始化失败: {e}")
            raise


    def _create_weaviate_schema(self):
        """创建 Weaviate 模式 - 按要求定义Document类"""
        try:
            collection_name = "Document"
            
            # 检查集合是否已存在
            if self.weaviate_client.collections.exists(collection_name):
                logger.info(f"📋 集合 {collection_name} 已存在，跳过创建")
                return collection_name
            
            # 创建集合 - 按要求设置vectorizer: none
            self.weaviate_client.collections.create(
                name=collection_name,
                vectorizer_config=wvc.config.Configure.Vectorizer.none(),
                properties=[
                    wvc.config.Property(name="content", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="file_path", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="file_name", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="project", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="file_type", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="source_type", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="image_path", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="section", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="sheet_name", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="chunk_index", data_type=wvc.config.DataType.INT),
                    wvc.config.Property(name="created_at", data_type=wvc.config.DataType.DATE),
                    wvc.config.Property(name="ocr_text", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="caption", data_type=wvc.config.DataType.TEXT)
                ]
            )
            
            logger.info(f"✅ Weaviate 集合创建成功: {collection_name}")
            return collection_name
            
        except Exception as e:
            logger.error(f"❌ Weaviate 集合创建失败: {e}")
            raise
     
    def _load_image_caption_model(self):
        """延迟加载图片描述模型"""
        if self.blip_processor is None:
            try:
                self.blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
                self.blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
                logger.info("✅ 图片描述模型加载成功")
            except Exception as e:
                logger.error(f"❌ 图片描述模型加载失败: {e}")
                self.blip_processor = None
                self.blip_model = None
    
    def _get_cache_key(self, file_path: str, cache_type: str) -> str:
        """生成缓存键 - 按要求使用指定格式"""
        return f"file:{file_path}:{cache_type}"
    
    def _get_cached_result(self, file_path: str, cache_type: str) -> Optional[Any]:
        """获取缓存结果"""
        try:
            cache_key = self._get_cache_key(file_path, cache_type)
            return self.redis_manager.get(cache_key, use_prefix=False)
        except Exception as e:
            logger.warning(f"获取缓存失败 {file_path}:{cache_type} - {e}")
            return None
    
    def _set_cached_result(self, file_path: str, cache_type: str, result: Any, ttl: int = 86400):
        """设置缓存结果"""
        try:
            cache_key = self._get_cache_key(file_path, cache_type)
            self.redis_manager.set(cache_key, result, ttl=ttl, use_prefix=False)
        except Exception as e:
            logger.warning(f"设置缓存失败 {file_path}:{cache_type} - {e}")
    
    def _extract_project_name(self, file_path: Path) -> str:
        """从文件路径提取项目名称"""
        try:
            # 获取相对于知识库根目录的路径
            relative_path = file_path.relative_to(self.knowledge_base_path)
            parts = relative_path.parts
            
            # 按要求，将目录结构存储为LS
            if len(parts) >= 1:
                # 检查是否包含特定的项目标识
                for part in parts:
                    if 'zqyl-ls' in part.lower():
                        return 'zqyl-ls'
                    elif 'ls' in part.lower() or '链数' in part:
                        return 'LS'
            
            # 默认返回LS
            return "LS"
            
        except Exception as e:
            logger.warning(f"提取项目名称失败 {file_path}: {e}")
            return "LS"
        
    def _preprocess_document(self, document_content: str) -> List[Dict[str, Any]]:
        
        """
        Step 1: 文档预处理
        将markdown文档或普通文本拆解为结构化内容块
        
        Args:
            document_content: markdown格式或普通文本的文档内容
            
        Returns:
            结构化内容块列表
        """
        structured_chunks = []
        
        if not document_content or not document_content.strip():
            logger.warning("文档内容为空，无法生成结构化块")
            return structured_chunks
        
        # 按行分割文档
        lines = document_content.split('\n')
        current_section = ""
        current_content = []
        current_level = 0
        has_markdown_headers = any(line.strip().startswith('#') for line in lines)
        
        logger.info(f"文档总行数: {len(lines)}, 是否包含Markdown标题: {has_markdown_headers}")
        
        if has_markdown_headers:
            # 处理Markdown格式文档
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
                            embedding = self.embeddings_model.encode(f"{current_section}\n{content_text}").tolist()
                            
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
                    embedding = self.embeddings_model.encode(f"{current_section}\n{content_text}").tolist()
                    
                    chunk = {
                        "section": current_section,
                        "content": content_text,
                        "level": current_level,
                        "embedding": embedding,
                        "image_refs": self._extract_image_refs(content_text)
                    }
                    structured_chunks.append(chunk)
        else:
            # 处理普通文本文档，按段落分割
            logger.info("处理普通文本文档，按段落分割")
            paragraphs = document_content.split('\n\n')
            
            for i, paragraph in enumerate(paragraphs):
                paragraph = paragraph.strip()
                if paragraph and len(paragraph) > 20:  # 过滤掉太短的段落
                    # 尝试从段落开头提取标题
                    lines_in_para = paragraph.split('\n')
                    first_line = lines_in_para[0].strip()
                    
                    # 生成段落标题
                    if len(first_line) < 100 and len(lines_in_para) > 1:
                        section_title = first_line
                        content = '\n'.join(lines_in_para[1:]).strip()
                    else:
                        section_title = f"段落 {i + 1}"
                        content = paragraph
                    
                    if content:
                        # 生成向量嵌入
                        embedding = self.embeddings_model.encode(f"{section_title}\n{content}").tolist()
                        
                        chunk = {
                            "section": section_title,
                            "content": content,
                            "level": 1,
                            "embedding": embedding,
                            "image_refs": self._extract_image_refs(content)
                        }
                        structured_chunks.append(chunk)
            
            # 如果按段落分割没有结果，使用文本分割器
            if not structured_chunks:
                logger.info("段落分割无结果，使用文本分割器")
                text_chunks = self.text_splitter.split_text(document_content)
                
                for i, text_chunk in enumerate(text_chunks):
                    if text_chunk.strip():
                        # 生成向量嵌入
                        embedding = self.embeddings_model.encode(text_chunk).tolist()
                        
                        chunk = {
                            "section": f"文本块 {i + 1}",
                            "content": text_chunk.strip(),
                            "level": 1,
                            "embedding": embedding,
                            "image_refs": self._extract_image_refs(text_chunk)
                        }
                        structured_chunks.append(chunk)
        
        logger.info(f"最终生成 {len(structured_chunks)} 个结构化块")
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
    
    def _delete_existing_document(self, file_name: str):
        """删除已存在的同名文档记录"""
        try:
            collection = self.weaviate_client.collections.get("Document")
            
            # 使用正确的查询语法，使用filters参数而不是where
            existing_docs = collection.query.fetch_objects(
                filters=wvc.query.Filter.by_property("file_name").equal(file_name)
            )
            
            if existing_docs.objects:
                logger.info(f"🗑️ 找到 {len(existing_docs.objects)} 条现有记录，开始删除...")
                
                # 删除所有匹配的记录
                for doc in existing_docs.objects:
                    collection.data.delete_by_id(doc.uuid)
                    
                logger.info(f"✅ 已删除 {len(existing_docs.objects)} 条记录")
            else:
                logger.info(f"📝 没有找到文件名为 {file_name} 的现有记录")
                
        except Exception as e:
            logger.error(f"❌ 删除现有记录失败: {e}")
            # 如果删除失败，我们继续处理，不要让这个错误阻止整个流程
            logger.warning(f"⚠️ 跳过删除步骤，继续处理文档")
            pass
    
    def _process_docx_file(self, file_path: Path) -> List[Document]:
        """处理Word文档文件"""
        try:
            logger.info(f"📄 开始处理Word文档: {file_path}")
            
            # 初始化documents列表
            documents = []
            
            #读取当前word文档，对当前文档提取文本转换成markdown格式      
            document_content = self.extract_text_from_file(file_path)
            
            #对当前文档进行预处理，转换成结构化内容块
            structured_chunks = self._preprocess_document(document_content)
                
            logger.info(f"📊 文档预处理完成，生成 {len(structured_chunks)} 个结构化块")
            
            # 为每个结构化块创建Document对象
            for i, chunk in enumerate(structured_chunks):
                # 准备元数据
                metadata = {
                    "file_path": str(file_path),
                    "file_name": file_path.name,
                    "project": "LS",
                    "file_type": "docx",
                    "source_type": "requirement_doc",
                    "section": chunk["section"],
                    "chunk_index": i,
                                            "created_at": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "image_refs": json.dumps(chunk["image_refs"], ensure_ascii=False),
                    "level": chunk["level"]
                }
                
                # 创建Document对象
                doc_obj = Document(
                    page_content=chunk["content"],
                    metadata=metadata
                )
                
                # 添加向量嵌入
                doc_obj.metadata["embedding"] = chunk["embedding"]
                
                documents.append(doc_obj)
            
            logger.info(f"✅ Word文档处理完成: {file_path.name}，生成 {len(documents)} 个文档块")
            return documents
            
        except Exception as e:
            logger.error(f"❌ 处理Word文档失败 {file_path}: {e}")
            raise
    def extract_text_from_file(self, file_path: str) -> str:
        """
        从文件路径读取文件内容并转换为Markdown或文本内容
        :param file_path: 文件路径
        :return: extracted_text
        """
        file_content = None
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                logger.info(f"从文件路径读取: {file_path}")
            except Exception as e:
                logger.warning(f"从文件路径读取失败: {e}")
        else:
            raise ValueError("无法获取文件内容，文件可能已被删除")

        # 处理文件内容
        try:
            file_name = os.path.basename(file_path)
            file_type = file_name.split('.')[-1] if '.' in file_name else ''

            if file_name.lower().endswith(('.doc', '.docx')) or 'word' in file_type.lower():
                logger.info(f"检测到Word文档，使用Markdown转换: {file_name}")
                transform_result = self.parse_word_document(file_content, file_name)
                extracted_text = transform_result.get("text_content", "Word文档解析失败")
                logger.info(f"解析结果长度: {len(extracted_text) if extracted_text else 0}")
                logger.info(f"解析结果前200字符: {extracted_text[:200] if extracted_text else 'None'}")
                if extracted_text and any(marker in extracted_text for marker in ['#', '|', '**', '*', '-']):
                    logger.info(f"Word文档已成功转换为Markdown格式，长度: {len(extracted_text)} 字符")
                else:
                    logger.warning("Word文档转换结果可能不是标准Markdown格式")
                    # 即使不是标准Markdown格式，只要有内容就继续处理
                    if extracted_text and extracted_text.strip() and extracted_text != "Word文档解析失败":
                        logger.info(f"继续处理文档内容，长度: {len(extracted_text)} 字符")
            else:
                logger.info(f"使用通用文件分析方法: {file_name}")
                # 对于非Word文档，暂时返回基础文本内容
                try:
                    extracted_text = file_content.decode('utf-8', errors='ignore')
                except:
                    extracted_text = "文件解析失败：无法读取文件内容"
        except Exception as e:
            logger.error(f"EnhancedAnalyzer使用失败: {e}，使用基础解析")
            if file_name.lower().endswith(('.doc', '.docx')) or 'word' in file_type.lower():
                extracted_text = f"Word文档解析失败: {str(e)}，建议检查文件格式或安装python-docx库"
            else:
                extracted_text = f"文件解析失败: {str(e)}"
        return extracted_text
    
    def _get_fallback_result(self, file_name: str, analysis_type: str, reason: str) -> Dict[str, Any]:
        """获取回退结果"""
        return {
            "text_content": f"{analysis_type}失败: {reason}",
            "file_type": "unknown",
            "file_name": file_name,
            "analysis_method": "fallback",
            "extraction_summary": {
                "status": "failed",
                "reason": reason
            }
        }
    
    def _handle_legacy_doc_file(self, file_content: bytes, file_name: str) -> Dict[str, Any]:
        """处理旧格式的.doc文件"""
        return self._get_fallback_result(file_name, "旧格式DOC文件解析", "不支持.doc格式，请转换为.docx格式")
    
    def _handle_invalid_word_file(self, file_content: bytes, file_name: str) -> Dict[str, Any]:
        """处理无效的Word文件"""
        return self._get_fallback_result(file_name, "无效Word文件", "文件结构不符合Word文档格式")
    
    def _handle_non_zip_file(self, file_content: bytes, file_name: str) -> Dict[str, Any]:
        """处理非ZIP格式文件"""
        return self._get_fallback_result(file_name, "非ZIP格式文件", "文件不是有效的ZIP格式")

    def parse_word_document(self, file_content: bytes, file_name: str) -> Dict[str, Any]:
        """
        解析Word文档 - 使用多种库的备用方案
        
        Args:
            file_content: Word文档的二进制内容
            file_name: 文件名
            
        Returns:
            解析结果字典
        """
        # 优先使用 mammoth 转换为 HTML 再转 Markdown
        if MAMMOTH_AVAILABLE:
            try:
                logger.info(f"尝试使用 mammoth 解析: {file_name}")
                file_stream = BytesIO(file_content)
                result = mammoth.convert_to_html(file_stream)
                html_content = result.value
                
                # 简单的HTML到Markdown转换
                markdown_content = self._html_to_markdown(html_content)
                
                return {
                    "text_content": markdown_content,
                    "file_type": "word",
                    "file_name": file_name,
                    "file_size": len(file_content),
                    "analysis_method": "mammoth_html_to_markdown",
                    "document_structure": {
                        "format": "markdown",
                        "conversion_messages": result.messages
                    },
                    "extraction_summary": {
                        "total_text_length": len(markdown_content),
                        "output_format": "markdown",
                        "method": "mammoth"
                    }
                }
            except Exception as e:
                logger.warning(f"mammoth 解析失败: {e}，尝试其他方法")
        
        # 备用方案：使用 docx2txt
        if DOCX2TXT_AVAILABLE:
            try:
                logger.info(f"尝试使用 docx2txt 解析: {file_name}")
                
                # 保存临时文件
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_file:
                    tmp_file.write(file_content)
                    tmp_file_path = tmp_file.name
                
                try:
                    # 使用 docx2txt 提取文本
                    text_content = docx2txt.process(tmp_file_path)
                    
                    # 简单的文本格式化为Markdown
                    markdown_content = self._text_to_markdown(text_content)
                    
                    return {
                        "text_content": markdown_content,
                        "file_type": "word",
                        "file_name": file_name,
                        "file_size": len(file_content),
                        "analysis_method": "docx2txt_to_markdown",
                        "document_structure": {
                            "format": "markdown"
                        },
                        "extraction_summary": {
                            "total_text_length": len(markdown_content),
                            "output_format": "markdown",
                            "method": "docx2txt"
                        }
                    }
                finally:
                    # 清理临时文件
                    if os.path.exists(tmp_file_path):
                        os.unlink(tmp_file_path)
                        
            except Exception as e:
                logger.warning(f"docx2txt 解析失败: {e}")
        
        # 最后的备用方案：返回错误信息
        return self._get_fallback_result(file_name, "Word解析", "所有Word解析库都不可用或解析失败")
    
    def _html_to_markdown(self, html_content: str) -> str:
        """
        将HTML内容转换为Markdown格式
        
        Args:
            html_content: HTML格式的内容
            
        Returns:
            Markdown格式的文本
        """
        try:
            import re
            
            # 移除HTML标签并转换为Markdown
            markdown_content = html_content
            
            # 转换标题
            for i in range(6, 0, -1):
                markdown_content = re.sub(f'<h{i}[^>]*>(.*?)</h{i}>', f'{"#" * i} \\1', markdown_content, flags=re.IGNORECASE | re.DOTALL)
            
            # 转换段落
            markdown_content = re.sub('<p[^>]*>(.*?)</p>', '\\1\n', markdown_content, flags=re.IGNORECASE | re.DOTALL)
            
            # 转换粗体
            markdown_content = re.sub('<strong[^>]*>(.*?)</strong>', '**\\1**', markdown_content, flags=re.IGNORECASE | re.DOTALL)
            markdown_content = re.sub('<b[^>]*>(.*?)</b>', '**\\1**', markdown_content, flags=re.IGNORECASE | re.DOTALL)
            
            # 转换斜体
            markdown_content = re.sub('<em[^>]*>(.*?)</em>', '*\\1*', markdown_content, flags=re.IGNORECASE | re.DOTALL)
            markdown_content = re.sub('<i[^>]*>(.*?)</i>', '*\\1*', markdown_content, flags=re.IGNORECASE | re.DOTALL)
            
            # 转换列表
            markdown_content = re.sub('<li[^>]*>(.*?)</li>', '- \\1', markdown_content, flags=re.IGNORECASE | re.DOTALL)
            markdown_content = re.sub('<[uo]l[^>]*>', '', markdown_content, flags=re.IGNORECASE)
            markdown_content = re.sub('</[uo]l>', '\n', markdown_content, flags=re.IGNORECASE)
            
            # 转换表格（简化处理）
            markdown_content = re.sub('<table[^>]*>.*?</table>', '[表格内容]', markdown_content, flags=re.IGNORECASE | re.DOTALL)
            
            # 移除剩余的HTML标签
            markdown_content = re.sub('<[^>]+>', '', markdown_content)
            
            # 清理多余的空行
            markdown_content = re.sub('\n\s*\n\s*\n', '\n\n', markdown_content)
            
            # 解码HTML实体
            import html
            markdown_content = html.unescape(markdown_content)
            
            return markdown_content.strip()
            
        except Exception as e:
            logger.error(f"HTML到Markdown转换失败: {e}")
            return html_content
    
    def _text_to_markdown(self, text_content: str) -> str:
        """
        将纯文本转换为Markdown格式
        
        Args:
            text_content: 纯文本内容
            
        Returns:
            Markdown格式的文本
        """
        try:
            if not text_content or not text_content.strip():
                return "文档内容为空"
            
            lines = text_content.split('\n')
            markdown_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    markdown_lines.append('')
                    continue
                
                # 检测可能的标题（全大写、较短、或包含数字编号）
                if (len(line) < 100 and 
                    (line.isupper() or 
                     re.match(r'^\d+[\.\)]\s*', line) or
                     re.match(r'^[一二三四五六七八九十]+[\.\)、]\s*', line) or
                     re.match(r'^第[一二三四五六七八九十\d]+[章节条]\s*', line))):
                    
                    # 判断标题级别
                    if re.match(r'^\d+[\.\)]\s*', line):
                        level = 2
                    elif re.match(r'^[一二三四五六七八九十]+[\.\)、]\s*', line):
                        level = 3
                    elif line.isupper():
                        level = 1
                    else:
                        level = 2
                        
                    markdown_lines.append('#' * level + ' ' + line)
                else:
                    # 普通段落
                    markdown_lines.append(line)
            
            result = '\n'.join(markdown_lines)
            
            # 清理多余的空行
            result = re.sub('\n\s*\n\s*\n', '\n\n', result)
            
            return result.strip()
            
        except Exception as e:
            logger.error(f"文本到Markdown转换失败: {e}")
            return text_content
    
    def _convert_word_to_markdown(self, doc, file_content: bytes, file_name: str) -> str:
        """
        将Word文档转换为Markdown格式 - 简化版本
        
        Args:
            doc: python-docx Document对象
            file_content: 原始文件内容
            file_name: 文件名
            
        Returns:
            Markdown格式的文本内容
        """
        markdown_parts = []
        
        try:
            # 处理段落
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text = paragraph.text.strip()
                    
                    # 检测标题级别（基于样式或格式）
                    if paragraph.style and paragraph.style.name:
                        style_name = paragraph.style.name.lower()
                        if 'heading' in style_name or '标题' in style_name:
                            # 提取标题级别
                            level = 1
                            if 'heading 1' in style_name or '标题 1' in style_name:
                                level = 1
                            elif 'heading 2' in style_name or '标题 2' in style_name:
                                level = 2
                            elif 'heading 3' in style_name or '标题 3' in style_name:
                                level = 3
                            elif 'heading 4' in style_name or '标题 4' in style_name:
                                level = 4
                            elif 'heading 5' in style_name or '标题 5' in style_name:
                                level = 5
                            elif 'heading 6' in style_name or '标题 6' in style_name:
                                level = 6
                            
                            markdown_parts.append('#' * level + ' ' + text)
                        else:
                            markdown_parts.append(text)
                    else:
                        # 普通段落
                        markdown_parts.append(text)
            
            # 处理表格
            for table_idx, table in enumerate(doc.tables):
                if table.rows:
                    table_md = []
                    
                    # 表头
                    header_row = table.rows[0]
                    headers = []
                    for cell in header_row.cells:
                        headers.append(cell.text.strip() or "列")
                    
                    if headers:
                        table_md.append("| " + " | ".join(headers) + " |")
                        table_md.append("| " + " | ".join(["---"] * len(headers)) + " |")
                        
                        # 数据行
                        for row in table.rows[1:]:
                            row_data = []
                            for cell in row.cells:
                                row_data.append(cell.text.strip().replace('\n', ' ') or "")
                            
                            # 确保行数据长度与表头一致
                            while len(row_data) < len(headers):
                                row_data.append("")
                            
                            table_md.append("| " + " | ".join(row_data) + " |")
                    
                    if table_md:
                        markdown_parts.append('\n'.join(table_md))
            
            return '\n\n'.join(markdown_parts) if markdown_parts else "文档内容为空"
            
        except Exception as e:
            logger.error(f"Markdown转换失败: {e}")
            # 回退到基本文本提取
            text_content = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text.strip())
            
            return '\n\n'.join(text_content) if text_content else "文档解析失败"
    



    def store_documents_to_weaviate(self, documents: List[Document]):
        """将文档存储到Weaviate"""
        try:
            collection = self.weaviate_client.collections.get("Document")
            
            # 批量插入数据
            batch_size = 100
            total_stored = 0
            
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                
                # 准备批量数据
                objects_to_insert = []
                
                for doc in batch:
                    # 提取嵌入向量
                    embedding = doc.metadata.pop("embedding", None)
                    
                    # 准备数据对象
                    data_object = {
                        "content": doc.page_content,
                        "file_path": doc.metadata.get("file_path", ""),
                        "file_name": doc.metadata.get("file_name", ""),
                        "project": doc.metadata.get("project", ""),
                        "file_type": doc.metadata.get("file_type", ""),
                        "source_type": doc.metadata.get("source_type", ""),
                        "image_path": doc.metadata.get("image_path", ""),
                        "section": doc.metadata.get("section", ""),
                        "sheet_name": doc.metadata.get("sheet_name", ""),
                        "chunk_index": doc.metadata.get("chunk_index", 0),
                        "created_at": doc.metadata.get("created_at", datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')),
                        "ocr_text": doc.metadata.get("ocr_text", ""),
                        "caption": doc.metadata.get("caption", "")
                    }
                    
                    objects_to_insert.append(wvc.data.DataObject(
                        properties=data_object,
                        vector=embedding
                    ))
                
                # 批量插入
                response = collection.data.insert_many(objects_to_insert)
                
                # 检查响应类型并处理错误
                failed_count = 0
                if hasattr(response, 'failed_objects'):
                    # 旧版本API
                    failed_objects = response.failed_objects
                    if failed_objects:
                        failed_count = len(failed_objects)
                        logger.warning(f"⚠️ 批次 {i//batch_size + 1} 中有 {failed_count} 个对象插入失败")
                        for failed_obj in failed_objects:
                            logger.warning(f"   失败原因: {failed_obj.message}")
                elif hasattr(response, 'all_responses'):
                    # 新版本API
                    for resp in response.all_responses:
                        if hasattr(resp, 'errors') and resp.errors:
                            failed_count += 1
                            logger.warning(f"   插入失败: {resp.errors}")
                elif hasattr(response, 'errors') and response.errors:
                    # 另一种新版本API格式
                    failed_count = len(response.errors)
                    logger.warning(f"⚠️ 批次 {i//batch_size + 1} 中有 {failed_count} 个对象插入失败")
                    for error in response.errors:
                        logger.warning(f"   失败原因: {error}")
                else:
                    # 假设全部成功
                    logger.info(f"✅ 批次 {i//batch_size + 1} 全部插入成功")
                
                successful_count = len(batch) - failed_count
                total_stored += successful_count
                
                logger.info(f"✅ 批次 {i//batch_size + 1}/{(len(documents) + batch_size - 1) // batch_size} 完成，成功存储 {successful_count} 个文档")
            
            logger.info(f"🎉 文档存储完成！总计存储 {total_stored}/{len(documents)} 个文档到Weaviate")
            return total_stored
            
        except Exception as e:
            logger.error(f"❌ 存储文档到Weaviate失败: {e}")
            raise
    
    def process_single_document(self, document_path: str):
        """处理单个文档的完整流程"""
        try:
            file_path = Path(document_path)
            
            # 检查文件是否存在
            if not file_path.exists():
                raise FileNotFoundError(f"文件不存在: {document_path}")
            
            # 检查文件格式
            if file_path.suffix.lower() != '.docx':
                raise ValueError(f"不支持的文件格式: {file_path.suffix}")
            
            logger.info(f"🚀 开始处理文档: {file_path.name}")
            
            # 1. 创建Weaviate模式
            collection_name = self._create_weaviate_schema()
            
            # 2. 删除已存在的同名文件记录
            self._delete_existing_document(file_path.name)
            
            # 3. 处理文档
            documents = self._process_docx_file(file_path)
            
            # 4. 存储到Weaviate
            stored_count = self.store_documents_to_weaviate(documents)
            
            logger.info(f"🎉 文档处理完成！")
            logger.info(f"   📄 文件: {file_path.name}")
            logger.info(f"   📊 生成文档块: {len(documents)}")
            logger.info(f"   💾 成功存储: {stored_count}")
            
            return {
                "success": True,
                "file_name": file_path.name,
                "total_chunks": len(documents),
                "stored_chunks": stored_count,
                "collection": collection_name
            }
            
        except Exception as e:
            logger.error(f"❌ 处理文档失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_name": Path(document_path).name if document_path else "unknown"
            }
    
    def close(self):
        """关闭连接"""
        try:
            if self.weaviate_client:
                self.weaviate_client.close()
                logger.info("✅ Weaviate 客户端连接已关闭")
        except Exception as e:
            logger.warning(f"⚠️ 关闭连接时出现警告: {e}")


def main():
    """主函数 - 处理特定文档向量化"""
    initializer = None
    
    try:
        # 指定要处理的文档路径
        document_path = r"D:\knowledge_base\链数_LS\需求文档\LS-1(YS-72)_需求文档-链数一期V1.8.docx"
        
        print(f"🚀 开始处理文档向量化...")
        print(f"📄 目标文档: {document_path}")
        
        # 创建初始化器
        initializer = KnowledgeBaseInitializer()
        
        # 处理单个文档
        result = initializer.process_single_document(document_path)
        
        # 输出结果
        if result["success"]:
            print(f"\n🎉 文档向量化成功！")
            print(f"   📄 文件名: {result['file_name']}")
            print(f"   📊 生成块数: {result['total_chunks']}")
            print(f"   💾 存储块数: {result['stored_chunks']}")
            print(f"   🗄️ 集合名称: {result['collection']}")
        else:
            print(f"\n❌ 文档向量化失败!")
            print(f"   📄 文件名: {result['file_name']}")
            print(f"   🔥 错误信息: {result['error']}")
            
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if initializer:
            initializer.close()


if __name__ == "__main__":
    main() 