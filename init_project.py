#!/usr/bin/env python3
"""
智能需求分析系统 - 项目初始化脚本
"""

import os
import sys
import shutil
from pathlib import Path

def create_directories():
    """创建必要的目录结构"""
    print("📁 创建项目目录结构...")
    
    directories = [
        "src",
        "templates", 
        "uploads",
        "outputs",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"  ✅ {directory}/")
    
    return True

def setup_env_file():
    """设置环境配置文件"""
    print("⚙️ 设置环境配置文件...")
    
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if env_example.exists() and not env_file.exists():
        shutil.copy(env_example, env_file)
        print("  ✅ .env 文件已创建")
    elif env_file.exists():
        print("  ℹ️ .env 文件已存在")
    else:
        print("  ⚠️ .env.example 文件不存在")
    
    return True

def create_basic_templates():
    """创建基础模板文件"""
    print("📝 创建基础模板文件...")
    
    backend_template = """# 后端详细设计文档模板

## 1. 系统概述
- 项目名称：{project_name}
- 开发团队：{team_name}
- 文档版本：1.0

## 2. 功能模块设计
{modules_design}

## 3. API接口设计
{api_design}

## 4. 数据库设计
{database_design}

## 5. 技术架构
{tech_architecture}
"""

    frontend_template = """# 前端详细设计文档模板

## 1. 界面设计概述
- 项目名称：{project_name}
- 设计风格：{design_style}
- 文档版本：1.0

## 2. 页面结构设计
{page_structure}

## 3. 组件设计
{component_design}

## 4. 交互设计
{interaction_design}

## 5. 响应式设计
{responsive_design}
"""
    
    # 写入模板文件
    with open("templates/backend_design_template.md", "w", encoding="utf-8") as f:
        f.write(backend_template)
    
    with open("templates/frontend_design_template.md", "w", encoding="utf-8") as f:
        f.write(frontend_template)
    
    print("  ✅ 后端设计模板已创建")
    print("  ✅ 前端设计模板已创建")
    
    return True

def check_python_version():
    """检查Python版本"""
    print("🐍 检查Python版本...")
    
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"  ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"  ❌ Python版本过低: {version.major}.{version.minor}.{version.micro}")
        print("  💡 建议使用Python 3.8或更高版本")
        return False

def show_next_steps():
    """显示下一步操作指南"""
    print("\n🎯 项目初始化完成！")
    print("\n📋 接下来的步骤：")
    print("1. 编辑 .env 文件，配置必要的参数：")
    print("   - DEEPSEEK_API_KEY=your_api_key_here")
    print("   - BUSINESS_DATABASE_URL=your_database_url")
    print("   - COMPANY_NAME=您的公司名称")
    
    print("\n2. 安装依赖包：")
    print("   - 运行: python setup_pip_mirror.py")
    print("   - 或者: pip install streamlit python-dotenv pydantic")
    
    print("\n3. 测试配置：")
    print("   - 运行: python test_setup.py")
    
    print("\n4. 启动系统：")
    print("   - 运行: python run.py")
    print("   - 或者: streamlit run src/enhanced_app.py")
    
    print("\n🌟 项目特性：")
    print("  - 支持多种文档格式分析")
    print("  - 智能需求分析和关键词提取")
    print("  - 自动生成设计文档")
    print("  - 支持前端截图分析")

def main():
    """主函数"""
    print("🚀 智能需求分析与设计文档生成系统")
    print("项目初始化脚本")
    print("=" * 50)
    
    # 检查Python版本
    if not check_python_version():
        return
    
    # 创建目录结构
    create_directories()
    
    # 设置环境文件
    setup_env_file()
    
    # 创建基础模板
    create_basic_templates()
    
    # 显示下一步操作
    show_next_steps()

if __name__ == "__main__":
    main() 