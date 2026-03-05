CREATE TABLE IF NOT EXISTS telemetry_samples (
    id BIGSERIAL PRIMARY KEY,
    ts TIMESTAMPTZ NOT NULL,
    zone TEXT NOT NULL,
    rack TEXT NOT NULL,
    host TEXT,
    container_id TEXT,
    container_name TEXT,
    cpu_pct DOUBLE PRECISION,
    ram_mb DOUBLE PRECISION,
    temp_c DOUBLE PRECISION,
    hum_pct DOUBLE PRECISION,
    payload JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rack_state (
    rack_key TEXT PRIMARY KEY,
    zone TEXT NOT NULL,
    rack TEXT NOT NULL,
    state TEXT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    event_type TEXT NOT NULL,
    correlation_id TEXT,
    command_id TEXT,
    zone TEXT,
    rack TEXT,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
