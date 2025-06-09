@echo off
echo 正在启动前端服务...
cd frontend

echo 检查node_modules是否存在...
if not exist "node_modules" (
    echo node_modules不存在，正在安装依赖...
    npm config set registry https://registry.npmmirror.com
    npm install
    if errorlevel 1 (
        echo npm安装失败，尝试使用yarn...
        yarn install
        if errorlevel 1 (
            echo 依赖安装失败，请手动安装
            pause
            exit /b 1
        )
    )
)

echo 启动前端开发服务器...
npm run dev

pause 