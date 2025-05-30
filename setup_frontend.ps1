# analyDesign 前端环境设置脚本
Write-Host "正在设置前端环境..." -ForegroundColor Green

# 检查 Node.js 是否安装
try {
    $nodeVersion = node --version
    Write-Host "发现 Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "错误：未找到 Node.js！请先安装 Node.js 16 或更高版本" -ForegroundColor Red
    Write-Host "下载地址: https://nodejs.org/" -ForegroundColor Cyan
    exit 1
}

# 检查 npm 是否可用
try {
    $npmVersion = npm --version
    Write-Host "发现 npm: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "错误：npm 不可用！" -ForegroundColor Red
    exit 1
}

# 进入前端目录
Set-Location frontend

# 安装前端依赖
Write-Host "正在安装前端依赖..." -ForegroundColor Yellow
npm install

if ($LASTEXITCODE -eq 0) {
    Write-Host "前端依赖安装完成！" -ForegroundColor Green
} else {
    Write-Host "前端依赖安装失败！" -ForegroundColor Red
    Set-Location ..
    exit 1
}

# 返回根目录
Set-Location ..

Write-Host "前端环境设置完成！" -ForegroundColor Green
Write-Host "使用以下命令启动前端开发服务器:" -ForegroundColor Cyan
Write-Host "  cd frontend && npm run dev" -ForegroundColor White
Write-Host "或者使用完整应用启动脚本:" -ForegroundColor Cyan
Write-Host "  .\start_full_app.ps1" -ForegroundColor White 