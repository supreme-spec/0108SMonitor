@echo off
cd /d "%~dp0"
echo Starting 0108SMonitor Development Environment...
call npm install
call npm run dev
pause
