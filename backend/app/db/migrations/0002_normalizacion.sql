-- 0002_normalizacion.sql
-- FR-001 / FR-011: esquema normalizado coexistiendo con tablas legacy

CREATE TABLE IF NOT EXISTS zonas (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(16) NOT NULL UNIQUE,
    nombre VARCHAR(128) NOT NULL
);

CREATE TABLE IF NOT EXISTS racks (
    id SERIAL PRIMARY KEY,
    zona_id INTEGER NOT NULL REFERENCES zonas(id) ON DELETE RESTRICT,
    codigo VARCHAR(16) NOT NULL,
    nombre VARCHAR(128) NOT NULL,
    clave_rack VARCHAR(64) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS contenedores (
    id SERIAL PRIMARY KEY,
    rack_id INTEGER NOT NULL REFERENCES racks(id) ON DELETE CASCADE,
    contenedor_id VARCHAR(128),
    nombre_contenedor VARCHAR(128) NOT NULL,
    host VARCHAR(128),
    rol VARCHAR(32),
    es_critico BOOLEAN NOT NULL DEFAULT FALSE,
    estado VARCHAR(32),
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_contenedor_nombre_por_rack UNIQUE (rack_id, nombre_contenedor)
);

CREATE TABLE IF NOT EXISTS estado_rack (
    clave_rack VARCHAR(64) PRIMARY KEY,
    rack_id INTEGER NOT NULL UNIQUE REFERENCES racks(id) ON DELETE CASCADE,
    estado VARCHAR(32) NOT NULL,
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS muestras_telemetria (
    id BIGSERIAL PRIMARY KEY,
    rack_id INTEGER NOT NULL REFERENCES racks(id) ON DELETE RESTRICT,
    contenedor_id_ref INTEGER REFERENCES contenedores(id) ON DELETE SET NULL,
    marca_tiempo TIMESTAMPTZ NOT NULL,
    host VARCHAR(128),
    cpu_pct DOUBLE PRECISION,
    ram_mb DOUBLE PRECISION,
    temp_c DOUBLE PRECISION,
    hum_pct DOUBLE PRECISION,
    power_w DOUBLE PRECISION,
    net_rx DOUBLE PRECISION,
    net_tx DOUBLE PRECISION,
    io_read DOUBLE PRECISION,
    io_write DOUBLE PRECISION,
    payload JSONB,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS auditoria (
    id BIGSERIAL PRIMARY KEY,
    rack_id INTEGER REFERENCES racks(id) ON DELETE SET NULL,
    tipo_evento VARCHAR(64) NOT NULL,
    id_correlacion VARCHAR(128),
    id_comando VARCHAR(128),
    detalles JSONB,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS mensaje_procesado (
    id_mensaje VARCHAR(128) PRIMARY KEY,
    fuente VARCHAR(64) NOT NULL,
    visto_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_racks_clave ON racks(clave_rack);
CREATE INDEX IF NOT EXISTS idx_mt_rack_ts ON muestras_telemetria(rack_id, creado_en DESC);
CREATE INDEX IF NOT EXISTS idx_auditoria_rack_ts ON auditoria(rack_id, creado_en DESC);
