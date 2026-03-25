# Migration Contracts - SEDCM

## Legacy to Normalized Mapping
- rack_state -> estado_rack (match por zone + rack)
- telemetry_samples -> muestras_telemetria (match por zone + rack, y contenedor si es posible)
- audit_log -> auditoria (match por zone + rack cuando exista)
- processed_message -> mensaje_procesado (copy directo)

## Backfill Rules
- Si no hay zona/rack valido, registrar en auditoria con motivo
- Si no hay contenedor valido, dejar contenedor_id_ref null

## Coexistence Exit Criteria (FR-013)
- Modo de escritura soportado: `legacy` -> `dual` -> `normalized`.
- Cierre permitido solo si se cumple SC-002 y SC-003.
- Deben existir 2 ventanas consecutivas de 30 minutos con 0 errores criticos de mapeo.
- Fuente de evidencia: `auditoria` + salida de `scripts/migration/validate_coexistence_exit.ps1`.

## Critical Mapping Error Taxonomy
- `missing_zone_or_rack`: fila legacy sin claves minimas de ubicacion.
- `duplicate_container_name`: nombre de contenedor ambiguo en un mismo rack durante backfill.
- `unknown_rack_live_ingestion`: payload de telemetria recibido para rack inexistente en inventario normalizado.
