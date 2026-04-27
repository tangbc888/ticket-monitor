#!/bin/bash
echo "========================================"
echo "   票务监控助手 - 本地开发启动"
echo "========================================"
echo ""

echo "[1/2] 启动后端服务..."
cd backend
pip install -r requirements.txt > /dev/null 2>&1
python run.py &
BACKEND_PID=$!
cd ..

echo "[2/2] 启动前端服务..."
cd frontend
npm install > /dev/null 2>&1
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "后端服务: http://localhost:8000"
echo "前端服务: http://localhost:3000"
echo "API 文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止所有服务"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
wait
