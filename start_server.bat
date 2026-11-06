@echo off
chcp 65001 >nul
title ETF资金看板本地服务器
echo 正在启动 ETF 资金看板本地服务...
echo 访问地址: http://127.0.0.1:8080
echo 访问密码: jinke@dongcai
python "%~dp0server.py"
pause
