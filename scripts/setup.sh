#!/bin/bash
set -e

echo "=== public.safeV3 Setup ==="

# Backend
echo ">> Setting up backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
mkdir -p logs reports

# Download YOLOv8 model
echo ">> Downloading YOLOv8n model..."
python3 -c "from ultralytics import YOLO; YOLO('yolov8n.pt')" || echo "YOLO download skipped"
mkdir -p ../ml/models
cp ~/.cache/ultralytics/hub/models/yolov8n.pt ../ml/models/ 2>/dev/null || true

deactivate
cd ..

# Frontend
echo ">> Setting up frontend..."
cd frontend
npm install
cd ..

echo ""
echo "=== Setup complete ==="
echo ""
echo "Start commands:"
echo "  Backend:  cd backend && source venv/bin/activate && uvicorn main:app --reload --port 8000"
echo "  Frontend: cd frontend && npm run dev"
echo "  Workers:  cd backend && source venv/bin/activate && celery -A app.workers.celery_app worker --loglevel=info"
echo ""
echo "Create admin (first run):"
echo "  curl -X POST http://localhost:8000/api/auth/create-admin \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"username\":\"admin\",\"email\":\"admin@example.com\",\"password\":\"admin123\"}'"
