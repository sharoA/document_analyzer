#!/usr/bin/env python3
"""
智能文档分析系统测试脚本
"""

import requests
import json
import time
import uuid

# API基础URL
API_BASE_URL = "http://localhost:8082/api/v2"

def test_health_check():
    """测试健康检查接口"""
    print("🔍 测试健康检查接口...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 健康检查通过: {data['status']}")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False

def test_analysis_pipeline():
    """测试完整分析流水线"""
    print("\n🚀 测试完整分析流水线...")
    
    # 测试数据
    test_data = {
        "execution_mode": "automatic",
        "file_name": "test_document.txt",
        "file_content": """
        # 系统需求文档
        
        ## 概述
        本系统是一个用户管理系统，需要支持用户注册、登录、权限管理等功能。
        
        ## 功能需求
        1. 用户注册功能
        2. 用户登录功能
        3. 权限管理功能
        4. 数据导出功能
        
        ## 技术要求
        - 使用微服务架构
        - 支持高并发访问
        - 数据安全性要求高
        """
    }
    
    try:
        # 1. 启动分析
        print("📤 启动分析任务...")
        response = requests.post(f"{API_BASE_URL}/analysis/start", json=test_data)
        
        if response.status_code != 200:
            print(f"❌ 启动分析失败: {response.status_code}")
            print(response.text)
            return False
        
        result = response.json()
        if not result.get("success"):
            print(f"❌ 启动分析失败: {result.get('error')}")
            return False
        
        task_id = result.get("task_id")
        print(f"✅ 分析任务已启动，任务ID: {task_id}")
        
        # 2. 监控进度
        print("📊 监控分析进度...")
        max_attempts = 30  # 最多等待30次（60秒）
        attempt = 0
        
        while attempt < max_attempts:
            time.sleep(2)  # 等待2秒
            attempt += 1
            
            # 查询进度
            progress_response = requests.get(f"{API_BASE_URL}/analysis/progress/{task_id}")
            
            if progress_response.status_code == 200:
                progress_data = progress_response.json()
                if progress_data.get("success"):
                    data = progress_data.get("data", {})
                    progress = data.get("progress", {})
                    current_stage = data.get("current_stage", "")
                    
                    print(f"📈 进度更新 (第{attempt}次查询):")
                    print(f"   当前阶段: {current_stage}")
                    print(f"   文档解析: {progress.get('document_parsing', 0)}%")
                    print(f"   内容分析: {progress.get('content_analysis', 0)}%")
                    print(f"   AI分析: {progress.get('ai_analysis', 0)}%")
                    
                    # 检查是否完成
                    if all(progress.get(stage, 0) == 100 for stage in ['document_parsing', 'content_analysis', 'ai_analysis']):
                        print("✅ 所有阶段已完成!")
                        break
                else:
                    print(f"⚠️  获取进度失败: {progress_data.get('error')}")
            else:
                print(f"⚠️  查询进度失败: {progress_response.status_code}")
        
        if attempt >= max_attempts:
            print("⏰ 等待超时，但继续尝试获取结果...")
        
        # 3. 获取结果
        print("\n📋 获取分析结果...")
        result_response = requests.get(f"{API_BASE_URL}/analysis/result/{task_id}")
        
        if result_response.status_code == 200:
            result_data = result_response.json()
            if result_data.get("success"):
                data = result_data.get("data", {})
                print("✅ 成功获取分析结果!")
                print(f"   任务状态: {data.get('status')}")
                print(f"   完成时间: {data.get('timestamp')}")
                
                # 显示摘要信息
                summary = data.get("summary", {})
                if summary:
                    print("\n📊 分析摘要:")
                    doc_info = summary.get("document_info", {})
                    print(f"   文件名: {doc_info.get('file_name')}")
                    print(f"   文件大小: {doc_info.get('file_size')} 字节")
                    
                    analysis_summary = summary.get("analysis_summary", {})
                    print(f"   总变更数: {analysis_summary.get('total_changes', 0)}")
                    print(f"   新增功能: {analysis_summary.get('new_features_count', 0)}")
                    print(f"   修改功能: {analysis_summary.get('modified_features_count', 0)}")
                
                return True
            else:
                print(f"❌ 获取结果失败: {result_data.get('error')}")
                return False
        else:
            print(f"❌ 获取结果请求失败: {result_response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def test_manual_mode():
    """测试手动模式"""
    print("\n🔧 测试手动模式...")
    
    test_data = {
        "execution_mode": "manual",
        "file_name": "manual_test.txt",
        "file_content": "这是手动模式测试文档。"
    }
    
    try:
        # 启动手动模式任务
        response = requests.post(f"{API_BASE_URL}/analysis/start", json=test_data)
        
        if response.status_code != 200:
            print(f"❌ 启动手动任务失败: {response.status_code}")
            return False
        
        result = response.json()
        if not result.get("success"):
            print(f"❌ 启动手动任务失败: {result.get('error')}")
            return False
        
        task_id = result.get("task_id")
        print(f"✅ 手动任务已创建，任务ID: {task_id}")
        
        # 手动执行第一个阶段
        stage_data = {
            "task_id": task_id,
            "stage": "document_parsing"
        }
        
        stage_response = requests.post(f"{API_BASE_URL}/analysis/stage", json=stage_data)
        
        if stage_response.status_code == 200:
            stage_result = stage_response.json()
            if stage_result.get("success"):
                print("✅ 手动执行文档解析阶段成功")
                return True
            else:
                print(f"❌ 手动执行阶段失败: {stage_result.get('error')}")
                return False
        else:
            print(f"❌ 手动执行阶段请求失败: {stage_response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ 手动模式测试异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 智能文档分析系统测试")
    print("=" * 50)
    
    # 测试健康检查
    if not test_health_check():
        print("\n❌ 系统未正常运行，请检查API服务器")
        return
    
    # 测试完整分析流水线
    pipeline_success = test_analysis_pipeline()
    
    # 测试手动模式
    manual_success = test_manual_mode()
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    print(f"   健康检查: ✅")
    print(f"   自动分析: {'✅' if pipeline_success else '❌'}")
    print(f"   手动模式: {'✅' if manual_success else '❌'}")
    
    if pipeline_success and manual_success:
        print("\n🎉 所有测试通过！系统运行正常。")
    else:
        print("\n⚠️  部分测试失败，请检查系统状态。")

if __name__ == "__main__":
    main() 