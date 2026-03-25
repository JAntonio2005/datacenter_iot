# Quickstart - Normalizacion de base de datos SEDCM

## Prerrequisitos
- Docker y Docker Compose
- Backend en Python 3.11
- PostgreSQL (via compose)

## Pasos

1) Levantar infraestructura
- Desde infra/: `docker compose up -d --build`

2) Aplicar migraciones
- Ejecutar el script SQL de migracion en PostgreSQL (se agregara en backend/app/db/migrations)

3) Backfill de datos legacy
- Ejecutar el script de migracion de datos (por definir en tasks)

4) Validar ingesta
- Publicar telemetria y verificar:
  - Insercion en muestras_telemetria
  - Estado actualizado en estado_rack
  - Eventos en auditoria

5) Validar API
- GET /racks
- GET /racks/{zone}/{rack}
- GET /inventory/zones
- GET /inventory/zones/{zone}/racks
- GET /inventory/racks/{rack}/containers

6) Validar cobertura SC-004 (inventario)
- Construir pares esperados (zone,rack) y pares observados desde API.
- Aplicar formula: `cobertura = pares_observados_validos / pares_esperados`.
- Criterio PASS: cobertura=1.0 y required fields=100%.

7) Medir downtime SC-003 (reproducible)
- Capturar timestamps de inicio/fin del cutover y ejecutar:
  - `pwsh scripts/migration/measure_downtime.ps1 -StartTimestamp <ISO8601> -EndTimestamp <ISO8601>`
- PASS cuando `downtime_seconds <= 60`.

8) Medir enlace contenedor SC-001 (24h, >=1000 mensajes)
- Ejecutar `scripts/migration/measure_container_link_rate.sql` en PostgreSQL.
- PASS cuando `status = PASS` y la muestra reporta al menos 1000 mensajes.

9) Cierre de convivencia (FR-013)
- Ejecutar:
  - `pwsh scripts/migration/validate_coexistence_exit.ps1 -SC002Passed $true -SC003Passed $true -CriticalMappingErrors 0`
- Requiere 2 ventanas consecutivas de 30 minutos con 0 errores criticos de mapeo.

## Trazabilidad tarea -> requisito
- FR-005/FR-012: `edge_ack` y correlacion por `command_id`/`correlation_id` en `auditoria`.
- FR-004/FR-013: coexistencia y cutover (`legacy`, `dual`, `normalized`) validado por evidencia de ventanas.
- FR-009/NFR-001: rechazos `telemetry_rejected` para payload invalido sin ejecutar reglas.

## Definition of Done (evidencia)
- Demo reproducible de ingesta, transiciones, `stop_critico` y ACK.
- Evidencia verificable en `auditoria` para `telemetry_ingested`, `telemetry_rejected`, `rack_state_transition`, `command_emitted`, `edge_ack`.
- Reportes ejecutables adjuntos: cobertura SC-004, downtime SC-003 y cierre de convivencia.

## Rollback
- Mantener tablas legacy intactas durante la primera fase.
- Si hay falla, desactivar escritura en tablas nuevas y continuar con legacy.
