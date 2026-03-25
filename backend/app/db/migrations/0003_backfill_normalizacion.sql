-- 0003_backfill_normalizacion.sql
-- FR-004 / SC-002: migracion legacy -> normalizado

WITH zones AS (
    SELECT DISTINCT UPPER(zone) AS codigo
    FROM rack_state
    WHERE zone IS NOT NULL AND zone <> ''
    UNION
    SELECT DISTINCT UPPER(zone) AS codigo
    FROM telemetry_samples
    WHERE zone IS NOT NULL AND zone <> ''
)
INSERT INTO zonas(codigo, nombre)
SELECT z.codigo, CONCAT('Zona ', z.codigo)
FROM zones z
ON CONFLICT (codigo) DO NOTHING;

WITH racks_src AS (
    SELECT DISTINCT UPPER(rs.zone) AS zone_code, UPPER(rs.rack) AS rack_code
    FROM rack_state rs
    WHERE rs.zone IS NOT NULL AND rs.rack IS NOT NULL
    UNION
    SELECT DISTINCT UPPER(ts.zone) AS zone_code, UPPER(ts.rack) AS rack_code
    FROM telemetry_samples ts
    WHERE ts.zone IS NOT NULL AND ts.rack IS NOT NULL
)
INSERT INTO racks(zona_id, codigo, nombre, clave_rack)
SELECT z.id, r.rack_code, CONCAT('Rack ', r.rack_code), CONCAT(r.zone_code, ':', r.rack_code)
FROM racks_src r
JOIN zonas z ON z.codigo = r.zone_code
ON CONFLICT (clave_rack) DO NOTHING;

INSERT INTO contenedores(rack_id, contenedor_id, nombre_contenedor, host, rol, es_critico, estado)
SELECT
    r.id,
    NULLIF(MAX(ts.container_id), ''),
    ts.container_name,
    NULLIF(MAX(ts.host), ''),
    CASE WHEN LOWER(ts.container_name) LIKE '%crit%' THEN 'critico' ELSE 'normal' END,
    CASE WHEN LOWER(ts.container_name) LIKE '%crit%' THEN TRUE ELSE FALSE END,
    'active'
FROM telemetry_samples ts
JOIN racks r ON r.clave_rack = CONCAT(UPPER(ts.zone), ':', UPPER(ts.rack))
WHERE ts.container_name IS NOT NULL AND ts.container_name <> ''
GROUP BY r.id, ts.container_name
ON CONFLICT (rack_id, nombre_contenedor) DO UPDATE
SET contenedor_id = EXCLUDED.contenedor_id,
    host = COALESCE(EXCLUDED.host, contenedores.host);

INSERT INTO estado_rack(clave_rack, rack_id, estado, actualizado_en)
SELECT
    CONCAT(UPPER(rs.zone), ':', UPPER(rs.rack)) AS clave_rack,
    r.id,
    rs.state,
    rs.updated_at
FROM rack_state rs
JOIN racks r ON r.clave_rack = CONCAT(UPPER(rs.zone), ':', UPPER(rs.rack))
ON CONFLICT (clave_rack) DO UPDATE
SET estado = EXCLUDED.estado,
    actualizado_en = EXCLUDED.actualizado_en;

INSERT INTO muestras_telemetria(
    rack_id,
    contenedor_id_ref,
    marca_tiempo,
    host,
    cpu_pct,
    ram_mb,
    temp_c,
    hum_pct,
    power_w,
    net_rx,
    net_tx,
    io_read,
    io_write,
    payload,
    creado_en
)
SELECT
    r.id,
    c.id,
    ts.ts,
    ts.host,
    ts.cpu_pct,
    ts.ram_mb,
    ts.temp_c,
    ts.hum_pct,
    COALESCE(ts.power_w, NULLIF(ts.payload->>'power_w', '')::double precision),
    NULLIF(ts.payload->>'net_rx', '')::double precision,
    NULLIF(ts.payload->>'net_tx', '')::double precision,
    NULLIF(ts.payload->>'io_read', '')::double precision,
    NULLIF(ts.payload->>'io_write', '')::double precision,
    ts.payload,
    ts.created_at
FROM telemetry_samples ts
JOIN racks r ON r.clave_rack = CONCAT(UPPER(ts.zone), ':', UPPER(ts.rack))
LEFT JOIN contenedores c ON c.rack_id = r.id AND c.nombre_contenedor = ts.container_name;

INSERT INTO auditoria(rack_id, tipo_evento, id_correlacion, id_comando, detalles, creado_en)
SELECT
    r.id,
    al.event_type,
    al.correlation_id,
    al.command_id,
    al.details,
    al.created_at
FROM audit_log al
LEFT JOIN racks r ON r.clave_rack = CONCAT(UPPER(al.zone), ':', UPPER(al.rack));

INSERT INTO mensaje_procesado(id_mensaje, fuente, visto_en)
SELECT pm.message_id, pm.source, pm.seen_at
FROM processed_message pm
ON CONFLICT (id_mensaje) DO NOTHING;

-- FR-004 / FR-005: marcadores de no mapeo
INSERT INTO auditoria(rack_id, tipo_evento, detalles)
SELECT
    NULL,
    'backfill_unmapped',
    jsonb_build_object(
        'reason', 'missing_zone_or_rack',
        'legacy_source', 'telemetry_samples',
        'sample_id', ts.id
    )
FROM telemetry_samples ts
WHERE ts.zone IS NULL OR ts.zone = '' OR ts.rack IS NULL OR ts.rack = '';

INSERT INTO auditoria(rack_id, tipo_evento, detalles)
SELECT
    r.id,
    'backfill_unmapped',
    jsonb_build_object(
        'reason', 'duplicate_container_name',
        'legacy_source', 'telemetry_samples',
        'container_name', ts.container_name,
        'rack_key', CONCAT(UPPER(ts.zone), ':', UPPER(ts.rack))
    )
FROM telemetry_samples ts
JOIN racks r ON r.clave_rack = CONCAT(UPPER(ts.zone), ':', UPPER(ts.rack))
WHERE ts.container_name IS NOT NULL AND ts.container_name <> ''
GROUP BY r.id, ts.container_name, ts.zone, ts.rack
HAVING COUNT(*) > 1;
