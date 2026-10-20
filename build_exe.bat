@echo off
title 抖音直播 AI 提词器 - EXE 打包工具
echo ========================================================
echo       抖音直播 AI 提词器 - Windows 一键打包 EXE 工具
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

echo [1/3] 正在安装依赖库与打包器...
python -m pip install --upgrade pip
pip install pyinstaller PyQt6 openai playwright
echo.

echo [可选] 检查 Playwright 浏览器内核...
playwright install chromium
echo.

echo [2/3] 正在执行 PyInstaller 打包(已注入 Playwright 驱动)...
pyinstaller --noconsole --clean --noconfirm --name "抖音直播AI提词器" --add-data "config.py;." --collect-all playwright main.py
echo.

echo [3/3] 正在同步配置文件...
if exist "dist\抖音直播AI提词器" (
    copy /y config.py "dist\抖音直播AI提词器\config.py" >nul
    echo ========================================================
    echo   打包成功完成！
    echo   程序生成在: dist\抖音直播AI提词器\抖音直播AI提词器.exe
    echo   直接双击该 exe 即可运行提词器！
    echo ========================================================
) else (
    echo [!] 打包未能完成，请检查上方的错误提示。
)

echo.
pause
