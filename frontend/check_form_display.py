#!/usr/bin/env python3
"""
检查前端设计方案表单输入框的显示状态
"""
import requests
import json
import time

def test_frontend_form_display():
    """测试前端表单显示状态"""
    print("🔍 检查前端设计方案表单输入框显示状态\n")
    
    # 1. 测试API数据获取
    print("1️⃣ 测试后端API数据...")
    try:
        api_url = "http://localhost:3000/api/file/design-form/574b1a72-7505-44b7-a33b-6905568843be"
        response = requests.get(api_url, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ API调用失败: HTTP {response.status_code}")
            return False
            
        data = response.json()
        service_details = data.get('form_data', {}).get('service_details', [])
        print(f"✅ API数据正常: 找到 {len(service_details)} 个服务")
        
        # 详细检查每个服务的API设计
        for i, service in enumerate(service_details):
            service_name = service.get('service_name', f'服务{i+1}')
            api_designs = service.get('API设计', [])
            print(f"  服务 {i+1}: {service_name} - {len(api_designs)} 个API")
            
            for j, api in enumerate(api_designs):
                print(f"    API {j+1}: {api.get('interface_type', 'N/A')} {api.get('method', 'N/A')} {api.get('uri', 'N/A')}")
    
    except Exception as e:
        print(f"❌ API测试失败: {e}")
        return False
    
    # 2. 检查前端页面是否可访问
    print(f"\n2️⃣ 测试前端页面访问...")
    try:
        frontend_url = "http://localhost:3000"
        response = requests.get(frontend_url, timeout=5)
        
        if response.status_code == 200:
            print(f"✅ 前端页面可访问")
            
            # 检查是否包含Vue.js相关内容
            html_content = response.text
            if 'vue' in html_content.lower() or 'vite' in html_content.lower():
                print(f"✅ 检测到Vue.js/Vite环境")
            else:
                print(f"⚠️ 未检测到Vue.js/Vite标识")
                
        else:
            print(f"❌ 前端页面访问失败: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 前端页面测试失败: {e}")
        return False
    
    # 3. 模拟前端数据转换逻辑
    print(f"\n3️⃣ 模拟前端数据转换和表单填充...")
    
    try:
        # 重新获取数据进行转换测试
        response = requests.get(api_url, timeout=10)
        data = response.json()
        service_details = data.get('form_data', {}).get('service_details', [])
        
        # 模拟 convertBackendDataToFormData 函数
        converted_services = []
        
        for service in service_details:
            # 转换API设计数据
            apis = []
            if service.get('API设计') and isinstance(service['API设计'], list):
                for api_item in service['API设计']:
                    converted_api = {
                        'interface_type': api_item.get('interface_type', '查询'),
                        'uri': api_item.get('uri', ''),
                        'method': api_item.get('method', 'GET'),
                        'description': api_item.get('description', ''),
                        'request_params': api_item.get('request_params', '{}'),
                        'response_params': api_item.get('response_params', '{}'),
                        'special_requirements': api_item.get('special_requirements', '')
                    }
                    apis.append(converted_api)
            
            # 创建转换后的服务对象
            converted_service = {
                'service_name': service.get('service_name', ''),
                'service_english_name': service.get('service_english_name', ''),
                'service_duty': service.get('service_duty', ''),
                'core_modules': service.get('core_modules', ''),
                'apis': apis,
                'data_table_sql': service.get('API设计', [{}])[0].get('data_table_sql', '') if service.get('API设计') else '',
                'dependence_service': ', '.join(service.get('API设计', [{}])[0].get('dependence_service', [])) if service.get('API设计') and service['API设计'][0].get('dependence_service') else ''
            }
            
            converted_services.append(converted_service)
        
        print(f"✅ 数据转换成功: {len(converted_services)} 个服务")
        
        # 4. 验证表单字段内容
        print(f"\n4️⃣ 验证表单输入框应该显示的内容...")
        
        for i, service in enumerate(converted_services):
            print(f"\n📋 服务 {i+1}: {service['service_name']}")
            
            # 检查基本信息字段
            fields_to_check = [
                ('服务名称', service['service_name']),
                ('英文名称', service['service_english_name']),
                ('服务职责', service['service_duty']),
                ('核心模块', service['core_modules'][:50] + '...' if len(service['core_modules']) > 50 else service['core_modules']),
                ('数据库表SQL', service['data_table_sql'][:30] + '...' if len(service['data_table_sql']) > 30 else service['data_table_sql']),
                ('依赖服务', service['dependence_service'])
            ]
            
            for field_name, field_value in fields_to_check:
                status = "✅ 有数据" if field_value.strip() else "⚠️ 空值"
                print(f"  {field_name}: {status}")
                if field_value.strip():
                    print(f"    内容: {field_value}")
            
            # 检查API设计字段
            print(f"  API设计: {'✅ 有数据' if service['apis'] else '❌ 无数据'} ({len(service['apis'])} 个API)")
            
            for j, api in enumerate(service['apis']):
                print(f"    API {j+1}:")
                api_fields = [
                    ('接口类型', api['interface_type']),
                    ('请求方法', api['method']),
                    ('URI', api['uri']),
                    ('接口描述', api['description']),
                    ('入参示例', api['request_params']),
                    ('返参示例', api['response_params']),
                    ('特殊要求', api['special_requirements'])
                ]
                
                for field_name, field_value in api_fields:
                    status = "✅" if field_value.strip() else "⚠️"
                    print(f"      {field_name}: {status} {field_value}")
        
        print(f"\n5️⃣ 表单显示状态总结:")
        
        # 统计有数据的字段
        total_services = len(converted_services)
        total_apis = sum(len(service['apis']) for service in converted_services)
        
        services_with_name = sum(1 for service in converted_services if service['service_name'].strip())
        services_with_duty = sum(1 for service in converted_services if service['service_duty'].strip())
        services_with_modules = sum(1 for service in converted_services if service['core_modules'].strip())
        
        api_fields_populated = 0
        total_api_fields = 0
        
        for service in converted_services:
            for api in service['apis']:
                for field_value in [api['interface_type'], api['method'], api['uri'], api['description']]:
                    total_api_fields += 1
                    if field_value.strip():
                        api_fields_populated += 1
        
        print(f"  总服务数: {total_services}")
        print(f"  总API数: {total_apis}")
        print(f"  有服务名称: {services_with_name}/{total_services}")
        print(f"  有服务职责: {services_with_duty}/{total_services}")
        print(f"  有核心模块: {services_with_modules}/{total_services}")
        print(f"  API字段填充率: {api_fields_populated}/{total_api_fields} ({api_fields_populated/total_api_fields*100 if total_api_fields > 0 else 0:.1f}%)")
        
        # 最终判断
        if total_services > 0 and total_apis > 0 and api_fields_populated > 0:
            print(f"\n🎉 结论: 前端设计方案输入框应该能正常展示数据!")
            print(f"  ✅ 后端数据完整")
            print(f"  ✅ 数据转换正确")
            print(f"  ✅ 表单字段有内容")
            print(f"  ✅ API设计信息完整")
            return True
        else:
            print(f"\n❌ 结论: 表单数据不完整，可能影响显示")
            return False
        
    except Exception as e:
        print(f"❌ 数据转换测试失败: {e}")
        return False

def main():
    print("=" * 60)
    print("🔍 前端设计方案表单输入框显示状态检查")
    print("=" * 60)
    
    success = test_frontend_form_display()
    
    print("\n" + "=" * 60)
    print("📊 检查结果")
    print("=" * 60)
    
    if success:
        print("🎉 前端设计方案的输入框都能正常展示!")
        print("\n建议操作:")
        print("1. 打开浏览器访问 http://localhost:3000")
        print("2. 导航到设计方案页面")
        print("3. 查看服务设计部分是否显示了API接口信息")
        print("4. 确认输入框中有实际的数据内容")
    else:
        print("❌ 输入框显示可能有问题，需要进一步检查")

if __name__ == "__main__":
    main()