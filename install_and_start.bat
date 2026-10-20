@echo off
title 抖音直播 AI 提词器 - 环境安装与启动
echo ========================================================
echo       抖音直播 AI 提词器 - Windows 首次环境配置
echo ========================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 当前电脑尚未检测到 Python 环境！
    echo 请先前往 https://www.python.org/downloads/ 下载安装 Python
    echo 务必勾选 Add python.exe to PATH
    pause
    exit /b
)

echo 1. 正在安装依赖库...
python -m pip install --upgrade pip
pip install -r requirements.txt
echo.

echo 2. 检查 Playwright 浏览器...
playwright install chromium
echo.

echo 3. 正在启动提词器...
start "" pythonw main.py
echo 提词器已在桌面启动！
timeout /t 3 >nul
exit
