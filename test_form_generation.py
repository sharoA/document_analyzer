#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试表单数据生成流程
"""

import requests
import json
import base64
import time

def test_form_generation():
    """测试表单数据生成流程"""
    
    # 1. 创建测试文档内容
    test_document = """
一局对接链数优化测试项目

需求文档

| 版本 | V0.1 |
| --- | --- |
| 撰写人 | 测试用户 |
| 类型 | 系统对接 |

# 项目介绍

## 需求背景

本项目旨在优化一局对接链数的系统功能，提升用户体验和系统性能。

## 建设目标及路线

- 调整接口校验逻辑，兼容企业重推数据的场景
- 新增组织单元额度管理功能
- 优化现有查询和统计功能

# 功能需求说明

## 接口校验规则调整

本期对【确权业务申请】接口中关于bizSerialNo的校验规则进行调整。

## 新增组织单元额度功能

支持用户查询当前登录企业下的具体组织单元的链数额度、云信额度明细。

### 功能说明

- 新增额度查询功能
- 修改额度管理界面
- 删除过期数据功能
- 查询筛选和统计功能
"""
    
    # 2. 将文档内容编码为base64
    file_content = test_document.encode('utf-8')
    base64_content = base64.b64encode(file_content).decode('utf-8')
    
    # 3. 构建请求数据
    request_data = {
        "file_info": {
            "name": "测试表单生成文档.txt",
            "type": "text/plain",
            "content": base64_content
        }
    }
    
    print("🚀 开始测试表单数据生成流程...")
    
    # 4. 发送V2完整分析请求
    print("📤 发送V2完整分析请求...")
    response = requests.post(
        "http://localhost:8082/api/v2/analysis/start",
        json=request_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code != 200:
        print(f"❌ 启动分析失败: {response.status_code}")
        print(response.text)
        return
    
    result = response.json()
    if not result.get('success'):
        print(f"❌ 启动分析失败: {result.get('error')}")
        return
    
    task_id = result['task_id']
    print(f"✅ 分析任务启动成功: {task_id}")
    
    # 5. 等待分析完成
    print("⏳ 等待分析流程完成...")
    max_wait = 300  # 最多等待5分钟
    wait_time = 0
    
    while wait_time < max_wait:
        # 检查进度
        progress_response = requests.get(f"http://localhost:8082/api/v2/analysis/progress/{task_id}")
        
        if progress_response.status_code == 200:
            progress = progress_response.json()
            overall_status = progress.get('overall_status', 'unknown')
            overall_progress = progress.get('overall_progress', 0)
            
            print(f"📊 分析进度: {overall_progress}% - 状态: {overall_status}")
            
            if overall_status == 'completed':
                print("🎉 分析流程完成!")
                break
            elif overall_status == 'failed':
                print(f"❌ 分析流程失败: {progress.get('error', '未知错误')}")
                return
        
        time.sleep(10)  # 等待10秒
        wait_time += 10
    
    if wait_time >= max_wait:
        print("⏰ 等待超时，分析可能仍在进行中")
        return
    
    # 6. 测试获取表单数据
    print("📋 测试获取表单数据...")
    form_response = requests.get(f"http://localhost:8082/api/file/design-form/{task_id}")
    
    if form_response.status_code == 200:
        form_result = form_response.json()
        if form_result.get('success'):
            print("✅ 表单数据获取成功!")
            form_data = form_result.get('form_data', {})
            print(f"📊 表单字段数: {len(form_data)}")
            print(f"🎯 项目名称: {form_data.get('project_name', '未设置')}")
            print(f"🏗️ 服务数量: {form_data.get('service_numbers', 0)}")
            print(f"💾 数据资源数: {form_data.get('data_resources', 0)}")
            
            # 输出关键字段
            print("\n📝 表单数据结构:")
            for key in ['project_name', 'service_numbers', 'data_resources']:
                if key in form_data:
                    print(f"  - {key}: {form_data[key]}")
            
            return True
        else:
            print(f"❌ 获取表单数据失败: {form_result.get('error')}")
    else:
        print(f"❌ 表单数据API调用失败: {form_response.status_code}")
        print(form_response.text)
    
    return False

if __name__ == "__main__":
    success = test_form_generation()
    if success:
        print("\n🎉 表单数据生成流程测试成功!")
    else:
        print("\n❌ 表单数据生成流程测试失败!")