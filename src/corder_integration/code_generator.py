#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码生成器
基于设计文档生成后端代码（Java8 + Spring Boot）和前端代码（Vue2）
"""

import os
import re
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from .config import get_coder_config, get_config_manager
from ..utils.openai_client import get_openai_client
from ..utils.volcengine_client import get_volcengine_client
from ..resource.config import get_config

logger = logging.getLogger(__name__)

class CodeGenerator:
    """代码生成器 - 使用AI模型智能生成代码"""
    
    def __init__(self):
        """初始化代码生成器"""
        self.config = get_config()
        self.ai_provider = self.config.get_coder_agent_config().get('ai_provider', 'openai')
        
        # 初始化AI客户端
        if self.ai_provider == 'volcengine':
            self.ai_client = get_volcengine_client()
            logger.info("代码生成器使用火山引擎作为AI提供商")
        else:
            self.ai_client = get_openai_client()
            logger.info("代码生成器使用OpenAI作为AI提供商")
    
    def generate_backend_code(
        self, 
        design_data: Dict[str, Any], 
        project_path: str
    ) -> Dict[str, Any]:
        """
        生成后端代码
        
        Args:
            design_data: 设计文档解析数据
            project_path: 项目路径
            
        Returns:
            生成结果
        """
        logger.info("开始生成后端代码")
        
        generated_files = []
        
        try:
            # 1. 生成项目配置文件
            config_files = self._generate_backend_config(design_data, project_path)
            generated_files.extend(config_files)
            
            # 2. 生成实体类
            entity_files = self._generate_entities(design_data, project_path)
            generated_files.extend(entity_files)
            
            # 3. 生成Repository层
            repository_files = self._generate_repositories(design_data, project_path)
            generated_files.extend(repository_files)
            
            # 4. 生成Service层
            service_files = self._generate_services(design_data, project_path)
            generated_files.extend(service_files)
            
            # 5. 生成Controller层
            controller_files = self._generate_controllers_with_ai(design_data, project_path)
            generated_files.extend(controller_files)
            
            # 6. 生成Application主类
            main_class_files = self._generate_main_application(design_data, project_path)
            generated_files.extend(main_class_files)
            
            return {
                "success": True,
                "generated_files": generated_files,
                "total_files": len(generated_files)
            }
            
        except Exception as e:
            logger.error(f"后端代码生成失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "generated_files": generated_files
            }
    
    def generate_frontend_code(
        self, 
        design_data: Dict[str, Any], 
        project_path: str
    ) -> Dict[str, Any]:
        """
        生成前端代码
        
        Args:
            design_data: 设计文档解析数据
            project_path: 项目路径
            
        Returns:
            生成结果
        """
        logger.info("开始生成前端代码")
        
        generated_files = []
        
        try:
            # 1. 生成项目配置文件
            config_files = self._generate_frontend_config(design_data, project_path)
            generated_files.extend(config_files)
            
            # 2. 生成路由配置
            router_files = self._generate_router_config_with_ai(design_data, project_path)
            generated_files.extend(router_files)
            
            # 3. 生成API接口文件
            api_files = self._generate_api_files_with_ai(design_data, project_path)
            generated_files.extend(api_files)
            
            # 4. 生成Vue组件
            component_files = self._generate_vue_components_with_ai(design_data, project_path)
            generated_files.extend(component_files)
            
            # 5. 生成页面组件
            page_files = self._generate_page_components_with_ai(design_data, project_path)
            generated_files.extend(page_files)
            
            return {
                "success": True,
                "generated_files": generated_files,
                "total_files": len(generated_files)
            }
            
        except Exception as e:
            logger.error(f"前端代码生成失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "generated_files": generated_files
            }

    def _call_ai_for_code_generation(self, prompt: str, context: str = "") -> str:
        """调用AI模型生成代码"""
        try:
            full_prompt = f"""你是一个专业的代码生成助手。请根据以下要求生成高质量的代码。

{context}

要求：
{prompt}

