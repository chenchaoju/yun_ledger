@echo off
chcp 65001 >nul 2>&1
title 云记账 - 快捷启动
echo ========================================
echo   云记账 快捷启动
echo ========================================
echo.

set ROOT=%~dp0..
set BACKEND=%ROOT%\backend
set MOBILE=%ROOT%\mobile
set PYTHON=%BACKEND%\.venv\Scripts\python.exe

:: ---- 查找 Node.js ----
set NODE=
for %%P in (node) do if exist "%%~$PATH:P" set NODE=%%~$PATH:P
if not defined NODE if exist "C:\Users\Administrator\AppData\Local\OpenAI\Codex\bin\node.exe" set NODE=C:\Users\Administrator\AppData\Local\OpenAI\Codex\bin\node.exe
if not defined NODE (
    echo 错误：未找到 Node.js，请安装后重试
    pause
    exit /b 1
)
echo [0/4] Node: %NODE%

:: ---- 1. Python 虚拟环境 ----
if not exist "%PYTHON%" (
    echo [1/4] 创建 Python 虚拟环境...
    py -3 -m venv "%BACKEND%\.venv"
    if errorlevel 1 (
        echo 错误：创建虚拟环境失败，请确认已安装 Python 3
        pause
        exit /b 1
    )
) else (
    echo [1/4] Python 虚拟环境已就绪
)

:: ---- 2. 安装后端依赖 ----
echo [2/4] 安装后端依赖...
"%PYTHON%" -m pip install -r "%BACKEND%\requirements.txt" -q

:: ---- 3. 复制 .env（如果不存在）----
if not exist "%BACKEND%\.env" (
    if exist "%BACKEND%\.env.example" (
        copy "%BACKEND%\.env.example" "%BACKEND%\.env" >nul
        echo [3/4] 已从 .env.example 创建 .env
    ) else (
        echo [3/4] 警告：未找到 .env.example
    )
) else (
    echo [3/4] .env 已就绪
)

:: ---- 4. 数据库迁移 ----
echo [4/4] 运行数据库迁移...
pushd "%BACKEND%"
"%PYTHON%" -m alembic upgrade head
popd

echo.
echo ========================================
echo   启动服务中...
echo ========================================
echo.

:: ---- 启动后端 ----
start "云记账-后端" cmd /k "cd /d "%BACKEND%" && "%PYTHON%" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8024"

:: ---- 安装移动端依赖（首次）----
if not exist "%MOBILE%\node_modules" (
    echo 首次运行，安装移动端依赖...
    cd /d "%MOBILE%" && call npm install 2>nul || echo 跳过npm install，请手动安装
)

:: ---- 启动移动端 ----
set VITE_API_PROXY_TARGET=http://127.0.0.1:8024
set VITE_BIN=%MOBILE%\node_modules\vite\bin\vite.js
if exist "%VITE_BIN%" (
    start "云记账-移动端" cmd /k "cd /d "%MOBILE%" && set VITE_API_PROXY_TARGET=http://127.0.0.1:8024 && "%NODE%" "%VITE_BIN%" --host 0.0.0.0 --port 8023"
) else (
    start "云记账-移动端" cmd /k "cd /d "%MOBILE%" && set VITE_API_PROXY_TARGET=http://127.0.0.1:8024 && npm run dev -- --host 0.0.0.0 --port 8023"
)

echo.
echo ========================================
echo   启动完成！
echo ========================================
echo.
echo   移动端：  http://127.0.0.1:8023/
echo   后端API： http://127.0.0.1:8024/docs
echo.
echo   提示：请确认 MySQL 已启动
echo   关闭此窗口不会停止服务
echo   需手动关闭弹出的两个窗口
echo ========================================
pause