#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_model_calling_debug():
    """测试并调试模型调用过程"""
    
    # 设置详细日志
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("🔍 开始调试模型调用...")
    
    try:
        from src.corder_integration.langgraph.nodes.intelligent_coding_node import IntelligentCodingAgent
        
        # 创建智能编码代理
        agent = IntelligentCodingAgent()
        
        print(f"📊 LLM客户端状态:")
        print(f"  - 客户端: {'已初始化' if agent.llm_client else '未初始化'}")
        print(f"  - 提供商: {agent.llm_provider}")
        print(f"  - 模板+AI: {agent.react_config.get('use_templates', True)}")
        print(f"  - ReAct模式: {agent.react_config.get('enabled', True)}")
        
        if agent.llm_client:
            print(f"✅ LLM客户端可用，尝试简单调用...")
            
            # 测试简单的LLM调用
            test_response = agent.llm_client.chat(
                messages=[{
                    "role": "user", 
                    "content": "请简单回答：你好"
                }],
                temperature=0.1,
                max_tokens=50
            )
            
            if test_response:
                print(f"✅ LLM调用成功: {test_response[:100]}...")
                
                # 测试代码生成流程
                print(f"\n🎯 测试代码生成流程...")
                
                # 模拟一个简单的代码生成请求
                interface_name = "TestExample"
                input_params = [{"name": "id", "type": "String", "description": "ID", "required": True}]
                output_params = {"message": {"type": "String", "description": "响应消息"}}
                description = "测试接口"
                http_method = "GET"
                project_context = {
                    "package_patterns": {"base_package": "com.test"},
                    "project_info": {"is_spring_boot": True, "is_mybatis_plus": False}
                }
                
                print(f"📋 模拟参数:")
                print(f"  - 接口名: {interface_name}")
                print(f"  - HTTP方法: {http_method}")
                print(f"  - 输入参数: {len(input_params)}个")
                print(f"  - 输出参数: {len(output_params)}个")
                
                # 调用代码生成
                try:
                    generated_code = agent._generate_code_with_llm(
                        interface_name, input_params, output_params, description,
                        http_method, project_context
                    )
                    
                    if generated_code:
                        print(f"✅ 代码生成成功!")
                        print(f"📝 生成的代码类型: {list(generated_code.keys())}")
                        
                        # 显示部分代码内容
                        for code_type, content in generated_code.items():
                            preview = content[:200] + "..." if len(content) > 200 else content
                            print(f"\n📄 {code_type}:")
                            print(f"   {preview}")
                    else:
                        print(f"❌ 代码生成返回空结果")
                        
                except Exception as e:
                    print(f"❌ 代码生成失败: {e}")
                    import traceback
                    traceback.print_exc()
                    
            else:
                print(f"❌ LLM调用返回空结果")
        else:
            print(f"❌ LLM客户端未初始化")
            
            # 检查配置文件
            print(f"\n🔧 检查配置文件...")
            import yaml
            try:
                if os.path.exists('config.yaml'):
                    with open('config.yaml', 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f)
                    
                    volcengine_config = config.get('volcengine', {})
                    openai_config = config.get('openai', {})
                    
                    print(f"  - 火山引擎API Key: {'已配置' if volcengine_config.get('api_key') else '未配置'}")
                    print(f"  - OpenAI API Key: {'已配置' if openai_config.get('api_key') else '未配置'}")
                else:
                    print(f"  - config.yaml文件不存在")
            except Exception as e:
                print(f"  - 配置文件读取失败: {e}")
    
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_model_calling_debug() 