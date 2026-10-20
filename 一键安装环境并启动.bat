@echo off
chcp 65001 >nul
title 抖音直播 AI 提词器 - 环境安装与启动
echo ========================================================
echo       抖音直播 AI 提词器 - Windows 首次环境配置
echo ========================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo 【错误提示】当前电脑尚未检测到 Python 环境！
    echo 请先前往 Python 官网下载并安装 Python:
    echo https://www.python.org/downloads/
    echo.
    echo ★ 务必勾选底部的 [√] Add python.exe to PATH
    echo.
    pause
    exit /b
)

echo 1. 正在安装核心依赖 (PyQt6, openai, playwright)...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo 2. 正在检查 Playwright 浏览器内核...
playwright install chromium

echo.
echo 3. 正在启动提词器...
start "" pythonw main.py

echo.
echo 提词器已在桌面启动！本窗口将在 3 秒后自动关闭...
timeout /t 3 >nul
exit
