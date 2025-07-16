"""
智能组件复用管理器单元测试
验证Feign Client复用、接口逻辑合并等功能
"""
import unittest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# 添加项目根目录到Python路径
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.corder_integration.code_generator.intelligent_component_reuse_manager import IntelligentComponentReuseManager


class TestIntelligentComponentReuseManager(unittest.TestCase):
    """智能组件复用管理器测试类"""
    
    def setUp(self):
        """测试前置设置"""
        self.mock_llm_client = Mock()
        self.manager = IntelligentComponentReuseManager(self.mock_llm_client)
        
        # 创建临时测试目录
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """测试后置清理"""
        # 清理临时目录
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_analyze_controller_component_dependencies(self):
        """测试Controller组件依赖分析"""
        # 准备测试数据
        controller_content = """
package com.yljr.crcl.limit.interfaces.rest;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import java.util.Map;
import java.util.List;

@RestController
@RequestMapping("/api/limit")
public class CompanyUnitLimitController {
    
    @Autowired
    private ZqylUserAuthFeignClient zqylUserAuthFeignClient;
    
    @Autowired
    private CompanyUnitLimitService companyUnitLimitService;
    
    @GetMapping("/queryCompanyUnitList")
    public ResponseEntity<List<Map<String, Object>>> queryCompanyUnitList(@RequestParam Map<String, Object> params) {
        return ResponseEntity.ok(zqylUserAuthFeignClient.queryCompanyUnitList(params));
    }
    
    @GetMapping("/exportCompanyUnitList")
    public ResponseEntity<byte[]> exportCompanyUnitList(@RequestParam Map<String, Object> params) {
        return ResponseEntity.ok(new byte[0]);
    }
}
"""
        
        # 创建临时Controller文件
        controller_path = os.path.join(self.temp_dir, "CompanyUnitLimitController.java")
        with open(controller_path, 'w', encoding='utf-8') as f:
            f.write(controller_content)
        
        # 执行测试
        result = self.manager.analyze_controller_component_dependencies(controller_path)
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertIn('dependencies', result)
        self.assertIn('feign_clients', result)
        self.assertIn('method_patterns', result)
        
        # 验证Feign Client识别
        feign_clients = result['feign_clients']
        self.assertEqual(len(feign_clients), 1)
        self.assertEqual(feign_clients[0]['class_name'], 'ZqylUserAuthFeignClient')
        self.assertEqual(feign_clients[0]['variable_name'], 'zqylUserAuthFeignClient')
        
        # 验证方法模式识别
        method_patterns = result['method_patterns']
        self.assertEqual(len(method_patterns), 2)
        method_names = [pattern['method_name'] for pattern in method_patterns]
        self.assertIn('queryCompanyUnitList', method_names)
        self.assertIn('exportCompanyUnitList', method_names)
        
    def test_find_reusable_feign_clients(self):
        """测试查找可复用的Feign Client"""
        # 创建模拟的Feign Client文件
        feign_client_content = """
package com.yljr.crcl.application.feign;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import java.util.Map;
import java.util.List;

@FeignClient(name = "zqyl-user-auth", url = "http://localhost:8080")
public interface ZqylUserAuthFeignClient {
    
    @GetMapping("/api/user/queryCompanyUnitList")
    List<Map<String, Object>> queryCompanyUnitList(@RequestParam Map<String, Object> params);
    
    @GetMapping("/api/user/queryUserList")
    List<Map<String, Object>> queryUserList(@RequestParam Map<String, Object> params);
}
"""
        
        # 创建项目目录结构
        feign_dir = os.path.join(self.temp_dir, "src", "main", "java", "com", "yljr", "crcl", "application", "feign")
        os.makedirs(feign_dir, exist_ok=True)
        
        feign_client_path = os.path.join(feign_dir, "ZqylUserAuthFeignClient.java")
        with open(feign_client_path, 'w', encoding='utf-8') as f:
            f.write(feign_client_content)
        
        # 执行测试
        target_controller = os.path.join(self.temp_dir, "TestController.java")
        api_path = "/api/limit/queryCompanyUnitList"
        business_domain = "companyUnit"
        
        result = self.manager.find_reusable_feign_clients(target_controller, api_path, business_domain)
        
        # 验证结果
        self.assertIsInstance(result, list)
        if result:  # 如果找到了可复用的客户端
            self.assertGreater(len(result), 0)
            first_client = result[0]
            self.assertIn('client_info', first_client)
            self.assertIn('similarity_score', first_client)
            self.assertIn('reuse_recommendation', first_client)
            
    def test_merge_similar_interface_logic(self):
        """测试合并相似接口逻辑"""
        # 准备测试数据
        interface_name = "CompanyUnitList"
        existing_methods = [
            {
                'method_name': 'queryCompanyUnitList',
                'method_type': 'query_list',
                'business_operation': 'CompanyUnitList'
            }
        ]
        new_interface_type = 'export_list'
        
        # 执行测试
        result = self.manager.merge_similar_interface_logic(interface_name, existing_methods, new_interface_type)
        
        # 验证结果
        self.assertIsInstance(result, dict)
        self.assertIn('can_merge', result)
        
        if result['can_merge']:
            self.assertIn('merge_strategy', result)
            self.assertIn('similar_patterns', result)
            self.assertIn('shared_logic', result)
            self.assertIn('special_handling', result)
            
    def test_generate_shared_service_method(self):
        """测试生成共享Service方法"""
        # 准备测试数据
        base_method = {
            'name': 'queryCompanyUnitList',
            'method_type': 'query_list',
            'description': '查询公司单位列表',
            'parameters': ['params'],
            'return_type': 'List<Map<String, Object>>'
        }
        interface_variants = ['query', 'export']
        
        # 执行测试
        result = self.manager.generate_shared_service_method(base_method, interface_variants)
        
        # 验证结果
        self.assertIsInstance(result, dict)
        self.assertIn('shared_method', result)
        self.assertIn('variant_methods', result)
        self.assertIn('dependencies', result)
        
        # 验证共享方法
        shared_method = result['shared_method']
        self.assertIn('name', shared_method)
        self.assertIn('signature', shared_method)
        self.assertIn('logic', shared_method)
        self.assertEqual(shared_method['name'], 'queryCompanyUnitListData')
        
        # 验证变体方法
        variant_methods = result['variant_methods']
        self.assertIn('query', variant_methods)
        self.assertIn('export', variant_methods)
        
    def test_generate_export_enhanced_method(self):
        """测试生成导出增强方法"""
        # 准备测试数据
        base_method = {
            'name': 'queryCompanyUnitList',
            'description': '查询公司单位列表',
            'service_call': 'zqylUserAuthFeignClient.queryCompanyUnitList(params)'
        }
        export_config = {'format': 'excel'}
        
        # 执行测试
        result = self.manager.generate_export_enhanced_method(base_method, export_config)
        
        # 验证结果
        self.assertIsInstance(result, str)
        self.assertIn('@GetMapping', result)
        self.assertIn('ResponseEntity<byte[]>', result)
        self.assertIn('exportToExcel', result)
        self.assertIn('queryCompanyUnitListData', result)
        
    def test_classify_method_type(self):
        """测试方法类型分类"""
        # 测试数据
        test_cases = [
            ('queryCompanyUnitList', 'query_list'),
            ('exportCompanyUnitList', 'export_list'),
            ('createCompanyUnit', 'create'),
            ('updateCompanyUnit', 'update'),
            ('deleteCompanyUnit', 'delete'),
            ('processData', 'other')
        ]
        
        for method_name, expected_type in test_cases:
            with self.subTest(method_name=method_name):
                result = self.manager._classify_method_type(method_name)
                self.assertEqual(result, expected_type)
                
    def test_calculate_feign_client_similarity(self):
        """测试Feign Client相似度计算"""
        # 准备测试数据
        client = {
            'class_name': 'ZqylUserAuthFeignClient',
            'business_domain': 'UserAuth'
        }
        domain_keywords = ['user', 'auth', 'company']
        api_path = '/api/user/queryCompanyUnitList'
        
        # 执行测试
        result = self.manager._calculate_feign_client_similarity(client, domain_keywords, api_path)
        
        # 验证结果
        self.assertIsInstance(result, float)
        self.assertGreaterEqual(result, 0.0)
        self.assertLessEqual(result, 1.0)
        
    def test_extract_business_domain_from_class(self):
        """测试从类名提取业务域"""
        # 测试数据
        test_cases = [
            ('ZqylUserAuthFeignClient', 'ZqylUserAuth'),
            ('CompanyUnitLimitService', 'CompanyUnitLimit'),
            ('UserController', 'User'),
            ('DataMapper', 'Data')
        ]
        
        for class_name, expected_domain in test_cases:
            with self.subTest(class_name=class_name):
                result = self.manager._extract_business_domain_from_class(class_name)
                self.assertEqual(result, expected_domain)
                
    def test_is_similar_operation(self):
        """测试相似操作判断"""
        # 测试数据
        test_cases = [
            ('query_list', 'export_list', True),
            ('query_list', 'query_list', True),
            ('create', 'update', False),
            ('delete', 'create', False)
        ]
        
        for existing_type, new_type, expected_result in test_cases:
            with self.subTest(existing_type=existing_type, new_type=new_type):
                result = self.manager._is_similar_operation(existing_type, new_type)
                self.assertEqual(result, expected_result)
                
    def test_extract_domain_keywords(self):
        """测试提取业务域关键字"""
        # 测试数据
        api_path = '/api/limit/queryCompanyUnitList'
        business_domain = 'companyUnit'
        
        # 执行测试
        result = self.manager._extract_domain_keywords(api_path, business_domain)
        
        # 验证结果
        self.assertIsInstance(result, list)
        self.assertIn('limit', result)
        self.assertIn('queryCompanyUnitList', result)
        self.assertIn('companyUnit', result)
        
    @patch('builtins.open', create=True)
    def test_update_controller_with_component_reuse(self, mock_open):
        """测试更新Controller支持组件复用"""
        # 准备测试数据
        controller_content = """
package com.yljr.crcl.limit.interfaces.rest;

import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/limit")
public class CompanyUnitLimitController {
    
    @GetMapping("/test")
    public String test() {
        return "test";
    }
}
"""
        
        reuse_plan = {
            'feign_clients': [
                {
                    'class_name': 'ZqylUserAuthFeignClient',
                    'variable_name': 'zqylUserAuthFeignClient'
                }
            ],
            'shared_methods': [
                {
                    'name': 'queryCompanyUnitListData',
                    'code': 'private List<Map<String, Object>> queryCompanyUnitListData(Map<String, Object> params) { return null; }'
                }
            ]
        }
        
        # 配置mock
        mock_file = MagicMock()
        mock_file.read.return_value = controller_content
        mock_open.return_value.__enter__.return_value = mock_file
        
        # 执行测试
        controller_path = "/test/CompanyUnitLimitController.java"
        result = self.manager.update_controller_with_component_reuse(controller_path, reuse_plan)
        
        # 验证结果
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        self.assertIn('message', result)
        
    def test_parse_feign_client(self):
        """测试解析Feign Client信息"""
        # 准备测试数据
        feign_client_content = """
package com.yljr.crcl.application.feign;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;

@FeignClient(name = "zqyl-user-auth", url = "http://localhost:8080")
public interface ZqylUserAuthFeignClient {
    
    @GetMapping("/api/user/queryCompanyUnitList")
    List<Map<String, Object>> queryCompanyUnitList(@RequestParam Map<String, Object> params);
}
"""
        
        # 执行测试
        file_path = "/test/ZqylUserAuthFeignClient.java"
        result = self.manager._parse_feign_client(feign_client_content, file_path)
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result['class_name'], 'ZqylUserAuthFeignClient')
        self.assertEqual(result['file_path'], file_path)
        self.assertIn('@FeignClient', result['feign_config'])
        self.assertGreater(len(result['methods']), 0)
        
    def test_generate_reuse_recommendation(self):
        """测试生成复用建议"""
        # 准备测试数据
        client = {'class_name': 'ZqylUserAuthFeignClient'}
        
        # 测试不同相似度得分
        test_cases = [
            (0.9, "强烈推荐复用"),
            (0.7, "推荐复用"),
            (0.5, "可以考虑复用")
        ]
        
        for similarity_score, expected_keyword in test_cases:
            with self.subTest(similarity_score=similarity_score):
                result = self.manager._generate_reuse_recommendation(client, similarity_score)
                self.assertIn(expected_keyword, result)
                self.assertIn('ZqylUserAuthFeignClient', result)


if __name__ == '__main__':
    unittest.main()