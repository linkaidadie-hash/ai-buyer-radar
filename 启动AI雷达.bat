@echo off
chcp 65001 >nul
title AI Buyer Radar - 启动中...

echo.
echo ========================================
echo   AI Buyer Radar 启动器
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装 Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [2/3] 检查依赖包...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo [提示] 正在安装依赖包...
    pip install -r requirements.txt
)

echo [3/3] 启动AI Buyer Radar...
echo.
echo 服务地址: http://localhost:8001
echo API文档:   http://localhost:8001/docs
echo.
echo 按 Ctrl+C 可以停止服务
echo.

python main.py

pause