"""
传统代码生成器
提供基于模板的Spring Boot微服务代码生成
"""

import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class TraditionalCodeGenerator:
    """传统模板代码生成器"""
    
    def generate_project(
        self,
        document_content: str,
        project_name: str,
        output_path: str,
        services: List[str] = None
    ) -> bool:
        """
        生成项目代码
        
        Args:
            document_content: 文档内容
            project_name: 项目名称
            output_path: 输出路径
            services: 服务列表（可选）
            
        Returns:
            是否成功
        """
        try:
            logger.info(f"传统代码生成器开始工作: {project_name} -> {output_path}")
            
            # 创建输出目录
            full_output_path = os.path.join(output_path, project_name)
            os.makedirs(full_output_path, exist_ok=True)
            
            # 如果没有提供服务列表，则自动识别
            if services is None:
                services = self._identify_services(document_content)
            
            # 为每个服务生成基础代码结构
            for service_name in services:
                service_path = os.path.join(full_output_path, service_name)
                self._generate_service_structure(service_name, service_path, document_content)
            
            logger.info(f"传统代码生成完成: {len(services)}个服务")
            return True
            
        except Exception as e:
            logger.error(f"传统代码生成失败: {e}")
            return False
    
    def _identify_services(self, document_content: str) -> List[str]:
        """从文档中识别微服务"""
        services = []
        
        # 基于关键词识别服务
        if "用户" in document_content or "登录" in document_content or "注册" in document_content:
            services.append("user-service")
        
        if "额度" in document_content or "确权" in document_content or "开立" in document_content:
            services.append("quota-service")
        
        if "数据同步" in document_content or "同步" in document_content:
            services.append("sync-service")
        
        if "监控" in document_content or "告警" in document_content:
            services.append("monitor-service")
        
        # 如果没有识别到服务，创建默认服务
        if not services:
            services = ["main-service"]
        
        return services
    
    def _generate_service_structure(self, service_name: str, service_path: str, document_content: str):
        """生成基础的Spring Boot服务结构"""
        
        # 创建目录结构
        dirs = [
            "src/main/java/com/example/service",
            "src/main/java/com/example/controller", 
            "src/main/java/com/example/entity",
            "src/main/java/com/example/mapper",
            "src/main/java/com/example/service/impl",
            "src/main/resources",
            "src/test/java/com/example"
        ]
        
        for dir_path in dirs:
            os.makedirs(os.path.join(service_path, dir_path), exist_ok=True)
        
        # 生成主要文件
        self._generate_application_main(service_name, service_path)
        self._generate_controller(service_name, service_path, document_content)
        self._generate_service_class(service_name, service_path)
        self._generate_entity(service_name, service_path)
        self._generate_application_yml(service_name, service_path)
        self._generate_pom_xml(service_name, service_path)
    
    def _generate_application_main(self, service_name: str, service_path: str):
        """生成Spring Boot主启动类"""
        class_name = ''.join(word.capitalize() for word in service_name.replace('-', '_').split('_'))
        
        content = f"""package com.example;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.mybatis.spring.annotation.MapperScan;

@SpringBootApplication
@MapperScan("com.example.mapper")
public class {class_name}Application {{

    public static void main(String[] args) {{
        SpringApplication.run({class_name}Application.class, args);
    }}
}}
"""
        
        file_path = os.path.join(service_path, f"src/main/java/com/example/{class_name}Application.java")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _generate_controller(self, service_name: str, service_path: str, document_content: str):
        """生成Controller类"""
        class_name = ''.join(word.capitalize() for word in service_name.replace('-', '_').split('_'))
        
        content = f"""package com.example.controller;

import org.springframework.web.bind.annotation.*;
import org.springframework.beans.factory.annotation.Autowired;
import com.example.service.{class_name}Service;
import java.util.Map;
import java.util.HashMap;

@RestController
@RequestMapping("/api/{service_name.replace('_', '-')}")
public class {class_name}Controller {{

    @Autowired
    private {class_name}Service {service_name.replace('-', '')}Service;

    @GetMapping("/health")
    public Map<String, Object> health() {{
        Map<String, Object> result = new HashMap<>();
        result.put("status", "healthy");
        result.put("service", "{service_name}");
        result.put("timestamp", System.currentTimeMillis());
        return result;
    }}

    @GetMapping("/info")
    public Map<String, Object> getInfo() {{
        return {service_name.replace('-', '')}Service.getServiceInfo();
    }}

    @PostMapping("/process")
    public Map<String, Object> processRequest(@RequestBody Map<String, Object> request) {{
        return {service_name.replace('-', '')}Service.processRequest(request);
    }}
}}
"""
        
        file_path = os.path.join(service_path, f"src/main/java/com/example/controller/{class_name}Controller.java")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _generate_service_class(self, service_name: str, service_path: str):
        """生成Service接口和实现类"""
        class_name = ''.join(word.capitalize() for word in service_name.replace('-', '_').split('_'))
        
        # Service接口
        interface_content = f"""package com.example.service;

import java.util.Map;

public interface {class_name}Service {{

    Map<String, Object> getServiceInfo();
    
    Map<String, Object> processRequest(Map<String, Object> request);
}}
"""
        
        interface_path = os.path.join(service_path, f"src/main/java/com/example/service/{class_name}Service.java")
        with open(interface_path, 'w', encoding='utf-8') as f:
            f.write(interface_content)

        # Service实现类
        impl_content = f"""package com.example.service.impl;

import com.example.service.{class_name}Service;
import org.springframework.stereotype.Service;
import java.util.Map;
import java.util.HashMap;

@Service
public class {class_name}ServiceImpl implements {class_name}Service {{

    @Override
    public Map<String, Object> getServiceInfo() {{
        Map<String, Object> info = new HashMap<>();
        info.put("serviceName", "{service_name}");
        info.put("version", "1.0.0");
        info.put("description", "Generated by AI Coder Agent");
        info.put("timestamp", System.currentTimeMillis());
        return info;
    }}

    @Override
    public Map<String, Object> processRequest(Map<String, Object> request) {{
        Map<String, Object> response = new HashMap<>();
        response.put("status", "success");
        response.put("service", "{service_name}");
        response.put("processedAt", System.currentTimeMillis());
        response.put("requestData", request);
        return response;
    }}
}}
"""
        
        impl_path = os.path.join(service_path, f"src/main/java/com/example/service/impl/{class_name}ServiceImpl.java")
        with open(impl_path, 'w', encoding='utf-8') as f:
            f.write(impl_content)
    
    def _generate_entity(self, service_name: str, service_path: str):
        """生成实体类"""
        class_name = ''.join(word.capitalize() for word in service_name.replace('-', '_').split('_'))
        
        content = f"""package com.example.entity;

import java.time.LocalDateTime;

public class {class_name}Entity {{

    private Long id;
    private String name;
    private String status;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    // Constructors
    public {class_name}Entity() {{}}

    public {class_name}Entity(String name, String status) {{
        this.name = name;
        this.status = status;
        this.createdAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }}

    // Getters and Setters
    public Long getId() {{ return id; }}
    public void setId(Long id) {{ this.id = id; }}

    public String getName() {{ return name; }}
    public void setName(String name) {{ this.name = name; }}

    public String getStatus() {{ return status; }}
    public void setStatus(String status) {{ this.status = status; }}

    public LocalDateTime getCreatedAt() {{ return createdAt; }}
    public void setCreatedAt(LocalDateTime createdAt) {{ this.createdAt = createdAt; }}

    public LocalDateTime getUpdatedAt() {{ return updatedAt; }}
    public void setUpdatedAt(LocalDateTime updatedAt) {{ this.updatedAt = updatedAt; }}
}}
"""
        
        file_path = os.path.join(service_path, f"src/main/java/com/example/entity/{class_name}Entity.java")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _generate_application_yml(self, service_name: str, service_path: str):
        """生成application.yml配置文件"""
        port = 8080
        if "user" in service_name:
            port = 8081
        elif "quota" in service_name or "sync" in service_name:
            port = 8082
        elif "monitor" in service_name:
            port = 8083
        
        content = f"""server:
  port: {port}

spring:
  application:
    name: {service_name}
  datasource:
    driver-class-name: com.mysql.cj.jdbc.Driver
    url: jdbc:mysql://localhost:3306/{service_name.replace('-', '_')}?useUnicode=true&characterEncoding=UTF-8&serverTimezone=Asia/Shanghai
    username: root
    password: password
  jpa:
    hibernate:
      ddl-auto: update
    show-sql: true

mybatis-plus:
  mapper-locations: classpath:mapper/*.xml
  configuration:
    log-impl: org.apache.ibatis.logging.stdout.StdOutImpl

logging:
  level:
    com.example: debug
  pattern:
    console: "%d{{yyyy-MM-dd HH:mm:ss}} [%thread] %-5level %logger{{36}} - %msg%n"
"""
        
        file_path = os.path.join(service_path, "src/main/resources/application.yml")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _generate_pom_xml(self, service_name: str, service_path: str):
        """生成pom.xml文件"""
        artifact_id = service_name.replace('_', '-')
        
        content = f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.example</groupId>
    <artifactId>{artifact_id}</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>

    <name>{artifact_id}</name>
    <description>Generated by AI Coder Agent</description>

    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>2.7.14</version>
        <relativePath/>
    </parent>

    <properties>
        <java.version>11</java.version>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
        <mybatis-plus.version>3.5.3.1</mybatis-plus.version>
    </properties>

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
            <groupId>com.baomidou</groupId>
            <artifactId>mybatis-plus-boot-starter</artifactId>
            <version>${{mybatis-plus.version}}</version>
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
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-actuator</artifactId>
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
</project>
"""
        
        file_path = os.path.join(service_path, "pom.xml")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content) 