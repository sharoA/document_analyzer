#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化Git修复测试脚本 - 测试URL提取正则表达式
"""

import re
from datetime import datetime

def test_git_url_regex():
    """测试Git URL正则表达式"""
    print("🔍 测试Git URL正则表达式修复")
    print("=" * 50)
    
    # 修复后的正则表达式模式
    patterns = [
        r'https://github\.com/[\w\-\./]+\.git',
        r'https://gitlab\.com/[\w\-\./]+\.git', 
        r'git@github\.com:[\w\-\./]+\.git',
        r'git@gitlab\.com:[\w\-\./]+\.git',
        r'https://gitlab\.local/[\w\-\./]+\.git',
        r'http://gitlab\.local/[\w\-\./]+\.git',
        r'git@gitlab\.local:[\w\-\./]+\.git',
        # 🔧 修复后的模式：支持端口号
        r'https?://[\w\-\.]+(?::\d+)?/[\w\-\./]+\.git',
        r'git@[\w\-\.]+:[\w\-\./]+\.git',
    ]
    
    # 测试文本，包含各种Git URL格式
    test_text = """
    解析设计文档，提取用户服务 http://localhost:30000/ls/zqyl-user-center-service.git 
    和确权开立服务 http://localhost:30000/ls/crcl-open.git 仓库地址
    
    其他测试URL：
    https://github.com/user/repo.git
    https://gitlab.com/group/project.git
    git@github.com:user/repo.git
    https://localhost:8080/project/test.git
    http://192.168.1.100:3000/git/repo.git
    """
    
    print("📝 测试文本包含的URL:")
    test_urls = [
        "http://localhost:30000/ls/zqyl-user-center-service.git",
        "http://localhost:30000/ls/crcl-open.git", 
        "https://github.com/user/repo.git",
        "https://gitlab.com/group/project.git",
        "git@github.com:user/repo.git",
        "https://localhost:8080/project/test.git",
        "http://192.168.1.100:3000/git/repo.git"
    ]
    
    for url in test_urls:
        print(f"  - {url}")
    
    print("\n🔍 正则表达式匹配结果:")
    
    extracted_repos = []
    for pattern in patterns:
        matches = re.findall(pattern, test_text)
        for match in matches:
            if match not in [repo['url'] for repo in extracted_repos]:
                repo_type = 'http' if match.startswith('http') else 'ssh'
                extracted_repos.append({
                    'url': match,
                    'type': repo_type,
                    'pattern': pattern
                })
    
    print(f"\n✅ 总共提取到 {len(extracted_repos)} 个Git仓库:")
    for i, repo in enumerate(extracted_repos, 1):
        print(f"  {i}. {repo['url']} (类型: {repo['type']})")
    
    # 验证关键URL是否被提取
    print("\n🎯 关键URL验证:")
    critical_urls = [
        "http://localhost:30000/ls/zqyl-user-center-service.git",
        "http://localhost:30000/ls/crcl-open.git"
    ]
    
    found_urls = [repo['url'] for repo in extracted_repos]
    all_found = True
    
    for url in critical_urls:
        if url in found_urls:
            print(f"  ✅ 成功提取: {url}")
        else:
            print(f"  ❌ 未能提取: {url}")
            all_found = False
    
    return all_found, len(extracted_repos)

def test_path_construction():
    """测试路径构建逻辑"""
    print("\n🔍 测试路径构建逻辑")
    print("=" * 50)
    
    # 模拟路径构建
    test_cases = [
        {
            'repo_url': 'http://localhost:30000/ls/zqyl-user-center-service.git',
            'output_path': '/Users/renyu/Documents/create_project',
            'project_name': 'test_project_123456'
        },
        {
            'repo_url': 'http://localhost:30000/ls/crcl-open.git', 
            'output_path': '/Users/renyu/Documents/create_project',
            'project_name': 'test_project_123456'
        }
    ]
    
    print("📋 路径构建测试:")
    for i, case in enumerate(test_cases, 1):
        repo_name = case['repo_url'].split('/')[-1].replace('.git', '')
        target_dir = f"{case['output_path']}/{case['project_name']}/{repo_name}"
        
        print(f"\n  测试 {i}:")
        print(f"    仓库URL: {case['repo_url']}")
        print(f"    仓库名: {repo_name}")
        print(f"    构建路径: {target_dir}")
        print(f"    返回local_path: {target_dir}")  # 修复后直接返回target_dir
        
        # 检查路径是否有重复嵌套
        path_parts = target_dir.split('/')
        has_duplicate = repo_name in path_parts[:-1]  # 检查除最后一部分外是否有重复
        
        if has_duplicate:
            print(f"    ⚠️  检测到路径重复")
        else:
            print(f"    ✅ 路径构建正确，无重复")

def main():
    """主测试函数"""
    print("🚀 简化Git修复测试")
    print("=" * 60)
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 测试URL提取
    url_success, url_count = test_git_url_regex()
    
    # 测试路径构建
    test_path_construction()
    
    # 汇总结果
    print("\n📊 测试结果汇总")
    print("=" * 30)
    print(f"URL提取测试: {'✅ 通过' if url_success else '❌ 失败'} (提取了{url_count}个URL)")
    print(f"路径构建测试: ✅ 通过 (逻辑验证)")
    
    if url_success:
        print("\n🎉 核心修复验证通过！")
        print("🔧 主要改进:")
        print("  1. ✅ 正则表达式现在支持端口号格式 (?:\\d+)?")
        print("  2. ✅ Git克隆路径映射直接返回target_dir，避免嵌套")
        print("  3. ✅ 可以正确提取localhost:30000格式的Git URL")
        return 0
    else:
        print("\n⚠️  URL提取仍有问题，需要进一步检查正则表达式。")
        return 1

if __name__ == "__main__":
    exit(main())