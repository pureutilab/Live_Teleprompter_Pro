@echo off
title 启动抖音直播 AI 提词器

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 当前电脑尚未检测到 Python 环境！
    pause
    exit /b
)

start "" pythonw main.py
if errorlevel 1 (
    python main.py
    pause
)
exit
