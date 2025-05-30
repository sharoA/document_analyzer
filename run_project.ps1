# analyDesign 项目运行脚本
Write-Host "正在使用虚拟环境运行 analyDesign 项目..." -ForegroundColor Green

# 检查虚拟环境是否存在
if (Test-Path ".\analyDesign_env\Scripts\python.exe") {
    Write-Host "虚拟环境已找到" -ForegroundColor Green
    
    # 显示 Python 版本
    Write-Host "Python 版本:" -ForegroundColor Yellow
    & ".\analyDesign_env\Scripts\python.exe" --version
    
    # 运行项目
    Write-Host "正在运行项目..." -ForegroundColor Yellow
    & ".\analyDesign_env\Scripts\python.exe" run.py
} else {
    Write-Host "错误：虚拟环境未找到！请先运行 setup_env.ps1 创建虚拟环境" -ForegroundColor Red
} 