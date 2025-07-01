@echo off
chcp 65001 >nul
echo ========================================
echo          编码智能体启动脚本
echo ========================================
echo.

:: 检查Python环境
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Python未安装或未添加到PATH
    echo 请先安装Python 3.7+
    pause
    exit /b 1
)

:: 检查虚拟环境
if not exist "venv\Scripts\activate.bat" (
    echo [信息] 虚拟环境不存在，正在创建...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [错误] 创建虚拟环境失败
        pause
        exit /b 1
    )
)

:: 激活虚拟环境
echo [信息] 激活虚拟环境...
call venv\Scripts\activate.bat

:: 安装依赖
echo [信息] 检查并安装依赖...
pip install -r requirements.txt >nul 2>&1

:: 检查配置文件
if not exist "config.yaml" (
    echo [错误] 配置文件 config.yaml 不存在
    echo 请确保配置文件存在
    pause
    exit /b 1
)

echo [信息] 环境检查完成
echo.

:: 显示菜单
:menu
echo ========================================
echo          请选择启动方式
echo ========================================
echo 1. 命令行模式 (交互式)
echo 2. API服务模式 (后台服务)
echo 3. 简单示例演示
echo 4. 运行测试
echo 5. 退出
echo ========================================
set /p choice=请输入选项 (1-5): 

if "%choice%"=="1" goto cli_mode
if "%choice%"=="2" goto api_mode
if "%choice%"=="3" goto demo_mode
if "%choice%"=="4" goto test_mode
if "%choice%"=="5" goto exit
goto menu

:cli_mode
echo.
echo [信息] 启动命令行模式...
python coder_agent_main.py
pause
goto menu

:api_mode
echo.
echo [信息] 启动API服务模式...
echo [提示] API服务将在 http://localhost:5000 运行
echo [提示] 按 Ctrl+C 停止服务
python run.py
pause
goto menu

:demo_mode
echo.
echo [信息] 运行简单示例演示...
python coder_agent_examples/simple_usage.py
pause
goto menu

:test_mode
echo.
echo [信息] 运行测试...
python -m pytest tests/test_coder_agent.py -v
pause
goto menu

:exit
echo.
echo [信息] 感谢使用编码智能体!
echo 正在退出...
timeout /t 2 >nul
exit /b 0 