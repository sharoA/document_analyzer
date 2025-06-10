@echo off
chcp 65001 >nul
echo ==========================================
echo    激活Python虚拟环境
echo ==========================================
echo.

if exist "analyDesign_env\Scripts\activate.bat" (
    echo ✅ 激活虚拟环境: analyDesign_env
    call analyDesign_env\Scripts\activate.bat
    echo.
    echo 虚拟环境已激活！
    echo 当前Python版本:
    python --version
    echo.
    echo 可用命令:
    echo - python run_analysis_api.py  : 启动后端服务
    echo - python test_analysis_api.py : 运行API测试
    echo - deactivate                  : 退出虚拟环境
    echo.
) else (
    echo ❌ 未找到虚拟环境
    echo 请确保虚拟环境位于: analyDesign_env
    echo.
    echo 如需创建虚拟环境，请运行:
    echo python -m venv analyDesign_env
    echo analyDesign_env\Scripts\activate
    echo pip install -r requirements.txt
    echo.
    pause
) 