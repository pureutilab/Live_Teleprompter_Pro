@echo off
title 安装 Playwright 浏览器内核 (国内镜像加速版)
echo ========================================================
echo   正在通过阿里云镜像高速下载 Chromium 内核...
echo ========================================================
echo.

set PLAYWRIGHT_DOWNLOAD_HOST=https://cdn.npmmirror.com/binaries/playwright/

python -m playwright install chromium
if %errorlevel% neq 0 (
    playwright install chromium
)

echo.
echo ========================================================
echo   ★ 浏览器内核下载安装完成！
echo   现在您可以启动提词器并切换到真实模式了！
echo ========================================================
pause