请只返回代码内容，不要包含任何解释或markdown格式。代码应该符合最佳实践和编码规范。
"""
            
            if self.ai_provider == 'volcengine':
                # 使用火山引擎的chat方法
                messages = [
                    {"role": "system", "content": "你是一个专业的代码生成助手。"},
                    {"role": "user", "content": full_prompt}
                ]
                response = self.ai_client.chat(messages)
            else:
                # 使用OpenAI的chat_completion方法
                response = self.ai_client.chat_completion([
                    {"role": "system", "content": "你是一个专业的代码生成助手。"},
                    {"role": "user", "content": full_prompt}
                ])
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"AI代码生成失败: {e}")
            raise e

    def _generate_entities(self, design_data: Dict[str, Any], project_path: str) -> List[str]:
        """生成实体类"""
        files = []
        
        database_design = design_data.get('database_design', [])
        package_path = self._get_package_path(design_data, "entity")
        
        for table in database_design:
            entity_content = self._create_entity_class(table, design_data)
            entity_name = self._normalize_name_for_java(table.get('name', 'Unknown'))
            entity_path = os.path.join(
                project_path, 
                f"src/main/java/{package_path}/{entity_name}.java"
            )
            self._write_file(entity_path, entity_content)
            files.append(entity_path)
        
        return files

    def _generate_repositories(self, design_data: Dict[str, Any], project_path: str) -> List[str]:
        """生成Repository层"""
        files = []
        
        database_design = design_data.get('database_design', [])
        package_path = self._get_package_path(design_data, "repository")
        
        for table in database_design:
            repository_content = self._create_repository_interface(table, design_data)
            entity_name = self._normalize_name_for_java(table.get('name', 'Unknown'))
            repo_path = os.path.join(
                project_path, 
                f"src/main/java/{package_path}/{entity_name}Repository.java"
            )
            self._write_file(repo_path, repository_content)
            files.append(repo_path)
        
        return files

    def _generate_services(self, design_data: Dict[str, Any], project_path: str) -> List[str]:
        """生成Service层"""
        files = []
        
        business_logic = design_data.get('business_logic', [])
        package_path = self._get_package_path(design_data, "service")
        
        for module in business_logic:
            service_content = self._create_service_class(module, design_data)
            module_name = self._normalize_name_for_java(module.get('module', 'Unknown'))
            service_path = os.path.join(
                project_path, 
                f"src/main/java/{package_path}/{module_name}Service.java"
            )
            self._write_file(service_path, service_content)
            files.append(service_path)
        
        return files

    def _generate_controllers(self, design_data: Dict[str, Any], project_path: str) -> List[str]:
        """生成Controller层"""
        files = []
        
        api_design = design_data.get('api_design', [])
        package_path = self._get_package_path(design_data, "controller")
        
        # 按路径分组API
        api_groups = {}
        for api in api_design:
            path_parts = api.get('path', '/').split('/')
            if len(path_parts) > 1:
                controller_name = self._normalize_name_for_java(path_parts[1])
                if controller_name not in api_groups:
                    api_groups[controller_name] = []
                api_groups[controller_name].append(api)
        
        for controller_name, apis in api_groups.items():
            controller_content = self._create_controller_class(controller_name, apis, design_data)
            controller_path = os.path.join(
                project_path, 
                f"src/main/java/{package_path}/{controller_name}Controller.java"
            )
            self._write_file(controller_path, controller_content)
            files.append(controller_path)
        
        return files

    def _generate_controllers_with_ai(self, design_data: Dict[str, Any], project_path: str) -> List[str]:
        """使用AI生成Controller类"""
        files = []
        api_design = design_data.get('api_design', [])
        
        # 按路径分组API
        api_groups = {}
        for api in api_design:
            path_parts = api.get('path', '/').split('/')
            if len(path_parts) > 1:
                controller_name = self._normalize_name_for_java(path_parts[1])
                if controller_name not in api_groups:
                    api_groups[controller_name] = []
                api_groups[controller_name].append(api)
        
        for controller_name, apis in api_groups.items():
            try:
                package_prefix = self._get_package_prefix(design_data)
                prompt = f"""
生成一个Spring Boot REST Controller类，要求：

1. 控制器名: {controller_name}Controller
2. 包名: {package_prefix}.controller
3. 使用@RestController和@RequestMapping注解
4. 包含以下API接口:

{json.dumps(apis, ensure_ascii=False, indent=2)}

要求:
- 使用适当的HTTP方法注解(@GetMapping, @PostMapping等)
- 包含请求参数验证
- 返回统一的响应格式(ResponseEntity)
- 包含异常处理
- 添加适当的日志记录
- 使用@Autowired注入Service

业务逻辑参考:
{json.dumps(design_data.get('business_logic', []), ensure_ascii=False)}

