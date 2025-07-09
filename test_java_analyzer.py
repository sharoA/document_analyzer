#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Java代码分析器 - 企业级架构分析
"""

import sys
import os
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from src.utils.java_code_analyzer import JavaCodeAnalyzer

def test_java_analyzer():
    """测试Java代码分析器"""
    print("🚀 开始测试Java代码分析器...")
    
    # 初始化分析器
    analyzer = JavaCodeAnalyzer()
    
    # 真实CRCL项目路径 - 企业级微服务项目测试用例
    test_project_path = r"D:\gitlab\create_project\链数中建一局_1751963474\crcl-open"
    
    # 检查路径是否存在
    if not Path(test_project_path).exists():
        print(f"❌ 测试项目路径不存在: {test_project_path}")
        print("💡 让我们创建一个模拟的Java项目结构进行测试...")
        
        # 创建模拟项目结构
        create_mock_java_project()
        test_project_path = "mock_java_project"
    
    try:
        # 执行分析
        print(f"🔍 分析项目: {test_project_path}")
        analysis_result = analyzer.analyze_project(test_project_path, "crcl-open")
        
        # 输出关键信息
        print("\n📊 分析结果摘要:")
        summary = analysis_result.get('summary', {})
        
        print(f"- Java文件数量: {summary.get('total_java_files', 0)}")
        print(f"- 架构类型: {summary.get('architecture_type', 'Unknown')}")
        print(f"- Spring Boot: {'✅' if summary.get('is_spring_boot') else '❌'}")
        print(f"- MyBatis Plus: {'✅' if summary.get('is_mybatis_plus') else '❌'}")
        print(f"- DTO使用率: {summary.get('dto_usage_rate', 0)}%")
        print(f"- 包命名规范度: {summary.get('package_compliance', 0)}%")
        print(f"- 可维护性指数: {summary.get('maintainability_index', 0)}/100")
        
        # 显示业务域
        business_domains = summary.get('business_domains', [])
        if business_domains:
            print(f"- 业务域: {', '.join(business_domains)}")
        
        # 显示分层结构
        print("\n🏗️ 分层结构:")
        layer_analysis = analysis_result.get('layer_analysis', {})
        for layer, files in layer_analysis.items():
            if files:
                print(f"  - {layer}: {len(files)}个文件")
        
        # 显示组件分布
        print("\n🔧 组件分布:")
        components = analysis_result.get('components_detected', {})
        for component, count in components.items():
            if count > 0:
                print(f"  - {component}: {count}个")
        
        # 导出报告
        print("\n📄 导出分析报告...")
        report_path = analyzer.export_analysis_report(analysis_result)
        print(f"✅ 报告已生成: {report_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def create_mock_java_project():
    """创建模拟的Java项目结构用于测试"""
    print("🏗️ 创建模拟Java项目结构...")
    
    mock_project = Path("mock_java_project")
    mock_project.mkdir(exist_ok=True)
    
    # 创建标准的企业级项目结构
    java_files = [
        # Interfaces层
        ("src/main/java/com/yljr/crcl/user/interfaces/facade/UserController.java", """
package com.yljr.crcl.user.interfaces.facade;

import org.springframework.web.bind.annotation.*;
import org.springframework.beans.factory.annotation.Autowired;
import com.yljr.crcl.user.application.service.UserService;
import com.yljr.crcl.user.interfaces.dto.UserRequest;
import com.yljr.crcl.user.interfaces.dto.UserResponse;

@RestController
@RequestMapping("/api/users")
public class UserController {
    
    @Autowired
    private UserService userService;
    
    @PostMapping
    public UserResponse createUser(@RequestBody UserRequest request) {
        return userService.createUser(request);
    }
    
    @GetMapping("/{id}")
    public UserResponse getUser(@PathVariable Long id) {
        return userService.getUserById(id);
    }
}
"""),
        
        # Application层
        ("src/main/java/com/yljr/crcl/user/application/service/UserService.java", """
package com.yljr.crcl.user.application.service;

import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Autowired;
import com.yljr.crcl.user.domain.entity.User;
import com.yljr.crcl.user.domain.mapper.UserMapper;
import com.yljr.crcl.user.interfaces.dto.UserRequest;
import com.yljr.crcl.user.interfaces.dto.UserResponse;

