#!/usr/bin/env python3
"""
简化版HTTP服务器 - 用于启动analyDesign项目
"""

import http.server
import socketserver
import os
import json
import webbrowser
from pathlib import Path

class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.getcwd(), **kwargs)
    
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>analyDesign - 智能需求分析与设计文档生成系统</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .status-card {
            background: rgba(255, 255, 255, 0.2);
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #4CAF50;
        }
        .status-card.warning {
            border-left-color: #FF9800;
        }
        .status-card.error {
            border-left-color: #F44336;
        }
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        .feature-card {
            background: rgba(255, 255, 255, 0.15);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            transition: transform 0.3s ease;
        }
        .feature-card:hover {
            transform: translateY(-5px);
        }
        .btn {
            display: inline-block;
            padding: 12px 24px;
            background: #4CAF50;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin: 10px;
            transition: background 0.3s ease;
        }
        .btn:hover {
            background: #45a049;
        }
        .btn.secondary {
            background: #2196F3;
        }
        .btn.secondary:hover {
            background: #1976D2;
        }
        .info-section {
            margin-top: 30px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 analyDesign</h1>
        <p style="text-align: center; font-size: 1.2em; margin-bottom: 30px;">
            智能需求分析与设计文档生成系统
        </p>
        
        <div class="status-grid">
            <div class="status-card">
                <h3>✅ 项目状态</h3>
                <p>项目已成功启动</p>
                <p>HTTP服务器运行在端口 8000</p>
            </div>
            
            <div class="status-card warning">
                <h3>⚠️ 依赖状态</h3>
                <p>部分AI功能需要配置API密钥</p>
                <p>前端需要Node.js环境</p>
            </div>
            
            <div class="status-card">
                <h3>📁 目录结构</h3>
                <p>uploads/ - 上传文件</p>
                <p>outputs/ - 输出文档</p>
                <p>templates/ - 模板文件</p>
            </div>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="/frontend/" class="btn">🎨 前端界面</a>
            <a href="/uploads/" class="btn secondary">📁 文件管理</a>
            <a href="/outputs/" class="btn secondary">📄 输出文档</a>
        </div>
        
        <div class="feature-grid">
            <div class="feature-card">
                <h3>📄 文档处理</h3>
                <p>支持PDF、Word、文本文档的智能解析</p>
            </div>
            
            <div class="feature-card">
                <h3>🔍 需求分析</h3>
                <p>AI驱动的需求文档智能分析</p>
            </div>
            
            <div class="feature-card">
                <h3>🎨 设计生成</h3>
                <p>自动生成前端和后端设计文档</p>
            </div>
            
            <div class="feature-card">
                <h3>🗄️ 数据库分析</h3>
                <p>智能分析数据库结构和字段映射</p>
            </div>
        </div>
        
        <div class="info-section">
            <h3>🚀 快速开始</h3>
            <ol>
                <li>点击上方"前端界面"按钮访问Web界面</li>
                <li>上传需求文档（PDF、Word、文本格式）</li>
                <li>可选：上传前端截图进行OCR识别</li>
                <li>点击"开始分析"生成设计文档</li>
                <li>在"输出文档"中查看生成的设计文档</li>
            </ol>
            
            <h3>⚙️ 配置说明</h3>
            <p>如需完整功能，请配置以下环境变量：</p>
            <ul>
                <li>DEEPSEEK_API_KEY - DeepSeek AI API密钥</li>
                <li>BUSINESS_DATABASE_URL - 业务数据库连接</li>
                <li>WEAVIATE_URL - 向量数据库地址</li>
            </ul>
        </div>
    </div>
</body>
</html>
            """
            self.wfile.write(html_content.encode('utf-8'))
        else:
            super().do_GET()

def main():
    PORT = 8080
    
    print("🤖 analyDesign 简化版服务器")
    print("=" * 50)
    print(f"🚀 启动HTTP服务器在端口 {PORT}")
    print(f"🌐 访问地址: http://localhost:{PORT}")
    print("📁 当前工作目录:", os.getcwd())
    print("=" * 50)
    
    # 创建必要的目录
    directories = ["uploads", "outputs", "templates", "logs"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    try:
        with socketserver.TCPServer(("", PORT), SimpleHTTPRequestHandler) as httpd:
            print(f"✅ 服务器已启动: http://localhost:{PORT}")
            print("按 Ctrl+C 停止服务器")
            
            # 自动打开浏览器
            try:
                webbrowser.open(f'http://localhost:{PORT}')
                print("🌐 已自动打开浏览器")
            except:
                print("⚠️ 无法自动打开浏览器，请手动访问上述地址")
            
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

if __name__ == "__main__":
    main() 