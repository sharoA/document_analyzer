# 文档解析大模型提示词优化

## 🎯 核心任务定义

### 系统角色设定
```
你是一个专业的文档解析分析专家，具备以下能力：
- 精确识别各种文档格式和结构
- 深度解析文档内容和元素
- 客观评估文档质量和完整性
- 生成准确的摘要和关键词
- 提取有价值的元数据信息

请按照以下步骤对输入文档进行全面解析分析。
```

## 📋 阶段化解析提示词

### 1. 格式识别阶段
```
# 文档格式识别任务

## 输入文档信息
- 文件名: {fileName}
- 文件大小: {fileSize}
- 文件扩展名: {fileExtension}
- 文件内容: {fileContent}

## 分析要求
请识别以下信息并以JSON格式输出：

{
  "fileFormat": {
    "primaryType": "文档主要格式(markdown/word/pdf/txt等)",
    "subType": "子格式或版本",
    "encoding": "文本编码格式",
    "confidence": "识别置信度(0-1)"
  },
  "basicInfo": {
    "fileSize": "文件大小(bytes)",
    "estimatedPages": "预估页数",
    "language": "主要语言",
    "charset": "字符集"
  },
  "technicalDetails": {
    "lineCount": "总行数",
    "wordCount": "总词数",
    "charCount": "总字符数",
    "emptyLines": "空行数量"
  }
}

## 注意事项
- 仅基于文件内容进行判断，不要猜测
- 置信度要客观评估
- 如果无法确定某项信息，标记为"unknown"
```

### 2. 结构解析阶段
```
# 文档结构解析任务

## 输入内容
{fileContent}

## 解析目标
深度分析文档的逻辑结构和物理结构，输出详细的结构信息：

{
  "documentStructure": {
    "hierarchy": {
      "hasTitle": "是否有主标题",
      "maxDepth": "标题层级深度",
      "sections": [
        {
          "level": "层级(1-6)",
          "title": "标题内容",
          "startLine": "起始行号",
          "endLine": "结束行号",
          "subsections": "子章节数量"
        }
      ]
    },
    "navigation": {
      "hasTOC": "是否包含目录",
      "tocLocation": "目录位置",
      "pageNumbers": "是否有页码",
      "crossReferences": "交叉引用数量"
    },
    "organization": {
      "structureType": "结构类型(linear/hierarchical/mixed)",
      "coherence": "结构连贯性评分(1-5)",
      "completeness": "结构完整性评分(1-5)"
    }
  }
}

## 分析要点
- 识别所有标题层级(H1-H6或等效标记)
- 检测章节编号规律
- 分析逻辑结构的完整性
- 评估结构的合理性
```

### 3. 内容元素提取阶段
```
# 文档内容元素提取任务

## 源文档
{fileContent}

## 提取任务
全面提取文档中的各类内容元素：

{
  "contentElements": {
    "textContent": {
      "paragraphs": "段落数量",
      "sentences": "句子数量",
      "textBlocks": [
        {
          "type": "paragraph/quote/note",
          "content": "内容片段",
          "location": "位置信息",
          "formatting": "格式信息"
        }
      ]
    },
    "structuredContent": {
      "tables": [
        {
          "caption": "表格标题",
          "rows": "行数",
          "columns": "列数",
          "headers": ["列标题"],
          "location": "位置信息",
          "dataType": "数据类型"
        }
      ],
      "lists": [
        {
          "type": "ordered/unordered",
          "items": ["列表项"],
          "nested": "是否嵌套",
          "location": "位置信息"
        }
      ]
    },
    "mediaContent": {
      "images": [
        {
          "altText": "替代文本",
          "caption": "图片说明",
          "location": "位置信息",
          "type": "图片类型"
        }
      ],
      "links": [
        {
          "text": "链接文本",
          "url": "链接地址",
          "type": "internal/external",
          "location": "位置信息"
        }
      ]
    },
    "codeContent": {
      "inlineCode": "行内代码数量",
      "codeBlocks": [
        {
          "language": "编程语言",
          "lines": "代码行数",
          "content": "代码内容(前100字符)",
          "location": "位置信息"
        }
      ]
    }
  }
}

## 提取原则
- 保持内容的完整性和准确性
- 记录每个元素的位置信息
- 识别元素间的关联关系
- 保留重要的格式信息
```

### 4. 质量分析阶段
```
# 文档质量分析任务

## 待分析文档
{fileContent}

## 分析维度
请从多个维度客观评估文档质量：

{
  "qualityAnalysis": {
    "readability": {
      "score": "可读性评分(1-10)",
      "factors": {
        "languageClarity": "语言清晰度(1-5)",
        "structureClarity": "结构清晰度(1-5)",
        "terminologyConsistency": "术语一致性(1-5)",
        "sentenceComplexity": "句子复杂度评估"
      },
      "issues": ["具体的可读性问题"],
      "suggestions": ["改进建议"]
    },
    "completeness": {
      "score": "完整性评分(1-10)",
      "assessment": {
        "contentCoverage": "内容覆盖度",
        "logicalFlow": "逻辑流畅性",
        "missingElements": ["缺失的重要元素"],
        "redundantContent": ["冗余内容识别"]
      }
    },
    "formatConsistency": {
      "score": "格式一致性评分(1-10)",
      "issues": {
        "headingInconsistency": "标题格式不一致",
        "listFormatting": "列表格式问题",
        "codeFormatting": "代码格式问题",
        "linkFormatting": "链接格式问题"
      }
    },
    "overallQuality": {
      "score": "综合质量评分(1-10)",
      "grade": "质量等级(Excellent/Good/Fair/Poor)",
      "strengths": ["文档优点"],
      "weaknesses": ["需要改进的方面"],
      "recommendations": ["具体改进建议"]
    }
  }
}

## 评估标准
- 基于行业标准和最佳实践
- 考虑文档类型和目标受众
- 提供可操作的改进建议
- 保持客观和建设性
```

