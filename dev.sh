#!/bin/bash

echo "========================================"
echo "  Roxy Dev Environment Startup"
echo "========================================"
echo

echo "[1/4] Cleaning __pycache__..."
find backend -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
echo "      Done!"
echo

echo "[2/4] Installing backend dependencies..."
cd backend && pip install -r requirements.txt -q && cd ..
echo "      Done!"
echo

echo "[3/4] Starting backend server..."
cd backend
osascript -e 'tell application "Terminal" to do script "cd \"'$(pwd)'\" && conda activate py313 && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8999"' 2>/dev/null || \
gnome-terminal -- bash -c "cd $(pwd) && source ~/anaconda3/etc/profile.d/conda.sh && conda activate py313 && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8999; exec bash" 2>/dev/null || \
xterm -e "cd $(pwd) && source ~/anaconda3/etc/profile.d/conda.sh && conda activate py313 && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8999; bash" 2>/dev/null || \
bash -c "source ~/anaconda3/etc/profile.d/conda.sh && conda activate py313 && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8999" &
cd ..
echo "      Backend starting at http://localhost:8999"
echo

echo "[3/4] Waiting for backend health..."
backend_ready=false
for _ in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8999/health >/dev/null 2>&1; then
    backend_ready=true
    break
  fi
  sleep 2
done

if [ "$backend_ready" = true ]; then
  echo "      Backend is healthy."
else
  echo "      Backend health check timed out. Starting frontend anyway..."
fi
echo

echo "[4/4] Starting frontend server..."
cd frontend
osascript -e 'tell application "Terminal" to do script "cd \"'$(pwd)'\" && npm run dev"' 2>/dev/null || \
gnome-terminal -- bash -c "cd $(pwd) && npm run dev; exec bash" 2>/dev/null || \
xterm -e "cd $(pwd) && npm run dev; bash" 2>/dev/null || \
npm run dev &
cd ..
echo "      Frontend starting..."
echo

echo "========================================"
echo "  All services started!"
echo "  Backend:  http://localhost:8999"
echo "  Frontend: http://localhost:5173"
echo "========================================"
