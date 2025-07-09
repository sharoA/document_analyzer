# 核心功能
## 项目结构分析
- 自动识别 Controller、Service、Application、Mapper、Feign Client 等核心层级
- 提取类的注解、继承关系、方法签名、字段定义
- 分析包路径与命名规范，辅助还原分层结构与模块边界

## 代码语义解析
- 深度解析 Java 文件结构：包名、类名、导入项、注解、字段、方法签名等
- 抽取类级别与方法级别的注解信息（如 @RestController、@Service、@FeignClient）
- 支持识别常见领域命名模式（如 XxxRequest、XxxResponse、XxxException）

## 智能结构分类
- 基于类名、注解与包路径自动归类至对应的 DDD 分层（如 domain/application/infrastructure）
- 自动识别是否为 Spring Boot 项目，并识别 MyBatis、Feign 等常用组件

- 可分析 Mapper XML 文件结构（如 SQL 语句、映射标签）或在mapperJava代码上的sql

## 报告生成与导出
自动生成结构化分析报告到项目/outputs/目录下，文件名：project_name+服务名（repo_name）,markdown格式
报告涵盖项目分层结构、类命名规范、注解使用模式、接口定义方式等
提供项目概览摘要，便于供大模型作为上下文提示使用