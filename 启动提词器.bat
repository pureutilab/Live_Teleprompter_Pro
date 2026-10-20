@echo off
chcp 65001 >nul
title 启动抖音直播 AI 提词器

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo 【错误提示】当前电脑尚未检测到 Python 环境！
    echo 请先前往 https://www.python.org/downloads/ 下载并安装 Python。
    echo 务必勾选 [√] Add python.exe to PATH
    pause
    exit /b
)

start "" pythonw main.py
if errorlevel 1 (
    echo [提示] 正在使用标准 python 模式启动...
    python main.py
    pause
)
exit