请生成完整的Controller类代码。
"""
                
                context = f"项目信息: {design_data.get('project_info', {})}"
                controller_code = self._call_ai_for_code_generation(prompt, context)
                controller_code = self._clean_ai_generated_code(controller_code)
                
                package_path = self._get_package_path(design_data, "controller")
                controller_path = os.path.join(
                    project_path, 
                    f"src/main/java/{package_path}/{controller_name}Controller.java"
                )
                
                self._write_file(controller_path, controller_code)
                files.append(controller_path)
                
                logger.info(f"生成Controller类: {controller_name}Controller")
                
            except Exception as e:
                logger.error(f"生成Controller {controller_name} 失败: {e}")
                continue
        
        return files

    def _generate_vue_components_with_ai(self, design_data: Dict[str, Any], project_path: str) -> List[str]:
        """使用AI生成Vue组件"""
        files = []
        components = design_data.get('components', [])
        
        for component in components:
            try:
                component_name = component.get('name', 'Unknown')
                
                prompt = f"""
生成一个Vue 2组件，要求：

1. 组件名: {component_name}
2. 类型: {component.get('type', 'component')}
3. 描述: {component.get('description', '')}
4. 使用Element UI组件库
5. 包含template、script、style三个部分
6. 使用Vue 2的语法
7. 包含适当的数据验证和错误处理
8. 添加loading状态和用户友好的提示

API接口参考:
{json.dumps(design_data.get('api_endpoints', []), ensure_ascii=False)}

项目页面信息:
{json.dumps(design_data.get('pages', []), ensure_ascii=False)}

请生成完整的Vue组件代码。
"""
                
                context = f"项目信息: {design_data.get('project_info', {})}"
                component_code = self._call_ai_for_code_generation(prompt, context)
                component_code = self._clean_ai_generated_code(component_code)
                
                component_path = os.path.join(
                    project_path, 
                    f"frontend/src/components/{component_name}.vue"
                )
                
                self._write_file(component_path, component_code)
                files.append(component_path)
                
                logger.info(f"生成Vue组件: {component_name}")
                
            except Exception as e:
                logger.error(f"生成Vue组件 {component_name} 失败: {e}")
                continue
        
        return files

    def _generate_page_components_with_ai(self, design_data: Dict[str, Any], project_path: str) -> List[str]:
        """使用AI生成页面组件"""
        files = []
        pages = design_data.get('pages', [])
        
        for page in pages:
            try:
                page_name = page.get('name', 'Unknown')
                
                prompt = f"""
生成一个Vue 2页面组件，要求：

1. 页面名: {page_name}
2. 路径: {page.get('path', '/')}
3. 描述: {page.get('description', '')}
4. 包含的组件: {', '.join(page.get('components', []))}
5. 使用Element UI组件库
6. 包含完整的页面布局
7. 实现响应式设计
8. 包含页面级的状态管理
9. 添加页面跳转和路由功能

相关API接口:
{json.dumps(design_data.get('api_endpoints', []), ensure_ascii=False)}

组件信息:
{json.dumps(design_data.get('components', []), ensure_ascii=False)}

