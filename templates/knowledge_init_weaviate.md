我需要一个 Python 脚本，将位于 `D:\knowledge_base` 的知识库初始化到本地运行的 Weaviate 向量数据库（地址为 `http://localhost:8080,config.py中有配置`）。知识库包含代码（Java 文件）、数据库表结构（Excel文件形式）、需求文档和链数模块划分，文件格式包括 Word (.docx，包含文本、图片和嵌入的 Excel 表格)、Excel (.xlsx) 和 Java 源代码 (.java)。在当前项目下创建，脚本需满足以下要求：

1. **读取文件**：
   - 递归遍历 `D:\knowledge_base` 目录，处理 `.docx`、`.xlsx` 和 `.java`、 `.xml`文件。
   - 对于 `.docx`：
     - 使用 `python-docx` 提取文本内容。
     - 提取图片，使用 `pytesseract` 进行 OCR 获取文本，并使用 `Salesforce/blip-image-captioning-base` 生成图片描述。
     - 提取嵌入的 Excel 表格（如果存在）并转换为文本。
   - 对于 `.xlsx`：
     - 使用 `openpyxl` 提取表格内容为文本。
   - 对于 `.java`、`.xml`：
     - 解析文件提取代码，尽可能按类或方法分割（使用简单正则表达式或 tree-sitter）。
   - 从目录结构中提取项目名称（例如，`D:\knowledge_base\代码\链数后端代码\zqyl-ls` 中的 `zqyl-ls`）。

2. **处理内容**：
   - 将word需求文档先转成markdown并且将图片剔除出来形成路径，word需求文档大段文本内容 按标题及标题下文本来分割
   例如：{
    "section": "3.1 额度申请",
    "content": "系统新增评分功能，分值低于80将被拒绝。",
    "image_refs": ["images/score_flow_1.png"]
  },确保语义完整性。
   - 使用 `sentence-transformers`（`bge-large-zh`）为所有文本（图片内容提取出到D:\knowledge_base\链数_LS\需求文党\需求文档图片，图片命名规则对应文件名+图片位置标识）生成向量嵌入。
   - 将处理结果（例如 OCR 文本、图片描述）缓存到 Redis，避免重复处理。

3. **Weaviate 集成**：
   - 使用 `weaviate-client` 连接到 Weaviate（`http://localhost:8080,config.py中有配置`）。
   - 定义 Weaviate 模式，包含 `Document` 类，字段包括：`content`（文本）、`file_path`（字符串）、`file_name`（字符串）、`project`（字符串）、`file_type`（字符串，例如 'docx'、'xlsx'、'java'）、`source_type`（字符串，例如 'text'、'ocr'、'image_description'、'excel'）、`image_path`（字符串，用于图片）。
   - 设置 `vectorizer: none`，使用外部嵌入。
   - 使用批量处理（`batch_size=100`）导入数据。
   - 使用 LangChain 的 Weaviate 集成（`langchain.vectorstores.Weaviate`）简化数据插入和查询。

4. **元数据**：
   - 将目录结构存储为 `LS`（例如，`D:\knowledge_base\LS` 的文件存储为 `LS`）。
   - 存储 `file_type` 以区分 `.docx`、`.xlsx`、`.java`、`.xml`。
   - 对于链数模块划分，存储为元数据（例如，如果识别为云链后台用户，标记为 `source_type='zqyl-ls'`）。

5. **输出**：
   - 生成完整的 Python 脚本，处理知识库并导入 Weaviate。
   - 包含一个使用 LangChain 的示例查询，检索与查询相关的文档（例如“LS中的数据库表结构”）。
   - 将脚本保存为 `src/utils/knowledge_init_weaviate.py`。

6. **错误处理**：
   - 处理文件读取错误（例如文件损坏）。
   - 优雅处理 OCR 和图片描述失败。
   - 检查 Redis 连接，缓存结果使用键格式如 `file:{file_path}:{type}`（例如 `file:D:\knowledge_base\project1\doc.docx:ocr`）。

7. **依赖**：
   - 使用 `weaviate-client`、`langchain`、`sentence-transformers`、`python-docx`、`openpyxl`、`pytesseract`、`pdf2image`、`transformers`、`redis`、`pillow`。
   - 假设 Tesseract 和 Poppler 已安装，用于 OCR 和 PDF 处理。

8. **约束**：
   - 不要将图片直接存储在 Weaviate 中，存储 `image_path` 指向本地文件（例如 `D:\knowledge_base\链数_LS\需求文党\需求文档图片\doc_page1.jpg`）。
   - 使用 UUID 生成 Weaviate 对象 ID。
# 技术要求
1、使用langchan框架进行rag；
2、当前使用的weavite向量数据做的向量存储，初始化客户端和模型 使用client = get_weaviate_client()这个方法
3、本次采用 `sentence-transformers`（`bge-large-zh`）向量化
4、模型调用	使用当前项目调用方法_call_llm()

请生成完整的 Python 脚本，包含在代码块中，带有清晰的注释和健壮的错误处理。脚本应可在安装了指定依赖的 Python 环境中直接运行。脚本末尾包含一个 LangChain 示例查询以展示检索功能。

