-- SC-001 reproducible measurement (24h window, min 1000 messages)
WITH windowed AS (
    SELECT id, rack_id, contenedor_id_ref
    FROM muestras_telemetria
    WHERE marca_tiempo >= NOW() - INTERVAL '24 hours'
),
agg AS (
    SELECT
        COUNT(*)::numeric AS total_messages,
        SUM(CASE WHEN contenedor_id_ref IS NOT NULL THEN 1 ELSE 0 END)::numeric AS linked_messages
    FROM windowed
)
SELECT
    total_messages,
    linked_messages,
    CASE WHEN total_messages = 0 THEN 0 ELSE ROUND(linked_messages / total_messages, 6) END AS container_link_rate,
    CASE
        WHEN total_messages < 1000 THEN 'INSUFFICIENT_SAMPLE'
        WHEN (linked_messages / NULLIF(total_messages, 0)) >= 0.95 THEN 'PASS'
        ELSE 'FAIL'
    END AS status
FROM agg;
