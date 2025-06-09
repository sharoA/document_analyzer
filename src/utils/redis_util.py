#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis 工具模块
提供便捷的 Redis 连接和缓存管理功能
"""

import redis
import json
import logging
from typing import Any, Optional, Dict, Union
from datetime import datetime, timedelta

# 处理导入问题
try:
    from ..resource.config import get_config
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    import sys
    import os
    # 添加项目根目录到 Python 路径
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, project_root)
    from src.resource.config import get_config

logger = logging.getLogger(__name__)

class RedisManager:
    """Redis 管理器类，提供连接管理和缓存功能"""
    
    def __init__(self):
        """初始化 Redis 管理器"""
        self._client = None
        self._config = None
        self._load_config()
    
    def _load_config(self):
        """加载 Redis 配置"""
        config = get_config()
        self._config = config.get_redis_config()
        
    @property
    def client(self) -> redis.Redis:
        """获取 Redis 客户端实例"""
        if self._client is None:
            self._connect()
        return self._client
    
    def _connect(self):
        """连接到 Redis"""
        try:
            # 构建连接参数
            connection_params = {
                'host': self._config.get('host', 'localhost'),
                'port': self._config.get('port', 6379),
                'db': self._config.get('db', 0),
                'decode_responses': self._config.get('decode_responses', True),
                'socket_timeout': self._config.get('socket_timeout', 30),
                'socket_connect_timeout': self._config.get('socket_connect_timeout', 30),
                'socket_keepalive': self._config.get('socket_keepalive', True),
                'socket_keepalive_options': self._config.get('socket_keepalive_options', {})
            }
            
            # 如果有密码，添加密码参数
            password = self._config.get('password', '')
            if password:
                connection_params['password'] = password
            
            # 连接池配置
            pool_config = self._config.get('connection_pool', {})
            max_connections = pool_config.get('max_connections', 50)
            
            # 创建连接池
            pool = redis.ConnectionPool(
                max_connections=max_connections,
                **connection_params
            )
            
            # 创建客户端
            self._client = redis.Redis(connection_pool=pool)
            
            # 测试连接
            self._client.ping()
            logger.info(f"成功连接到 Redis: {connection_params['host']}:{connection_params['port']}")
            
        except redis.ConnectionError as e:
            logger.error(f"连接 Redis 失败: {e}")
            raise
        except Exception as e:
            logger.error(f"Redis 连接时发生未知错误: {e}")
            raise
    
    def test_connection(self) -> bool:
        """测试 Redis 连接"""
        try:
            self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis 连接测试失败: {e}")
            return False
    
    def get_key_with_prefix(self, key: str) -> str:
        """获取带前缀的键名"""
        prefix = self._config.get('cache', {}).get('key_prefix', 'analydesign:')
        return f"{prefix}{key}"
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, use_prefix: bool = True) -> bool:
        """
        设置键值对
        
        Args:
            key: 键名
            value: 值
            ttl: 过期时间（秒），如果为None则使用默认TTL
            use_prefix: 是否使用键前缀
            
        Returns:
            bool: 设置成功返回 True
        """
        try:
            if use_prefix:
                key = self.get_key_with_prefix(key)
            
            # 如果值不是字符串，序列化为JSON
            if not isinstance(value, (str, bytes)):
                value = json.dumps(value, ensure_ascii=False, default=str)
            
            # 设置TTL
            if ttl is None:
                ttl = self._config.get('cache', {}).get('default_ttl', 3600)
            
            if ttl > 0:
                return self.client.setex(key, ttl, value)
            else:
                return self.client.set(key, value)
                
        except Exception as e:
            logger.error(f"Redis 设置键值失败 {key}: {e}")
            return False
    
    def get(self, key: str, use_prefix: bool = True, default: Any = None) -> Any:
        """
        获取键值
        
        Args:
            key: 键名
            use_prefix: 是否使用键前缀
            default: 默认值
            
        Returns:
            Any: 键对应的值，如果不存在返回默认值
        """
        try:
            if use_prefix:
                key = self.get_key_with_prefix(key)
            
            value = self.client.get(key)
            if value is None:
                return default
            
            # 尝试解析JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            logger.error(f"Redis 获取键值失败 {key}: {e}")
            return default
    
    def delete(self, key: str, use_prefix: bool = True) -> bool:
        """
        删除键
        
        Args:
            key: 键名
            use_prefix: 是否使用键前缀
            
        Returns:
            bool: 删除成功返回 True
        """
        try:
            if use_prefix:
                key = self.get_key_with_prefix(key)
            
            return bool(self.client.delete(key))
            
        except Exception as e:
            logger.error(f"Redis 删除键失败 {key}: {e}")
            return False
    
    def exists(self, key: str, use_prefix: bool = True) -> bool:
        """
        检查键是否存在
        
        Args:
            key: 键名
            use_prefix: 是否使用键前缀
            
        Returns:
            bool: 键存在返回 True
        """
        try:
            if use_prefix:
                key = self.get_key_with_prefix(key)
            
            return bool(self.client.exists(key))
            
        except Exception as e:
            logger.error(f"Redis 检查键存在失败 {key}: {e}")
            return False
    
    def expire(self, key: str, ttl: int, use_prefix: bool = True) -> bool:
        """
        设置键的过期时间
        
        Args:
            key: 键名
            ttl: 过期时间（秒）
            use_prefix: 是否使用键前缀
            
        Returns:
            bool: 设置成功返回 True
        """
        try:
            if use_prefix:
                key = self.get_key_with_prefix(key)
            
            return bool(self.client.expire(key, ttl))
            
        except Exception as e:
            logger.error(f"Redis 设置过期时间失败 {key}: {e}")
            return False
    
    def get_ttl(self, key: str, use_prefix: bool = True) -> int:
        """
        获取键的剩余过期时间
        
        Args:
            key: 键名
            use_prefix: 是否使用键前缀
            
        Returns:
            int: 剩余过期时间（秒），-1表示永不过期，-2表示键不存在
        """
        try:
            if use_prefix:
                key = self.get_key_with_prefix(key)
            
            return self.client.ttl(key)
            
        except Exception as e:
            logger.error(f"Redis 获取TTL失败 {key}: {e}")
            return -2
    
    def clear_cache(self, pattern: str = None) -> int:
        """
        清理缓存
        
        Args:
            pattern: 键模式，如果为None则清理所有带前缀的键
            
        Returns:
            int: 删除的键数量
        """
        try:
            if pattern is None:
                prefix = self._config.get('cache', {}).get('key_prefix', 'analydesign:')
                pattern = f"{prefix}*"
            
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
            
        except Exception as e:
            logger.error(f"Redis 清理缓存失败: {e}")
            return 0
    
    def get_info(self) -> Dict[str, Any]:
        """
        获取 Redis 服务器信息
        
        Returns:
            Dict[str, Any]: Redis 服务器信息
        """
        try:
            return self.client.info()
        except Exception as e:
            logger.error(f"获取 Redis 信息失败: {e}")
            return {}
    
    def close(self):
        """关闭连接"""
        if self._client:
            self._client.close()
            self._client = None
            logger.info("Redis 连接已关闭")

# 全局 Redis 管理器实例
_redis_manager = None

def get_redis_manager() -> RedisManager:
    """获取全局 Redis 管理器实例"""
    global _redis_manager
    if _redis_manager is None:
        _redis_manager = RedisManager()
    return _redis_manager

def get_redis_client() -> redis.Redis:
    """获取 Redis 客户端"""
    return get_redis_manager().client

def test_redis_connection() -> bool:
    """测试 Redis 连接"""
    return get_redis_manager().test_connection()

# 便捷函数
def cache_set(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """缓存设置"""
    return get_redis_manager().set(key, value, ttl)

def cache_get(key: str, default: Any = None) -> Any:
    """缓存获取"""
    return get_redis_manager().get(key, default=default)

def cache_delete(key: str) -> bool:
    """缓存删除"""
    return get_redis_manager().delete(key)

def cache_exists(key: str) -> bool:
    """检查缓存是否存在"""
    return get_redis_manager().exists(key)

# 使用示例和测试
if __name__ == "__main__":
    try:
        # 测试连接
        if test_redis_connection():
            print("✅ Redis 连接测试成功")
            
            # 获取配置信息
            config = get_config()
            redis_config = config.get_redis_config()
            print(f"📋 Redis 配置: {redis_config}")
            
            # 测试基本操作
            manager = get_redis_manager()
            
            # 设置和获取
            test_key = "test_key"
            test_value = {"message": "Hello, Redis!", "timestamp": datetime.now().isoformat()}
            
            if manager.set(test_key, test_value):
                print(f"✅ 设置缓存成功: {test_key}")
                
                retrieved_value = manager.get(test_key)
                print(f"✅ 获取缓存成功: {retrieved_value}")
                
                # 检查TTL
                ttl = manager.get_ttl(test_key)
                print(f"⏰ 剩余过期时间: {ttl} 秒")
                
                # 删除测试键
                if manager.delete(test_key):
                    print(f"✅ 删除缓存成功: {test_key}")
            
            # 获取服务器信息
            info = manager.get_info()
            print(f"📊 Redis 版本: {info.get('redis_version', 'unknown')}")
            print(f"📊 已用内存: {info.get('used_memory_human', 'unknown')}")
            
        else:
            print("❌ Redis 连接测试失败")
            
    except Exception as e:
        logger.error(f"Redis 测试失败: {e}")
        print(f"❌ Redis 测试失败: {e}")