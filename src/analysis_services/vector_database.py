"""
向量数据库接口
用于文档内容的向量化存储和相似性搜索
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

class VectorDatabase(ABC):
    """向量数据库抽象基类"""
    
    @abstractmethod
    async def insert(self, text: str, metadata: Dict[str, Any] = None) -> str:
        """插入文本向量"""
        pass
    
    @abstractmethod
    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索相似文档"""
        pass
    
    @abstractmethod
    async def delete(self, doc_id: str) -> bool:
        """删除文档"""
        pass

class MockVectorDatabase(VectorDatabase):
    """模拟向量数据库实现（用于开发测试）"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.documents = {}
        self.vectors = {}
        self.doc_counter = 0
    
    async def insert(self, text: str, metadata: Dict[str, Any] = None) -> str:
        """插入文本向量"""
        doc_id = f"doc_{self.doc_counter}"
        self.doc_counter += 1
        
        # 模拟向量化（实际应该使用embedding模型）
        vector = self._mock_vectorize(text)
        
        self.documents[doc_id] = {
            "text": text,
            "metadata": metadata or {},
            "vector": vector
        }
        
        self.logger.info(f"插入文档: {doc_id}, 文本长度: {len(text)}")
        return doc_id
    
    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索相似文档"""
        if not self.documents:
            return []
        
        query_vector = self._mock_vectorize(query)
        similarities = []
        
        for doc_id, doc_data in self.documents.items():
            similarity = self._calculate_similarity(query_vector, doc_data["vector"])
            similarities.append({
                "doc_id": doc_id,
                "text": doc_data["text"],
                "metadata": doc_data["metadata"],
                "similarity": similarity
            })
        
        # 按相似度排序
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        
        results = similarities[:top_k]
        self.logger.info(f"搜索查询: '{query[:50]}...', 返回 {len(results)} 个结果")
        
        return results
    
    async def delete(self, doc_id: str) -> bool:
        """删除文档"""
        if doc_id in self.documents:
            del self.documents[doc_id]
            self.logger.info(f"删除文档: {doc_id}")
            return True
        return False
    
    def _mock_vectorize(self, text: str) -> np.ndarray:
        """模拟文本向量化"""
        # 简单的字符频率向量化（实际应该使用预训练模型）
        vector = np.zeros(100)
        for i, char in enumerate(text[:100]):
            vector[i] = ord(char) % 256
        return vector / np.linalg.norm(vector) if np.linalg.norm(vector) > 0 else vector
    
    def _calculate_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)

class ChromaVectorDatabase(VectorDatabase):
    """Chroma向量数据库实现"""
    
    def __init__(self, collection_name: str = "documents", persist_directory: str = "./chroma_db"):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None
        
        try:
            import chromadb
            self.client = chromadb.PersistentClient(path=persist_directory)
            self.collection = self.client.get_or_create_collection(name=collection_name)
            self.logger.info(f"初始化Chroma数据库: {collection_name}")
        except ImportError:
            self.logger.warning("Chroma未安装，将使用模拟向量数据库")
            self.fallback = MockVectorDatabase()
        except Exception as e:
            self.logger.error(f"Chroma初始化失败: {str(e)}, 使用模拟数据库")
            self.fallback = MockVectorDatabase()
    
    async def insert(self, text: str, metadata: Dict[str, Any] = None) -> str:
        """插入文本向量"""
        if hasattr(self, 'fallback'):
            return await self.fallback.insert(text, metadata)
        
        try:
            doc_id = f"doc_{len(self.collection.get()['ids'])}"
            
            self.collection.add(
                documents=[text],
                metadatas=[metadata or {}],
                ids=[doc_id]
            )
            
            self.logger.info(f"插入文档到Chroma: {doc_id}")
            return doc_id
            
        except Exception as e:
            self.logger.error(f"Chroma插入失败: {str(e)}")
            raise
    
    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索相似文档"""
        if hasattr(self, 'fallback'):
            return await self.fallback.search(query, top_k)
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    formatted_results.append({
                        "doc_id": results['ids'][0][i],
                        "text": doc,
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                        "similarity": 1 - results['distances'][0][i] if results['distances'] else 0.0
                    })
            
            self.logger.info(f"Chroma搜索返回 {len(formatted_results)} 个结果")
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Chroma搜索失败: {str(e)}")
            return []
    
    async def delete(self, doc_id: str) -> bool:
        """删除文档"""
        if hasattr(self, 'fallback'):
            return await self.fallback.delete(doc_id)
        
        try:
            self.collection.delete(ids=[doc_id])
            self.logger.info(f"从Chroma删除文档: {doc_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Chroma删除失败: {str(e)}")
            return False

class VectorDatabaseFactory:
    """向量数据库工厂类"""
    
    @staticmethod
    def create_database(db_type: str = "mock", **kwargs) -> VectorDatabase:
        """创建向量数据库实例"""
        if db_type.lower() == "chroma":
            return ChromaVectorDatabase(**kwargs)
        elif db_type.lower() == "mock":
            return MockVectorDatabase()
        else:
            raise ValueError(f"不支持的向量数据库类型: {db_type}")

# 预置一些示例文档用于相似性比较
SAMPLE_DOCUMENTS = [
    {
        "text": "用户管理系统需要实现用户注册、登录、信息修改和注销功能",
        "metadata": {"type": "用户管理", "domain": "系统管理"}
    },
    {
        "text": "商品管理模块包括商品添加、查询、更新价格和删除商品等操作",
        "metadata": {"type": "商品管理", "domain": "电商系统"}
    },
    {
        "text": "订单处理流程涉及订单创建、状态查询、订单修改和取消订单",
        "metadata": {"type": "订单管理", "domain": "电商系统"}
    },
    {
        "text": "权限控制系统需要角色管理、权限分配、访问控制和审计日志",
        "metadata": {"type": "权限管理", "domain": "系统安全"}
    },
    {
        "text": "数据分析平台要求数据采集、清洗、分析和报表生成功能",
        "metadata": {"type": "数据分析", "domain": "数据平台"}
    }
]

async def initialize_sample_data(vector_db: VectorDatabase):
    """初始化示例数据"""
    logger = logging.getLogger("VectorDatabase")
    
    try:
        for doc in SAMPLE_DOCUMENTS:
            await vector_db.insert(doc["text"], doc["metadata"])
        
        logger.info(f"初始化了 {len(SAMPLE_DOCUMENTS)} 个示例文档")
        
    except Exception as e:
        logger.error(f"初始化示例数据失败: {str(e)}") 