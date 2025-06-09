# 分析服务模块 (Analysis Services)

## 概述

分析服务模块是一个完整的文档分析解决方案，提供从文档解析到AI智能分析的全流程处理能力。

## 目录结构

```
src/analysis_services/
├── __init__.py              # 模块初始化和导出
├── base_service.py          # 基础服务抽象类
├── document_parser.py       # 文档解析服务
├── content_analyzer.py      # 内容分析服务
├── ai_analyzer.py          # AI智能分析服务
├── vector_database.py      # 向量数据库接口
├── service_manager.py      # 服务管理器
├── config.py               # 配置管理
├── utils.py                # 工具类和函数
├── test_services.py        # 测试文件
└── README.md               # 本文档
```

## 项目目录结构

```
项目根目录/
├── logs/                   # 日志文件存储目录
│   └── analysis_services.log
├── uploads/                # 文件上传和处理目录
│   ├── temp/              # 临时文件目录
│   ├── analysis_results/  # 分析结果存储目录
│   └── cache/             # 缓存文件目录
└── src/
    └── analysis_services/ # 分析服务模块
```

## 核心功能

### 1. 文档解析服务 (DocumentParserService)
- 支持多种文档格式解析 (txt, md, doc, docx, pdf, html, json, xml)
- 智能文档结构分析
- 内容提取和预处理

### 2. 内容分析服务 (ContentAnalyzerService)
- CRUD操作识别和分析
- 业务需求提取
- 复杂度评估
- 向量数据库相似性搜索

### 3. AI智能分析服务 (AIAnalyzerService)
- API接口设计生成
- 消息队列配置设计
- 技术架构建议
- 实现规划和风险评估

### 4. 向量数据库支持
- 抽象接口设计
- Mock和Chroma实现
- 文档相似性搜索
- 知识库构建

### 5. 服务管理器 (AnalysisServiceManager)
- 统一服务生命周期管理
- 完整分析流水线
- 资源协调和调度
- 错误处理和恢复

## 快速开始

### 基本使用

```python
from analysis_services import (
    AnalysisServiceManager,
    get_analysis_config,
    validate_input,
    setup_analysis_logger,
    ensure_analysis_directories
)

# 确保目录结构存在
ensure_analysis_directories()

# 设置日志
logger = setup_analysis_logger("my_analysis")

# 获取配置
config = get_analysis_config()

# 验证输入
validation = validate_input("task_001", "文档内容", "txt")
if all(validation.values()):
    # 初始化服务管理器
    manager = AnalysisServiceManager(llm_client=None, vector_db_type="mock")
    
    # 执行完整分析
    result = await manager.execute_full_analysis(
        task_id="task_001",
        content="文档内容",
        file_type="txt"
    )
    
    logger.info(f"分析完成: {result['success']}")
```

### 文件上传验证

```python
from analysis_services import validate_file_upload, save_analysis_result

# 验证文件上传
file_validation = validate_file_upload("document.txt", 1024)
if all(file_validation.values()):
    # 处理文件...
    
    # 保存分析结果
    result_file = save_analysis_result("task_001", analysis_result)
    print(f"结果保存至: {result_file}")
```

### 单独使用各个服务

```python
from analysis_services import (
    DocumentParserService,
    ContentAnalyzerService,
    AIAnalyzerService
)

# 文档解析
parser = DocumentParserService()
parsing_result = await parser.parse_document("task_001", "文档内容", "txt")

# 内容分析
analyzer = ContentAnalyzerService()
content_result = await analyzer.analyze_content("task_001", parsing_result)

# AI分析
ai_analyzer = AIAnalyzerService()
ai_result = await ai_analyzer.analyze_with_ai("task_001", content_result, crud_operations)
```

## 配置管理

### 环境变量配置

```bash
# 向量数据库配置
export VECTOR_DB_TYPE=mock
export VECTOR_DB_DIR=./vector_db

# 大模型配置
export LLM_MAX_TOKENS=3000
export LLM_TEMPERATURE=0.7

# 性能配置
export MAX_CONCURRENT_TASKS=5
export TASK_TIMEOUT=300

# 日志配置
export LOG_LEVEL=INFO
export LOG_DIR=logs

# 存储配置
export UPLOADS_DIR=uploads
```

### 代码配置

```python
from analysis_services import get_analysis_config, update_analysis_config

# 获取配置
config = get_analysis_config()
llm_config = get_analysis_config("llm")

# 更新配置
update_analysis_config("llm", {"max_tokens": 4000})
```

## 工具函数

### 文本处理

```python
from analysis_services import clean_text, TextProcessor

# 清理文本
clean_content = clean_text("  这是一个   测试文本  \n\n  ")

# 提取关键词
keywords = TextProcessor.extract_keywords("文档内容", top_k=10)

# 统计文本信息
stats = TextProcessor.count_words("文档内容")
```

### 数据验证

```python
from analysis_services import validate_input, validate_file_upload, DataValidator

# 验证输入参数
validation = validate_input("task_001", "内容", "txt")

# 验证文件上传
file_validation = validate_file_upload("test.txt", 1024)

# 验证任务ID
is_valid = DataValidator.validate_task_id("task_001")
```

### 文件操作

```python
from analysis_services import FileUtils

# 确保目录存在
FileUtils.ensure_directory("uploads/temp")

# 获取安全文件名
safe_name = FileUtils.get_safe_filename("文档<>名称.txt")

# 获取唯一文件名
unique_name = FileUtils.get_unique_filename("uploads", "document.txt")

# 安全读写JSON
FileUtils.safe_write_json("data.json", {"key": "value"})
data = FileUtils.safe_read_json("data.json")
```

## 测试

运行测试套件：

```python
from analysis_services.test_services import run_tests

# 运行所有测试
run_tests()
```

或者直接运行测试文件：

```bash
python -m src.analysis_services.test_services
```

## 日志管理

分析服务会自动在 `logs/analysis_services.log` 中记录日志。您也可以设置自定义日志：

```python
from analysis_services import setup_analysis_logger

# 使用默认配置
logger = setup_analysis_logger("my_service")

# 使用自定义日志文件
logger = setup_analysis_logger("my_service", "logs/custom.log")
```

## 错误处理

```python
from analysis_services import ErrorHandler

# 安全执行函数
result = ErrorHandler.safe_execute(some_function, arg1, arg2, default_return={})

# 格式化错误信息
try:
    # 一些操作
    pass
except Exception as e:
    error_info = ErrorHandler.format_error(e)
    ErrorHandler.log_error(e, "执行分析时")
```

## 注意事项

1. **目录权限**: 确保应用有权限在 `logs/` 和 `uploads/` 目录中创建和写入文件
2. **文件大小**: 默认最大文件大小为50MB，可通过配置调整
3. **并发限制**: 默认最大并发任务数为5，可通过环境变量调整
4. **内存使用**: 大文件处理时注意内存使用情况
5. **日志轮转**: 建议配置日志轮转以避免日志文件过大

## 版本信息

当前版本: 1.0.0

## 许可证

请参考项目根目录的许可证文件。 