请生成完整的Vue页面组件代码。
"""
                
                context = f"项目信息: {design_data.get('project_info', {})}"
                page_code = self._call_ai_for_code_generation(prompt, context)
                page_code = self._clean_ai_generated_code(page_code)
                
                page_path = os.path.join(
                    project_path, 
                    f"frontend/src/views/{page_name}.vue"
                )
                
                self._write_file(page_path, page_code)
                files.append(page_path)
                
                logger.info(f"生成Vue页面: {page_name}")
                
            except Exception as e:
                logger.error(f"生成Vue页面 {page_name} 失败: {e}")
                continue
        
        # 生成App.vue
        app_code = self._generate_app_vue_with_ai(design_data)
        app_path = os.path.join(project_path, "frontend/src/App.vue")
        self._write_file(app_path, app_code)
        files.append(app_path)
        
        return files

    def _clean_ai_generated_code(self, code: str) -> str:
        """清理AI生成的代码"""
        # 移除可能的markdown代码块标记
        code = code.replace('```java', '').replace('```vue', '').replace('```javascript', '').replace('```', '')
        
        # 移除开头和结尾的空行
        code = code.strip()
        
        return code
    
    def _normalize_name_for_java(self, name: str) -> str:
        """
        规范化名称为Java类名格式（UpperCamelCase）
        将中文、特殊字符转换为英文Java标识符
        """
        if not name:
            return 'Unknown'
        
        # 移除版本号信息
        normalized_name = re.sub(r'[Vv]\d+(\.\d+)*', '', name).strip()
        
        # 常见中文到英文的映射（按长度排序，先处理长的词组）
        chinese_to_english = [
            ('需求文档', 'Requirements'),
            ('设计文档', 'Design'),
            ('一局对接', 'BusinessIntegration'),
            ('链数优化', 'ChainOptimization'),
            ('优化记录', 'OptimizationRecord'),
            ('用户管理', 'UserManagement'),
            ('购物车', 'ShoppingCart'),
            ('用户', 'Users'),
            ('管理', 'Management'),
            ('系统', 'System'),
            ('平台', 'Platform'),
            ('项目', 'Project'),
            ('应用', 'Application'),
            ('服务', 'Service'),
            ('模块', 'Module'),
            ('组件', 'Component'),
            ('业务', 'Business'),
            ('数据', 'Data'),
            ('分析', 'Analysis'),
            ('监控', 'Monitor'),
            ('报告', 'Report'),
            ('统计', 'Statistics'),
            ('查询', 'Query'),
            ('搜索', 'Search'),
            ('导入', 'Import'),
            ('导出', 'Export'),
            ('配置', 'Config'),
            ('设置', 'Settings'),
            ('订单', 'Orders'),
            ('产品', 'Products'),
            ('商品', 'Products'),
            ('库存', 'Inventory'),
            ('支付', 'Payment'),
            ('地址', 'Address'),
            ('评论', 'Comments'),
            ('评价', 'Reviews'),
            ('分类', 'Categories'),
            ('标签', 'Tags'),
            ('权限', 'Permissions'),
            ('角色', 'Roles'),
            ('菜单', 'Menus'),
            ('日志', 'Logs'),
            ('文件', 'Files'),
            ('图片', 'Images'),
            ('文档', 'Documents'),
            ('消息', 'Messages'),
            ('通知', 'Notifications'),
            ('邮件', 'Emails'),
            ('优化', 'Optimization')
        ]
        
        # 按顺序进行中文替换（先长词组，后短词）
        for chinese, english in chinese_to_english:
            normalized_name = normalized_name.replace(chinese, f' {english} ')
        
        # 将特殊字符替换为空格
        normalized_name = re.sub(r'[^\w\s]', ' ', normalized_name)
        
        # 移除剩余的中文字符
        normalized_name = re.sub(r'[\u4e00-\u9fff]', ' ', normalized_name)
        
        # 分割单词并清理空字符串
        words = [word.strip() for word in re.split(r'[\s_\-]+', normalized_name) if word.strip()]
        
        if not words:
            return 'Unknown'
        
        # 转换为UpperCamelCase，但保持已经是CamelCase格式的单词不变
        camel_case_parts = []
        for word in words:
            # 检查是否已经是CamelCase格式（首字母大写，包含其他大写字母）
            if word[0].isupper() and any(c.isupper() for c in word[1:]):
                # 已经是CamelCase格式，保持不变
                camel_case_parts.append(word)
            else:
                # 转换为首字母大写
                camel_case_parts.append(word.capitalize())
        
        camel_case_name = ''.join(camel_case_parts)
        
        # 确保以字母开头
        if camel_case_name and camel_case_name[0].isdigit():
            camel_case_name = 'Class' + camel_case_name
        
        return camel_case_name if camel_case_name else 'Unknown'

    def _generate_app_vue_with_ai(self, design_data: Dict[str, Any]) -> str:
        """使用AI生成App.vue"""
        prompt = f"""
生成一个Vue 2的主应用组件App.vue，要求：

1. 作为整个应用的根组件
2. 包含导航栏/菜单
3. 包含路由视图(<router-view/>)
4. 使用Element UI布局组件
5. 包含用户认证状态管理
6. 响应式设计
7. 包含全局样式

项目页面:
{json.dumps(design_data.get('pages', []), ensure_ascii=False)}

项目信息:
{json.dumps(design_data.get('project_info', {}), ensure_ascii=False)}

请生成完整的App.vue代码。
"""
        
        context = f"项目信息: {design_data.get('project_info', {})}"
        app_code = self._call_ai_for_code_generation(prompt, context)
        return self._clean_ai_generated_code(app_code)

    def _generate_router_config_with_ai(self, design_data: Dict[str, Any], project_path: str) -> List[str]:
        """使用AI生成路由配置文件"""
        files = []
        
        try:
            prompt = f"""
