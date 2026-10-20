@echo off
chcp 936 >nul
title 安装/检测 Playwright 浏览器内核 (国内镜像极速版)
echo ========================================================
echo       通过国内镜像检测与下载 Chromium 浏览器内核
echo ========================================================
echo.

echo [1/3] 正在检测当前电脑是否存在系统自带浏览器...
set BROWSER_FOUND=0
if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
    echo [好消息] 检测到系统已预装 Microsoft Edge 浏览器！
    set BROWSER_FOUND=1
)
if exist "C:\Program Files\Microsoft\Edge\Application\msedge.exe" (
    echo [好消息] 检测到系统已预装 Microsoft Edge 浏览器！
    set BROWSER_FOUND=1
)
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    echo [好消息] 检测到系统已预装 Google Chrome 浏览器！
    set BROWSER_FOUND=1
)

if "%BROWSER_FOUND%"=="1" (
    echo.
    echo ========================================================
    echo   您的电脑已自带可用浏览器 (Edge / Chrome)！
    echo   提词器最新版已全面支持免下载直接使用系统浏览器。
    echo   您可以直接关闭此窗口，双击【3_启动提词器.bat】开始使用！
    echo ========================================================
    echo.
    echo 如果您依然希望下载独立的 Playwright Chromium 内核，请按任意键继续...
    pause >nul
)

echo.
echo [2/3] 检查 Python 环境与依赖库...
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 当前电脑尚未检测到 Python 环境！
    echo 请先安装 Python 并勾选 Add python.exe to PATH
    pause
    exit /b
)

python -c "import playwright" 2>nul
if %errorlevel% neq 0 (
    echo 正在自动补充安装 Playwright 依赖库...
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple playwright
)

echo.
echo [3/3] 正在通过国内镜像高速下载 Chromium (约 140MB)...
echo [提示] 下载通常需要 10-30 秒，请耐心等待出现 100%% 进度条：
echo.

set PLAYWRIGHT_DOWNLOAD_HOST=https://cdn.npmmirror.com/binaries/playwright
set PLAYWRIGHT_CHROMIUM_DOWNLOAD_HOST=https://cdn.npmmirror.com/binaries/chrome-for-testing
set PLAYWRIGHT_BROWSERS_PATH=%LOCALAPPDATA%\ms-playwright

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
    echo   [提示] 只要您的电脑有 Edge 或 Chrome 浏览器，
    echo   提词器就可以直接免下载正常运行！
    echo ========================================================
)
echo.
pause
