@echo off
REM ============================================================
REM Buyer Radar MVP - Windows Deployment Script
REM ============================================================
echo ==============================================
echo   Buyer Radar MVP - 部署脚本 (Windows)
echo ==============================================

set PROJECT_DIR=%~dp0..
set DB_DIR=%PROJECT_DIR%\database
set LOG_DIR=%PROJECT_DIR%\logs
set PORT=8000

REM --- Pre-flight ---
echo [1/5] 环境检查...
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found. Install Python 3.10+ first.
    pause
    exit /b 1
)

REM --- Create dirs ---
echo [2/5] 创建目录...
if not exist "%DB_DIR%" mkdir "%DB_DIR%"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM --- Install deps ---
echo [3/5] 安装Python依赖...
cd /d "%PROJECT_DIR%"
pip install -r requirements.txt -q
echo    Python 依赖安装完成

REM --- Init database ---
echo [4/5] 初始化数据库...
cd /d "%PROJECT_DIR%"
python -c "import sys; sys.path.insert(0, 'backend'); from services.database import get_conn; conn = get_conn(); conn.execute('SELECT COUNT(*) FROM buyers'); print('Database ready')"
echo    数据库就绪

REM --- Start ---
echo [5/5] 启动服务 (PORT=%PORT%)...
cd /d "%PROJECT_DIR%"
start /B python backend\main.py > "%LOG_DIR%\backend.log" 2>&1
echo    服务已启动
echo    访问地址: http://localhost:%PORT%

echo ==============================================
echo  部署完成
echo ==============================================
pause