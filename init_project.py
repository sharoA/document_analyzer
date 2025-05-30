#!/usr/bin/env python3
"""
analyDesign 后端服务 - 项目初始化脚本
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
        "logs",
        "frontend"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"  ✅ {directory}/")
    
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
    print("1. 设置虚拟环境：")
    print("   - 运行: powershell -ExecutionPolicy Bypass -File setup_env.ps1")
    
    print("\n2. 配置API密钥：")
    print("   - 编辑 src/simple_config.py")
    print("   - 设置火山引擎API密钥")
    
    print("\n3. 安装依赖包：")
    print("   - 激活虚拟环境后运行: pip install -r requirements.txt")
    
    print("\n4. 测试配置：")
    print("   - 运行: python test_setup.py")
    
    print("\n5. 启动后端服务：")
    print("   - 快速启动: 双击 start_backend_quick.bat")
    print("   - 选择模式: 双击 start_backend.bat")
    print("   - 开发调试: 双击 start_backend_dev.bat")
    
    print("\n6. 启动前端服务：")
    print("   - cd frontend")
    print("   - npm install")
    print("   - npm run dev")
    
    print("\n🌟 项目特性：")
    print("  - 前后端分离架构 (Vue 3 + Python Flask)")
    print("  - WebSocket 实时通信")
    print("  - 智能文档分析和AI对话")
    print("  - 支持多种文档格式")
    print("  - 现代化用户界面")

def main():
    """主函数"""
    print("🚀 analyDesign 智能分析系统")
    print("项目初始化脚本")
    print("=" * 50)
    
    # 检查Python版本
    if not check_python_version():
        return
    
    # 创建目录结构
    create_directories()
    
    # 创建基础模板
    create_basic_templates()
    
    # 显示下一步操作
    show_next_steps()

if __name__ == "__main__":
    main() 