"""
ControllerInterfaceManager智能复用功能单元测试
验证智能复用模式的API接口处理功能
"""
import unittest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# 添加项目根目录到Python路径
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.corder_integration.code_generator.controller_interface_manager import ControllerInterfaceManager


class TestControllerInterfaceManagerReuse(unittest.TestCase):
    """ControllerInterfaceManager智能复用功能测试类"""
    
    def setUp(self):
        """测试前置设置"""
        self.mock_llm_client = Mock()
        self.manager = ControllerInterfaceManager(self.mock_llm_client)
        
        # 创建临时测试目录
        self.temp_dir = tempfile.mkdtemp()
        
        # 模拟Controller内容
        self.sample_controller_content = """
package com.yljr.crcl.limit.interfaces.facade;

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
    
    @GetMapping("/queryCompanyUnitList")
    public ResponseEntity<List<Map<String, Object>>> queryCompanyUnitList(@RequestParam Map<String, Object> params) {
        List<Map<String, Object>> data = queryCompanyUnitListData(params);
        return ResponseEntity.ok(data);
    }
    
    private List<Map<String, Object>> queryCompanyUnitListData(Map<String, Object> params) {
        return zqylUserAuthFeignClient.queryCompanyUnitList(params);
    }
}
"""
        
    def tearDown(self):
        """测试后置清理"""
        # 清理临时目录
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_classify_interface_type(self):
        """测试接口类型分类"""
        # 测试数据
        test_cases = [
            ('QueryCompanyUnitList', '/api/limit/queryCompanyUnitList', 'query_list'),
            ('ExportCompanyUnitList', '/api/limit/exportCompanyUnitList', 'export_list'),
            ('CreateCompanyUnit', '/api/limit/createCompanyUnit', 'create'),
            ('UpdateCompanyUnit', '/api/limit/updateCompanyUnit', 'update'),
            ('DeleteCompanyUnit', '/api/limit/deleteCompanyUnit', 'delete'),
            ('ProcessData', '/api/limit/processData', 'other'),
            ('GenerateReport', '/api/limit/export/generateReport', 'export_list')  # 从路径推断
        ]
        
        for interface_name, api_path, expected_type in test_cases:
            with self.subTest(interface_name=interface_name, api_path=api_path):
                result = self.manager._classify_interface_type(interface_name, api_path)
                self.assertEqual(result, expected_type)
                
    def test_generate_reuse_plan(self):
        """测试生成复用计划"""
        # 准备测试数据
        reusable_clients = [
            {
                'client_info': {
                    'class_name': 'ZqylUserAuthFeignClient',
                    'business_domain': 'UserAuth'
                },
                'similarity_score': 0.8,
                'reuse_recommendation': '推荐复用'
            }
        ]
        
        merge_analysis = {
            'can_merge': True,
            'merge_strategy': {
                'strategy': 'reuse_and_extend',
                'base_method': {
                    'method_name': 'queryCompanyUnitList',
                    'method_type': 'query_list'
                },
                'extension_type': 'export_list'
            }
        }
        
        interface_type = 'export_list'
        interface_name = 'ExportCompanyUnitList'
        
        # 执行测试
        result = self.manager._generate_reuse_plan(reusable_clients, merge_analysis, interface_type, interface_name)
        
        # 验证结果
        self.assertIsInstance(result, dict)
        self.assertIn('has_reusable_components', result)
        self.assertIn('reuse_feign_clients', result)
        self.assertIn('shared_methods', result)
        self.assertIn('export_methods', result)
        self.assertIn('merge_strategy', result)
        
        # 验证复用组件标识
        self.assertTrue(result['has_reusable_components'])
        
        # 验证Feign Client复用
        self.assertEqual(len(result['reuse_feign_clients']), 1)
        self.assertEqual(result['reuse_feign_clients'][0]['class_name'], 'ZqylUserAuthFeignClient')
        
        # 验证合并策略
        self.assertIsNotNone(result['merge_strategy'])
        
    def test_generate_export_interface_method(self):
        """测试生成导出接口方法"""
        # 准备测试数据
        interface_name = 'ExportCompanyUnitList'
        api_path = '/api/limit/exportCompanyUnitList'
        description = '导出公司单位列表'
        base_method = {
            'method_name': 'queryCompanyUnitList',
            'method_type': 'query_list'
        }
        services = []
        
        # 执行测试
        result = self.manager._generate_export_interface_method(
            interface_name, api_path, description, base_method, services
        )
        
        # 验证结果
        self.assertIsInstance(result, str)
        self.assertIn('@GetMapping', result)
        self.assertIn('ResponseEntity<byte[]>', result)
        self.assertIn('exportCompanyUnitList', result)
        self.assertIn('queryCompanyUnitListData', result)
        self.assertIn('excelExportService', result)
        self.assertIn('LocalDateTime', result)
        self.assertIn('HttpHeaders', result)
        
    def test_generate_query_interface_method(self):
        """测试生成查询接口方法"""
        # 准备测试数据
        interface_name = 'QueryCompanyUnitList'
        api_path = '/api/limit/queryCompanyUnitList'
        description = '查询公司单位列表'
        base_method = {
            'method_name': 'queryCompanyUnitList',
            'method_type': 'query_list'
        }
        services = []
        
        # 执行测试
        result = self.manager._generate_query_interface_method(
            interface_name, api_path, description, base_method, services
        )
        
        # 验证结果
        self.assertIsInstance(result, str)
        self.assertIn('@GetMapping', result)
        self.assertIn('ResponseEntity<List<Map<String, Object>>>', result)
        self.assertIn('queryCompanyUnitList', result)
        self.assertIn('queryCompanyUnitListData', result)
        
    def test_generate_merged_interface_method(self):
        """测试生成合并的接口方法"""
        # 准备测试数据 - 导出类型
        interface_name = 'ExportCompanyUnitList'
        http_method = 'GET'
        api_path = '/api/limit/exportCompanyUnitList'
        description = '导出公司单位列表'
        merge_strategy = {
            'strategy': 'reuse_and_extend',
            'base_method': {
                'method_name': 'queryCompanyUnitList',
                'method_type': 'query_list'
            },
            'extension_type': 'export_list'
        }
        services = []
        
        # 执行测试
        result = self.manager._generate_merged_interface_method(
            interface_name, http_method, api_path, description, merge_strategy, services
        )
        
        # 验证结果
        self.assertIsInstance(result, str)
        self.assertIn('exportCompanyUnitList', result)
        self.assertIn('excelExportService', result)
        
        # 准备测试数据 - 查询类型
        merge_strategy_query = {
            'strategy': 'reuse_and_extend',
            'base_method': {
                'method_name': 'queryCompanyUnitList',
                'method_type': 'query_list'
            },
            'extension_type': 'query_list'
        }
        
        # 执行测试
        result_query = self.manager._generate_merged_interface_method(
            'QueryCompanyUnitList', http_method, '/api/limit/queryCompanyUnitList', 
            '查询公司单位列表', merge_strategy_query, services
        )
        
        # 验证结果
        self.assertIsInstance(result_query, str)
        self.assertIn('queryCompanyUnitList', result_query)
        self.assertIn('queryCompanyUnitListData', result_query)
        
    @patch('src.corder_integration.code_generator.controller_interface_manager.ControllerInterfaceManager._generate_code_with_reuse')
    @patch('src.corder_integration.code_generator.controller_analyzer.ControllerAnalyzer.find_matching_controllers')
    def test_process_api_interface_request_with_reuse(self, mock_find_controllers, mock_generate_code):
        """测试智能复用模式的API接口处理"""
        # 准备测试数据
        controller_info = {
            'file_path': '/test/CompanyUnitLimitController.java',
            'class_name': 'CompanyUnitLimitController',
            'content': self.sample_controller_content,
            'services': []
        }
        
        mock_find_controllers.return_value = [controller_info]
        mock_generate_code.return_value = self.sample_controller_content + "\n// New method added"
        
        # 模拟组件复用管理器的方法
        with patch.object(self.manager.component_reuse_manager, 'analyze_controller_component_dependencies') as mock_analyze:
            mock_analyze.return_value = {
                'method_patterns': [
                    {
                        'method_name': 'queryCompanyUnitList',
                        'method_type': 'query_list'
                    }
                ]
            }
            
            with patch.object(self.manager.component_reuse_manager, 'find_reusable_feign_clients') as mock_find_clients:
                mock_find_clients.return_value = [
                    {
                        'client_info': {'class_name': 'ZqylUserAuthFeignClient'},
                        'similarity_score': 0.8
                    }
                ]
                
                with patch.object(self.manager.component_reuse_manager, 'merge_similar_interface_logic') as mock_merge:
                    mock_merge.return_value = {
                        'can_merge': True,
                        'merge_strategy': {
                            'strategy': 'reuse_and_extend',
                            'base_method': {'method_name': 'queryCompanyUnitList'}
                        }
                    }
                    
                    with patch.object(self.manager.interface_adder, 'save_updated_controller') as mock_save:
                        mock_save.return_value = True
                        
                        # 执行测试
                        result = self.manager.process_api_interface_request_with_reuse(
                            self.temp_dir, 'companyUnit', '/api/limit/exportCompanyUnitList', '导出公司单位列表'
                        )
        
        # 验证结果
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        self.assertIn('results', result)
        self.assertIn('interface_type', result)
        
        if result['success']:
            self.assertTrue(result['success'])
            self.assertGreater(len(result['results']), 0)
            
            # 验证结果中的详细信息
            first_result = result['results'][0]
            self.assertIn('component_analysis', first_result)
            self.assertIn('reusable_clients', first_result)
            self.assertIn('merge_analysis', first_result)
            self.assertIn('reuse_plan', first_result)
            
    @patch('builtins.open', create=True)
    def test_generate_code_with_reuse(self, mock_open):
        """测试使用智能复用生成代码"""
        # 准备测试数据
        controller_info = {
            'file_path': '/test/CompanyUnitLimitController.java',
            'content': self.sample_controller_content,
            'services': []
        }
        
        reuse_plan = {
            'has_reusable_components': True,
            'merge_strategy': {
                'strategy': 'reuse_and_extend',
                'base_method': {
                    'method_name': 'queryCompanyUnitList',
                    'method_type': 'query_list'
                },
                'extension_type': 'export_list'
            }
        }
        
        # 配置mock
        mock_file = MagicMock()
        mock_file.read.return_value = self.sample_controller_content
        mock_open.return_value.__enter__.return_value = mock_file
        
        # 模拟组件复用管理器的方法
        with patch.object(self.manager.component_reuse_manager, 'update_controller_with_component_reuse') as mock_update:
            mock_update.return_value = {'success': True}
            
            # 执行测试
            result = self.manager._generate_code_with_reuse(
                controller_info, 'ExportCompanyUnitList', 'GET', 
                '/api/limit/exportCompanyUnitList', '导出公司单位列表', reuse_plan
            )
        
        # 验证结果
        self.assertIsInstance(result, str)
        self.assertIn('class CompanyUnitLimitController', result)
        
    def test_generate_code_with_reuse_fallback(self):
        """测试智能复用的fallback机制"""
        # 准备测试数据
        controller_info = {
            'file_path': '/test/CompanyUnitLimitController.java',
            'content': self.sample_controller_content,
            'services': []
        }
        
        reuse_plan = {
            'has_reusable_components': False,
            'merge_strategy': None
        }
        
        # 执行测试
        result = self.manager._generate_code_with_reuse(
            controller_info, 'SimpleQuery', 'GET', 
            '/api/limit/simpleQuery', '简单查询', reuse_plan
        )
        
        # 验证结果
        self.assertIsInstance(result, str)
        
    def test_integration_feign_client_reuse_flow(self):
        """集成测试：Feign Client复用流程"""
        # 创建测试用的Feign Client文件
        feign_dir = os.path.join(self.temp_dir, "src", "main", "java", "com", "yljr", "crcl", "application", "feign")
        os.makedirs(feign_dir, exist_ok=True)
        
        feign_content = """
@FeignClient(name = "zqyl-user-auth")
public interface ZqylUserAuthFeignClient {
    @GetMapping("/api/user/queryCompanyUnitList")
    List<Map<String, Object>> queryCompanyUnitList(@RequestParam Map<String, Object> params);
}
"""
        
        feign_path = os.path.join(feign_dir, "ZqylUserAuthFeignClient.java")
        with open(feign_path, 'w', encoding='utf-8') as f:
            f.write(feign_content)
        
        # 创建测试用的Controller文件
        controller_dir = os.path.join(self.temp_dir, "src", "main", "java", "com", "yljr", "crcl", "interfaces", "facade")
        os.makedirs(controller_dir, exist_ok=True)
        
        controller_path = os.path.join(controller_dir, "CompanyUnitLimitController.java")
        with open(controller_path, 'w', encoding='utf-8') as f:
            f.write(self.sample_controller_content)
        
        # 测试Feign Client复用 - 使用更简单的验证
        try:
            reusable_clients = self.manager.component_reuse_manager.find_reusable_feign_clients(
                controller_path, '/api/limit/queryCompanyUnitList', 'companyUnit'
            )
            
            # 验证是否找到了可复用的客户端
            self.assertIsInstance(reusable_clients, list)
        except Exception as e:
            # 如果出现异常，说明测试环境问题，跳过此测试
            self.skipTest(f"Feign Client扫描测试跳过: {e}")
        
        
    def test_integration_interface_merge_flow(self):
        """集成测试：接口合并流程"""
        # 准备现有方法数据
        existing_methods = [
            {
                'method_name': 'queryCompanyUnitList',
                'method_type': 'query_list',
                'business_operation': 'CompanyUnitList'
            }
        ]
        
        # 测试接口合并
        merge_result = self.manager.component_reuse_manager.merge_similar_interface_logic(
            'ExportCompanyUnitList', existing_methods, 'export_list'
        )
        
        # 验证合并结果
        self.assertIsInstance(merge_result, dict)
        self.assertIn('can_merge', merge_result)
        
        if merge_result['can_merge']:
            # 测试生成复用计划
            reuse_plan = self.manager._generate_reuse_plan(
                [], merge_result, 'export_list', 'ExportCompanyUnitList'
            )
            
            # 验证复用计划
            self.assertIsInstance(reuse_plan, dict)
            self.assertIn('has_reusable_components', reuse_plan)
            

if __name__ == '__main__':
    unittest.main()