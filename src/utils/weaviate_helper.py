#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Weaviate 辅助工具模块
提供便捷的 Weaviate 连接和配置管理功能
"""

import weaviate
import logging
from typing import Dict, Any, Optional
import weaviate.classes as wvc
from weaviate.auth import AuthApiKey
from ..resource.config import get_config

logger = logging.getLogger(__name__)

def get_weaviate_client() -> weaviate.WeaviateClient:
    """
    获取配置好的 Weaviate 客户端实例
    
    Returns:
        weaviate.WeaviateClient: 已连接的 Weaviate 客户端
        
    Raises:
        Exception: 连接失败时抛出异常
    """
    config = get_config()
    weaviate_config = config.get_weaviate_config()
    
    host = weaviate_config.get('host', 'localhost')
    port = weaviate_config.get('port', 8080)
    grpc_port = weaviate_config.get('grpc_port', 50051)
    api_key = weaviate_config.get('api_key', 'root-user-key')
    
    try:
        client = weaviate.connect_to_local(
            host=host,
            port=port,
            grpc_port=grpc_port,
            auth_credentials=AuthApiKey(api_key)
        )
        
        if not client.is_ready():
            raise Exception("Weaviate 服务未就绪")
            
        logger.info(f"成功连接到 Weaviate: {host}:{port}")
        return client
        
    except Exception as e:
        logger.error(f"连接 Weaviate 失败: {e}")
        raise

def create_default_collection(client: weaviate.WeaviateClient, 
                            collection_name: str = None) -> bool:
    """
    创建默认的文档集合
    
    Args:
        client: Weaviate 客户端
        collection_name: 集合名称，如果为None则使用配置文件中的默认名称
        
    Returns:
        bool: 创建成功返回 True
    """
    config = get_config()
    weaviate_config = config.get_weaviate_config()
    default_collection = weaviate_config.get('default_collection', {})
    
    name = collection_name or default_collection.get('name', 'AnalyDesignDocuments')
    vector_dimension = default_collection.get('vector_dimension', 768)
    
    try:
        # 检查集合是否已存在
        if client.collections.exists(name):
            logger.info(f"集合 {name} 已存在")
            return True
            
        # 创建集合
        client.collections.create(
            name=name,
            vectorizer_config=wvc.config.Configure.Vectorizer.none(),
            properties=[
                wvc.config.Property(name="title", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="content", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="file_type", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="file_path", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="created_at", data_type=wvc.config.DataType.DATE),
                wvc.config.Property(name="file_size", data_type=wvc.config.DataType.INT),
                wvc.config.Property(name="tags", data_type=wvc.config.DataType.TEXT_ARRAY)
            ]
        )
        
        logger.info(f"成功创建集合: {name}")
        return True
        
    except Exception as e:
        logger.error(f"创建集合失败: {e}")
        return False

def get_weaviate_config_dict() -> Dict[str, Any]:
    """
    获取 Weaviate 配置字典
    
    Returns:
        Dict[str, Any]: Weaviate 配置字典
    """
    config = get_config()
    return config.get_weaviate_config()

def test_weaviate_connection() -> bool:
    """
    测试 Weaviate 连接
    
    Returns:
        bool: 连接成功返回 True
    """
    try:
        client = get_weaviate_client()
        client.close()
        return True
    except Exception as e:
        logger.error(f"Weaviate 连接测试失败: {e}")
        return False

class WeaviateManager:
    """Weaviate 管理器类，提供上下文管理功能"""
    
    def __init__(self, collection_name: str = None):
        """
        初始化 Weaviate 管理器
        
        Args:
            collection_name: 集合名称
        """
        self.collection_name = collection_name
        self.client = None
        
    def __enter__(self):
        """进入上下文管理器"""
        self.client = get_weaviate_client()
        return self.client
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文管理器"""
        if self.client:
            self.client.close()
            
    def get_collection(self):
        """获取集合对象"""
        if not self.client:
            raise Exception("客户端未初始化，请在 with 语句中使用")
            
        config = get_config()
        weaviate_config = config.get_weaviate_config()
        default_collection = weaviate_config.get('default_collection', {})
        
        name = self.collection_name or default_collection.get('name', 'AnalyDesignDocuments')
        return self.client.collections.get(name)

# 使用示例
if __name__ == "__main__":
    # 测试连接
    if test_weaviate_connection():
        print("✅ Weaviate 连接测试成功")
        
        # 使用上下文管理器
        with WeaviateManager() as client:
            print(f"✅ 客户端已连接，版本: {client.get_meta()}")
            
            # 创建默认集合
            if create_default_collection(client):
                print("✅ 默认集合创建成功")
    else:
        print("❌ Weaviate 连接测试失败") 