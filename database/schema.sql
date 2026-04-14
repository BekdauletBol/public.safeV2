-- public.safeV3 — Full schema
-- Run this manually or via alembic

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cameras (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    stream_url TEXT NOT NULL,
    address VARCHAR(500) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_connected BOOLEAN DEFAULT FALSE,
    latitude FLOAT,
    longitude FLOAT,
    fps INTEGER DEFAULT 15,
    resolution_width INTEGER DEFAULT 1280,
    resolution_height INTEGER DEFAULT 720,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS roi_configs (
    id SERIAL PRIMARY KEY,
    camera_id INTEGER UNIQUE NOT NULL REFERENCES cameras(id) ON DELETE CASCADE,
    x FLOAT DEFAULT 0.0,
    y FLOAT DEFAULT 0.0,
    width FLOAT DEFAULT 1.0,
    height FLOAT DEFAULT 1.0,
    is_active BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS analytics_records (
    id SERIAL PRIMARY KEY,
    camera_id INTEGER NOT NULL REFERENCES cameras(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    people_count INTEGER DEFAULT 0,
    confidence_avg FLOAT DEFAULT 0.0,
    period_type VARCHAR(20) DEFAULT 'realtime'
);

CREATE INDEX IF NOT EXISTS idx_analytics_camera_ts ON analytics_records(camera_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_analytics_ts ON analytics_records(timestamp DESC);

CREATE TABLE IF NOT EXISTS hourly_aggregates (
    id SERIAL PRIMARY KEY,
    camera_id INTEGER NOT NULL REFERENCES cameras(id) ON DELETE CASCADE,
    hour_start TIMESTAMPTZ NOT NULL,
    total_count INTEGER DEFAULT 0,
    avg_count FLOAT DEFAULT 0.0,
    max_count INTEGER DEFAULT 0,
    min_count INTEGER DEFAULT 0,
    sample_count INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_hourly_camera ON hourly_aggregates(camera_id, hour_start DESC);

CREATE TABLE IF NOT EXISTS daily_aggregates (
    id SERIAL PRIMARY KEY,
    camera_id INTEGER NOT NULL REFERENCES cameras(id) ON DELETE CASCADE,
    date TIMESTAMPTZ NOT NULL,
    total_count INTEGER DEFAULT 0,
    avg_count FLOAT DEFAULT 0.0,
    max_count INTEGER DEFAULT 0,
    peak_hour INTEGER
);

CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    report_type VARCHAR(50) DEFAULT 'weekly',
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    file_path VARCHAR(500),
    file_format VARCHAR(10) DEFAULT 'pdf',
    status VARCHAR(20) DEFAULT 'pending',
    ai_insights TEXT,
    is_reset_done BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- TimescaleDB hypertable (optional — run if TimescaleDB is installed)
-- SELECT create_hypertable('analytics_records', 'timestamp', if_not_exists => TRUE);
