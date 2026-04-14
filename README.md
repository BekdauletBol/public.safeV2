# public.safeV3

**Real-time AI-powered video surveillance and people counting system** with analytics, weekly reporting, ROI editor, ML adaptation, and admin dashboard.

---

## Architecture Overview

```
public-safe-v3/
├── backend/                  # FastAPI backend
│   ├── main.py               # App entry point
│   ├── requirements.txt
│   ├── .env.example
│   └── app/
│       ├── api/routes/       # cameras, streams, analytics, reports, roi, websocket, auth
│       ├── core/             # config, logging, security (JWT)
│       ├── db/               # SQLAlchemy async session
│       ├── models/           # Camera, User, Analytics, Report, ROI
│       ├── schemas/          # Pydantic schemas
│       ├── services/         # StreamManager, AnalyticsService, ReportService, WSManager
│       └── workers/          # Celery tasks + async scheduler
├── ml/
│   ├── pipeline/
│   │   ├── detector.py       # YOLOv8 + SimpleTracker (IoU-based ByteTrack-style)
│   │   ├── inference.py      # Per-camera inference workers + orchestrator
│   │   └── adaptive.py       # CPU-adaptive FPS control
│   └── models/               # Place yolov8n.pt here
├── frontend/                 # React + Vite + Tailwind
│   └── src/
│       ├── pages/            # Dashboard, Analytics, Reports, CameraSettings, ROIEditor, Login
│       ├── components/       # CameraCard, AddCameraModal, Layout
│       ├── hooks/            # useWebSocket, useClock
│       ├── services/         # axios API client
│       └── store/            # Zustand state
├── database/
│   └── schema.sql            # Full PostgreSQL schema
└── scripts/
    └── setup.sh              # One-command setup
```

---

## Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+ (with optional TimescaleDB extension)
- Redis (for Celery workers)

---

## 1. Database Setup (PostgreSQL)

### Install PostgreSQL (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Create database
```bash
sudo -u postgres psql
```
```sql
CREATE DATABASE publicsafe;
CREATE USER postgres WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE publicsafe TO postgres;
\q
```

### Run schema
```bash
psql -U postgres -d publicsafe -f database/schema.sql
```

### Optional: TimescaleDB (for time-series performance)
```bash
# Ubuntu
sudo add-apt-repository ppa:timescale/timescaledb-ppa
sudo apt install timescaledb-2-postgresql-14
sudo timescaledb-tune

# Then in psql:
# CREATE EXTENSION IF NOT EXISTS timescaledb;
# SELECT create_hypertable('analytics_records', 'timestamp', if_not_exists => TRUE);
```

---

## 2. Redis Setup

```bash
# Ubuntu
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis

# Test
redis-cli ping  # should return PONG
```

---

## 3. Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — set your DATABASE_URL, SECRET_KEY, etc.

mkdir -p logs reports

# Run
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be live at `http://localhost:8000`
Swagger docs: `http://localhost:8000/docs`

---

## 4. ML Model Setup

YOLOv8n is downloaded automatically on first inference. You can pre-download:

```bash
cd backend
source venv/bin/activate
python3 -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

# Copy to ml/models/
mkdir -p ../ml/models
cp ~/.cache/ultralytics/hub/models/yolov8n.pt ../ml/models/
```

Update `.env`:
```
MODEL_PATH=../ml/models/yolov8n.pt
INFERENCE_DEVICE=cpu    # or 'cuda' for GPU
```

---

## 5. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend available at `http://localhost:3000`

---

## 6. Background Workers (Celery)

```bash
cd backend
source venv/bin/activate

# Worker
celery -A app.workers.celery_app worker --loglevel=info

# Optional: Celery Beat scheduler (for cron-style weekly reports)
celery -A app.workers.celery_app beat --loglevel=info
```

> **Note:** The built-in `asyncio` scheduler in `app/workers/scheduler.py` runs inside the FastAPI process and handles Sunday 23:59 reports without Celery. Celery is optional for distributed workloads.

---

## 7. Create First Admin

```bash
curl -X POST http://localhost:8000/api/auth/create-admin \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","email":"admin@example.com","password":"yourpassword"}'
```

