# Implementation Plan: SEDCM MVP Event-Driven Monitoring and Thermal Mitigation

**Branch**: `001-sedcm-mvp` | **Date**: 2026-03-04 | **Spec**: /specs/001-sedcm-mvp/spec.md
**Input**: Feature specification from `/specs/001-sedcm-mvp/spec.md`

## Summary

Implementar un MVP distribuido para monitoreo y control de un datacenter simulado con Docker: ingesta de telemetría por MQTT, fusión/correlación de señales cAdvisor + ambientales por `zone/rack/timestamp`, persistencia en PostgreSQL, motor de reglas con histéresis, emisión de `stop_critico`, ejecución de stop por labels vía Docker API local y dashboard en tiempo real por WebSockets.

## Technical Context

**Language/Version**: Python 3.11 (backend y edge), TypeScript 5.x (dashboard)
**Primary Dependencies**: FastAPI, paho-mqtt, SQLAlchemy, psycopg2-binary, websockets; React + Vite
**Storage**: PostgreSQL
**Testing**: pytest + pytest-asyncio; pruebas de integración con Docker Compose
**Target Platform**: Docker Compose local (Linux containers)
**Project Type**: Web application + event-driven services
**Performance Goals**: actualización de dashboard <= 2s desde recepción de telemetría crítica
**Constraints**: desacoplamiento por MQTT, idempotencia de eventos, histéresis obligatoria, fusión de telemetría cAdvisor+ambiental, logs JSON
**Scale/Scope**: 2 zonas, 6 racks, 18 contenedores simulados

## Constitution Check

- **Thermal Safety Gate**: Definido `T2=45°C` y comando `stop_critico` con ACK obligatorio.
- **Event-Decoupling Gate**: Backend, simuladores y edge se comunican por MQTT; dashboard por HTTP/WebSocket al backend.
- **Traceability Gate**: Telemetría, comandos, ACKs y cambios de estado persisten en auditoría PostgreSQL.
- **Telemetry Fusion Gate**: La evaluación de reglas usa telemetría combinada cAdvisor+ambiental correlacionada por `zone/rack/timestamp`.
- **Idempotency Gate**: Procesamiento deduplicado por `command_id`/`correlation_id`.
- **Hysteresis Gate**: Umbrales `T1=40`, `T2=45`, `Treset=42`, `margen_hist=1` para anti-flapping.

## Project Structure

### Documentation (this feature)

```text
specs/001-sedcm-mvp/
├── plan.md
├── spec.md
├── tasks.md
├── quickstart.md
└── validation-report.md
```

### Source Code (repository root)

```text
infra/
├── docker-compose.yml
├── mosquitto/
└── postgres/

backend/
├── app/
│   ├── api/
│   ├── mqtt/
│   ├── rules/
│   ├── db/
│   └── websocket/
└── tests/

edge-executor/
├── app/
└── tests/

simulators/
├── cadvisor-bridge/
└── environment/

dashboard/
├── src/
└── tests/

contracts/
└── mqtt/
```

**Structure Decision**: Arquitectura multi-servicio con backend, edge executor, simuladores y dashboard, orquestada por Docker Compose para demo reproducible.
