@echo off
chcp 65001 >nul
title 抖音直播 AI 提词器 - EXE 打包工具
echo ========================================================
echo       抖音直播 AI 提词器 - Windows 一键打包 EXE 工具
echo ========================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo 【错误提示】当前电脑尚未检测到 Python 环境！
    echo 请先前往 Python 官网下载并安装 Python (推荐 3.10~3.13):
    echo https://www.python.org/downloads/
    echo.
    echo ★【安装关键步骤】：安装向导第一页务必勾选底部的
    echo   [√] Add python.exe to PATH (添加到环境变量)
    echo 安装完成后，重新双击运行本脚本即可！
    echo.
    pause
    exit /b
)

echo [步骤 1/3] 正在检查并自动安装 Windows 依赖库与打包器...
python -m pip install --upgrade pip
pip install pyinstaller PyQt6 openai playwright

echo.
echo [可选步骤] 正在检查 Playwright 浏览器内核 (用于真实直播网页监听)...
playwright install chromium

echo.
echo [步骤 2/3] 正在执行 PyInstaller 编译打包为 Windows 原生程序...
echo (采用独立文件夹模式，保持 config.py 在同级，方便主播随时修改知识库)
echo.

pyinstaller --noconsole --clean --noconfirm ^
    --name "抖音直播AI提词器" ^
    --add-data "config.py;." ^
    main.py

echo.
echo [步骤 3/3] 正在同步配置文件...
if exist "dist\抖音直播AI提词器" (
    copy /y config.py "dist\抖音直播AI提词器\config.py" >nul
    echo.
    echo ========================================================
    echo   ★ 打包成功完成！
    echo   可执行程序已生成在：
    echo   dist\抖音直播AI提词器\抖音直播AI提词器.exe
    echo.
    echo   【日常使用指南】：
    echo   你可以将 "dist\抖音直播AI提词器" 整个文件夹拷贝到桌面任意位置，
    echo   双击其中的 "抖音直播AI提词器.exe" 即可直接启动！
    echo   右键该 exe 选择【发送到 -> 桌面快捷方式】即可在桌面生成图标。
    echo ========================================================
) else (
    echo.
    echo [!] 打包未能完成，请检查上方的错误提示。
)

echo.
pause
