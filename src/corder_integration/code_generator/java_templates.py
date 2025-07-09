#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Java代码模板管理器
专门负责管理Java代码生成模板
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class JavaTemplateManager:
    """Java代码模板管理器 - 负责提供和管理Java代码模板"""
    
    def __init__(self):
        self.templates = {
            'controller': self._get_controller_template(),
            'service_interface': self._get_service_interface_template(),
            'service_impl': self._get_service_impl_template(),
            'request_dto': self._get_request_dto_template(),
            'response_dto': self._get_response_dto_template(),
            'entity': self._get_entity_template(),
            'mapper': self._get_mapper_template()
        }
        logger.info("✅ Java模板管理器初始化完成")
    
    def get_template(self, template_type: str) -> str:
        """获取指定类型的模板"""
        return self.templates.get(template_type, "")
    
    def get_all_templates(self) -> Dict[str, str]:
        """获取所有模板"""
        return self.templates.copy()
    
    def build_template_variables(self, interface_name: str, input_params: List[Dict], 
                               output_params: Dict, description: str, http_method: str,
                               project_context: Dict[str, Any], api_path: str = '', 
                               business_logic: str = '') -> Dict[str, str]:
        """构建模板变量字典"""
        
        # 获取基础包路径
        package_patterns = project_context.get('package_patterns', {})
        base_package = package_patterns.get('base_package', 'com.main')
        
        # 类名生成
        controller_name = f"{interface_name}Controller"
        service_interface_name = f"{interface_name}Service"
        service_impl_name = f"{interface_name}ServiceImpl"
        request_dto_name = f"{interface_name}Req"
        response_dto_name = f"{interface_name}Resp"
        entity_name = interface_name.replace("Controller", "").replace("Service", "")
        mapper_name = f"{interface_name}Mapper"
        
        # HTTP方法映射
        http_method_mapping = {
            'GET': 'GetMapping',
            'POST': 'PostMapping',
            'PUT': 'PutMapping',
            'DELETE': 'DeleteMapping'
        }
        
        # 处理方法参数
        method_parameters = self._build_method_parameters(input_params, interface_name)
        request_fields = self._build_request_fields(input_params)
        response_fields = self._build_response_fields(output_params)
        entity_fields = self._build_entity_fields(input_params, output_params)
        custom_methods = self._build_custom_mapper_methods(interface_name, input_params)
        
        template_vars = {
            'PACKAGE_NAME': base_package,
            'CONTROLLER_CLASS_NAME': controller_name,
            'SERVICE_NAME': service_interface_name,
            'SERVICE_INTERFACE_NAME': service_interface_name,
            'SERVICE_IMPL_NAME': service_impl_name,
            'SERVICE_FIELD_NAME': service_interface_name[0].lower() + service_interface_name[1:],
            'REQUEST_DTO_NAME': request_dto_name,
            'RESPONSE_DTO_NAME': response_dto_name,
            'ENTITY_NAME': entity_name,
            'MAPPER_NAME': mapper_name,
            'MAPPER_FIELD_NAME': mapper_name[0].lower() + mapper_name[1:],
            'API_PATH': api_path or f"/api/{interface_name.lower()}",
            'HTTP_METHOD_ANNOTATION': http_method_mapping.get(http_method.upper(), 'PostMapping'),
            'REQUEST_MAPPING_PATH': '',  # 如果需要额外路径
            'METHOD_NAME': interface_name,
            'METHOD_PARAMETERS': method_parameters,
            'RETURN_TYPE': response_dto_name,
            'CONTROLLER_DESCRIPTION': f"{interface_name} Controller - {description}",
            'SERVICE_DESCRIPTION': f"{interface_name} Service - {description}",
            'ENTITY_DESCRIPTION': f"{entity_name} Entity",
            'MAPPER_DESCRIPTION': f"{mapper_name} Mapper",
            'REQUEST_DESCRIPTION': f"{interface_name} Request DTO",
            'RESPONSE_DESCRIPTION': f"{interface_name} Response DTO",
            'METHOD_DESCRIPTION': description or f"Process {interface_name} request",
            'TABLE_NAME': entity_name.lower(),
            'REQUEST_FIELDS': request_fields,
            'RESPONSE_FIELDS': response_fields,
            'ENTITY_FIELDS': entity_fields,
            'CUSTOM_METHODS': custom_methods,
            'CUSTOM_METHOD_DESCRIPTION': f"Custom query for {interface_name}",
            # 业务逻辑占位符
            'BUSINESS_LOGIC_CALL': f'{service_interface_name[0].lower() + service_interface_name[1:]}.{interface_name}(request)',
            'BUSINESS_LOGIC_IMPLEMENTATION': f'// TODO: 实现{description}业务逻辑',
            'REQUEST_PARAM_LOG': 'request',
            'PARAM_LOG': 'request',
            'RESPONSE_CREATION': f'new {response_dto_name}()',
            'RETURN_STATEMENT': f'new {response_dto_name}()'
        }
        
        return template_vars
    
    def apply_template_variables(self, template: str, variables: Dict[str, str]) -> str:
        """将变量应用到模板中"""
        result = template
        for var_name, var_value in variables.items():
            placeholder = f"{{{{{var_name}}}}}"
            result = result.replace(placeholder, str(var_value))
        return result
    
    def _build_method_parameters(self, input_params: List[Dict], interface_name: str = "") -> str:
        """构建方法参数"""
        if not input_params:
            return ""
        
        # 如果有输入参数，使用Request DTO
        request_dto_name = f"{interface_name}Req"
        return f"@Valid @RequestBody {request_dto_name} request"
    
    def _build_request_fields(self, input_params: List[Dict]) -> str:
        """构建请求DTO字段"""
        if not input_params:
            return "// 无输入参数"
        
        fields = []
        for param in input_params:
            name = param.get('name', 'field')
            param_type = self._map_java_type(param.get('type', 'String'))
            desc = param.get('description', '')
            required = param.get('required', False)
            
            field_lines = []
            if desc:
                field_lines.append(f'    @ApiModelProperty(value = "{desc}", required = {str(required).lower()})')
            
            if required:
                field_lines.append('    @NotNull(message = "不能为空")')
                if param_type == 'String':
                    field_lines.append('    @NotBlank(message = "不能为空白")')
            
            field_lines.append(f'    private {param_type} {name};')
            fields.append('\n'.join(field_lines))
        
        return '\n\n'.join(fields)
    
    def _build_response_fields(self, output_params: Dict) -> str:
        """构建响应DTO字段"""
        if not output_params:
            return """    @ApiModelProperty("响应状态码")
    private Integer code = 200;
    
    @ApiModelProperty("响应消息")
    private String message = "success";
    
    @ApiModelProperty("响应数据")
    private Object data;"""
        
        fields = []
        for name, info in output_params.items():
            param_type = self._map_java_type(info.get('type', 'String'))
            desc = info.get('description', '')
            
            field_lines = []
            if desc:
                field_lines.append(f'    @ApiModelProperty("{desc}")')
            field_lines.append(f'    private {param_type} {name};')
            fields.append('\n'.join(field_lines))
        
        return '\n\n'.join(fields)
    
    def _build_entity_fields(self, input_params: List[Dict], output_params: Dict) -> str:
        """构建Entity字段"""
        fields = []
        
        # 从输入参数构建字段
        for param in input_params:
            name = param.get('name', 'field')
            param_type = self._map_java_type(param.get('type', 'String'))
            desc = param.get('description', '')
            
            field_lines = []
            if desc:
                field_lines.append(f'    @ApiModelProperty("{desc}")')
            field_lines.append(f'    @TableField("{name}")')
            field_lines.append(f'    private {param_type} {name};')
            fields.append('\n'.join(field_lines))
        
        # 从输出参数构建字段（避免重复）
        input_names = {param.get('name') for param in input_params}
        for name, info in output_params.items():
            if name not in input_names:
                param_type = self._map_java_type(info.get('type', 'String'))
                desc = info.get('description', '')
                
                field_lines = []
                if desc:
                    field_lines.append(f'    @ApiModelProperty("{desc}")')
                field_lines.append(f'    @TableField("{name}")')
                field_lines.append(f'    private {param_type} {name};')
                fields.append('\n'.join(field_lines))
        
        return '\n\n'.join(fields) if fields else '    // TODO: 定义实体字段'
    
    def _build_custom_mapper_methods(self, interface_name: str, input_params: List[Dict]) -> str:
        """构建自定义Mapper方法"""
        if not input_params:
            return f"List<{{{{ENTITY_NAME}}}}> select{interface_name}List();"
        
        # 构建参数列表
        param_list = []
        for param in input_params:
            name = param.get('name', 'field')
            param_type = self._map_java_type(param.get('type', 'String'))
            param_list.append(f'@Param("{name}") {param_type} {name}')
        
        params_str = ', '.join(param_list)
        
        return f"""List<{{{{ENTITY_NAME}}}}> select{interface_name}List({params_str});"""
    
    def _map_java_type(self, param_type: str) -> str:
        """映射Java类型"""
        type_mapping = {
            'string': 'String',
            'str': 'String',
            'int': 'Integer',
            'integer': 'Integer',
            'long': 'Long',
            'float': 'Float',
            'double': 'Double',
            'boolean': 'Boolean',
            'bool': 'Boolean',
            'date': 'LocalDate',
            'datetime': 'LocalDateTime',
            'time': 'LocalTime',
            'bigdecimal': 'BigDecimal',
            'decimal': 'BigDecimal'
        }
        
        return type_mapping.get(param_type.lower(), 'String')
    
    def _get_controller_template(self) -> str:
        """获取Controller模板"""
        return '''package {{PACKAGE_NAME}}.interfaces.rest;

import {{PACKAGE_NAME}}.application.service.{{SERVICE_NAME}};
import {{PACKAGE_NAME}}.interfaces.dto.{{REQUEST_DTO_NAME}};
import {{PACKAGE_NAME}}.interfaces.dto.{{RESPONSE_DTO_NAME}};
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import javax.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;

/**
 * {{CONTROLLER_DESCRIPTION}}
 * Generated by Template + AI
 */
@Api(tags = "{{CONTROLLER_DESCRIPTION}}")
@RestController
@RequestMapping("{{API_PATH}}")
@CrossOrigin(origins = "*")
public class {{CONTROLLER_CLASS_NAME}} {
    
    private static final Logger logger = LoggerFactory.getLogger({{CONTROLLER_CLASS_NAME}}.class);
    
    @Autowired
    private {{SERVICE_NAME}} {{SERVICE_FIELD_NAME}};
    
    /**
     * {{METHOD_DESCRIPTION}}
     */
    @ApiOperation("{{METHOD_DESCRIPTION}}")
    @{{HTTP_METHOD_ANNOTATION}}{{REQUEST_MAPPING_PATH}}
    public ResponseEntity<{{RESPONSE_DTO_NAME}}> {{METHOD_NAME}}({{METHOD_PARAMETERS}}) {
        try {
            logger.info("Processing {{METHOD_NAME}} request: {}", {{REQUEST_PARAM_LOG}});
            
            {{RESPONSE_DTO_NAME}} response = {{BUSINESS_LOGIC_CALL}};
            
            logger.info("{{METHOD_NAME}} completed successfully");
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            logger.error("Error in {{METHOD_NAME}}: ", e);
            return ResponseEntity.internalServerError().build();
        }
    }
}'''

    def _get_service_interface_template(self) -> str:
        """获取Service接口模板"""
        return '''package {{PACKAGE_NAME}}.application.service;

import {{PACKAGE_NAME}}.interfaces.dto.{{REQUEST_DTO_NAME}};
import {{PACKAGE_NAME}}.interfaces.dto.{{RESPONSE_DTO_NAME}};
import java.util.List;

/**
 * {{SERVICE_DESCRIPTION}}
 * Generated by Template + AI
 */
public interface {{SERVICE_INTERFACE_NAME}} {
    
    /**
     * {{METHOD_DESCRIPTION}}
     */
    {{RETURN_TYPE}} {{METHOD_NAME}}({{REQUEST_DTO_NAME}} request);
}'''

    def _get_service_impl_template(self) -> str:
        """获取ServiceImpl模板"""
        return '''package {{PACKAGE_NAME}}.application.service.impl;

import {{PACKAGE_NAME}}.application.service.{{SERVICE_INTERFACE_NAME}};
import {{PACKAGE_NAME}}.domain.entity.{{ENTITY_NAME}};
import {{PACKAGE_NAME}}.domain.mapper.{{MAPPER_NAME}};
import {{PACKAGE_NAME}}.interfaces.dto.{{REQUEST_DTO_NAME}};
import {{PACKAGE_NAME}}.interfaces.dto.{{RESPONSE_DTO_NAME}};
import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.transaction.annotation.Transactional;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import java.util.List;
import java.util.stream.Collectors;

/**
 * {{SERVICE_DESCRIPTION}}
 * Generated by Template + AI
 */
@Service
@Transactional
public class {{SERVICE_IMPL_NAME}} implements {{SERVICE_INTERFACE_NAME}} {
    
    private static final Logger logger = LoggerFactory.getLogger({{SERVICE_IMPL_NAME}}.class);
    
    @Autowired
    private {{MAPPER_NAME}} {{MAPPER_FIELD_NAME}};
    
    @Override
    public {{RETURN_TYPE}} {{METHOD_NAME}}({{REQUEST_DTO_NAME}} request) {
        logger.info("Executing {{METHOD_NAME}} with parameters: {}", {{PARAM_LOG}});
        
        try {
            {{BUSINESS_LOGIC_IMPLEMENTATION}}
            
            logger.info("{{METHOD_NAME}} completed successfully");
            return {{RETURN_STATEMENT}};
        } catch (Exception e) {
            logger.error("Error in {{METHOD_NAME}}: ", e);
            throw new RuntimeException("{{METHOD_NAME}} failed", e);
        }
    }
}'''

    def _get_request_dto_template(self) -> str:
        """获取请求DTO模板"""
        return '''package {{PACKAGE_NAME}}.interfaces.dto;

import javax.validation.constraints.*;
import lombok.Data;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;

/**
 * {{REQUEST_DESCRIPTION}}
 * Generated by Template + AI
 */
@Data
@ApiModel(description = "{{REQUEST_DESCRIPTION}}")
public class {{REQUEST_DTO_NAME}} {
    
{{REQUEST_FIELDS}}
}'''

    def _get_response_dto_template(self) -> str:
        """获取响应DTO模板"""
        return '''package {{PACKAGE_NAME}}.interfaces.dto;

import lombok.Data;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;

/**
 * {{RESPONSE_DESCRIPTION}}
 * Generated by Template + AI
 */
@Data
@ApiModel(description = "{{RESPONSE_DESCRIPTION}}")
public class {{RESPONSE_DTO_NAME}} {
    
{{RESPONSE_FIELDS}}
}'''

    def _get_entity_template(self) -> str:
        """获取Entity模板"""
        return '''package {{PACKAGE_NAME}}.domain.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import java.time.LocalDateTime;

/**
 * {{ENTITY_DESCRIPTION}}
 * Generated by Template + AI
 */
@Data
@ApiModel(description = "{{ENTITY_DESCRIPTION}}")
@TableName("{{TABLE_NAME}}")
public class {{ENTITY_NAME}} {
    
    @ApiModelProperty("主键ID")
    @TableId(type = IdType.AUTO)
    private Long id;
    
{{ENTITY_FIELDS}}
    
    @ApiModelProperty("创建时间")
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    
    @ApiModelProperty("更新时间")
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}'''

    def _get_mapper_template(self) -> str:
        """获取Mapper模板"""
        return '''package {{PACKAGE_NAME}}.domain.mapper;

import {{PACKAGE_NAME}}.domain.entity.{{ENTITY_NAME}};
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import java.util.List;

/**
 * {{MAPPER_DESCRIPTION}}
 * Generated by Template + AI
 */
@Mapper
public interface {{MAPPER_NAME}} extends BaseMapper<{{ENTITY_NAME}}> {
    
    /**
     * {{CUSTOM_METHOD_DESCRIPTION}}
     */
    {{CUSTOM_METHODS}}
}''' 