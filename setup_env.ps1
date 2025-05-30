# analyDesign 项目环境设置脚本
Write-Host "正在设置 analyDesign 项目环境..." -ForegroundColor Green

# 检查 Python 是否安装
try {
    $pythonVersion = python --version
    Write-Host "发现 Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "错误：未找到 Python！请先安装 Python 3.10 或更高版本" -ForegroundColor Red
    exit 1
}

# 创建虚拟环境（如果不存在）
if (-not (Test-Path ".\analyDesign_env")) {
    Write-Host "正在创建虚拟环境..." -ForegroundColor Yellow
    python -m venv analyDesign_env
    Write-Host "虚拟环境创建完成" -ForegroundColor Green
} else {
    Write-Host "虚拟环境已存在" -ForegroundColor Green
}

# 升级 pip
Write-Host "正在升级 pip..." -ForegroundColor Yellow
& ".\analyDesign_env\Scripts\python.exe" -m pip install --upgrade pip

# 安装项目依赖
Write-Host "正在安装项目依赖..." -ForegroundColor Yellow
& ".\analyDesign_env\Scripts\python.exe" -m pip install -r requirements.txt

# 测试安装
Write-Host "正在测试安装..." -ForegroundColor Yellow
& ".\analyDesign_env\Scripts\python.exe" -c "import pydantic_settings; print('✓ pydantic_settings 安装成功')"

Write-Host "环境设置完成！" -ForegroundColor Green
Write-Host "使用以下命令运行项目:" -ForegroundColor Cyan
Write-Host "  .\run_project.ps1" -ForegroundColor White 