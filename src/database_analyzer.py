from sqlalchemy import create_engine, inspect, MetaData, Table
from sqlalchemy.orm import sessionmaker
from typing import Dict, List, Any, Optional
from .config import settings
import logging

logger = logging.getLogger(__name__)

class DatabaseAnalyzer:
    def __init__(self):
        if settings.BUSINESS_DATABASE_URL:
            self.engine = create_engine(settings.BUSINESS_DATABASE_URL)
            self.inspector = inspect(self.engine)
            self.metadata = MetaData()
            self.Session = sessionmaker(bind=self.engine)
        else:
            logger.warning("未配置业务数据库连接")
            self.engine = None
    
    def get_all_tables(self) -> List[str]:
        """获取所有表名"""
        if not self.engine:
            return []
        return self.inspector.get_table_names()
    
    def get_table_structure(self, table_name: str) -> Dict[str, Any]:
        """获取表结构信息"""
        if not self.engine:
            return {}
        
        try:
            columns = self.inspector.get_columns(table_name)
            foreign_keys = self.inspector.get_foreign_keys(table_name)
            indexes = self.inspector.get_indexes(table_name)
            primary_keys = self.inspector.get_pk_constraint(table_name)
            
            return {
                "table_name": table_name,
                "columns": [
                    {
                        "name": col["name"],
                        "type": str(col["type"]),
                        "nullable": col["nullable"],
                        "default": col.get("default"),
                        "comment": col.get("comment", "")
                    }
                    for col in columns
                ],
                "primary_keys": primary_keys["constrained_columns"],
                "foreign_keys": [
                    {
                        "constrained_columns": fk["constrained_columns"],
                        "referred_table": fk["referred_table"],
                        "referred_columns": fk["referred_columns"]
                    }
                    for fk in foreign_keys
                ],
                "indexes": [
                    {
                        "name": idx["name"],
                        "column_names": idx["column_names"],
                        "unique": idx["unique"]
                    }
                    for idx in indexes
                ]
            }
        except Exception as e:
            logger.error(f"获取表结构失败: {str(e)}")
            return {}
    
    def search_related_tables(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """根据关键词搜索相关表"""
        if not self.engine:
            return []
        
        related_tables = []
        all_tables = self.get_all_tables()
        
        for table_name in all_tables:
            # 检查表名是否包含关键词
            table_matches = any(keyword.lower() in table_name.lower() for keyword in keywords)
            
            if table_matches:
                table_info = self.get_table_structure(table_name)
                related_tables.append(table_info)
                continue
            
            # 检查字段名和注释是否包含关键词
            table_info = self.get_table_structure(table_name)
            column_matches = False
            
            for column in table_info.get("columns", []):
                if any(keyword.lower() in column["name"].lower() or 
                      keyword.lower() in column.get("comment", "").lower() 
                      for keyword in keywords):
                    column_matches = True
                    break
            
            if column_matches:
                related_tables.append(table_info)
        
        return related_tables
    
    def check_field_availability(self, required_fields: List[str]) -> Dict[str, List[str]]:
        """检查所需字段在数据库中的可用性"""
        if not self.engine:
            return {"available": [], "missing": required_fields}
        
        available_fields = []
        missing_fields = []
        all_tables = self.get_all_tables()
        
        for field in required_fields:
            found = False
            for table_name in all_tables:
                table_info = self.get_table_structure(table_name)
                for column in table_info.get("columns", []):
                    if field.lower() in column["name"].lower():
                        available_fields.append(f"{table_name}.{column['name']}")
                        found = True
                        break
                if found:
                    break
            
            if not found:
                missing_fields.append(field)
        
        return {
            "available": available_fields,
            "missing": missing_fields
        }
    
    def generate_database_summary(self) -> str:
        """生成数据库结构摘要"""
        if not self.engine:
            return "未连接到业务数据库"
        
        all_tables = self.get_all_tables()
        summary = f"数据库包含 {len(all_tables)} 个表:\n\n"
        
        for table_name in all_tables:
            table_info = self.get_table_structure(table_name)
            columns_count = len(table_info.get("columns", []))
            summary += f"- {table_name}: {columns_count} 个字段\n"
        
        return summary 