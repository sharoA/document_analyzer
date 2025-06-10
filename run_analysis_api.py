#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
启动智能文档分析API服务
基于Redis存储和HTTP轮询
"""

import sys
import os
import logging
import subprocess

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def activate_virtual_env():
    """激活虚拟环境"""
    venv_path = os.path.join(project_root, 'analyDesign_env')
    
    # 检查虚拟环境是否存在
    if os.path.exists(venv_path):
        # 检查是否已经在虚拟环境中
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            logger.info("已在虚拟环境中运行")
            return True
        
        # Windows系统的虚拟环境激活
        if os.name == 'nt':
            activate_script = os.path.join(venv_path, 'Scripts', 'python.exe')
            if os.path.exists(activate_script):
                logger.info("检测到虚拟环境，重新启动使用虚拟环境...")
                # 使用虚拟环境的Python重新启动当前脚本
                args = [activate_script] + sys.argv
                subprocess.run(args)
                return False  # 表示需要退出当前进程
        # Unix/Linux系统
        else:
            activate_script = os.path.join(venv_path, 'bin', 'python')
            if os.path.exists(activate_script):
                logger.info("检测到虚拟环境，重新启动使用虚拟环境...")
                args = [activate_script] + sys.argv
                subprocess.run(args)
                return False
    
    logger.warning("未找到虚拟环境，使用系统Python")
    return True

def main():
    """主函数"""
    # 首先检查并激活虚拟环境
    if not activate_virtual_env():
        # 如果返回False，说明重新启动了进程，需要退出当前进程
        return 0
    
    try:
        logger.info("正在启动智能文档分析API服务...")
        
        # 导入完整的API服务器（包含聊天和分析功能）
        from src.apis.api_server import app
        
        # 启动服务
        logger.info("启动完整API服务 - http://localhost:8082")
        logger.info("包含功能:")
        logger.info("- 聊天接口: /api/chat")
        logger.info("- 文件上传: /api/file/upload")
        logger.info("- 文档分析: /api/file/parsing/<task_id>")
        logger.info("- 内容分析: /api/file/analyze/<task_id>")
        logger.info("- AI分析: /api/file/ai-analyze/<task_id>")
        logger.info("- 健康检查: /api/health")
        
        app.run(host='0.0.0.0', port=8082, debug=False)
        
    except KeyboardInterrupt:
        logger.info("服务被用户中断")
    except Exception as e:
        logger.error(f"启动失败: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main()) 