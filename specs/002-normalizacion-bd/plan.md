# Implementation Plan: Normalizacion de base de datos SEDCM

**Branch**: `002-normalizacion-bd` | **Date**: 2026-03-24 | **Spec**: [specs/002-normalizacion-bd/spec.md](specs/002-normalizacion-bd/spec.md)
**Input**: Feature specification from `/specs/002-normalizacion-bd/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Normalizar la base de datos con entidades maestras (zonas, racks, contenedores) y
relacionarlas con estado, telemetria y auditoria, manteniendo compatibilidad con
payloads MQTT actuales y migrando datos legacy sin perdida de historial.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: FastAPI, SQLAlchemy, Pydantic, paho-mqtt, psycopg2-binary  
**Storage**: PostgreSQL 16  
**Testing**: pytest  
**Target Platform**: Linux containers (Docker Compose)  
**Project Type**: Web service + edge worker + frontend  
**Performance Goals**: Telemetria continua sin interrupciones mayores a 1 minuto durante migracion  
**Constraints**: Compatibilidad con payloads MQTT actuales; migracion incremental  
**Scale/Scope**: 2 zonas, 3 racks por zona, 3 contenedores por rack (MVP)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Thermal Safety Gate**: Plan defines critical threshold behavior and explicit
  `stop_critico` emission/handling path for critical events.
- **Event-Decoupling Gate**: Inter-module communication uses MQTT events and avoids
  direct service-to-service calls (except Dashboard ↔ Backend HTTP/WebSocket).
- **Traceability Gate**: Plan includes auditable event trail (telemetry, alarms,
  commands, ACKs) with persistence strategy in PostgreSQL.
- **Idempotency Gate**: Plan defines deduplication/idempotent handling for MQTT
  duplicates using `command_id` and/or `correlation_id`.
- **Hysteresis Gate**: Plan documents non-flapping state transition logic and
  threshold parameters.

**Gate Status**: PASS. El plan mantiene MQTT como bus, conserva trazabilidad en
PostgreSQL, preserva idempotencia, y no altera reglas de histeresis.

## Project Structure

### Documentation (this feature)

```text
specs/002-normalizacion-bd/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
```text
backend/
├── app/
│   ├── api/
│   ├── db/
│   ├── mqtt/
│   ├── rules/
│   └── services/
└── tests/

edge-executor/
├── app/
│   ├── docker/
│   ├── handlers/
│   └── mqtt/

dashboard/
├── src/

infra/
└── docker-compose.yml

simulators/
├── cadvisor-bridge/
└── environment/

scripts/
└── migration/
```

**Structure Decision**: Web application with backend (FastAPI), edge worker, and
frontend Angular. Data model changes apply to backend/app/db and related services.

## Phase 0: Research Summary

Research focuses on migration strategy and compatibility constraints. See
[specs/002-normalizacion-bd/research.md](specs/002-normalizacion-bd/research.md).

## Phase 1: Design Summary

Data model and contracts defined in:
- [specs/002-normalizacion-bd/data-model.md](specs/002-normalizacion-bd/data-model.md)
- [specs/002-normalizacion-bd/contracts](specs/002-normalizacion-bd/contracts)
- [specs/002-normalizacion-bd/quickstart.md](specs/002-normalizacion-bd/quickstart.md)

**Post-Design Constitution Check**: PASS

## Migration Strategy (Incremental)

- Crear tablas normalizadas en paralelo a las legacy.
- Fase A (pre-backfill): mantener legacy como fuente principal y preparar tablas nuevas.
- Fase B (durante backfill): habilitar escritura dual controlada (legacy + nuevas) para telemetria y auditoria.
- Fase C (post-validacion): usar escritura solo en tablas nuevas cuando SC-002 y SC-003 esten cumplidos.
- Ejecutar backfill controlado con auditoria de filas no mapeadas.
- Mantener tablas legacy intactas hasta validar consistencia.

## Backfill de Datos

- Poblar zonas y racks a partir de `rack_state` y `telemetry_samples`.
- Poblar contenedores desde `telemetry_samples.container_name` + rack.
- Migrar estado y telemetria con FK a rack_id/contenedor_id_ref.
- Registrar en auditoria los casos sin match.

## Adaptacion de Backend

- Resolver rack_id y contenedor_id_ref al ingerir telemetria.
- Actualizar reglas de estado para operar por rack_id.
- Ajustar consultas de API para usar tablas normalizadas.
- Mantener compatibilidad con payloads MQTT (sin cambios de formato).
- Implementar modo de escritura controlado por fase (`legacy`, `dual`, `normalized`) para soportar convivencia y cutover verificable.

## Estrategia de Validacion de Payloads

- Validar esquema esperado de telemetria antes de persistencia.
- Verificar campos obligatorios (`timestamp`, `zone`, `rack`, metricas base requeridas).
- Verificar tipos de datos y rangos numericos.
- Ante payload invalido: registrar `telemetry_rejected`, no insertar en BD y no ejecutar rules engine.

## Estrategia de Logging Estructurado

- Mantener logs en JSON estructurado en backend para rutas de ingesta, reglas, comandos y auditoria.
- Incluir identificadores de trazabilidad cuando existan (`message_id`, `command_id`, `correlation_id`).
- Estandarizar eventos minimos: `telemetry_ingested`, `telemetry_rejected`, `rack_state_transition`, `command_emitted`, `edge_ack`.

## Definition of Done (Constitucion)

- La feature se considera cerrada solo cuando exista demo reproducible documentada en `quickstart.md`.
- Debe existir evidencia verificable de auditoria para ingesta, rechazo, transicion de estado, emision de comando y ACK.
- La validacion final debe incluir trazabilidad por IDs tecnicos (`message_id`, `command_id`, `correlation_id`) cuando aplique.

## Validacion Funcional

- Validar inventario por zona/rack/contenedor.
- Verificar telemetria y estado ligados por FK.
- Confirmar emision `stop_critico`, recepcion de ACK y no flapping.
- Verificar idempotencia ante mensajes duplicados.
- Medir downtime total de ingesta <= 1 minuto.

## Rollback

- Mantener tablas legacy sin cambios durante la migracion.
- Desactivar escritura en tablas nuevas si falla el backfill.
- Volver a usar consultas legacy hasta corregir inconsistencias.

## Criterio de Salida de Convivencia Temporal

- La convivencia se considera completa cuando se cumple SC-002, se cumple SC-003 y no hay errores criticos de mapeo abiertos en 2 ventanas consecutivas de 30 minutos cada una.
- Las tablas legacy se marcan para retiro solo despues de cumplir estos criterios y registrar evidencia en auditoria y quickstart.

## Riesgos y Mitigaciones

- Riesgo: mapeo incompleto de contenedores. Mitigacion: registrar auditoria y permitir contenedor_id_ref null.
- Riesgo: downtime > 1 minuto. Mitigacion: backfill por lotes y ejecucion fuera de pico.
- Riesgo: drift entre tablas legacy y nuevas. Mitigacion: validaciones de conteo y muestreo.

## Complexity Tracking

No constitution violations identified for this feature.
