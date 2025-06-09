@echo off
chcp 65001 >nul
echo ========================================
echo       analyDesign 服务状态检查
echo ========================================

echo.
echo 🔍 检查后端API服务器 (端口8082)...
netstat -ano | findstr ":8082" | findstr "LISTENING" >nul
if %errorlevel% == 0 (
    echo ✅ 后端API服务器正在运行 (端口8082)
) else (
    echo ❌ 后端API服务器未运行 (端口8082)
)

echo.
echo 🔍 检查WebSocket服务器 (端口8081)...
netstat -ano | findstr ":8081" | findstr "LISTENING" >nul
if %errorlevel% == 0 (
    echo ✅ WebSocket服务器正在运行 (端口8081)
) else (
    echo ❌ WebSocket服务器未运行 (端口8081)
)

echo.
echo 🔍 检查前端服务器 (端口3000)...
netstat -ano | findstr ":3000" | findstr "LISTENING" >nul
if %errorlevel% == 0 (
    echo ✅ 前端服务器正在运行 (端口3000)
) else (
    echo ❌ 前端服务器未运行 (端口3000)
)

echo.
echo ========================================
echo           服务访问地址
echo ========================================
echo 🌐 前端界面: http://localhost:3000
echo 📡 API接口: http://localhost:8082
echo 🔌 WebSocket: ws://localhost:8081
echo ❤️  健康检查: http://localhost:8082/api/health
echo ========================================
pause 