from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # 火山引擎API配置（默认使用）
    VOLCENGINE_API_KEY: str = os.getenv("VOLCENGINE_API_KEY", "")
    VOLCENGINE_MODEL_ID: str = os.getenv("VOLCENGINE_MODEL_ID", "ep-20250528194304-wbvcf")
    VOLCENGINE_BASE_URL: str = os.getenv("VOLCENGINE_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
    
    # DeepSeek API配置（备用）
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    
    # OpenAI API配置（备用）
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    
    # 默认使用的API配置
    DEFAULT_API_PROVIDER: str = "volcengine"
    DEFAULT_MODEL: str = os.getenv("VOLCENGINE_MODEL_ID", "ep-20250528194304-wbvcf")
    DEFAULT_API_KEY: str = os.getenv("VOLCENGINE_API_KEY", "")
    DEFAULT_BASE_URL: str = os.getenv("VOLCENGINE_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
    
    # AI模型参数配置
    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_MAX_TOKENS: int = 2000
    DEFAULT_TIMEOUT: int = 120  # 调整为2分钟，适应大模型响应时间
    
    # Weaviate配置
    WEAVIATE_URL: str = os.getenv("WEAVIATE_URL", "http://localhost:8080")
    WEAVIATE_API_KEY: Optional[str] = os.getenv("WEAVIATE_API_KEY")
    
    # 业务数据库配置
    BUSINESS_DATABASE_URL: str = os.getenv("BUSINESS_DATABASE_URL", "")
    
    # 系统数据库配置
    SYSTEM_DATABASE_URL: str = os.getenv("SYSTEM_DATABASE_URL", "sqlite:///./analy_design.db")
    
    # OCR配置
    TESSERACT_CMD: str = os.getenv("TESSERACT_CMD", "tesseract")
    
    # 文件存储配置
    UPLOAD_FOLDER: str = "uploads"
    TEMPLATE_FOLDER: str = "templates"
    OUTPUT_FOLDER: str = "outputs"
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB
    
    # 文档模板配置
    BACKEND_DESIGN_TEMPLATE: str = "backend_design_template.md"
    FRONTEND_DESIGN_TEMPLATE: str = "frontend_design_template.md"
    API_DESIGN_TEMPLATE: str = "api_design_template.md"
    
    # 业务配置
    COMPANY_NAME: str = os.getenv("COMPANY_NAME", "公司名称")
    PRODUCT_LINE: str = os.getenv("PRODUCT_LINE", "产品线")
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/app.log")
    
    class Config:
        env_file = ".env"

settings = Settings() 