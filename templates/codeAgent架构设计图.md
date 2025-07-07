graph TB
    subgraph 输入层
        ReqDoc["需求文档<br/>- 功能需求<br/>- 业务规则<br/>- 接口定义"]
        DesignDoc["设计文档<br/>- 数据模型<br/>- API设计<br/>- 架构设计"]
        User["用户触发<br/>- 执行指令<br/>- 参数配置<br/>- 优先级设置"]
        Feedback["用户反馈<br/>- 修改建议<br/>- 质量要求<br/>- 验收标准"]
    end
    
    subgraph LangGraph核心组件
        StateGraph["LangGraph StateGraph<br/>- 状态节点定义<br/>- 边条件设置<br/>- 工作流编排"]
        WorkflowState["工作流状态管理<br/>- 当前状态跟踪<br/>- 状态变更记录<br/>- 错误状态处理"]
        Checkpointer["PostgreSQL Checkpointer<br/>- 自动状态保存<br/>- 断点恢复<br/>- 事务回滚"]
        ConditionalEdge["条件边控制<br/>- 分支逻辑判断<br/>- 动态路由选择<br/>- 循环控制"]
        ParallelNode["并行节点执行<br/>- 任务并发调度<br/>- 资源分配管理<br/>- 同步点控制"]
        AlertSystem["警报系统<br/>- 异常监控<br/>- 性能警告<br/>- 超时提醒"]
    end
    
    subgraph 步骤1__任务拆分调度
        TaskSplitAgent["任务拆分智能体<br/>🧠 核心决策器"]
        RequirementAnalyzer["需求分析器<br/>- 功能点提取<br/>- 业务逻辑分析<br/>- 依赖关系识别<br/>- 复杂度评估"]
        DesignAnalyzer["设计分析器<br/>- 架构模式识别<br/>- 数据流分析<br/>- 组件依赖分析<br/>- 接口定义解析"]
        TaskScheduler["任务调度器<br/>- 执行序列规划<br/>- 依赖关系排序<br/>- 并行任务识别<br/>- 资源分配策略"]
        TaskQueue["任务队列<br/>- 优先级队列<br/>- 任务状态跟踪<br/>- 重试机制<br/>- 超时处理"]
        TaskPriority["任务优先级评估<br/>- 业务价值评分<br/>- 技术难度评估<br/>- 风险等级分析<br/>- 依赖紧急度"]
    end
    
    subgraph 步骤2__Git管理
        GitAgent["Git管理智能体<br/>🔧 版本控制器"]
        GitExtractor["Git地址提取器<br/>- 文档Git链接识别<br/>- 仓库可访问性验证<br/>- 权限检查<br/>- 分支策略分析"]
        BranchManager["分支管理器<br/>- 开发分支创建<br/>- 分支命名规范<br/>- 分支保护策略<br/>- 合并策略配置"]
        CodeAnalyzer["现有代码分析器<br/>- 项目结构扫描<br/>- 代码风格识别<br/>- 框架版本检测<br/>- 依赖库分析"]
        ConflictResolver["冲突解决器<br/>- 自动冲突检测<br/>- 智能合并策略<br/>- 冲突解决建议<br/>- 回滚机制"]
    end
    
    subgraph 步骤3__智能编码执行
        CodingAgent["🤖 智能编码智能体<br/>核心编码大脑"]
        
        subgraph 代码结构分析模块
            StructureAnalyzer["代码结构分析器<br/>- 包结构扫描<br/>- 分层架构识别<br/>- 命名规范分析<br/>- 设计模式识别"]
            PatternRecognizer["模式识别器<br/>- MVC模式检测<br/>- DDD模式识别<br/>- 微服务架构分析<br/>- 自定义模式学习"]
            LayerMapper["分层映射器<br/>- Controller层定位<br/>- Service层识别<br/>- Repository层分析<br/>- Entity层映射"]
            CodeStyleExtractor["代码风格提取器<br/>- 命名约定识别<br/>- 注释风格分析<br/>- 代码格式规范<br/>- 异常处理模式"]
        end
        
        subgraph 智能代码生成模块
            CodePlanner["代码规划器<br/>- 功能模块规划<br/>- 类关系设计<br/>- 方法签名定义<br/>- 数据流设计"]
            TemplateEngine["模板引擎<br/>- 动态模板生成<br/>- 现有代码适配<br/>- 个性化定制<br/>- 最佳实践集成"]
            CodeGenerator["代码生成器<br/>- 智能代码生成<br/>- 上下文感知<br/>- 业务逻辑实现<br/>- 异常处理添加"]
            CodeIntegrator["代码集成器<br/>- 新旧代码融合<br/>- 依赖关系更新<br/>- 配置文件同步<br/>- 测试代码生成"]
        end
        
        subgraph 分层编码器组
            ControllerCoder["Controller编码器<br/>- REST API实现<br/>- 请求参数验证<br/>- 响应格式统一<br/>- 异常处理<br/>- 权限控制集成"]
            ServiceCoder["Service编码器<br/>- 业务逻辑实现<br/>- 事务管理<br/>- 缓存策略<br/>- 异步处理<br/>- 业务规则验证"]
            RepositoryCoder["Repository编码器<br/>- 数据访问层<br/>- 复杂查询构建<br/>- 分页排序<br/>- 批量操作<br/>- 性能优化"]
            EntityCoder["Entity编码器<br/>- 实体类生成<br/>- 关联关系映射<br/>- 验证注解<br/>- 审计字段<br/>- 序列化配置"]
            DTOCoder["DTO编码器<br/>- 数据传输对象<br/>- 字段映射<br/>- 验证规则<br/>- 转换器生成<br/>- 版本兼容"]
            ConfigCoder["配置编码器<br/>- 配置文件生成<br/>- 环境变量设置<br/>- 依赖注入配置<br/>- 安全配置<br/>- 监控配置"]
            SQLCoder["SQL编码器<br/>- 建表语句生成<br/>- 索引创建<br/>- 数据迁移脚本<br/>- 视图创建<br/>- 存储过程"]
        end
        
        CodeRefactorer["代码重构器<br/>- 代码优化建议<br/>- 重复代码消除<br/>- 性能优化<br/>- 可读性改进<br/>- 设计模式应用"]
    end
    
    subgraph 步骤4__代码审查
        ReviewAgent["代码审查智能体<br/>🔍 质量把关者"]
        StaticAnalyzer["静态代码分析<br/>- 语法错误检查<br/>- 代码质量评估<br/>- 复杂度分析<br/>- 重复代码检测<br/>- 死代码识别"]
        SecurityChecker["安全检查<br/>- SQL注入检测<br/>- XSS漏洞扫描<br/>- 认证授权检查<br/>- 敏感信息泄露<br/>- 依赖漏洞扫描"]
        PerformanceChecker["性能检查<br/>- 性能热点分析<br/>- 内存泄漏检测<br/>- 数据库查询优化<br/>- 并发问题识别<br/>- 资源使用评估"]
        StandardChecker["规范检查<br/>- 编码规范验证<br/>- 命名规范检查<br/>- 文档完整性<br/>- 测试覆盖率<br/>- 版本兼容性"]
    end
    
    subgraph 步骤5__单元测试
        TestAgent["单元测试智能体<br/>🧪 测试专家"]
        TestGenerator["测试用例生成器<br/>- 业务场景测试<br/>- 边界条件测试<br/>- 异常情况测试<br/>- 性能测试用例<br/>- 集成测试用例"]
        TestRunner["测试执行器<br/>- 单元测试运行<br/>- 集成测试执行<br/>- 性能测试运行<br/>- 并发测试执行<br/>- 回归测试运行"]
        CoverageAnalyzer["覆盖率分析器<br/>- 代码覆盖率统计<br/>- 分支覆盖率分析<br/>- 条件覆盖率检查<br/>- 路径覆盖率评估<br/>- 覆盖率报告生成"]
        TestReporter["测试报告生成器<br/>- 测试结果汇总<br/>- 失败原因分析<br/>- 性能指标报告<br/>- 趋势分析<br/>- 质量评估报告"]
        RegressionTester["回归测试<br/>- 历史测试重运行<br/>- 功能兼容性测试<br/>- 性能回归检测<br/>- 接口兼容性测试<br/>- 数据完整性测试"]
    end
    
    subgraph 步骤6__Git提交推送
        CommitAgent["提交智能体<br/>📤 版本管理者"]
        CodeCommitter["代码提交器<br/>- 提交信息生成<br/>- 文件变更分析<br/>- 提交策略选择<br/>- 标签管理<br/>- 变更日志生成"]
        PushManager["推送管理器<br/>- 推送前检查<br/>- 冲突预防<br/>- 推送策略执行<br/>- 权限验证<br/>- 推送状态跟踪"]
        PRCreator["PR创建器<br/>- Pull Request生成<br/>- 代码审查请求<br/>- 变更说明生成<br/>- 审查者分配<br/>- 自动化检查集成"]
        TagManager["版本标签管理<br/>- 语义版本控制<br/>- 发布标签创建<br/>- 版本历史维护<br/>- 回滚点标记<br/>- 版本对比分析"]
    end
    
    subgraph MCP工具集
        SpringBootMCP["Spring Boot MCP<br/>- 项目脚手架<br/>- 配置管理<br/>- 依赖注入<br/>- 自动配置<br/>- 监控集成"]
        MavenMCP["Maven MCP<br/>- 依赖管理<br/>- 构建生命周期<br/>- 插件配置<br/>- 多模块管理<br/>- 发布管理"]
        JpaMCP["JPA MCP<br/>- 实体映射<br/>- 查询构建<br/>- 事务管理<br/>- 缓存配置<br/>- 数据库迁移"]
        GitMCP["Git MCP<br/>- 版本控制<br/>- 分支管理<br/>- 合并策略<br/>- 冲突解决<br/>- 历史追踪"]
        TestMCP["JUnit MCP<br/>- 测试框架<br/>- Mock对象<br/>- 断言工具<br/>- 测试套件<br/>- 覆盖率工具"]
        SonarMCP["SonarQube MCP<br/>- 代码质量<br/>- 安全扫描<br/>- 技术债务<br/>- 质量门禁<br/>- 趋势分析"]
        DockerMCP["Docker MCP<br/>- 容器化<br/>- 镜像构建<br/>- 部署配置<br/>- 环境隔离<br/>- 微服务支持"]
    end
    
    subgraph LangGraph记忆系统
        LongTermMemory["长期记忆 PostgreSQL<br/>- 项目历史记录<br/>- 代码模式库<br/>- 最佳实践库<br/>- 问题解决方案<br/>- 性能基准数据"]
        ShortTermMemory["短期记忆 线程检查点<br/>- 当前会话状态<br/>- 临时变量存储<br/>- 中间结果缓存<br/>- 错误恢复点<br/>- 用户交互历史"]
        CodePatternMemory["代码模式记忆 向量数据库<br/>- 代码相似性搜索<br/>- 设计模式库<br/>- 重构模式<br/>- 性能优化模式<br/>- 安全模式库"]
        ProjectMemory["项目记忆 Redis<br/>- 项目配置信息<br/>- 团队偏好设置<br/>- 代码风格规范<br/>- 业务规则库<br/>- 技术栈信息"]
        FeedbackMemory["反馈记忆 NoSQL<br/>- 用户反馈历史<br/>- 代码审查意见<br/>- 测试失败记录<br/>- 性能瓶颈记录<br/>- 改进建议库"]
    end
    
    %% 主要数据流连接
    User --> StateGraph
    ReqDoc --> StateGraph
    DesignDoc --> StateGraph
    Feedback --> FeedbackMemory

    StateGraph --> WorkflowState
    WorkflowState --> TaskSplitAgent
    WorkflowState <--> Checkpointer
    
    %% 任务拆分阶段详细流程
    TaskSplitAgent --> RequirementAnalyzer
    TaskSplitAgent --> DesignAnalyzer
    RequirementAnalyzer --> TaskScheduler
    DesignAnalyzer --> TaskScheduler
    TaskScheduler --> TaskPriority
    TaskPriority --> TaskQueue
    
    %% Git管理阶段详细流程
    TaskQueue --> ConditionalEdge
    ConditionalEdge --> GitAgent
    GitAgent --> GitExtractor
    GitExtractor --> GitMCP
    GitExtractor --> GitAddressCheck{"找到Git地址?"}
    GitAddressCheck -->|"是"| BranchManager
    GitAddressCheck -->|"否"| DefaultRepo["默认仓库初始化"]
    BranchManager --> DevBranch["开发分支就绪"]
    DefaultRepo --> NewRepo["新仓库就绪"]
    DevBranch --> CodeAnalyzer
    NewRepo --> CodeAnalyzer
    
    %% 智能编码阶段详细流程
    CodeAnalyzer --> CodingAgent
    CodingAgent --> StructureAnalyzer
    StructureAnalyzer --> PatternRecognizer
    PatternRecognizer --> LayerMapper
    LayerMapper --> CodeStyleExtractor
    CodeStyleExtractor --> CodePlanner
    CodePlanner --> TemplateEngine
    TemplateEngine --> CodeGenerator
    CodeGenerator --> ParallelNode
    
    %% 并行编码执行
    ParallelNode --> ControllerCoder
    ParallelNode --> ServiceCoder
    ParallelNode --> RepositoryCoder
    ParallelNode --> EntityCoder
    ParallelNode --> DTOCoder
    ParallelNode --> ConfigCoder
    ParallelNode --> SQLCoder
    
    %% 编码器工具调用
    ControllerCoder --> SpringBootMCP
    ServiceCoder --> SpringBootMCP
    RepositoryCoder --> JpaMCP
    EntityCoder --> JpaMCP
    DTOCoder --> SpringBootMCP
    ConfigCoder --> MavenMCP
    SQLCoder --> JpaMCP
    
    %% 代码集成
    ControllerCoder --> CodeIntegrator
    ServiceCoder --> CodeIntegrator
    RepositoryCoder --> CodeIntegrator
    EntityCoder --> CodeIntegrator
    DTOCoder --> CodeIntegrator
    ConfigCoder --> CodeIntegrator
    SQLCoder --> CodeIntegrator
    CodeIntegrator --> CodeRefactorer
    CodeRefactorer --> CodingComplete["编码完成"]
    
    %% 代码审查阶段
    CodingComplete --> ReviewAgent
    ReviewAgent --> StaticAnalyzer
    ReviewAgent --> SecurityChecker
    ReviewAgent --> PerformanceChecker
    ReviewAgent --> StandardChecker
    
    StaticAnalyzer --> SonarMCP
    SecurityChecker --> SonarMCP
    PerformanceChecker --> SonarMCP
    StandardChecker --> SonarMCP
    
    StaticAnalyzer --> ReviewResult{"审查结果"}
    SecurityChecker --> ReviewResult
    PerformanceChecker --> ReviewResult
    StandardChecker --> ReviewResult
    
    ReviewResult -->|"通过"| TestAgent
    ReviewResult -->|"不通过"| ReviewFeedback["审查反馈与修复"]
    ReviewFeedback --> CodeGenerator
    
    %% 单元测试阶段
    TestAgent --> TestGenerator
    TestGenerator --> TestMCP
    TestGenerator --> TestRunner
    TestRunner --> CoverageAnalyzer
    CoverageAnalyzer --> TestReporter
    TestReporter --> RegressionTester
    RegressionTester --> TestResult{"测试结果"}
    
    TestResult -->|"通过"| CommitAgent
    TestResult -->|"失败"| TestFeedback["测试反馈与修复"]
    TestFeedback --> CodeGenerator
    
    %% Git提交阶段
    CommitAgent --> CodeCommitter
    CodeCommitter --> GitMCP
    CodeCommitter --> PushManager
    PushManager --> GitMCP
    PushManager --> PRCreator
    PRCreator --> TagManager
    TagManager --> GitMCP
    PRCreator --> Success["🎉 任务完成"]
    Success --> User
    
    %% 记忆系统连接
    TaskSplitAgent <--> LongTermMemory
    TaskSplitAgent <--> ShortTermMemory
    GitAgent <--> ProjectMemory
    CodingAgent <--> CodePatternMemory
    CodingAgent <--> LongTermMemory
    StructureAnalyzer <--> CodePatternMemory
    PatternRecognizer <--> CodePatternMemory
    CodeGenerator <--> CodePatternMemory
    ReviewAgent <--> CodePatternMemory
    TestAgent <--> CodePatternMemory
    ReviewAgent <--> AlertSystem
    
    %% LangGraph核心组件连接
    WorkflowState <--> ShortTermMemory
    ConditionalEdge <--> ShortTermMemory
    ParallelNode <--> ShortTermMemory
    
    %% 反馈循环
    ReviewFeedback --> ConditionalEdge
    TestFeedback --> ConditionalEdge
    
    %% 样式定义
    classDef coreClass fill:#e8f5e8,stroke:#2e7d32,stroke-width:3px,font-weight:bold
    classDef agentClass fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,font-weight:bold
    classDef analyzerClass fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef coderClass fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    classDef mcpClass fill:#e0f2f1,stroke:#00695c,stroke-width:2px
    classDef memoryClass fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef decisionClass fill:#ffebee,stroke:#d32f2f,stroke-width:2px
    
    class StateGraph,WorkflowState,Checkpointer,ConditionalEdge,ParallelNode,AlertSystem coreClass
    class TaskSplitAgent,GitAgent,CodingAgent,ReviewAgent,TestAgent,CommitAgent agentClass
    class StructureAnalyzer,PatternRecognizer,LayerMapper,CodeStyleExtractor,CodePlanner,TemplateEngine,CodeGenerator,CodeIntegrator analyzerClass
    class ControllerCoder,ServiceCoder,RepositoryCoder,EntityCoder,DTOCoder,ConfigCoder,SQLCoder coderClass
    class SpringBootMCP,MavenMCP,JpaMCP,GitMCP,TestMCP,SonarMCP,DockerMCP mcpClass
    class LongTermMemory,ShortTermMemory,CodePatternMemory,ProjectMemory,FeedbackMemory memoryClass
    class GitAddressCheck,ReviewResult,TestResult decisionClass