#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库初始化脚本 - Weaviate 版本
将 D:\knowledge_base 下的知识库内容转换为向量并存储到 Weaviate 中
"""

import os
import re
import uuid
import json
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# 文件处理相关
import docx
from openpyxl import load_workbook
from PIL import Image
import pytesseract
from transformers import BlipProcessor, BlipForConditionalGeneration

# 向量化和嵌入
from sentence_transformers import SentenceTransformer

# Weaviate 和 LangChain
import weaviate
import weaviate.classes as wvc
from weaviate.auth import AuthApiKey
from langchain_community.vectorstores import Weaviate
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
        self.knowledge_base_path = Path(knowledge_base_path)
        self.weaviate_client = None
        self.redis_manager = None
        self.embeddings_model = None
        self.text_splitter = None
        self.blip_processor = None
        self.blip_model = None
        
        # 支持的文件类型
        self.supported_extensions = {'.docx', '.xlsx', '.java', '.xml'}
        
        # 初始化组件
        self._initialize_components()
    
    def _initialize_components(self):
        """初始化各种组件"""
        try:
            # 初始化 Weaviate 客户端
            self.weaviate_client = get_weaviate_client()
            logger.info("✅ Weaviate 客户端初始化成功")
            
            # 初始化 Redis 管理器
            self.redis_manager = get_redis_manager()
            logger.info("✅ Redis 管理器初始化成功")
            
            # 初始化嵌入模型
            self.embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ 嵌入模型加载成功")
            
            # 初始化文本分割器
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50,
                length_function=len,
                separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""]
            )
            logger.info("✅ 文本分割器初始化成功")
            
            # 初始化图片描述模型（延迟加载）
            logger.info("✅ 组件初始化完成")
            
        except Exception as e:
            logger.error(f"❌ 组件初始化失败: {e}")
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
        """生成缓存键"""
        file_hash = hashlib.md5(file_path.encode()).hexdigest()
        return f"knowledge_base:{file_hash}:{cache_type}"
    
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
            
            # 如果路径包含多个部分，尝试提取项目名称
            if len(parts) >= 2:
                # 例如: 代码/链数后端代码/zqyl-ls/... -> zqyl-ls
                for part in parts:
                    if part not in ['代码', '文档', '需求', '数据库', '链数后端代码', '链数前端代码']:
                        return part
            
            # 默认使用第一个目录作为项目名称
            return parts[0] if parts else "unknown"
            
        except Exception as e:
            logger.warning(f"提取项目名称失败 {file_path}: {e}")
            return "unknown"
    
    def _process_docx_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """处理 DOCX 文件"""
        results = []
        
        try:
            # 检查缓存
            cached_result = self._get_cached_result(str(file_path), "docx_content")
            if cached_result:
                logger.info(f"📋 使用缓存的 DOCX 内容: {file_path.name}")
                return cached_result
            
            doc = docx.Document(file_path)
            
            # 提取文本内容
            text_content = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text.strip())
            
            full_text = "\n".join(text_content)
            
            if full_text.strip():
                # 分割文本
                text_chunks = self.text_splitter.split_text(full_text)
                
                for i, chunk in enumerate(text_chunks):
                    results.append({
                        'content': chunk,
                        'file_path': str(file_path),
                        'file_name': file_path.name,
                        'project': self._extract_project_name(file_path),
                        'file_type': 'docx',
                        'source_type': 'text',
                        'chunk_index': i,
                        'image_path': None
                    })
            
            # 处理图片（如果存在）
            try:
                # 提取文档中的图片
                for rel in doc.part.rels.values():
                    if "image" in rel.target_ref:
                        # 这里可以添加图片处理逻辑
                        # 由于 python-docx 提取图片比较复杂，暂时跳过
                        pass
            except Exception as e:
                logger.warning(f"处理 DOCX 图片失败 {file_path}: {e}")
            
            # 缓存结果
            self._set_cached_result(str(file_path), "docx_content", results)
            logger.info(f"✅ DOCX 文件处理完成: {file_path.name} ({len(results)} 个块)")
            
        except Exception as e:
            logger.error(f"❌ DOCX 文件处理失败 {file_path}: {e}")
        
        return results
    
    def _process_xlsx_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """处理 XLSX 文件"""
        results = []
        
        try:
            # 检查缓存
            cached_result = self._get_cached_result(str(file_path), "xlsx_content")
            if cached_result:
                logger.info(f"📋 使用缓存的 XLSX 内容: {file_path.name}")
                return cached_result
            
            workbook = load_workbook(file_path, read_only=True)
            
            for sheet_name in workbook.sheetnames:
                sheet = workbook[sheet_name]
                
                # 提取表格内容
                sheet_content = []
                headers = []
                
                # 获取表头
                for cell in sheet[1]:
                    if cell.value:
                        headers.append(str(cell.value))
                
                if headers:
                    sheet_content.append("表头: " + " | ".join(headers))
                
                # 获取数据行
                for row in sheet.iter_rows(min_row=2, values_only=True):
                    row_data = []
                    for cell_value in row:
                        if cell_value is not None:
                            row_data.append(str(cell_value))
                    
                    if row_data:
                        sheet_content.append(" | ".join(row_data))
                
                if sheet_content:
                    full_content = f"工作表: {sheet_name}\n" + "\n".join(sheet_content)
                    
                    # 分割内容
                    text_chunks = self.text_splitter.split_text(full_content)
                    
                    for i, chunk in enumerate(text_chunks):
                        results.append({
                            'content': chunk,
                            'file_path': str(file_path),
                            'file_name': file_path.name,
                            'project': self._extract_project_name(file_path),
                            'file_type': 'xlsx',
                            'source_type': 'excel',
                            'chunk_index': i,
                            'sheet_name': sheet_name,
                            'image_path': None
                        })
            
            workbook.close()
            
            # 缓存结果
            self._set_cached_result(str(file_path), "xlsx_content", results)
            logger.info(f"✅ XLSX 文件处理完成: {file_path.name} ({len(results)} 个块)")
            
        except Exception as e:
            logger.error(f"❌ XLSX 文件处理失败 {file_path}: {e}")
        
        return results
    
    def _process_java_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """处理 Java 文件"""
        results = []
        
        try:
            # 检查缓存
            cached_result = self._get_cached_result(str(file_path), "java_content")
            if cached_result:
                logger.info(f"📋 使用缓存的 Java 内容: {file_path.name}")
                return cached_result
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 简单的 Java 代码分割（按类和方法）
            # 这里使用简单的正则表达式，实际项目中可以使用 tree-sitter 获得更好的解析
            
            # 分割为类
            class_pattern = r'(public\s+class\s+\w+.*?(?=public\s+class|\Z))'
            classes = re.findall(class_pattern, content, re.DOTALL)
            
            if not classes:
                # 如果没有找到类，按方法分割
                method_pattern = r'(public\s+\w+.*?\{.*?\n\s*\})'
                methods = re.findall(method_pattern, content, re.DOTALL)
                
                if methods:
                    for i, method in enumerate(methods):
                        if len(method.strip()) > 50:  # 过滤太短的内容
                            results.append({
                                'content': method.strip(),
                                'file_path': str(file_path),
                                'file_name': file_path.name,
                                'project': self._extract_project_name(file_path),
                                'file_type': 'java',
                                'source_type': 'code_method',
                                'chunk_index': i,
                                'image_path': None
                            })
                else:
                    # 如果都没有找到，按文本分割
                    text_chunks = self.text_splitter.split_text(content)
                    for i, chunk in enumerate(text_chunks):
                        results.append({
                            'content': chunk,
                            'file_path': str(file_path),
                            'file_name': file_path.name,
                            'project': self._extract_project_name(file_path),
                            'file_type': 'java',
                            'source_type': 'code_text',
                            'chunk_index': i,
                            'image_path': None
                        })
            else:
                for i, class_content in enumerate(classes):
                    if len(class_content.strip()) > 100:  # 过滤太短的类
                        results.append({
                            'content': class_content.strip(),
                            'file_path': str(file_path),
                            'file_name': file_path.name,
                            'project': self._extract_project_name(file_path),
                            'file_type': 'java',
                            'source_type': 'code_class',
                            'chunk_index': i,
                            'image_path': None
                        })
            
            # 缓存结果
            self._set_cached_result(str(file_path), "java_content", results)
            logger.info(f"✅ Java 文件处理完成: {file_path.name} ({len(results)} 个块)")
            
        except Exception as e:
            logger.error(f"❌ Java 文件处理失败 {file_path}: {e}")
        
        return results
    
    def _process_xml_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """处理 XML 文件"""
        results = []
        
        try:
            # 检查缓存
            cached_result = self._get_cached_result(str(file_path), "xml_content")
            if cached_result:
                logger.info(f"📋 使用缓存的 XML 内容: {file_path.name}")
                return cached_result
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 按文本分割 XML 内容
            text_chunks = self.text_splitter.split_text(content)
            
            for i, chunk in enumerate(text_chunks):
                results.append({
                    'content': chunk,
                    'file_path': str(file_path),
                    'file_name': file_path.name,
                    'project': self._extract_project_name(file_path),
                    'file_type': 'xml',
                    'source_type': 'config',
                    'chunk_index': i,
                    'image_path': None
                })
            
            # 缓存结果
            self._set_cached_result(str(file_path), "xml_content", results)
            logger.info(f"✅ XML 文件处理完成: {file_path.name} ({len(results)} 个块)")
            
        except Exception as e:
            logger.error(f"❌ XML 文件处理失败 {file_path}: {e}")
        
        return results
    
    def _create_weaviate_schema(self):
        """创建 Weaviate 模式"""
        try:
            collection_name = "KnowledgeDocument"
            
            # 检查集合是否已存在
            if self.weaviate_client.collections.exists(collection_name):
                logger.info(f"📋 集合 {collection_name} 已存在，跳过创建")
                return collection_name
            
            # 创建集合
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
                    wvc.config.Property(name="chunk_index", data_type=wvc.config.DataType.INT),
                    wvc.config.Property(name="image_path", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="created_at", data_type=wvc.config.DataType.DATE),
                    wvc.config.Property(name="file_size", data_type=wvc.config.DataType.INT)
                ]
            )
            
            logger.info(f"✅ Weaviate 集合创建成功: {collection_name}")
            return collection_name
            
        except Exception as e:
            logger.error(f"❌ Weaviate 集合创建失败: {e}")
            raise
    
    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """生成文本嵌入"""
        try:
            embeddings = self.embeddings_model.encode(texts, convert_to_tensor=False)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"❌ 生成嵌入失败: {e}")
            return []
    
    def _batch_insert_to_weaviate(self, documents: List[Dict[str, Any]], collection_name: str, batch_size: int = 100):
        """批量插入文档到 Weaviate"""
        try:
            collection = self.weaviate_client.collections.get(collection_name)
            
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                
                # 生成嵌入
                texts = [doc['content'] for doc in batch]
                embeddings = self._generate_embeddings(texts)
                
                if not embeddings:
                    logger.warning(f"跳过批次 {i//batch_size + 1}，嵌入生成失败")
                    continue
                
                # 准备批量插入数据
                batch_data = []
                for j, doc in enumerate(batch):
                    if j < len(embeddings):
                        # 添加时间戳和文件大小
                        doc['created_at'] = datetime.now()
                        doc['file_size'] = len(doc['content'])
                        
                        batch_data.append({
                            'properties': doc,
                            'vector': embeddings[j]
                        })
                
                # 批量插入
                if batch_data:
                    try:
                        with collection.batch.dynamic() as batch_client:
                            for item in batch_data:
                                batch_client.add_object(
                                    properties=item['properties'],
                                    vector=item['vector']
                                )
                        
                        logger.info(f"✅ 批次 {i//batch_size + 1}/{(len(documents) + batch_size - 1)//batch_size} 插入成功 ({len(batch_data)} 个文档)")
                        
                    except Exception as e:
                        logger.error(f"❌ 批次 {i//batch_size + 1} 插入失败: {e}")
            
            logger.info(f"🎉 所有文档插入完成，总计: {len(documents)} 个文档")
            
        except Exception as e:
            logger.error(f"❌ 批量插入失败: {e}")
            raise
    
    def scan_knowledge_base(self) -> List[Path]:
        """扫描知识库目录，获取所有支持的文件"""
        files = []
        
        try:
            for file_path in self.knowledge_base_path.rglob("*"):
                if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                    files.append(file_path)
            
            logger.info(f"📁 扫描完成，找到 {len(files)} 个支持的文件")
            
            # 按文件类型统计
            stats = {}
            for file_path in files:
                ext = file_path.suffix.lower()
                stats[ext] = stats.get(ext, 0) + 1
            
            for ext, count in stats.items():
                logger.info(f"   {ext}: {count} 个文件")
            
        except Exception as e:
            logger.error(f"❌ 扫描知识库失败: {e}")
        
        return files
    
    def process_files(self, files: List[Path]) -> List[Dict[str, Any]]:
        """处理所有文件"""
        all_documents = []
        
        for i, file_path in enumerate(files, 1):
            logger.info(f"🔄 处理文件 {i}/{len(files)}: {file_path.name}")
            
            try:
                documents = []
                
                if file_path.suffix.lower() == '.docx':
                    documents = self._process_docx_file(file_path)
                elif file_path.suffix.lower() == '.xlsx':
                    documents = self._process_xlsx_file(file_path)
                elif file_path.suffix.lower() == '.java':
                    documents = self._process_java_file(file_path)
                elif file_path.suffix.lower() == '.xml':
                    documents = self._process_xml_file(file_path)
                
                all_documents.extend(documents)
                
            except Exception as e:
                logger.error(f"❌ 处理文件失败 {file_path}: {e}")
        
        logger.info(f"📊 文件处理完成，总计生成 {len(all_documents)} 个文档块")
        return all_documents
    
    def initialize_knowledge_base(self):
        """初始化知识库"""
        try:
            logger.info("🚀 开始初始化知识库...")
            
            # 1. 检查知识库目录
            if not self.knowledge_base_path.exists():
                raise FileNotFoundError(f"知识库目录不存在: {self.knowledge_base_path}")
            
            # 2. 扫描文件
            files = self.scan_knowledge_base()
            if not files:
                logger.warning("⚠️ 没有找到支持的文件")
                return
            
            # 3. 创建 Weaviate 模式
            collection_name = self._create_weaviate_schema()
            
            # 4. 处理文件
            documents = self.process_files(files)
            if not documents:
                logger.warning("⚠️ 没有生成任何文档")
                return
            
            # 5. 插入到 Weaviate
            self._batch_insert_to_weaviate(documents, collection_name)
            
            logger.info("🎉 知识库初始化完成！")
            
        except Exception as e:
            logger.error(f"❌ 知识库初始化失败: {e}")
            raise
    
    def query_knowledge_base(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """查询知识库"""
        try:
            collection = self.weaviate_client.collections.get("KnowledgeDocument")
            
            # 生成查询向量
            query_embedding = self._generate_embeddings([query])[0]
            
            # 向量搜索
            result = collection.query.near_vector(
                near_vector=query_embedding,
                limit=limit,
                return_metadata=['distance']
            )
            
            # 格式化结果
            results = []
            for obj in result.objects:
                results.append({
                    'content': obj.properties.get('content', ''),
                    'file_name': obj.properties.get('file_name', ''),
                    'project': obj.properties.get('project', ''),
                    'file_type': obj.properties.get('file_type', ''),
                    'source_type': obj.properties.get('source_type', ''),
                    'distance': obj.metadata.distance,
                    'file_path': obj.properties.get('file_path', '')
                })
            
            return results
            
        except Exception as e:
            logger.error(f"❌ 查询知识库失败: {e}")
            return []
    
    def close(self):
        """关闭连接"""
        if self.weaviate_client:
            self.weaviate_client.close()
        if self.redis_manager:
            self.redis_manager.close()

def main():
    """主函数"""
    initializer = None
    
    try:
        # 创建初始化器
        initializer = KnowledgeBaseInitializer()
        
        # 初始化知识库
        initializer.initialize_knowledge_base()
        
        # 示例查询
        print("\n" + "="*50)
        print("🔍 示例查询测试")
        print("="*50)
        
        queries = [
            "LS中的数据库表结构",
            "用户管理相关的代码",
            "链数后端的配置文件",
            "Java类的定义"
        ]
        
        for query in queries:
            print(f"\n查询: {query}")
            print("-" * 30)
            
            results = initializer.query_knowledge_base(query, limit=3)
            
            if results:
                for i, result in enumerate(results, 1):
                    print(f"{i}. 文件: {result['file_name']} (项目: {result['project']})")
                    print(f"   类型: {result['file_type']} | 来源: {result['source_type']}")
                    print(f"   相似度: {1 - result['distance']:.3f}")
                    print(f"   内容预览: {result['content'][:100]}...")
                    print()
            else:
                print("   没有找到相关结果")
        
        print("🎉 示例查询完成！")
        
    except Exception as e:
        logger.error(f"❌ 程序执行失败: {e}")
        raise
    
    finally:
        if initializer:
            initializer.close()

if __name__ == "__main__":
    main()
