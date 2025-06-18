# 内容分析实现步骤
## 角色定义
你是一名资深AI开发工程师

## 执行步骤
### Step 1：文档预处理
目的：将上传的当前需求文档拆解为结构化内容块，为后续向量化与对比做好准备。
操作流程：
识别文档格式：支持 .docx、.md，统一转为纯文本 + 标题结构。
段落级拆分：
每一段落包含：
标题（如3.1额度申请）
内容块（自然段或子标题）
识别插图并上传：
提取 Word 中的图示、流程图、类图，存储至 OSS/本地路径；
文档中引用替换为：[图片：路径]
使用同一模型对当前段落进行向量表示（如使用 `sentence-transformers`（`bge-large-zh`）为所有文本（包括 OCR 文本和图片描述）生成向量嵌入）。
输出结构样例：
[
  {
    "section": "3.1 额度申请",
    "content": "系统新增评分功能，分值低于80将被拒绝。",
    "image_refs": ["images/score_flow_1.png"]
  },
  ...
]
### Step 2：与历史知识库内容对比
目的：找出与当前内容最接近的历史内容段，进行对比。

#### Step 2-A：历史内容匹配与相似度判断
对每个当前内容块 current_chunk，执行如下：
向 Weaviate 查询最近历史版本（topK=5）
对比每条结果的相似度：
若 max(similarity) ≥ 阈值（如 0.4），视为候选修改项
若 max(similarity) < 阈值（如 0.4），视为新增项

### Step 2-B：识别“删除项”
你提供了关键信息：“当前需求文档中有明确删除描述”，因此：
➤ 操作方式：
对当前文档中内容块执行 关键词搜索，如：
“删除了...功能”
“去除...接口”
“取消...服务”
涉及删除、去除、取消、下划线等内容
若匹配这些关键词，可视为“主动删除”
抽取关键词后的内容（如模块名、接口名） → 与历史文档比对，确认该内容历史中存在
{
  "changeType": "删除",
  "deletedItems": [
    "取消接口 /credit/query",
    "删除手动审批功能"
  ]
}


#### Step 2-c：结构化最终差异比对输出history_content

{
  "module": "额度模块",
  "changeType": "修改",
  "matchedHistory": {
    "similarity": 0.83,
    "version": "LS-4_需求文档 - 北京银行直连链数V1.6.docx",
    "content": "用户通过App申请额度，后台人工审批"
  },
  "currentContent": "用户通过App发起额度申请，系统自动调用审批服务，采用评分模型自动审批。",
  "changeItem": {
    "调用审批服务"
    }
}

### Step 3：大模型变更判断与结构化输出
目的：结合内容、相似段落，大模型判断是否为新增、修改、删除，并输出结构化变更项。

输入大模型样例：
---

【当前版本内容】：
{{current_content}}

【历史版本内容】：
{{history_content}}

请按照以下 JSON 格式输出分析结果：

{
    "current_change":
  [
    "changeType": "新增 | 修改 | 删除",
  "changeReason": "简要说明判断依据",
  "changeItems": {
    "变更点1"
  }
  "version":["LS-4_需求文档 - 北京银行直连链数V1.6.docx"]
  ]
}

### Step 4：对变更项从原文档提取详细变更点
根据第三步：change_analysis.changeItems的变更点到当前文档提取具体的字段要求
输入格式：
【Step 3分析结果】：
{{change_analysis}}

【当前版本完整文档】：
{{document_content}}
输出格式：
{
    "current_change":
  [
    "changeType": "新增 | 修改 | 删除",
  "changeReason": "简要说明判断依据",
  "changeItems": {
    "变更点1"
  },
  "changeDetails"{
    "详细变更内容"
  }

  "version":["LS-4_需求文档 - 北京银行直连链数V1.6.docx"]
  ]
}
注意事项
确保所有变更项都有对应的详细内容
对于字段类变更，必须提取完整的字段定义
保持JSON格式的严格性，确保可解析
对于复杂变更，提供充分的上下文信息
标注变更的业务影响和技术影响


## 技术要求
1、使用langchan框架进行rag；
2、当前使用的weavite向量数据做的向量存储，初始化客户端和模型 使用client = get_weaviate_client()这个方法
3、本次采用 `sentence-transformers`（`bge-large-zh`）向量化
4、模型调用	使用当前项目调用方法_call_llm()