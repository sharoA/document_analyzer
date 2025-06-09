# analyDesign 完整环境设置脚本
Write-Host "🚀 analyDesign 环境设置开始..." -ForegroundColor Green
Write-Host "=" * 60

# 检查 Python 是否安装
Write-Host "📋 检查 Python 环境..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "✅ 发现 Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ 错误：未找到 Python！请先安装 Python 3.8 或更高版本" -ForegroundColor Red
    Write-Host "下载地址: https://www.python.org/downloads/" -ForegroundColor Cyan
    exit 1
}

# 检查 Node.js 是否安装
Write-Host "📋 检查 Node.js 环境..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version
    Write-Host "✅ 发现 Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ 错误：未找到 Node.js！请先安装 Node.js 16 或更高版本" -ForegroundColor Red
    Write-Host "下载地址: https://nodejs.org/" -ForegroundColor Cyan
    exit 1
}

# 创建 Python 虚拟环境
Write-Host "🐍 设置 Python 虚拟环境..." -ForegroundColor Yellow
if (Test-Path "analyDesign_env") {
    Write-Host "✅ 虚拟环境已存在" -ForegroundColor Green
} else {
    Write-Host "正在创建虚拟环境..." -ForegroundColor Yellow
    python -m venv analyDesign_env
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 虚拟环境创建成功" -ForegroundColor Green
    } else {
        Write-Host "❌ 虚拟环境创建失败" -ForegroundColor Red
        exit 1
    }
}

# 激活虚拟环境并安装 Python 依赖
Write-Host "📦 安装 Python 依赖..." -ForegroundColor Yellow
& "analyDesign_env\Scripts\Activate.ps1"
pip install --upgrade pip
pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Python 依赖安装完成" -ForegroundColor Green
} else {
    Write-Host "❌ Python 依赖安装失败" -ForegroundColor Red
    exit 1
}

# 设置前端环境
Write-Host "🌐 设置前端环境..." -ForegroundColor Yellow
if (Test-Path "frontend") {
    Set-Location frontend
    
    Write-Host "正在安装前端依赖..." -ForegroundColor Yellow
    npm install
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 前端依赖安装完成" -ForegroundColor Green
    } else {
        Write-Host "❌ 前端依赖安装失败" -ForegroundColor Red
        Set-Location ..
        exit 1
    }
    
    Set-Location ..
} else {
    Write-Host "⚠️ 前端目录不存在，跳过前端环境设置" -ForegroundColor Yellow
}

# 创建必要的目录
Write-Host "📁 创建必要目录..." -ForegroundColor Yellow
$directories = @("uploads", "logs", "outputs", "templates")
foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "✅ 创建目录: $dir" -ForegroundColor Green
    }
}

Write-Host "=" * 60
Write-Host "🎉 环境设置完成！" -ForegroundColor Green
Write-Host ""
Write-Host "📋 使用指南:" -ForegroundColor Cyan
Write-Host "  启动完整服务: python run.py" -ForegroundColor White
Write-Host "  只启动API:    python run.py --mode api" -ForegroundColor White
Write-Host "  只启动WebSocket: python run.py --mode websocket" -ForegroundColor White
Write-Host ""
Write-Host "🌐 前端开发:" -ForegroundColor Cyan
Write-Host "  cd frontend && npm run dev" -ForegroundColor White
Write-Host ""
Write-Host "⚠️ 请确保在 src/simple_config.py 中配置火山引擎API密钥" -ForegroundColor Yellow
Write-Host "=" * 60 