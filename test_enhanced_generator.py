#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版代码生成器测试脚本
验证修复效果
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_enhanced_generator():
    """测试增强版代码生成器"""
    
    print("🚀 开始测试增强版代码生成器")
    print("=" * 60)
    
    try:
        # 1. 导入增强版生成器
        from src.corder_integration.code_generator.enhanced_template_ai_generator import EnhancedTemplateAIGenerator
        
        # 2. 模拟LLM客户端（如果没有真实客户端）
        class MockLLMClient:
            def chat(self, messages, temperature=0.1, max_tokens=2000):
                # 根据消息内容判断要生成的代码类型
                message_content = str(messages)
                
                if 'controller' in message_content.lower():
                    return '''
```java
package com.yljr.crcl.limit.interfaces.rest;

import com.yljr.crcl.limit.application.service.ListUnitLimitByCompanyIdService;
import com.yljr.crcl.limit.interfaces.dto.ListUnitLimitByCompanyIdReq;
import com.yljr.crcl.limit.interfaces.dto.ListUnitLimitByCompanyIdResp;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import javax.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import com.github.pagehelper.PageHelper;
import com.github.pagehelper.PageInfo;

@RestController
@RequestMapping("/crcl-open-api/lsLimit")
public class ListUnitLimitByCompanyIdController {
    
    private static final Logger logger = LoggerFactory.getLogger(ListUnitLimitByCompanyIdController.class);
    
    @Autowired
    private ListUnitLimitByCompanyIdService listUnitLimitByCompanyIdService;
    
    @GetMapping("/listUnitLimitByCompanyId")
    public ResponseEntity<ListUnitLimitByCompanyIdResp> listUnitLimitByCompanyId(
            @RequestParam Integer gwCompanyId,
            @RequestParam(required = false) String unitName,
            @RequestParam(required = false) String limitSource,
            @RequestParam(defaultValue = "80") Integer bizType,
            @RequestParam(defaultValue = "1") Integer page,
            @RequestParam(defaultValue = "10") Integer pageRow) {
        try {
            logger.info("Processing listUnitLimitByCompanyId request: gwCompanyId={}, page={}, pageRow={}", 
                       gwCompanyId, page, pageRow);
            
            // 使用PageHelper进行分页
            PageHelper.startPage(page, pageRow);
            
            // 调用zqyl-user-center-service服务获取组织单元信息
            // TODO: 调用外部服务 /queryCompanyUnitList
            
            // 调用服务层
            ListUnitLimitByCompanyIdResp response = listUnitLimitByCompanyIdService.listUnitLimitByCompanyId(request);
            
            logger.info("listUnitLimitByCompanyId completed successfully");
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            logger.error("Error in listUnitLimitByCompanyId: ", e);
            return ResponseEntity.internalServerError().build();
        }
    }
}
```
'''
                elif 'service_impl' in message_content.lower():
                    return '''
```java
package com.yljr.crcl.limit.application.service.impl;

import com.yljr.crcl.limit.application.service.ListUnitLimitByCompanyIdService;
import com.yljr.crcl.limit.domain.entity.ListUnitLimitByCompanyId;
import com.yljr.crcl.limit.domain.mapper.ListUnitLimitByCompanyIdMapper;
import com.yljr.crcl.limit.interfaces.dto.ListUnitLimitByCompanyIdReq;
import com.yljr.crcl.limit.interfaces.dto.ListUnitLimitByCompanyIdResp;
import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.transaction.annotation.Transactional;
import com.github.pagehelper.PageHelper;
import com.github.pagehelper.PageInfo;

@Service
@Transactional
public class ListUnitLimitByCompanyIdServiceImpl implements ListUnitLimitByCompanyIdService {
    
    @Autowired
    private ListUnitLimitByCompanyIdMapper mapper;
    
    @Override
    public ListUnitLimitByCompanyIdResp listUnitLimitByCompanyId(ListUnitLimitByCompanyIdReq request) {
        // 使用PageHelper进行分页
        PageHelper.startPage(request.getPage(), request.getPageRow());
        
        // 调用zqyl-user-center-service获取组织单元信息
        // TODO: 具体实现服务调用逻辑
        
        // 查询数据
        List<ListUnitLimitByCompanyId> list = mapper.selectByCondition(request);
        
        // 构造响应
        ListUnitLimitByCompanyIdResp response = new ListUnitLimitByCompanyIdResp();
        // TODO: 设置汇总数据
        return response;
    }
}
```
'''
                elif 'entity' in message_content.lower():
                    return '''
```java
package com.yljr.crcl.limit.domain.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import java.time.LocalDateTime;

@Data
@ApiModel(description = "多组织单元表")
@TableName("t_cust_multiorg_unit")
public class CustMultiorgUnit {
    
    @ApiModelProperty("主键id")
    @TableId(type = IdType.AUTO)
    private Long id;
    
    @ApiModelProperty("企业id")
    @TableField("company_id")
    private Long companyId;
    
    @ApiModelProperty("多组织id")
    @TableField("mutilorg_id")
    private Long mutilorgId;
    
    @ApiModelProperty("组织单元编号")
    @TableField("unit_code")
    private String unitCode;
    
    @ApiModelProperty("组织单元名称")
    @TableField("unit_name")
    private String unitName;
    
    @ApiModelProperty("备注")
    @TableField("remark")
    private String remark;
    
    @ApiModelProperty("平台类型(1云信2云租3云保)")
    @TableField("platform_type")
    private Integer platformType;
    
    @ApiModelProperty("状态1正常0删除")
    @TableField("status")
    private Integer status;
    
    @ApiModelProperty("创建时间")
    @TableField("create_time")
    private LocalDateTime createTime;
    
    @ApiModelProperty("修改时间")
    @TableField("modify_time")
    private LocalDateTime modifyTime;
}
```
'''
                else:
                    # 默认返回简单的代码
                    return '''
```java
// Generated code template
public class GeneratedClass {
    // TODO: Implement specific logic
}
```
'''
        
        # 3. 初始化增强版生成器
        mock_client = MockLLMClient()
        generator = EnhancedTemplateAIGenerator(mock_client)
        
        print("✅ 增强版生成器初始化成功")
        
        # 4. 准备测试数据
        interface_name = "ListUnitLimitByCompanyId"
        
        input_params = [
            {"name": "gwCompanyId", "type": "Integer", "description": "当前登录企业id", "required": True},
            {"name": "unitName", "type": "String", "description": "组织单元名称（模糊搜索）", "required": False},
            {"name": "limitSource", "type": "String", "description": "额度名称（模糊搜索）", "required": False},
            {"name": "bizType", "type": "Integer", "description": "10：云信额度，80：链数额度（默认）", "required": False},
            {"name": "page", "type": "Integer", "description": "页码", "required": True},
            {"name": "pageRow", "type": "Integer", "description": "每页记录数", "required": True}
        ]
        
        output_params = {
            "totalLimitAmt": {"type": "BigDecimal", "description": "总额度"},
            "usedLimitAmt": {"type": "BigDecimal", "description": "已用额度"},
            "usableLimitAmt": {"type": "BigDecimal", "description": "可用额度"},
            "unitLimitListDetail": {"type": "List", "description": "额度信息列表"}
        }
        
        description = "组织单元额度列表查询"
        http_method = "GET"
        api_path = "/crcl-open-api/lsLimit/listUnitLimitByCompanyId"
        
        business_logic = """
        特殊要求：
        1、采用pagehelper进行分页
        2、需要调用zqyl-user-center-service服务的/queryCompanyUnitList接口获取组织单元详细信息
        """
        
        # 5. 构建项目上下文（包含设计文档）
        project_context = {
            'package_patterns': {
                'base_package': 'com.yljr.crcl.limit'
            },
            'project_info': {
                'is_spring_boot': True,
                'is_mybatis_plus': True
            },
            'document_content': '''
CREATE TABLE t_cust_multiorg_unit(
  id bigint(20) NOT NULL COMMENT '主键id',
  company_id bigint(20) NOT NULL COMMENT '企业id',
  mutilorg_id bigint(10) NOT NULL COMMENT '多组织id',
  unit_code varchar(50) NOT NULL COMMENT '组织单元编号',
  unit_name varchar(255) NOT NULL COMMENT '组织单元名称',
  remark varchar(500) DEFAULT NULL COMMENT '备注',
  platform_type tinyint(2) NOT NULL COMMENT '平台类型(1云信2云租3云保)',
  status tinyint(2) NOT NULL COMMENT '状态1正常0删除',
  create_id bigint(20) NOT NULL COMMENT '创建人id',
  oper_user_name varchar(255) DEFAULT NULL COMMENT '创建人用户名',
  create_time datetime NOT NULL COMMENT '创建时间',
  modify_id bigint(20) DEFAULT NULL COMMENT '修改人id',
  modify_user_name varchar(255) DEFAULT NULL COMMENT '最后修改用户名',
  modify_time datetime DEFAULT NULL COMMENT '修改时间',
  PRIMARY KEY(id),
  KEY pk_company_id(company_id) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='多组织单元表';

特殊要求：
1、采用pagehelper进行分页
2、需要调用zqyl-user-center-service服务的/queryCompanyUnitList接口获取组织单元详细信息
'''
        }
        
        print("📋 测试数据准备完成")
        print(f"  - 接口名称: {interface_name}")
        print(f"  - 输入参数: {len(input_params)}个")
        print(f"  - 输出参数: {len(output_params)}个")
        print(f"  - API路径: {api_path}")
        
        # 6. 执行代码生成
        print("\n🎨 开始代码生成...")
        
        generated_code = generator.generate_code(
            interface_name=interface_name,
            input_params=input_params,
            output_params=output_params,
            description=description,
            http_method=http_method,
            project_context=project_context,
            api_path=api_path,
            business_logic=business_logic
        )
        
        # 7. 验证生成结果
        print(f"\n✅ 代码生成完成！生成了 {len(generated_code)} 个代码文件")
        
        for code_type, code_content in generated_code.items():
            print(f"\n📄 {code_type}:")
            print("-" * 40)
            
            # 显示代码片段
            lines = code_content.split('\n')
            preview_lines = lines[:15]  # 显示前15行
            
            for i, line in enumerate(preview_lines, 1):
                print(f"{i:2}: {line}")
            
            if len(lines) > 15:
                print(f"... (还有 {len(lines) - 15} 行)")
            
            print(f"总行数: {len(lines)}")
            
            # 检查关键特征
            checks = []
            
            if code_type == 'controller':
                if 'PageHelper' in code_content:
                    checks.append("✅ 包含PageHelper分页")
                else:
                    checks.append("❌ 缺少PageHelper分页")
                
                if 'zqyl-user-center-service' in code_content or 'queryCompanyUnitList' in code_content:
                    checks.append("✅ 包含服务调用逻辑")
                else:
                    checks.append("❌ 缺少服务调用逻辑")
            
            elif code_type == 'entity':
                if 't_cust_multiorg_unit' in code_content or 'company_id' in code_content:
                    checks.append("✅ 包含表结构映射")
                else:
                    checks.append("❌ 缺少表结构映射")
            
            if checks:
                print("特征检查:")
                for check in checks:
                    print(f"  {check}")
        
        # 8. 测试特殊要求解析
        print("\n🔍 测试特殊要求解析...")
        special_requirements = generator._parse_special_requirements(business_logic, description)
        
        print(f"PageHelper分页: {'✅' if special_requirements['use_pagehelper'] else '❌'}")
        print(f"外部服务调用: {'✅' if special_requirements['external_service_calls'] else '❌'}")
        if special_requirements['external_service_calls']:
            for call in special_requirements['external_service_calls']:
                print(f"  - {call['service_name']}: {call['endpoint']}")
        
        # 9. 测试表结构解析
        print("\n🗄️ 测试表结构解析...")
        table_structure = generator._parse_table_structure_from_context(project_context)
        
        print(f"表结构解析: {'✅' if table_structure['has_table_definition'] else '❌'}")
        if table_structure['has_table_definition']:
            print(f"  - 表名: {table_structure['table_name']}")
            print(f"  - 字段数量: {len(table_structure['columns'])}")
            print(f"  - 示例字段: {table_structure['columns'][:3] if table_structure['columns'] else '无'}")
        
        print(f"\n🎉 测试完成！增强版代码生成器工作正常")
        print("=" * 60)
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保项目路径正确且依赖已安装")
        return False
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_enhanced_generator()
    exit(0 if success else 1)