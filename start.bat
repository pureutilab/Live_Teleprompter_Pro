@echo off
chcp 936 >nul
title 启动抖音直播 AI 提词器

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 当前电脑尚未检测到 Python 环境！
    pause
    exit /b
)

set PLAYWRIGHT_DOWNLOAD_HOST=https://cdn.npmmirror.com/binaries/playwright
set PLAYWRIGHT_CHROMIUM_DOWNLOAD_HOST=https://cdn.npmmirror.com/binaries/chrome-for-testing
set PLAYWRIGHT_BROWSERS_PATH=%LOCALAPPDATA%\ms-playwright

start "" pythonw main.py
if errorlevel 1 (
    python main.py
    pause
)
exit
