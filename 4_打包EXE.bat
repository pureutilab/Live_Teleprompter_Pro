@echo off
chcp 936 >nul
title 抖音直播 AI 提词器 - EXE 打包工具
echo ========================================================
echo       抖音直播 AI 提词器 - Windows 一键打包 EXE 工具
echo ========================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 当前电脑尚未检测到 Python 环境！
    echo 请先安装 Python 并勾选 Add python.exe to PATH
    pause
    exit /b
)

set PLAYWRIGHT_DOWNLOAD_HOST=https://cdn.npmmirror.com/binaries/playwright
set PLAYWRIGHT_CHROMIUM_DOWNLOAD_HOST=https://cdn.npmmirror.com/binaries/chrome-for-testing
set PLAYWRIGHT_BROWSERS_PATH=%LOCALAPPDATA%\ms-playwright

echo [1/3] 正在更新依赖库...
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pyinstaller PyQt6 openai playwright
echo.

echo [2/3] 检查浏览器内核...
python -m playwright install chromium
echo.

echo [3/3] 正在执行 PyInstaller 封装打包...
pyinstaller --noconsole --clean --noconfirm --name "抖音直播AI提词器" --add-data "config.py;." --collect-all playwright main.py
echo.

if exist "dist\抖音直播AI提词器" (
    copy /y config.py "dist\抖音直播AI提词器\config.py" >nul
    echo ========================================================
    echo   打包成功完成！
    echo   生成路径: dist\抖音直播AI提词器\抖音直播AI提词器.exe
    echo   直接双击该 exe 即可独立运行提词器！
    echo ========================================================
) else (
    echo [!] 打包未能完成，请检查上方的错误提示。
)

echo.
pause
