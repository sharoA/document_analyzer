#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API路径关键字提取的修复效果
"""

def test_extract_api_path_keyword():
    """测试API路径关键字提取逻辑"""
    
    # 模拟原来的逻辑（错误的）
    def old_extract_logic(api_path: str) -> str:
        if not api_path:
            return ""
        path_parts = [part for part in api_path.split('/') if part.strip()]
        if len(path_parts) < 2:
            return ""
        return path_parts[-2]  # 倒数第二个
    
    # 模拟新的逻辑（修复后的）
    def new_extract_logic(api_path: str) -> str:
        if not api_path:
            return ""
        
        path_parts = [part for part in api_path.split('/') if part.strip()]
        if len(path_parts) < 1:
            return ""
        
        raw_keyword = ""
        ignored_prefixes = ['api', 'crcl-open-api', 'v1', 'v2', 'service']
        
        # 从路径中找到第一个有意义的业务关键字
        for part in path_parts:
            if part.lower() not in ignored_prefixes:
                raw_keyword = part
                break
        
        # 如果没找到有意义的关键字，使用最后一个非接口名的部分
        if not raw_keyword and len(path_parts) >= 2:
            raw_keyword = path_parts[-2] if path_parts[-2].lower() not in ignored_prefixes else path_parts[-1]
        elif not raw_keyword:
            raw_keyword = path_parts[-1]
        
        return raw_keyword
    
    # 测试用例
    test_cases = [
        {
            'api_path': '/crcl-open-api/lsLimit/listUnitLimitByCompanyIdExport',
            'expected_keyword': 'lsLimit',
            'description': '问题案例：导出接口'
        },
        {
            'api_path': '/general/multiorgManage/queryCompanyUnitList',
            'expected_keyword': 'general',
            'description': '正常案例：查询接口'
        },
        {
            'api_path': '/api/users',
            'expected_keyword': 'users',
            'description': '简单案例：用户接口'
        },
        {
            'api_path': '/crcl-open-api/lsLimit/listLsLimitMain',
            'expected_keyword': 'lsLimit',
            'description': '其他limit接口'
        }
    ]
    
    print("🧪 测试API路径关键字提取修复效果")
    print("=" * 60)
    
    for case in test_cases:
        api_path = case['api_path']
        expected = case['expected_keyword']
        description = case['description']
        
        old_result = old_extract_logic(api_path)
        new_result = new_extract_logic(api_path)
        
        print(f"\n📋 {description}")
        print(f"   API路径: {api_path}")
        print(f"   期望关键字: {expected}")
        print(f"   ❌ 旧逻辑结果: {old_result}")
        print(f"   ✅ 新逻辑结果: {new_result}")
        
        if new_result == expected:
            print(f"   ✅ 修复成功！")
        else:
            print(f"   ❌ 还需调整")
    
    print("\n" + "=" * 60)
    print("🎯 修复总结:")
    print("   - 旧逻辑：简单取倒数第二个路径片段，容易取到通用前缀")
    print("   - 新逻辑：智能忽略通用前缀，提取有意义的业务关键字")

if __name__ == "__main__":
    test_extract_api_path_keyword()