生成一个Vue 2路由配置文件，要求：

1. 文件名: router/index.js
2. 使用Vue Router 3.x语法
3. 配置以下页面路由:

{json.dumps(design_data.get('pages', []), ensure_ascii=False, indent=2)}

要求:
- 包含路由懒加载
- 设置路由元信息(meta)
- 包含导航守卫
- 添加404页面处理
- 包含权限验证逻辑

请生成完整的路由配置代码。
"""
            
            context = f"项目信息: {design_data.get('project_info', {})}"
            router_code = self._call_ai_for_code_generation(prompt, context)
            router_code = self._clean_ai_generated_code(router_code)
            
            router_path = os.path.join(project_path, "frontend/src/router/index.js")
            self._write_file(router_path, router_code)
            files.append(router_path)
            
            logger.info("生成路由配置文件")
            
        except Exception as e:
            logger.error(f"生成路由配置失败: {e}")
        
        return files
    
    def _generate_api_files_with_ai(self, design_data: Dict[str, Any], project_path: str) -> List[str]:
        """使用AI生成API接口文件"""
        files = []
        
        try:
            # 生成通用的API配置
            api_config_prompt = """
生成一个Vue 2项目的API请求配置文件，要求：

1. 文件名: utils/request.js
2. 使用axios库
3. 包含请求和响应拦截器
4. 包含错误处理
5. 包含token自动添加
6. 包含loading状态管理
7. 包含请求超时配置

请生成完整的API配置代码。
"""
            
            api_config_code = self._call_ai_for_code_generation(api_config_prompt)
            api_config_code = self._clean_ai_generated_code(api_config_code)
            
            api_config_path = os.path.join(project_path, "frontend/src/utils/request.js")
            self._write_file(api_config_path, api_config_code)
            files.append(api_config_path)
            
            # 生成具体的API文件
            user_api_prompt = f"""
生成一个用户相关的API接口文件，要求：

1. 文件名: api/user.js
2. 使用上面的request.js作为基础
3. 实现以下API接口:

{json.dumps(design_data.get('api_endpoints', []), ensure_ascii=False, indent=2)}

要求:
- 使用async/await语法
- 包含参数验证
- 返回Promise
- 包含JSDoc注释

请生成完整的API接口代码。
"""
            
            context = f"项目信息: {design_data.get('project_info', {})}"
            user_api_code = self._call_ai_for_code_generation(user_api_prompt, context)
            user_api_code = self._clean_ai_generated_code(user_api_code)
            
            user_api_path = os.path.join(project_path, "frontend/src/api/user.js")
            self._write_file(user_api_path, user_api_code)
            files.append(user_api_path)
            
            logger.info("生成API接口文件")
            
        except Exception as e:
            logger.error(f"生成API接口文件失败: {e}")
        
        return files

    def _generate_main_application(self, design_data: Dict[str, Any], project_path: str) -> List[str]:
        """使用AI生成Spring Boot主应用类"""
        files = []
        
        try:
            project_name = design_data.get('project_info', {}).get('name', 'UserManagementSystem')
            package_prefix = self._get_package_prefix(design_data)
            
            # 使用规范化方法生成Java类名（大驼峰命名法）
            normalized_project_name = self._normalize_name_for_java(project_name)
            
            prompt = f"""
生成一个Spring Boot主应用类，要求：

1. 类名: {normalized_project_name}Application
2. 包名: {package_prefix}
3. 使用@SpringBootApplication注解
4. 包含main方法
5. 包含Swagger配置
6. 包含CORS配置
7. 包含数据库连接池配置
8. 添加应用启动日志

项目信息:
{json.dumps(design_data.get('project_info', {}), ensure_ascii=False)}

