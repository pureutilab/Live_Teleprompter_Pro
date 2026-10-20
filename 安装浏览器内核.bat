@echo off
title 安装 Playwright 浏览器内核
echo ========================================================
echo   正在自动下载 Chromium 浏览器内核 (仅需执行一次)...
echo ========================================================
echo.

python -m playwright install chromium
if %errorlevel% neq 0 (
    playwright install chromium
)

echo.
echo ========================================================
echo   内核下载安装完毕！
echo   请重新打开提词器并切换到真实网页监听即可！
echo ========================================================
pause