@Service
public class UserService {
    
    @Autowired
    private UserMapper userMapper;
    
    public UserResponse createUser(UserRequest request) {
        User user = new User();
        user.setName(request.getName());
        userMapper.insert(user);
        
        UserResponse response = new UserResponse();
        response.setId(user.getId());
        response.setName(user.getName());
        return response;
    }
    
    public UserResponse getUserById(Long id) {
        User user = userMapper.selectById(id);
        UserResponse response = new UserResponse();
        response.setId(user.getId());
        response.setName(user.getName());
        return response;
    }
}
"""),
        
        # Domain层
        ("src/main/java/com/yljr/crcl/user/domain/entity/User.java", """
package com.yljr.crcl.user.domain.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.baomidou.mybatisplus.annotation.IdType;

@TableName("t_user")
public class User {
    
    @TableId(type = IdType.AUTO)
    private Long id;
    
    private String name;
    
    private String email;
    
    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
}
"""),
        
        ("src/main/java/com/yljr/crcl/user/domain/mapper/UserMapper.java", """
package com.yljr.crcl.user.domain.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;
import com.yljr.crcl.user.domain.entity.User;

@Mapper
public interface UserMapper extends BaseMapper<User> {
    // 自定义查询方法可以在这里添加
}
"""),
        
        # DTO层
        ("src/main/java/com/yljr/crcl/user/interfaces/dto/UserRequest.java", """
package com.yljr.crcl.user.interfaces.dto;

import javax.validation.constraints.NotBlank;

public class UserRequest {
    
    @NotBlank
    private String name;
    
    private String email;
    
    // Getters and Setters
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
}
"""),
        
        ("src/main/java/com/yljr/crcl/user/interfaces/dto/UserResponse.java", """
package com.yljr.crcl.user.interfaces.dto;

public class UserResponse {
    
    private Long id;
    private String name;
    private String email;
    
    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
}
"""),
        
        # Feign Client
        ("src/main/java/com/yljr/crcl/user/application/feign/CompanyFeignClient.java", """
package com.yljr.crcl.user.application.feign;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

@FeignClient(name = "company-service", url = "${feign.company.url}")
public interface CompanyFeignClient {
    
    @GetMapping("/api/companies/{id}")
    CompanyDto getCompanyById(@PathVariable("id") Long id);
}
"""),
        
        # 启动类
        ("src/main/java/com/yljr/crcl/user/UserApplication.java", """
package com.yljr.crcl.user;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.openfeign.EnableFeignClients;

@SpringBootApplication
@EnableFeignClients
public class UserApplication {
    public static void main(String[] args) {
        SpringApplication.run(UserApplication.class, args);
    }
}
""")
    ]
    
    # 创建文件
    for file_path, content in java_files:
        full_path = mock_project / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding='utf-8')
    
    print(f"✅ 模拟项目创建完成: {mock_project}")

def test_analyzer_methods():
    """测试分析器的具体方法"""
    print("\n🧪 测试分析器的具体方法...")
    
    analyzer = JavaCodeAnalyzer()
    
    # 测试企业模式识别
    print("1. 测试企业模式识别:")
    print(f"   - CRCL包模式: {analyzer.enterprise_patterns['crcl_package']}")
    print(f"   - DTO模式: {analyzer.enterprise_patterns['dto_patterns']}")
    print(f"   - 分层标记: {analyzer.enterprise_patterns['layer_markers']}")
    
    # 测试分层模式
    print("2. 测试分层模式:")
    for layer, patterns in analyzer.layer_patterns.items():
        print(f"   - {layer}: {patterns}")
    
    # 测试命名模式
    print("3. 测试命名模式:")
    for pattern, regex in analyzer.naming_patterns.items():
        print(f"   - {pattern}: {regex}")
    
    print("✅ 方法测试完成")

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Java代码分析器测试")
    print("=" * 60)
    
    # 测试分析器方法
    test_analyzer_methods()
    
    # 测试完整分析流程
    success = test_java_analyzer()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 测试成功完成！")
    else:
        print("❌ 测试失败！")
    print("=" * 60) 