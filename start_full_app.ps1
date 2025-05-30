# analyDesign 完整应用启动脚本
Write-Host "正在启动 analyDesign 完整应用..." -ForegroundColor Green

# 检查虚拟环境
if (-not (Test-Path ".\analyDesign_env\Scripts\python.exe")) {
    Write-Host "错误：虚拟环境未找到！请先运行 setup_env.ps1" -ForegroundColor Red
    exit 1
}

# 检查前端依赖
if (-not (Test-Path ".\frontend\node_modules")) {
    Write-Host "前端依赖未安装，正在安装..." -ForegroundColor Yellow
    Set-Location frontend
    npm install
    Set-Location ..
}

# 启动后端 WebSocket 服务器
Write-Host "正在启动后端 WebSocket 服务器..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\analyDesign_env\Scripts\python.exe src\websocket_server.py"

# 等待后端启动
Start-Sleep -Seconds 3

# 启动前端开发服务器
Write-Host "正在启动前端开发服务器..." -ForegroundColor Yellow
Set-Location frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; npm run dev"
Set-Location ..

Write-Host "应用启动完成！" -ForegroundColor Green
Write-Host "前端地址: http://localhost:3000" -ForegroundColor Cyan
Write-Host "WebSocket 地址: ws://localhost:8765" -ForegroundColor Cyan
Write-Host ""
Write-Host "服务已在后台启动，请查看新打开的窗口" -ForegroundColor Gray