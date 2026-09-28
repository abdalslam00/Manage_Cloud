@echo off
title SSH Tunnel for Cloud MySQL (Auto-Reconnect)
:start
echo ---------------------------------------------------
echo [%time%] Connecting to SSH Server...
echo ---------------------------------------------------

:: Add keepalive options to prevent disconnects
ssh -o ExitOnForwardFailure=yes -o ServerAliveInterval=60 -o ServerAliveCountMax=3 -L 3307:127.0.0.1:3306 username@your_vps_ip

echo [%time%] Connection lost. Reconnecting in 5 seconds...
timeout /t 5
goto start
