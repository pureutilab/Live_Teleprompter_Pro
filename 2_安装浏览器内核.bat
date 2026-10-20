@echo off
chcp 936 >nul
title 安装 Playwright 浏览器内核 (国内镜像极速版)
echo ========================================================
echo       通过国内镜像极速下载 Chromium 浏览器内核
echo ========================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 当前电脑尚未检测到 Python 环境！
    echo 请先前往 Python 官网下载安装 Python (推荐 3.10-3.12):
    echo https://www.python.org/downloads/
    echo 注意：安装时请务必勾选 Add python.exe to PATH
    pause
    exit /b
)

set PLAYWRIGHT_DOWNLOAD_HOST=https://cdn.npmmirror.com/binaries/playwright
set PLAYWRIGHT_CHROMIUM_DOWNLOAD_HOST=https://cdn.npmmirror.com/binaries/chrome-for-testing
set PLAYWRIGHT_BROWSERS_PATH=%LOCALAPPDATA%\ms-playwright

echo 正在通过阿里云镜像高速下载 Chromium (约 140MB)...
echo [提示] 下载通常需要 10-30 秒，请耐心等待出现 100%% 进度条：
echo.

python -m playwright install chromium
if %errorlevel% neq 0 (
    echo.
    echo 正在尝试备用安装命令...
    playwright install chromium
)

echo.
if %errorlevel% equ 0 (
    echo ========================================================
    echo   浏览器内核安装成功！
    echo   现在您可以双击【3_启动提词器.bat】开始使用了！
    echo ========================================================
) else (
    echo ========================================================
    echo   [!] 安装遇到异常，请检查网络连接后重新运行本脚本。
    echo ========================================================
)
echo.
pause