Then log in at `http://localhost:3000/login`.

---

## Camera Setup

### Connect an RTSP Camera
```
rtsp://username:password@192.168.1.100:554/stream
rtsp://192.168.1.100:554/h264/ch1/main/av_stream
rtsp://admin:12345@10.0.0.50:554/Streaming/Channels/101
```

### Connect a Local Webcam
```
0       # First webcam (index 0)
1       # Second webcam (index 1)
```

### Connect an HTTP/MJPEG Camera
```
http://192.168.1.100:8080/video
http://192.168.1.100/mjpg/video.mjpg
```

### Connect an Edge / IP Camera
```
rtsp://10.10.0.5:554/stream1
http://192.168.0.200:8080/?action=stream
```

---

## Usage Guide

### Adding a Camera
1. Click **"Add Camera"** in the Dashboard or Camera Settings page
2. Fill in:
   - **Camera Name**: e.g. "Front Entrance"
   - **Stream URL**: RTSP/HTTP/local index
   - **Address**: Physical location, e.g. "42 Main St, North Door"
3. Click **"Add Camera"** — it instantly appears on the dashboard without page reload

### Viewing the Dashboard
- Grid auto-adjusts based on camera count (1→4→6→many)
- Each card shows: live video feed, location label, live clock, live people count
- Green = live, Red = offline

### ROI Editor
1. Go to **Camera Settings** and click **"ROI"** next to any camera
2. A snapshot of the stream loads in the canvas editor
3. Drag the cyan rectangle to define your counting zone
4. Drag corner/edge handles to resize
5. Click **"Save ROI"** — the backend applies it to ML filtering immediately

### Reports
- Reports auto-generate every **Sunday at 23:59 UTC**
- Trigger manually: click **"Generate Now"** in the Reports page
- Each report includes:
  - Peak hours analysis
  - Total & average traffic per camera
  - AI-generated insights paragraph
  - Full hourly breakdown
- Download as **PDF**
- After generation, weekly stats are reset

### Analytics
- Select camera and time range (6h / 24h / 48h / 7 days)
- Charts: Hourly traffic (area), Daily totals (bar), Peak hour distribution
- Export: **CSV** or **PNG**

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:password@localhost:5432/publicsafe` | Async PostgreSQL URL |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis for Celery |
| `SECRET_KEY` | — | JWT signing key (change in production!) |
| `MODEL_PATH` | `../ml/models/yolov8n.pt` | Path to YOLO weights |
| `INFERENCE_DEVICE` | `cpu` | `cpu` or `cuda` |
| `CONFIDENCE_THRESHOLD` | `0.5` | Detection confidence |
| `REPORTS_DIR` | `./reports` | Where PDF/CSV reports are stored |

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Login → JWT |
| POST | `/api/auth/register` | Register user |
| GET | `/api/cameras/` | List all cameras |
| POST | `/api/cameras/` | Add camera (auto-ID) |
| PUT | `/api/cameras/{id}` | Update camera |
| DELETE | `/api/cameras/{id}` | Remove camera |
| GET | `/api/streams/{id}/feed` | MJPEG stream |
| GET | `/api/streams/{id}/snapshot` | JPEG snapshot |
| GET | `/api/analytics/realtime` | Live counts |
| GET | `/api/analytics/camera/{id}/hourly` | Hourly data |
| GET | `/api/analytics/camera/{id}/peaks` | Peak hours |
| GET | `/api/reports/` | List reports |
| POST | `/api/reports/generate` | Trigger report |
| GET | `/api/reports/{id}/download` | Download PDF |
| GET | `/api/roi/{id}` | Get ROI config |
| POST | `/api/roi/{id}` | Save ROI config |
| WS | `/ws/live` | Real-time WebSocket |

---

## Production Notes

- Set `SECRET_KEY` to a random 64-char string
- Use nginx to reverse-proxy both frontend (`:3000`) and backend (`:8000`)
- Enable TimescaleDB for high-volume analytics
- Use `INFERENCE_DEVICE=cuda` if GPU is available
- Run Celery with `--concurrency=4` for multi-camera load
- Set up log rotation for `backend/logs/`

---

## License

MIT — built for real-world deployment.