请生成完整的Spring Boot主应用类代码。
"""
            
            context = f"项目信息: {design_data.get('project_info', {})}"
            main_app_code = self._call_ai_for_code_generation(prompt, context)
            main_app_code = self._clean_ai_generated_code(main_app_code)
            
            main_app_path = os.path.join(
                project_path, 
                f"src/main/java/{package_prefix.replace('.', '/')}/{normalized_project_name}Application.java"
            )
            
            self._write_file(main_app_path, main_app_code)
            files.append(main_app_path)
            
            logger.info(f"生成主应用类: {normalized_project_name}Application")
            
        except Exception as e:
            logger.error(f"生成主应用类失败: {e}")
        
        return files

    def _generate_backend_config(self, design_data: Dict[str, Any], project_path: str) -> List[str]:
        """生成后端配置文件"""
        files = []
        
        # 生成pom.xml
        pom_content = self._create_pom_xml(design_data)
        pom_path = os.path.join(project_path, "pom.xml")
        self._write_file(pom_path, pom_content)
        files.append(pom_path)
        
        # 生成application.properties
        app_props_content = self._create_application_properties(design_data)
        app_props_path = os.path.join(project_path, "src/main/resources/application.properties")
        self._write_file(app_props_path, app_props_content)
        files.append(app_props_path)
        
        return files
    
    def _create_pom_xml(self, design_data: Dict[str, Any]) -> str:
        """创建pom.xml内容"""
        project_name = design_data.get('project_info', {}).get('name', 'example-project')
        package_prefix = self._get_package_prefix(design_data)
        
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    
    <groupId>{package_prefix}</groupId>
    <artifactId>{project_name.lower().replace(' ', '-')}</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>
    
    <name>{project_name}</name>
    <description>Generated project by CoderAgent</description>
    
    <properties>
        <java.version>8</java.version>
        <spring-boot.version>2.7.14</spring-boot.version>
        <maven.compiler.source>8</maven.compiler.source>
        <maven.compiler.target>8</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    </properties>
    
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>2.7.14</version>
        <relativePath/>
    </parent>
    
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
        
        <dependency>
            <groupId>org.mybatis.spring.boot</groupId>
            <artifactId>mybatis-spring-boot-starter</artifactId>
            <version>2.3.1</version>
        </dependency>
        
        <dependency>
            <groupId>mysql</groupId>
            <artifactId>mysql-connector-java</artifactId>
            <scope>runtime</scope>
        </dependency>
        
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
        
        <dependency>
            <groupId>io.springfox</groupId>
            <artifactId>springfox-swagger2</artifactId>
            <version>3.0.0</version>
        </dependency>
        
        <dependency>
            <groupId>io.springfox</groupId>
            <artifactId>springfox-swagger-ui</artifactId>
            <version>3.0.0</version>
        </dependency>
    </dependencies>
    
    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>"""
    
    def _create_application_properties(self, design_data: Dict[str, Any]) -> str:
        """创建application.properties内容"""
        package_prefix = self._get_package_prefix(design_data)
        return f"""# Application Configuration
spring.application.name={design_data.get('project_info', {}).get('name', 'example-app')}
server.port=8080

# Database Configuration
spring.datasource.url=jdbc:mysql://localhost:3306/example_db?useSSL=false&serverTimezone=UTC
spring.datasource.username=root
spring.datasource.password=password
spring.datasource.driver-class-name=com.mysql.cj.jdbc.Driver

# JPA Configuration
spring.jpa.hibernate.ddl-auto=update
spring.jpa.show-sql=true
spring.jpa.properties.hibernate.dialect=org.hibernate.dialect.MySQL8Dialect

# MyBatis Configuration
mybatis.mapper-locations=classpath:mapper/*.xml
mybatis.type-aliases-package={package_prefix}.entity

# Swagger Configuration
spring.mvc.pathmatch.matching-strategy=ant_path_matcher

# Logging Configuration
logging.level.{package_prefix}=DEBUG
logging.pattern.console=%d{{yyyy-MM-dd HH:mm:ss}} - %msg%n

# Generated by CoderAgent at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
    
    def _write_file(self, file_path: str, content: str):
        """写入文件"""
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.debug(f"生成文件: {file_path}")
    
    # 其他辅助方法（简化实现）
    def _create_entity_class(self, table: Dict[str, str], design_data: Dict[str, Any]) -> str:
        """创建实体类（简化版本）"""
        entity_name = table.get('name', 'Unknown').capitalize()
        return f"""package {self._get_package_path(design_data, 'entity')};

import javax.persistence.*;
import java.time.LocalDateTime;

/**
 * {entity_name} Entity
 * Generated by CoderAgent
 */
@Entity
@Table(name = "{table.get('name', 'unknown')}")
public class {entity_name} {{
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(name = "created_at")
    private LocalDateTime createdAt;
    
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
    
    // Getters and Setters
    public Long getId() {{
        return id;
    }}
    
    public void setId(Long id) {{
        this.id = id;
    }}
    
    public LocalDateTime getCreatedAt() {{
        return createdAt;
    }}
    
