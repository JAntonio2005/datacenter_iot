CREATE TABLE IF NOT EXISTS processed_message (
    message_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    seen_at TIMESTAMPTZ DEFAULT NOW()
);