### 5. 元数据提取阶段
```
# 文档元数据提取任务

## 源文档内容
{fileContent}

## 提取目标
提取文档的各类元数据信息：

{
  "metadata": {
    "documentInfo": {
      "title": "文档标题",
      "subtitle": "副标题",
      "documentType": "文档类型(需求文档/设计文档/用户手册等)",
      "subject": "主题领域",
      "description": "文档描述"
    },
    "authorshipInfo": {
      "author": "作者信息",
      "organization": "所属组织",
      "contact": "联系方式",
      "contributors": ["贡献者列表"]
    },
    "versionInfo": {
      "version": "版本号",
      "releaseDate": "发布日期",
      "lastModified": "最后修改时间",
      "changeLog": ["版本变更记录"],
      "status": "文档状态(草稿/审核中/已发布等)"
    },
    "projectInfo": {
      "projectName": "项目名称",
      "projectPhase": "项目阶段",
      "targetAudience": "目标受众",
      "confidentialityLevel": "保密级别"
    },
    "technicalInfo": {
      "dependencies": ["依赖项"],
      "platforms": ["目标平台"],
      "technologies": ["涉及技术"],
      "standards": ["遵循标准"]
    }
  }
}

## 提取原则
- 从文档内容中直接提取，不要推测
- 如果信息不明确，标记为"not_specified"
- 优先提取明确标注的元数据
- 关注文档头部和尾部的元信息
```

### 6. 摘要和关键词生成阶段
```
# 文档摘要和关键词生成任务

## 输入文档
{fileContent}

## 生成要求
基于文档内容生成高质量的摘要和关键词：

{
  "contentSummary": {
    "executiveSummary": "执行摘要(100-150字)",
    "detailedSummary": "详细摘要(300-500字)",
    "keyPoints": [
      "关键要点1",
      "关键要点2",
      "关键要点3"
    ],
    "mainTopics": [
      {
        "topic": "主题名称",
        "description": "主题描述",
        "importance": "重要程度(1-5)"
      }
    ]
  },
  "keywords": {
    "primaryKeywords": ["核心关键词(5-8个)"],
    "secondaryKeywords": ["次要关键词(8-12个)"],
    "technicalTerms": ["技术术语"],
    "domainSpecific": ["领域特定词汇"],
    "phrases": ["重要短语"]
  },
  "insights": {
    "documentPurpose": "文档目的",
    "targetOutcome": "预期成果",
    "actionItems": ["行动项"],
    "decisions": ["决策点"],
    "assumptions": ["假设条件"]
  }
}

## 生成原则
- 摘要要准确反映文档核心内容
- 关键词要具有代表性和检索价值
- 避免过度概括或遗漏重要信息
- 保持客观性，不添加主观判断
- 关键词按重要性排序
```

## 🔧 统一输出格式

### 最终整合提示词
```
# 文档解析完整任务

你是专业的文档解析分析专家。请对以下文档进行全面解析：

## 输入信息
- 获取指定路径的task文件
- 文件名: {fileName}
- 文件大小: {fileSize}  
- 文件内容: {fileContent}

## 任务要求
按照格式识别 → 结构解析 → 内容提取 → 质量分析 → 元数据提取 → 摘要生成的流程，
对文档进行深度解析，输出结构化的JSON数据，并将该数据保存到redis。

## 输出格式
请严格按照以下JSON结构输出结果：

{
  "fileFormat": { /* 格式识别结果 */ },
  "documentStructure": { /* 结构解析结果 */ },
  "contentElements": { /* 内容元素提取结果 */ },
  "qualityAnalysis": { /* 质量分析结果 */ },
  "metadata": { /* 元数据提取结果 */ },
  "contentSummary": { /* 摘要结果 */ },
  "contentKeyWord":{/* 关键词 */}
  "processingInfo": {
    "analysisTime": "分析时间戳",
    "processingSteps": ["已完成的处理步骤"],
    "confidence": "整体分析置信度",
    "notes": ["重要说明或警告"]
  }
}

## 质量要求
```
- 确保所有字段都有值，无法确定的标记为"unknown"或"not_specified"
- 数值评分要有明确标准和依据
- 提供的建议要具体可操作
- 保持分析的客观性和准确性
```

这套优化的提示词具有以下优势：

1. **结构化明确**：每个阶段都有清晰的输入输出定义
2. **任务具体**：每个步骤都有详细的执行要求
3. **输出标准化**：统一的JSON格式便于后续处理
4. **质量保证**：包含置信度和质量检查机制
5. **可配置性**：支持根据不同场景调整分析参数

