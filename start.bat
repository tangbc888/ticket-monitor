@echo off
echo ========================================
echo    票务监控助手 - 本地开发启动
echo ========================================
echo.

echo [1/2] 启动后端服务...
cd backend
start "Backend" cmd /c "pip install -r requirements.txt && python run.py"
cd ..

echo [2/2] 启动前端服务...
cd frontend
start "Frontend" cmd /c "npm install && npm run dev"
cd ..

echo.
echo 后端服务: http://localhost:8000
echo 前端服务: http://localhost:3000
echo API 文档: http://localhost:8000/docs
echo.
echo 按任意键退出...
pause > nul
