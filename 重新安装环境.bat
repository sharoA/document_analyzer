@echo off
echo 正在重新创建Python虚拟环境...
python -m venv analyDesign_env

echo 激活虚拟环境...
call analyDesign_env\Scripts\activate.bat

echo 安装Python依赖...
pip install -r requirements.txt

echo 进入前端目录安装依赖...
cd frontend
npm install
cd ..

echo 环境重新安装完成！
echo 使用以下命令启动项目：
echo 1. 激活虚拟环境: analyDesign_env\Scripts\activate.bat
echo 2. 启动后端: python run.py
echo 3. 启动前端: cd frontend && npm run dev
pause 