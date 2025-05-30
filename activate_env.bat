@echo off
echo 正在激活 analyDesign 虚拟环境...
call analyDesign_env\Scripts\activate.bat
echo 虚拟环境已激活！
echo 当前 Python 版本：
python --version
echo 当前 pip 版本：
pip --version
echo.
echo 要退出虚拟环境，请输入: deactivate
cmd /k 