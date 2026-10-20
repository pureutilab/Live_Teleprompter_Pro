@echo off
chcp 936 >nul
title 抖音直播 AI 提词器 - 环境一键初始化与启动
echo ========================================================
echo       抖音直播 AI 实时提词器 - 一键初始化运行
echo ========================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 电脑尚未检测到 Python 环境！
    echo 请先安装 Python (推荐 3.10-3.12)，安装时勾选 Add python.exe to PATH
    pause
    exit /b
)

set PLAYWRIGHT_DOWNLOAD_HOST=https://cdn.npmmirror.com/binaries/playwright
set PLAYWRIGHT_CHROMIUM_DOWNLOAD_HOST=https://cdn.npmmirror.com/binaries/chrome-for-testing
set PLAYWRIGHT_BROWSERS_PATH=%LOCALAPPDATA%\ms-playwright

echo [1/3] 正在通过国内清华镜像安装必要依赖 (PyQt6, Playwright, OpenAI)...
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
echo.

echo [2/3] 正在通过国内镜像下载 Chromium 浏览器内核 (约 140MB)...
python -m playwright install chromium
echo.

echo [3/3] 初始化完成！正在启动提词器...
start "" pythonw main.py
exit
