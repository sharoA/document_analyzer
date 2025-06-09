"""
AI智能分析服务
基于CRUD操作生成API接口设计和MQ配置
"""

import json
import time
from typing import Dict, Any, List
from .base_service import BaseAnalysisService

class AIAnalyzerService(BaseAnalysisService):
    """AI智能分析服务类"""
    
    async def analyze(self, task_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行AI智能分析
        
        Args:
            task_id: 任务ID
            input_data: 包含内容分析结果的数据
            
        Returns:
            AI分析结果字典
        """
        start_time = time.time()
        
        try:
            # 提取内容分析结果
            content_analysis = input_data.get("content_analysis", {})
            crud_operations = content_analysis.get("crud_analysis", {}).get("crud_operations", [])
            business_analysis = content_analysis.get("business_analysis", {})
            
            self._log_analysis_start(task_id, "AI智能分析", len(crud_operations))
            
            # API接口设计
            api_design = await self._generate_api_design(crud_operations, business_analysis)
            
            # MQ消息队列配置
            mq_config = await self._generate_mq_config(crud_operations, business_analysis)
            
            # 技术架构建议
            architecture_design = await self._generate_architecture_design(content_analysis)
            
            # 实现优先级规划
            implementation_plan = await self._generate_implementation_plan(crud_operations, business_analysis)
            
            # 代码生成建议
            code_generation = await self._generate_code_suggestions(api_design, mq_config)
            
            # 合并AI分析结果
            ai_result = {
                "api_design": api_design,
                "mq_config": mq_config,
                "architecture_design": architecture_design,
                "implementation_plan": implementation_plan,
                "code_generation": code_generation,
                "metadata": {
                    "analysis_method": "AI智能分析",
                    "analysis_time": time.time() - start_time,
                    "crud_operations_count": len(crud_operations)
                }
            }
            
            duration = time.time() - start_time
            self._log_analysis_complete(task_id, "AI智能分析", duration, len(str(ai_result)))
            
            return self._create_response(
                success=True,
                data=ai_result,
                metadata={"analysis_duration": duration}
            )
            
        except Exception as e:
            self._log_error(task_id, "AI智能分析", e)
            return self._create_response(
                success=False,
                error=f"AI智能分析失败: {str(e)}"
            )
    
    async def _generate_api_design(self, crud_operations: List[Dict], business_analysis: Dict) -> Dict[str, Any]:
        """生成API接口设计"""
        system_prompt = """你是一个专业的API架构师，请根据CRUD操作需求设计RESTful API接口。

对每个CRUD操作，请设计：
1. HTTP方法和URL路径
2. 请求参数（路径参数、查询参数、请求体）
3. 响应格式（成功和错误响应）
4. 状态码
5. 认证和权限要求
6. 接口描述和使用场景

返回JSON格式：
{
    "api_interfaces": [
        {
            "name": "接口名称",
            "method": "GET/POST/PUT/DELETE",
            "path": "/api/resource/{id}",
            "description": "接口描述",
            "parameters": {
                "path": [{"name": "id", "type": "string", "required": true}],
                "query": [{"name": "page", "type": "int", "required": false}],
                "body": {"type": "object", "properties": {}}
            },
            "responses": {
                "200": {"description": "成功", "schema": {}},
                "400": {"description": "请求错误"},
                "401": {"description": "未授权"},
                "404": {"description": "资源不存在"}
            },
            "authentication": "Bearer Token",
            "permissions": ["read", "write"],
            "crud_type": "Create/Read/Update/Delete"
        }
    ],
    "api_summary": {
        "total_interfaces": 数量,
        "base_url": "/api/v1",
        "authentication_method": "JWT",
        "rate_limiting": "100 requests/minute"
    }
}"""
        
        crud_summary = self._summarize_crud_operations(crud_operations)
        business_entities = business_analysis.get("data_entities", [])
        
        user_prompt = f"""请根据以下CRUD操作需求设计API接口：

CRUD操作摘要：
{json.dumps(crud_summary, ensure_ascii=False, indent=2)}

业务实体：
{json.dumps(business_entities, ensure_ascii=False, indent=2)}

请按照指定的JSON格式返回API设计结果。"""
        
        try:
            response = await self._call_llm(user_prompt, system_prompt, max_tokens=3000)
            if response:
                try:
                    api_design = json.loads(response)
                    # 添加接口验证和优化
                    api_design["validation"] = self._validate_api_design(api_design)
                    return api_design
                except json.JSONDecodeError:
                    return {"raw_response": response, "parse_error": "JSON解析失败"}
            else:
                return {"error": "LLM响应为空"}
        except Exception as e:
            return {"error": f"API设计生成失败: {str(e)}"}
    
    def _summarize_crud_operations(self, crud_operations: List[Dict]) -> Dict[str, Any]:
        """总结CRUD操作"""
        summary = {
            "create_operations": [],
            "read_operations": [],
            "update_operations": [],
            "delete_operations": []
        }
        
        for operation in crud_operations:
            op_type = operation.get("type", "").lower()
            if "create" in op_type:
                summary["create_operations"].append(operation)
            elif "read" in op_type:
                summary["read_operations"].append(operation)
            elif "update" in op_type:
                summary["update_operations"].append(operation)
            elif "delete" in op_type:
                summary["delete_operations"].append(operation)
        
        return summary
    
    def _validate_api_design(self, api_design: Dict) -> Dict[str, Any]:
        """验证API设计"""
        validation_results = {
            "valid_interfaces": 0,
            "issues": [],
            "suggestions": []
        }
        
        interfaces = api_design.get("api_interfaces", [])
        
        for interface in interfaces:
            # 检查必要字段
            required_fields = ["name", "method", "path", "description"]
            missing_fields = [field for field in required_fields if not interface.get(field)]
            
            if missing_fields:
                validation_results["issues"].append(f"接口 {interface.get('name', '未知')} 缺少字段: {missing_fields}")
            else:
                validation_results["valid_interfaces"] += 1
            
            # 检查HTTP方法和路径的匹配
            method = interface.get("method", "").upper()
            path = interface.get("path", "")
            
            if method == "GET" and "{id}" not in path and "list" not in interface.get("name", "").lower():
                validation_results["suggestions"].append(f"GET接口 {interface.get('name')} 建议添加分页参数")
            
            if method in ["POST", "PUT"] and not interface.get("parameters", {}).get("body"):
                validation_results["suggestions"].append(f"{method}接口 {interface.get('name')} 建议添加请求体参数")
        
        return validation_results
    
    async def _generate_mq_config(self, crud_operations: List[Dict], business_analysis: Dict) -> Dict[str, Any]:
        """生成MQ消息队列配置"""
        system_prompt = """你是一个专业的消息队列架构师，请根据业务需求设计消息队列配置。

请设计：
1. 消息主题(Topic)和队列(Queue)
2. 生产者和消费者配置
3. 消息格式和路由规则
4. 错误处理和重试机制
5. 监控和告警配置

返回JSON格式：
{
    "mq_topics": [
        {
            "name": "topic_name",
            "description": "主题描述",
            "message_type": "事件类型",
            "producers": ["服务A", "服务B"],
            "consumers": ["服务C", "服务D"],
            "message_schema": {
                "type": "object",
                "properties": {}
            },
            "routing_key": "routing.key.pattern",
            "retention_policy": "7 days",
            "partition_count": 3
        }
    ],
    "mq_queues": [
        {
            "name": "queue_name",
            "description": "队列描述",
            "binding_topic": "topic_name",
            "consumer_group": "group_name",
            "max_retry_count": 3,
            "dead_letter_queue": "dlq_name"
        }
    ],
    "mq_config": {
        "broker_type": "RabbitMQ/Kafka",
        "cluster_nodes": ["node1", "node2"],
        "authentication": "SASL_PLAINTEXT",
        "monitoring": {
            "metrics": ["message_rate", "consumer_lag"],
            "alerts": ["high_lag", "failed_messages"]
        }
    }
}"""
        
        business_processes = business_analysis.get("business_processes", [])
        
        user_prompt = f"""请根据以下业务需求设计消息队列配置：

CRUD操作数量：{len(crud_operations)}
业务流程：
{json.dumps(business_processes, ensure_ascii=False, indent=2)}

主要考虑的消息场景：
1. 数据变更通知
2. 异步处理任务
3. 系统间集成
4. 事件驱动架构

请按照指定的JSON格式返回MQ配置结果。"""
        
        try:
            response = await self._call_llm(user_prompt, system_prompt, max_tokens=2500)
            if response:
                try:
                    mq_config = json.loads(response)
                    # 添加配置验证
                    mq_config["validation"] = self._validate_mq_config(mq_config)
                    return mq_config
                except json.JSONDecodeError:
                    return {"raw_response": response, "parse_error": "JSON解析失败"}
            else:
                return {"error": "LLM响应为空"}
        except Exception as e:
            return {"error": f"MQ配置生成失败: {str(e)}"}
    
    def _validate_mq_config(self, mq_config: Dict) -> Dict[str, Any]:
        """验证MQ配置"""
        validation_results = {
            "valid_topics": 0,
            "valid_queues": 0,
            "issues": [],
            "suggestions": []
        }
        
        topics = mq_config.get("mq_topics", [])
        queues = mq_config.get("mq_queues", [])
        
        # 验证主题配置
        for topic in topics:
            if topic.get("name") and topic.get("description"):
                validation_results["valid_topics"] += 1
            else:
                validation_results["issues"].append(f"主题配置不完整: {topic.get('name', '未知')}")
        
        # 验证队列配置
        for queue in queues:
            if queue.get("name") and queue.get("binding_topic"):
                validation_results["valid_queues"] += 1
            else:
                validation_results["issues"].append(f"队列配置不完整: {queue.get('name', '未知')}")
        
        # 检查主题和队列的绑定关系
        topic_names = {topic.get("name") for topic in topics}
        for queue in queues:
            binding_topic = queue.get("binding_topic")
            if binding_topic and binding_topic not in topic_names:
                validation_results["issues"].append(f"队列 {queue.get('name')} 绑定的主题 {binding_topic} 不存在")
        
        return validation_results
    
    async def _generate_architecture_design(self, content_analysis: Dict) -> Dict[str, Any]:
        """生成技术架构设计"""
        complexity_level = content_analysis.get("complexity_analysis", {}).get("complexity_level", "中等")
        crud_count = len(content_analysis.get("crud_analysis", {}).get("crud_operations", []))
        
        architecture_suggestions = {
            "简单": {
                "architecture_pattern": "单体架构",
                "database": "MySQL/PostgreSQL",
                "cache": "Redis",
                "framework": "Spring Boot/Django",
                "deployment": "Docker容器"
            },
            "中等": {
                "architecture_pattern": "分层架构/微服务",
                "database": "MySQL主从 + MongoDB",
                "cache": "Redis集群",
                "framework": "Spring Cloud/Django + Celery",
                "deployment": "Kubernetes"
            },
            "复杂": {
                "architecture_pattern": "微服务架构",
                "database": "分布式数据库 + 数据湖",
                "cache": "Redis集群 + CDN",
                "framework": "Spring Cloud Gateway + 服务网格",
                "deployment": "Kubernetes + Istio"
            }
        }
        
        base_suggestion = architecture_suggestions.get(complexity_level, architecture_suggestions["中等"])
        
        return {
            "complexity_level": complexity_level,
            "recommended_architecture": base_suggestion,
            "scalability_considerations": [
                f"预计支持{crud_count * 10}个并发操作",
                "考虑水平扩展能力",
                "设计缓存策略",
                "实现负载均衡"
            ],
            "security_recommendations": [
                "实现JWT认证",
                "API网关限流",
                "数据加密传输",
                "审计日志记录"
            ],
            "monitoring_strategy": [
                "应用性能监控(APM)",
                "业务指标监控",
                "错误率和响应时间监控",
                "资源使用率监控"
            ]
        }
    
    async def _generate_implementation_plan(self, crud_operations: List[Dict], business_analysis: Dict) -> Dict[str, Any]:
        """生成实现优先级规划"""
        # 根据复杂度和业务重要性排序
        prioritized_operations = self._prioritize_operations(crud_operations)
        
        phases = []
        current_phase = []
        phase_complexity = 0
        
        for operation in prioritized_operations:
            op_complexity = self._calculate_operation_complexity(operation)
            
            if phase_complexity + op_complexity > 10 and current_phase:
                phases.append({
                    "phase": len(phases) + 1,
                    "operations": current_phase.copy(),
                    "estimated_time": self._estimate_phase_time(current_phase),
                    "complexity_score": phase_complexity
                })
                current_phase = []
                phase_complexity = 0
            
            current_phase.append(operation)
            phase_complexity += op_complexity
        
        if current_phase:
            phases.append({
                "phase": len(phases) + 1,
                "operations": current_phase,
                "estimated_time": self._estimate_phase_time(current_phase),
                "complexity_score": phase_complexity
            })
        
        return {
            "implementation_phases": phases,
            "total_phases": len(phases),
            "estimated_total_time": sum(phase["estimated_time"] for phase in phases),
            "priority_strategy": "核心功能优先，复杂度递增",
            "risk_assessment": self._assess_implementation_risks(phases)
        }
    
    def _prioritize_operations(self, crud_operations: List[Dict]) -> List[Dict]:
        """操作优先级排序"""
        def priority_score(operation):
            # 基础CRUD操作优先级：Read > Create > Update > Delete
            type_priority = {
                "read": 4,
                "create": 3,
                "update": 2,
                "delete": 1
            }
            
            op_type = operation.get("type", "").lower()
            base_score = type_priority.get(op_type, 2)
            
            # 复杂度影响（简单的优先）
            complexity = operation.get("complexity", "中等")
            complexity_score = {"简单": 3, "中等": 2, "复杂": 1}.get(complexity, 2)
            
            return base_score + complexity_score
        
        return sorted(crud_operations, key=priority_score, reverse=True)
    
    def _calculate_operation_complexity(self, operation: Dict) -> int:
        """计算操作复杂度分数"""
        complexity_map = {"简单": 2, "中等": 5, "复杂": 8}
        return complexity_map.get(operation.get("complexity", "中等"), 5)
    
    def _estimate_phase_time(self, operations: List[Dict]) -> int:
        """估算阶段开发时间（天）"""
        total_complexity = sum(self._calculate_operation_complexity(op) for op in operations)
        return max(3, total_complexity)  # 最少3天
    
    def _assess_implementation_risks(self, phases: List[Dict]) -> List[str]:
        """评估实现风险"""
        risks = []
        
        if len(phases) > 4:
            risks.append("项目阶段过多，可能导致开发周期过长")
        
        max_complexity = max(phase["complexity_score"] for phase in phases) if phases else 0
        if max_complexity > 15:
            risks.append("存在高复杂度阶段，需要额外的技术评审")
        
        total_time = sum(phase["estimated_time"] for phase in phases)
        if total_time > 30:
            risks.append("总开发时间超过1个月，建议考虑资源投入")
        
        return risks or ["风险评估正常"]
    
    async def _generate_code_suggestions(self, api_design: Dict, mq_config: Dict) -> Dict[str, Any]:
        """生成代码建议"""
        return {
            "framework_recommendations": {
                "backend": ["Spring Boot", "Django", "FastAPI"],
                "frontend": ["React", "Vue.js", "Angular"],
                "database": ["MySQL", "PostgreSQL", "MongoDB"]
            },
            "code_structure": {
                "controller_layer": "处理HTTP请求和响应",
                "service_layer": "业务逻辑处理",
                "repository_layer": "数据访问层",
                "message_layer": "消息队列处理"
            },
            "best_practices": [
                "使用依赖注入",
                "实现统一异常处理",
                "添加参数验证",
                "实现分页查询",
                "使用事务管理",
                "添加单元测试"
            ],
            "generated_examples": {
                "api_count": len(api_design.get("api_interfaces", [])),
                "mq_topic_count": len(mq_config.get("mq_topics", [])),
                "estimated_code_lines": len(api_design.get("api_interfaces", [])) * 50
            }
        } 