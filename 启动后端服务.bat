@echo off
chcp 65001 >nul
title analyDesign 后端服务

echo 🚀 启动 analyDesign 后端服务...
echo.

REM 激活虚拟环境
call .\analyDesign_env\Scripts\activate.bat

REM 启动服务
.\start_back.bat

pause 