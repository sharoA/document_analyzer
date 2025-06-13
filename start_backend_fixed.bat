@echo off
chcp 65001 >nul
title analyDesign 后端服务启动器

echo.
echo ========================================
echo    analyDesign 后端服务启动器
echo ========================================
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 未安装或未添加到PATH
    echo 请先安装Python并添加到系统PATH
    pause
    exit /b 1
)

:: 显示Python版本
echo ✅ Python 版本:
python --version

:: 检查当前目录是否正确
if not exist "src\apis\api_server.py" (
    echo ❌ 错误：请在项目根目录运行此脚本
    echo 当前目录：%CD%
    echo 应该包含 src\apis\api_server.py 文件
    pause
    exit /b 1
)

:: 检查虚拟环境
if exist "analyDesign_env\Scripts\activate.bat" (
    echo ✅ 发现虚拟环境，正在激活...
    call analyDesign_env\Scripts\activate.bat
) else (
    echo ⚠️  未发现虚拟环境，使用系统Python
)

:: 检查必要的依赖
echo.
echo 🔍 检查依赖包...
python -c "import flask, flask_socketio, flask_cors, requests, loguru" 2>nul
if errorlevel 1 (
    echo ❌ 缺少必要的依赖包
    echo 正在安装依赖...
    pip install -r requirements.txt
    pip install loguru
    if errorlevel 1 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
)

echo ✅ 依赖检查完成

:: 启动服务器
echo.
echo 🚀 启动后端服务...
echo.

python -m src.apis.api_server

pause