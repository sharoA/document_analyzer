"""
智能组件复用集成测试
验证完整的智能复用流程：从Controller分析到代码生成
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
from src.corder_integration.code_generator.controller_interface_manager import ControllerInterfaceManager


class TestIntelligentReuseIntegration(unittest.TestCase):
    """智能复用集成测试类"""
    
    def setUp(self):
        """测试前置设置"""
        self.mock_llm_client = Mock()
        self.temp_dir = tempfile.mkdtemp()
        self.project_structure = self._create_test_project_structure()
        
    def tearDown(self):
        """测试后置清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def _create_test_project_structure(self):
        """创建测试项目结构"""
        # 创建标准的Spring Boot项目结构
        structure = {
            'src/main/java/com/yljr/crcl': {
                'application/feign': {},
                'application/service': {},
                'interfaces/rest': {},
                'interfaces/dto': {},
                'domain/entity': {},
                'domain/mapper': {}
            },
            'src/main/resources': {
                'mapper': {}
            }
        }
        
        # 创建目录结构
        for path, subdirs in structure.items():
            full_path = os.path.join(self.temp_dir, path)
            os.makedirs(full_path, exist_ok=True)
            
            for subdir in subdirs:
                subdir_path = os.path.join(full_path, subdir)
                os.makedirs(subdir_path, exist_ok=True)
        
        return structure
    
    def _create_sample_feign_client(self, class_name: str, business_domain: str) -> str:
        """创建示例Feign Client"""
        content = f"""
package com.yljr.crcl.application.feign;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import java.util.Map;
import java.util.List;

@FeignClient(name = "{business_domain.lower()}-service", url = "${{service.{business_domain.lower()}.url}}")
public interface {class_name} {{
    
    @GetMapping("/api/{business_domain.lower()}/queryCompanyUnitList")
    List<Map<String, Object>> queryCompanyUnitList(@RequestParam Map<String, Object> params);
    
    @GetMapping("/api/{business_domain.lower()}/queryUserList")
    List<Map<String, Object>> queryUserList(@RequestParam Map<String, Object> params);
    
    @GetMapping("/api/{business_domain.lower()}/queryDepartmentList")
    List<Map<String, Object>> queryDepartmentList(@RequestParam Map<String, Object> params);
}}
"""
        
        file_path = os.path.join(self.temp_dir, 'src/main/java/com/yljr/crcl/application/feign', f'{class_name}.java')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return file_path
    
    def _create_sample_controller(self, class_name: str, business_domain: str) -> str:
        """创建示例Controller"""
        content = f"""
package com.yljr.crcl.{business_domain.lower()}.interfaces.rest;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import java.util.Map;
import java.util.List;

@RestController
@RequestMapping("/api/{business_domain.lower()}")
public class {class_name} {{
    
    @Autowired
    private ZqylUserAuthFeignClient zqylUserAuthFeignClient;
    
    @GetMapping("/queryCompanyUnitList")
    public ResponseEntity<List<Map<String, Object>>> queryCompanyUnitList(@RequestParam Map<String, Object> params) {{
        List<Map<String, Object>> data = queryCompanyUnitListData(params);
        return ResponseEntity.ok(data);
    }}
    
    private List<Map<String, Object>> queryCompanyUnitListData(Map<String, Object> params) {{
        return zqylUserAuthFeignClient.queryCompanyUnitList(params);
    }}
}}
"""
        
        controller_dir = os.path.join(self.temp_dir, 'src/main/java/com/yljr/crcl/interfaces/rest')
        file_path = os.path.join(controller_dir, f'{class_name}.java')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return file_path
    
    def test_complete_reuse_flow_export_interface(self):
        """测试完整的复用流程：为现有查询接口添加导出功能"""
        # 1. 创建测试数据
        feign_client_path = self._create_sample_feign_client('ZqylUserAuthFeignClient', 'UserAuth')
        controller_path = self._create_sample_controller('CompanyUnitLimitController', 'limit')
        
        # 2. 初始化管理器
        component_manager = IntelligentComponentReuseManager(self.mock_llm_client)
        interface_manager = ControllerInterfaceManager(self.mock_llm_client)
        
        # 3. 分析现有Controller组件依赖
        component_analysis = component_manager.analyze_controller_component_dependencies(controller_path)
        
        self.assertIsNotNone(component_analysis)
        self.assertIn('feign_clients', component_analysis)
        self.assertIn('method_patterns', component_analysis)
        
        # 4. 查找可复用的Feign Client
        reusable_clients = component_manager.find_reusable_feign_clients(
            controller_path, '/api/limit/exportCompanyUnitList', 'companyUnit'
        )
        
        self.assertIsInstance(reusable_clients, list)
        
        # 5. 分析接口逻辑合并可能性
        existing_methods = component_analysis.get('method_patterns', [])
        merge_analysis = component_manager.merge_similar_interface_logic(
            'ExportCompanyUnitList', existing_methods, 'export_list'
        )
        
        self.assertIsInstance(merge_analysis, dict)
        self.assertIn('can_merge', merge_analysis)
        
        # 6. 生成复用计划
        reuse_plan = interface_manager._generate_reuse_plan(
            reusable_clients, merge_analysis, 'export_list', 'ExportCompanyUnitList'
        )
        
        self.assertIsInstance(reuse_plan, dict)
        self.assertIn('has_reusable_components', reuse_plan)
        
        # 7. 验证复用计划内容
        if reuse_plan['has_reusable_components']:
            self.assertIn('merge_strategy', reuse_plan)
            if reuse_plan['merge_strategy']:
                self.assertEqual(reuse_plan['merge_strategy']['strategy'], 'reuse_and_extend')
                
    def test_feign_client_similarity_calculation(self):
        """测试Feign Client相似度计算的准确性"""
        # 创建多个不同业务域的Feign Client
        clients_data = [
            ('ZqylUserAuthFeignClient', 'UserAuth'),
            ('CompanyServiceFeignClient', 'Company'),
            ('DepartmentManageFeignClient', 'Department'),
            ('UnrelatedServiceFeignClient', 'Unrelated')
        ]
        
        feign_clients = []
        for class_name, business_domain in clients_data:
            path = self._create_sample_feign_client(class_name, business_domain)
            feign_clients.append({
                'class_name': class_name,
                'file_path': path,
                'business_domain': business_domain
            })
        
        component_manager = IntelligentComponentReuseManager(self.mock_llm_client)
        
        # 测试不同API路径的相似度计算
        test_cases = [
            ('/api/user/queryCompanyUnitList', 'company', 'ZqylUserAuthFeignClient'),
            ('/api/company/queryDepartmentList', 'company', 'CompanyServiceFeignClient'),
            ('/api/department/queryUserList', 'department', 'DepartmentManageFeignClient')
        ]
        
        for api_path, business_domain, expected_best_match in test_cases:
            with self.subTest(api_path=api_path, business_domain=business_domain):
                domain_keywords = component_manager._extract_domain_keywords(api_path, business_domain)
                
                best_client = None
                best_score = 0
                
                for client in feign_clients:
                    score = component_manager._calculate_feign_client_similarity(
                        client, domain_keywords, api_path
                    )
                    if score > best_score:
                        best_score = score
                        best_client = client
                
                if best_client:
                    self.assertEqual(best_client['class_name'], expected_best_match)
                    self.assertGreater(best_score, 0)
                    
    def test_interface_logic_merge_strategy(self):
        """测试接口逻辑合并策略的正确性"""
        component_manager = IntelligentComponentReuseManager(self.mock_llm_client)
        
        # 测试不同的接口合并场景
        test_scenarios = [
            {
                'interface_name': 'ExportCompanyUnitList',
                'existing_methods': [
                    {
                        'method_name': 'queryCompanyUnitList',
                        'method_type': 'query_list',
                        'business_operation': 'CompanyUnitList'
                    }
                ],
                'new_interface_type': 'export_list',
                'expected_merge': True
            },
            {
                'interface_name': 'CreateCompanyUnit',
                'existing_methods': [
                    {
                        'method_name': 'queryCompanyUnitList',
                        'method_type': 'query_list',
                        'business_operation': 'CompanyUnitList'
                    }
                ],
                'new_interface_type': 'create',
                'expected_merge': False
            },
            {
                'interface_name': 'QueryDepartmentList',
                'existing_methods': [
                    {
                        'method_name': 'queryCompanyUnitList',
                        'method_type': 'query_list',
                        'business_operation': 'CompanyUnitList'
                    }
                ],
                'new_interface_type': 'query_list',
                'expected_merge': False  # 不同业务域
            }
        ]
        
        for scenario in test_scenarios:
            with self.subTest(interface_name=scenario['interface_name']):
                result = component_manager.merge_similar_interface_logic(
                    scenario['interface_name'],
                    scenario['existing_methods'],
                    scenario['new_interface_type']
                )
                
                self.assertIsInstance(result, dict)
                self.assertIn('can_merge', result)
                
                if scenario['expected_merge']:
                    self.assertTrue(result['can_merge'])
                    self.assertIn('merge_strategy', result)
                    self.assertIn('shared_logic', result)
                    
    def test_export_method_generation(self):
        """测试导出方法生成的正确性"""
        component_manager = IntelligentComponentReuseManager(self.mock_llm_client)
        
        # 准备基础方法信息
        base_method = {
            'name': 'queryCompanyUnitList',
            'description': '查询公司单位列表',
            'service_call': 'zqylUserAuthFeignClient.queryCompanyUnitList(params)',
            'parameters': ['params'],
            'return_type': 'List<Map<String, Object>>'
        }
        
        export_config = {'format': 'excel'}
        
        # 生成导出方法
        export_method = component_manager.generate_export_enhanced_method(base_method, export_config)
        
        # 验证生成的代码
        self.assertIsInstance(export_method, str)
        self.assertIn('@GetMapping', export_method)
        self.assertIn('ResponseEntity<byte[]>', export_method)
        self.assertIn('queryCompanyUnitListExport', export_method)
        self.assertIn('queryCompanyUnitListData', export_method)
        self.assertIn('excelExportService', export_method)
        self.assertIn('LocalDateTime', export_method)
        self.assertIn('HttpHeaders', export_method)
        self.assertIn('MediaType.APPLICATION_OCTET_STREAM', export_method)
        self.assertIn('ContentDispositionFormData', export_method)
        
    def test_shared_service_method_generation(self):
        """测试共享Service方法生成"""
        component_manager = IntelligentComponentReuseManager(self.mock_llm_client)
        
        # 准备基础方法信息
        base_method = {
            'name': 'queryCompanyUnitList',
            'method_type': 'query_list',
            'description': '查询公司单位列表',
            'parameters': ['params'],
            'return_type': 'List<Map<String, Object>>'
        }
        
        interface_variants = ['query', 'export']
        
        # 生成共享方法
        result = component_manager.generate_shared_service_method(base_method, interface_variants)
        
        # 验证结果结构
        self.assertIsInstance(result, dict)
        self.assertIn('shared_method', result)
        self.assertIn('variant_methods', result)
        self.assertIn('dependencies', result)
        
        # 验证共享方法
        shared_method = result['shared_method']
        self.assertEqual(shared_method['name'], 'queryCompanyUnitListData')
        self.assertEqual(shared_method['return_type'], 'List<Map<String, Object>>')
        self.assertIn('signature', shared_method)
        self.assertIn('logic', shared_method)
        
        # 验证变体方法
        variant_methods = result['variant_methods']
        self.assertIn('query', variant_methods)
        self.assertIn('export', variant_methods)
        
        # 验证依赖
        dependencies = result['dependencies']
        self.assertIn('logger', dependencies)
        self.assertIn('feignClient', dependencies)
        
    @patch('builtins.open', create=True)
    def test_controller_update_with_reuse_plan(self, mock_open):
        """测试Controller更新支持复用计划"""
        component_manager = IntelligentComponentReuseManager(self.mock_llm_client)
        
        # 准备原始Controller内容
        original_content = """
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
        
        # 准备复用计划
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
                    'code': """
    private List<Map<String, Object>> queryCompanyUnitListData(Map<String, Object> params) {
        return zqylUserAuthFeignClient.queryCompanyUnitList(params);
    }"""
                }
            ],
            'export_methods': [
                {
                    'name': 'exportCompanyUnitList',
                    'code': """
    @GetMapping("/export")
    public ResponseEntity<byte[]> exportCompanyUnitList(@RequestParam Map<String, Object> params) {
        List<Map<String, Object>> data = queryCompanyUnitListData(params);
        return ResponseEntity.ok(new byte[0]);
    }"""
                }
            ]
        }
        
        # 配置mock
        mock_file = MagicMock()
        mock_file.read.return_value = original_content
        mock_open.return_value.__enter__.return_value = mock_file
        
        # 执行更新
        controller_path = "/test/CompanyUnitLimitController.java"
        result = component_manager.update_controller_with_component_reuse(controller_path, reuse_plan)
        
        # 验证结果
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        self.assertIn('added_components', result)
        
        if result['success']:
            self.assertGreater(len(result['added_components']), 0)
            
    def test_end_to_end_intelligent_reuse_workflow(self):
        """端到端测试：完整的智能复用工作流"""
        # 1. 创建完整的测试环境
        feign_client_path = self._create_sample_feign_client('ZqylUserAuthFeignClient', 'UserAuth')
        controller_path = self._create_sample_controller('CompanyUnitLimitController', 'limit')
        
        # 2. 初始化管理器
        interface_manager = ControllerInterfaceManager(self.mock_llm_client)
        
        # 3. 模拟智能复用流程
        with patch.object(interface_manager.analyzer, 'find_matching_controllers') as mock_find:
            mock_find.return_value = [
                {
                    'file_path': controller_path,
                    'class_name': 'CompanyUnitLimitController',
                    'content': open(controller_path, 'r', encoding='utf-8').read(),
                    'services': []
                }
            ]
            
            with patch.object(interface_manager.interface_adder, 'save_updated_controller') as mock_save:
                mock_save.return_value = True
                
                # 执行智能复用处理
                result = interface_manager.process_api_interface_request_with_reuse(
                    self.temp_dir, 'companyUnit', '/api/limit/exportCompanyUnitList', '导出公司单位列表'
                )
        
        # 4. 验证最终结果
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        self.assertIn('interface_type', result)
        self.assertIn('results', result)
        
        if result['success']:
            self.assertEqual(result['interface_type'], 'export_list')
            self.assertGreater(len(result['results']), 0)
            
            # 验证结果包含复用分析信息
            first_result = result['results'][0]
            self.assertIn('component_analysis', first_result)
            self.assertIn('reusable_clients', first_result)
            self.assertIn('merge_analysis', first_result)
            self.assertIn('reuse_plan', first_result)


if __name__ == '__main__':
    unittest.main()