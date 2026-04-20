@echo off
setlocal enabledelayedexpansion

set IMAGE_NAME=roxy
set VERSION=%1
if "%VERSION%"=="" set VERSION=latest
set TAG=%IMAGE_NAME%:%VERSION%

echo ==========================================
echo   Roxy Docker Build ^& Deploy Script
echo ==========================================
echo Version: %VERSION%
echo.

echo [1/5] Cleaning up previous builds...
docker compose down --remove-orphans 2>nul

echo [2/5] Building Docker images...
docker compose build --no-cache
if errorlevel 1 (
    echo Build failed!
    exit /b 1
)

echo [3/5] Tagging images...
docker tag roxy-frontend:latest "%TAG%-frontend"
docker tag roxy-backend:latest "%TAG%-backend"

echo [4/5] Starting services...
docker compose up -d

echo [5/5] Waiting for services to be healthy...
timeout /t 5 /nobreak >nul

echo.
echo ==========================================
echo   Deployment Complete!
echo ==========================================
echo.
echo Frontend: http://localhost
echo Backend API: http://localhost:8999
echo API Docs: http://localhost:8999/docs
echo.
echo Useful commands:
echo   View logs:     docker compose logs -f
echo   Stop services: docker compose down
echo   Restart:       docker compose restart
echo.

endlocal
