@echo off
echo 正在启动 analyDesign 前端开发服务器...
echo.

REM 检查Node.js是否安装
node --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Node.js，请先安装 Node.js
    pause
    exit /b 1
)

REM 检查npm是否可用
npm --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 npm
    pause
    exit /b 1
)

REM 切换到正确的目录
cd /d "%~dp0"

REM 检查package.json是否存在
if not exist package.json (
    echo 错误: 未找到 package.json 文件
    echo 当前目录: %CD%
    pause
    exit /b 1
)

REM 清理可能的端口占用
echo 检查端口 3000 是否被占用...
netstat -ano | findstr :3000 >nul
if not errorlevel 1 (
    echo 警告: 端口 3000 已被占用，尝试终止相关进程...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000') do (
        taskkill /f /pid %%a >nul 2>&1
    )
)

REM 设置环境变量
set NODE_OPTIONS=--max-old-space-size=4096

REM 启动开发服务器
echo 启动开发服务器...
echo 访问地址: http://localhost:3000
echo 按 Ctrl+C 停止服务器
echo.

npm run dev

REM 如果服务器意外退出，暂停以查看错误信息
if errorlevel 1 (
    echo.
    echo 服务器异常退出，错误代码: %errorlevel%
    pause
) 