@echo off
chcp 936 >nul
title 清理 Windows 提词器缓存与残留进程
echo ========================================================
echo       正在全面清理提词器缓存与历史进程...
echo ========================================================
echo.

echo [1/3] 正在结束可能残留的后台进程 (Python / 浏览器 / 提词器)...
taskkill /F /IM python.exe >nul 2>nul
taskkill /F /IM pythonw.exe >nul 2>nul
taskkill /F /IM node.exe >nul 2>nul
taskkill /F /IM "抖音直播AI提词器.exe" >nul 2>nul
echo [完成] 后台进程已清理。
echo.

echo [2/3] 正在清理 Playwright 下载缓存目录...
if exist "%LOCALAPPDATA%\ms-playwright" (
    rd /s /q "%LOCALAPPDATA%\ms-playwright" >nul 2>nul
    echo [完成] 已清除: %LOCALAPPDATA%\ms-playwright
) else (
    echo [提示] 尚未发现历史 Playwright 缓存。
)
echo.

echo [3/3] 正在清理项目历史构建与临时文件...
if exist "dist" rd /s /q "dist" >nul 2>nul
if exist "build" rd /s /q "build" >nul 2>nul
if exist "__pycache__" rd /s /q "__pycache__" >nul 2>nul
del /q /f *.spec >nul 2>nul
echo [完成] 项目临时文件已清理。
echo.

echo ========================================================
echo   全部旧缓存与残留进程已清理完毕！
echo   接下来请双击运行【2_安装浏览器内核.bat】
echo ========================================================
echo.
pause
