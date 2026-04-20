@echo off
chcp 65001 >nul
echo ========================================
echo   Roxy Dev Environment Startup
echo ========================================
echo.

echo [1/4] Cleaning __pycache__...
for /d /r backend %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
echo       Done!
echo.

echo [2/4] Installing backend dependencies...
cd backend
pip install -r requirements.txt -q
cd ..
echo       Done!
echo.

echo [3/4] Starting backend server...
cd backend
start "Roxy Backend" cmd /k "conda activate py313 && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8999"
cd ..
echo       Backend starting at http://localhost:8999
echo.

echo       Waiting for backend health...
powershell -NoProfile -Command "$deadline = (Get-Date).AddSeconds(60); while ((Get-Date) -lt $deadline) { try { $response = Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8999/health -TimeoutSec 2; if ($response.StatusCode -eq 200) { exit 0 } } catch { Start-Sleep -Seconds 2 } }; exit 1"
if errorlevel 1 (
    echo       Backend health check timed out. Starting frontend anyway...
) else (
    echo       Backend is healthy.
)
echo.

echo [4/4] Starting frontend server...
cd frontend
start "Roxy Frontend" cmd /k "npm run dev"
cd ..
echo       Frontend starting...
echo.

echo ========================================
echo   All services started!
echo   Backend:  http://localhost:8999
echo   Frontend: http://localhost:5173
echo ========================================
echo.
echo Press any key to exit this window...
pause >nul