    public void setCreatedAt(LocalDateTime createdAt) {{
        this.createdAt = createdAt;
    }}
    
    public LocalDateTime getUpdatedAt() {{
        return updatedAt;
    }}
    
    public void setUpdatedAt(LocalDateTime updatedAt) {{
        this.updatedAt = updatedAt;
    }}
}}"""
    
    def _create_repository_interface(self, table: Dict[str, str], design_data: Dict[str, Any]) -> str:
        """创建Repository接口"""
        entity_name = table.get('name', 'Unknown').capitalize()
        package_prefix = self._get_package_prefix(design_data)
        return f"""package {package_prefix}.repository;

import {package_prefix}.entity.{entity_name};
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

/**
 * {entity_name} Repository
 * Generated by CoderAgent
 */
@Repository
public interface {entity_name}Repository extends JpaRepository<{entity_name}, Long> {{
    
}}"""
    
    def _create_service_class(self, module: Dict[str, str], design_data: Dict[str, Any]) -> str:
        """创建Service类"""
        module_name = module.get('module', 'Unknown').replace('功能', '').replace('模块', '').strip()
        package_prefix = self._get_package_prefix(design_data)
        return f"""package {package_prefix}.service;

import org.springframework.stereotype.Service;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * {module_name} Service
 * {module.get('description', '业务逻辑处理')}
 * Generated by CoderAgent
 */
@Service
public class {module_name}Service {{
    
    private static final Logger logger = LoggerFactory.getLogger({module_name}Service.class);
    
    // TODO: Implement business logic for {module_name}
    
}}"""
    
    def _create_controller_class(self, controller_name: str, apis: List[Dict[str, str]], design_data: Dict[str, Any]) -> str:
        """创建Controller类"""
        package_prefix = self._get_package_prefix(design_data)
        return f"""package {package_prefix}.controller;

import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * {controller_name} Controller
 * Generated by CoderAgent
 */
@RestController
@RequestMapping("/{controller_name.lower()}")
public class {controller_name}Controller {{
    
    private static final Logger logger = LoggerFactory.getLogger({controller_name}Controller.class);
    
    // TODO: Implement API endpoints
    
}}"""
    
    def _create_package_json(self, design_data: Dict[str, Any]) -> str:
        """创建package.json内容"""
        project_name = design_data.get('project_info', {}).get('name', 'example-project')
        return json.dumps({
            "name": project_name.lower().replace(' ', '-'),
            "version": "1.0.0",
            "description": "Generated by CoderAgent",
            "scripts": {
                "dev": "webpack-dev-server --inline --progress --config build/webpack.dev.conf.js",
                "start": "npm run dev",
                "build": "node build/build.js"
            },
            "dependencies": {
                "vue": "^2.6.14",
                "vue-router": "^3.2.0",
                "axios": "^0.27.2",
                "element-ui": "^2.15.9"
            },
            "devDependencies": {
                "webpack": "^4.46.0",
                "webpack-dev-server": "^3.11.3",
                "vue-loader": "^15.9.8",
                "vue-template-compiler": "^2.6.14"
            }
        }, indent=2)
    
    def _create_index_html(self, design_data: Dict[str, Any]) -> str:
        """创建index.html"""
        project_name = design_data.get('project_info', {}).get('name', 'Example Project')
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1.0">
    <title>{project_name}</title>
</head>
<body>
    <div id="app"></div>
    <!-- built files will be auto injected -->
</body>
</html>"""
    
    def _create_main_js(self, design_data: Dict[str, Any]) -> str:
        """创建main.js"""
        return """import Vue from 'vue'
import App from './App'
import router from './router'
import ElementUI from 'element-ui'
import 'element-ui/lib/theme-chalk/index.css'

Vue.config.productionTip = false
Vue.use(ElementUI)

/* eslint-disable no-new */
new Vue({
  el: '#app',
  router,
  components: { App },
  template: '<App/>'
})"""
    
    def _get_package_prefix(self, design_data: Dict[str, Any]) -> str:
        """获取包名前缀"""
        return design_data.get('project_info', {}).get('package_prefix', 'com')
    
    def _get_package_path(self, design_data: Dict[str, Any], sub_package: str = None) -> str:
        """获取包路径"""
        package_prefix = self._get_package_prefix(design_data)
        if sub_package:
            return f"{package_prefix}/{sub_package}"
        return package_prefix 