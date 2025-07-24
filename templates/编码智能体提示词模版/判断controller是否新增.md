flowchart TD
    A[API接口生成任务] --> B[扫描项目路径下所有Controller]
    B --> C{找到Controller文件?}
    C -->|是| D[提取Controller信息<br/>类名/包名/路径/方法]
    C -->|否| E[直接创建新Controller]
    D --> F{LLM客户端可用?}
    F -->|是| G[LLM语义相似度分析]
    F -->|否| H[规则匹配分析]
    G --> I{相似度>=0.6?}
    H --> J{匹配分数>=0.5?}
    I -->|是| K[使用现有Controller路径]
    I -->|否| L[创建新Controller]
    J -->|是| K
    J -->|否| L
    K --> M[在相似Controller目录生成代码]
    L --> N[在新目录生成代码]


对比项	原方案	新方案
扫描范围	只搜索目录名	扫描所有Java文件
匹配方式	简单关键字匹配	LLM语义分析+规则匹配
信息获取	目录结构	Controller类名/路径/包名/方法
准确性	容易误匹配	基于业务语义的精确匹配
可扩展性	依赖硬编码规则	LLM可学习新的业务模式