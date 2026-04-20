@echo off
echo Setting up Roxy Backend...

echo Creating conda environment with Python 3.13...
conda create -n roxy-backend python=3.13 -y

echo Activating environment...
call conda activate roxy-backend

echo Installing dependencies...
pip install -r requirements.txt

echo Copying .env.example to .env...
if not exist .env (
    copy .env.example .env
    echo Created .env file. Please update with your credentials.
)

echo Setup complete!
echo.
echo To start the server:
echo   conda activate roxy-backend
echo   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
