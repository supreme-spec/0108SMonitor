@echo off
call :check_python_version
call :start_services
goto :eof

:check_python_version
for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PY_VER=%%i
echo [INFO] %PY_VER%
goto :eof

:start_services
echo [INFO] Starting Smart Security Monitor...

echo [1/3] Starting Python Face Engine...
start "FaceEngine" cmd /k "cd /d D:\smart-security-monitor && venv\Scripts\python.exe face_server.py"
timeout /t 5 >nul

echo [2/3] Starting Node.js API...
start "NodeAPI" cmd /k "cd /d D:\smart-security-monitor && npm run start:ts"
timeout /t 5 >nul

echo [3/3] Starting Vite Dev Server...
start "ViteDev" cmd /k "cd /d D:\smart-security-monitor && npm run dev"
timeout /t 10 >nul

echo [INFO] All services started:
echo   Vite Frontend:  http://localhost:5173
echo   Node.js API:    http://localhost:3000
echo   Face Engine:    http://localhost:8001
echo [INFO] Check health: curl http://localhost:3000/api/health
echo [INFO] Services logs visible in respective terminal windows.
goto :eof
