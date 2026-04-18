@echo off
chcp 65001 >nul
echo ========================================
echo 启动服务...
echo ========================================

:::: 启动 Mitmproxy（独立进程）
echo [1/3] 启动 Mitmproxy...
start /b python mitmproxy_service.py

:::: 等待3秒让 Mitmproxy 启动
timeout /t 3 /nobreak >nul

:::: 启动服务管理器
echo [2/3] 启动服务管理器 (Chrome, Burp)...
start /b python service_manager.py

:::: 等待5秒让服务管理器启动
timeout /t 5 /nobreak >nul

:::: 启动 Flask
echo [3/3] 启动 Flask...
start /b python app.py

echo ========================================
echo 服务已启动！
echo - Mitmproxy: 端口 18081
echo - Chrome监控: 每10秒自动检测
echo - Flask Web: 端口 5001
echo ========================================
echo 按任意键停止所有服务...
pause >nul

:::: 停止除了Burp之外的所有服务
echo 正在关闭服务（保留Burp Suite）...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im chrome.exe >nul 2>&1
echo 服务已关闭，Burp Suite 保持运行
