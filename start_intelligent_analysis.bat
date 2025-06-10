@echo off
chcp 65001 >nul
echo ==========================================
echo    智能文档分析系统启动脚本
echo ==========================================
echo.

echo 🔍 检查Python虚拟环境...
if exist "analyDesign_env\Scripts\python.exe" (
    echo ✅ 检测到虚拟环境: analyDesign_env
    set PYTHON_CMD=analyDesign_env\Scripts\python.exe
    set PIP_CMD=analyDesign_env\Scripts\pip.exe
) else (
    echo ⚠️ 未检测到虚拟环境，使用系统Python
    set PYTHON_CMD=python
    set PIP_CMD=pip
)

echo.
echo 正在检查Redis连接...
redis-cli ping >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Redis服务未启动，请先启动Redis服务
    echo 可以使用以下命令启动Redis:
    echo docker run -d --name redis -p 6379:6379 redis:latest
    echo 或者启动本地Redis服务
    pause
    exit /b 1
) else (
    echo ✅ Redis服务正常
)

echo.
echo 🚀 启动智能分析API服务 (端口: 8082)...
echo 使用Python: %PYTHON_CMD%
start "智能分析API" cmd /k "cd /d %~dp0 && %PYTHON_CMD% run_analysis_api.py"

echo.
echo ⏳ 等待API服务启动...
timeout /t 3 /nobreak >nul

echo.
echo 🌐 启动前端服务 (端口: 3000)...
start "前端服务" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ✅ 服务启动完成！
echo.
echo 访问地址：
echo - 前端界面: http://localhost:3000
echo - 后端API:  http://localhost:8082
echo.
echo 按任意键运行API测试...
pause >nul

echo.
echo 🧪 运行API功能测试...
%PYTHON_CMD% test_analysis_api.py

echo.
echo 测试完成！按任意键退出...
pause >nul 