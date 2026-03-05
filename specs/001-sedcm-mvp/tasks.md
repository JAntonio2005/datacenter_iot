# Tasks: SEDCM MVP

**Input**: Design documents from `/specs/001-sedcm-mvp/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Incluidas porque la especificación exige validaciones de lógica crítica (stop_critico, ACK, histéresis e idempotencia).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Inicializar estructura y entorno reproducible del MVP

- [ ] T001 Create service folder structure for backend, edge-executor, simulators, dashboard, and infra in backend/, edge-executor/, simulators/, dashboard/, infra/
- [ ] T002 Create Docker Compose baseline with mosquitto, postgres, backend, edge-executor, simulators, and dashboard services in infra/docker-compose.yml
- [ ] T003 [P] Add Mosquitto broker configuration and mounted config file in infra/mosquitto/mosquitto.conf
- [ ] T004 [P] Add PostgreSQL initialization script and base database setup in infra/postgres/init.sql
- [ ] T005 [P] Initialize backend Python dependencies and entrypoint in backend/requirements.txt and backend/app/main.py
- [ ] T006 [P] Initialize edge executor Python dependencies and entrypoint in edge-executor/requirements.txt and edge-executor/app/main.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Infraestructura núcleo que bloquea toda historia hasta completarse

- [ ] T007 Define MQTT topic constants and parsing helpers in backend/app/mqtt/topics.py
- [ ] T008 [P] Define shared JSON schemas for telemetry, command, and ack contracts in backend/app/mqtt/schemas.py
- [ ] T009 [P] Implement PostgreSQL models for telemetry, rack_state, command_event, ack_event, and audit_log in backend/app/db/models.py
- [ ] T010 Implement DB session and migration bootstrap in backend/app/db/session.py and backend/app/db/migrations/0001_initial.sql
- [ ] T011 [P] Implement structured JSON logging utilities for all services in backend/app/core/logging.py and edge-executor/app/core/logging.py
- [ ] T012 Implement backend MQTT subscriber/publisher base client with reconnect handling in backend/app/mqtt/client.py
- [ ] T013 [P] Implement edge MQTT subscriber/publisher base client with reconnect handling in edge-executor/app/mqtt/client.py
- [ ] T014 Implement idempotency repository and dedup checks by command_id/correlation_id in backend/app/core/idempotency.py and edge-executor/app/core/idempotency.py
- [ ] T059 [P] Implement telemetry fusion/correlation module (cAdvisor + ambient) by zone/rack/timestamp in backend/app/mqtt/telemetry_fusion.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Monitoreo y mitigación térmica automática (Priority: P1) 🎯 MVP

**Goal**: Detectar condición crítica y ejecutar `stop_critico` con ACK auditable sobre el contenedor crítico correcto.

**Independent Test**: Forzar `temp_c >= 45` para un rack y verificar comando MQTT, stop del contenedor crítico por labels, ACK persistido y estado actualizado.

### Tests for User Story 1

- [ ] T015 [P] [US1] Create contract test for telemetry payload validation in backend/tests/contract/test_telemetry_schema.py
- [ ] T016 [P] [US1] Create contract test for command and ack payload contracts in backend/tests/contract/test_command_ack_schema.py
- [ ] T017 [P] [US1] Create integration test for critical temperature triggering stop_critico in backend/tests/integration/test_critical_command_flow.py
- [ ] T018 [P] [US1] Create integration test for edge stop execution by dc.critical label in edge-executor/tests/integration/test_stop_critical_by_label.py
- [ ] T052 [P] [US1] Create integration/perf test for telemetry-to-command publish latency <2s in backend/tests/integration/test_command_latency_under_2s.py
- [ ] T060 [P] [US1] Create integration test for invalid telemetry payload rejection with audit evidence in backend/tests/integration/test_invalid_payload_audit.py
- [ ] T061 [P] [US1] Create integration test for cAdvisor+ambient telemetry fusion consistency in backend/tests/integration/test_telemetry_fusion.py

### Implementation for User Story 1

- [ ] T019 [US1] Implement temperature state machine with built-in hysteresis thresholds and critical transition hooks in backend/app/rules/state_machine.py
- [ ] T020 [US1] Implement rule engine to emit stop_critico command events on Critical transition in backend/app/rules/engine.py
- [ ] T021 [US1] Implement telemetry consumer pipeline (validate, persist, evaluate rules) in backend/app/mqtt/telemetry_consumer.py
- [ ] T022 [US1] Implement command publisher with correlation metadata in backend/app/mqtt/command_publisher.py
- [ ] T023 [US1] Implement edge command handler for stop_critico action in edge-executor/app/handlers/command_handler.py
- [ ] T024 [US1] Implement Docker API adapter to resolve and stop dc.critical=true container by rack labels in edge-executor/app/docker/docker_client.py
- [ ] T025 [US1] Implement edge ACK publisher with execution result details in edge-executor/app/mqtt/ack_publisher.py
- [ ] T026 [US1] Implement backend ACK consumer and persistence in backend/app/mqtt/ack_consumer.py
- [ ] T027 [US1] Implement audit logging for telemetry critical events, commands, and ACKs in backend/app/services/audit_service.py
- [ ] T053 [US1] Add backend latency metric instrumentation and assertion hooks in backend/app/rules/engine.py and backend/app/services/audit_service.py
- [ ] T062 [US1] Integrate telemetry fusion into ingestion pipeline before rules evaluation in backend/app/mqtt/telemetry_consumer.py and backend/app/mqtt/telemetry_fusion.py

**Checkpoint**: US1 funcional y demostrable de forma independiente

---

## Phase 4: User Story 2 - Visibilidad operativa en tiempo real (Priority: P2)

**Goal**: Mostrar estado por zona/rack, métricas recientes y eventos de auditoría con actualización en tiempo real.

**Independent Test**: Publicar telemetría y eventos simulados; verificar UI actualizada por WebSocket en <=2s con estado y feed de auditoría.

### Tests for User Story 2

- [ ] T028 [P] [US2] Create backend API integration test for rack state and latest metrics endpoints in backend/tests/integration/test_dashboard_state_api.py
- [ ] T029 [P] [US2] Create WebSocket integration test for realtime event broadcasting in backend/tests/integration/test_websocket_events.py
- [ ] T030 [P] [US2] Create dashboard component test for rack status and metrics rendering in dashboard/tests/rack_status_panel.test.tsx
- [ ] T054 [P] [US2] Create E2E test for event-to-dashboard-render latency <=2s in dashboard/tests/e2e/test_realtime_latency.spec.ts
- [ ] T056 [P] [US2] Create integration test for WebSocket reconnect and snapshot recovery in backend/tests/integration/test_ws_reconnect_snapshot.py

### Implementation for User Story 2

- [ ] T031 [US2] Implement dashboard REST endpoints for zones/racks state and latest metrics in backend/app/api/dashboard_routes.py
- [ ] T032 [US2] Implement WebSocket hub for pushing state and audit events in backend/app/websocket/hub.py
- [ ] T033 [US2] Implement backend event broadcaster from telemetry/ack transitions to WebSocket clients in backend/app/websocket/publisher.py
- [ ] T034 [US2] Implement dashboard API client for REST and WebSocket subscriptions in dashboard/src/services/apiClient.ts
- [ ] T035 [US2] Implement zone/rack status view with Normal/Warning/Critical/Recovery badges in dashboard/src/components/RackStatusGrid.tsx
- [ ] T036 [US2] Implement latest metrics panel (temp/hum/cpu/ram) in dashboard/src/components/MetricsPanel.tsx
- [ ] T037 [US2] Implement audit event timeline view in dashboard/src/components/AuditEventList.tsx
- [ ] T038 [US2] Wire dashboard page with realtime state refresh in dashboard/src/pages/DashboardPage.tsx
- [ ] T055 [US2] Add timestamp propagation and client-side render-latency capture in backend/app/websocket/publisher.py and dashboard/src/services/apiClient.ts
- [ ] T057 [US2] Implement snapshot endpoint and reconnect flow in backend/app/api/dashboard_routes.py, backend/app/websocket/hub.py, dashboard/src/services/apiClient.ts

**Checkpoint**: US2 funcional y demostrable de forma independiente

---

## Phase 5: User Story 3 - Estabilidad de estado e idempotencia (Priority: P3)

**Goal**: Evitar flapping y acciones duplicadas ante reentregas MQTT y oscilaciones en umbral.

**Independent Test**: Enviar telemetría oscilante y comandos/ACK duplicados; validar estabilidad de estados y ausencia de efectos destructivos duplicados.

### Tests for User Story 3

- [ ] T039 [P] [US3] Create integration test for warning hysteresis anti-flapping behavior in backend/tests/integration/test_warning_hysteresis.py
- [ ] T040 [P] [US3] Create integration test for duplicate command idempotency in edge-executor/tests/integration/test_duplicate_command_idempotency.py
- [ ] T041 [P] [US3] Create integration test for duplicate ACK consolidation in backend/tests/integration/test_ack_deduplication.py

### Implementation for User Story 3

- [ ] T042 [US3] Extract and harden hysteresis transition guards into backend/app/rules/hysteresis.py preserving US1 behavior
- [ ] T043 [US3] Refactor state machine/engine to consume extracted hysteresis module with parity tests in backend/app/rules/state_machine.py and backend/app/rules/engine.py
- [ ] T044 [US3] Implement duplicate command suppression in edge command handler by command_id in edge-executor/app/handlers/command_handler.py
- [ ] T045 [US3] Implement backend ACK deduplication and last-write-safe update rules in backend/app/mqtt/ack_consumer.py
- [ ] T046 [US3] Implement audit markers for deduplicated/discarded messages in backend/app/services/audit_service.py

**Checkpoint**: US3 funcional y demostrable de forma independiente

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Cierre de demo reproducible y hardening básico del MVP

- [ ] T047 [P] Add MQTT contract documentation and examples in contracts/mqtt/README.md
- [ ] T048 Add operator quickstart with critical scenario walkthrough in specs/001-sedcm-mvp/quickstart.md
- [ ] T049 Add compose healthchecks and startup ordering for backend, mqtt, and postgres in infra/docker-compose.yml
- [ ] T050 [P] Add environment variable templates for backend and edge services in backend/.env.example and edge-executor/.env.example
- [ ] T051 Run end-to-end MVP validation scenario and capture expected outputs in specs/001-sedcm-mvp/validation-report.md
- [ ] T058 Add automated topology validation (2 zonas, 6 racks, 18 contenedores, labels dc.zone/dc.rack/dc.critical) in infra/scripts/validate_topology.sh and include result in specs/001-sedcm-mvp/validation-report.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Sin dependencias.
- **Phase 2 (Foundational)**: Depende de Phase 1; bloquea todas las historias.
- **Phase 3 (US1)**: Depende de Phase 2; entrega el MVP mínimo operativo.
- **Phase 4 (US2)**: Depende de Phase 2 y usa eventos/estado producidos por US1.
- **Phase 5 (US3)**: Depende de Phase 2 y endurece comportamiento de US1.
- **Phase 6 (Polish)**: Depende de las historias a incluir en release.

### User Story Dependencies

- **US1 (P1)**: Puede iniciar inmediatamente tras Foundational.
- **US2 (P2)**: Puede iniciar tras Foundational, pero su valor completo depende de eventos de US1.
- **US3 (P3)**: Puede iniciar tras Foundational y refuerza US1/US2.

### Dependency Graph

- Foundation -> US1 -> (US2, US3 en paralelo) -> Polish

---

## Parallel Execution Examples

### User Story 1

- Ejecutar en paralelo T015, T016, T017, T018 (tests)
- Ejecutar en paralelo T023 y T024 (handler y Docker adapter en archivos distintos)

### User Story 2

- Ejecutar en paralelo T028, T029, T030 (tests)
- Ejecutar en paralelo T035, T036, T037 (componentes de dashboard)

### User Story 3

- Ejecutar en paralelo T039, T040, T041 (tests)
- Ejecutar en paralelo T044 y T045 (deduplicación edge/backend)

---

## Implementation Strategy

### MVP First (US1 Only)

1. Completar Phase 1 y Phase 2.
2. Completar Phase 3 (US1).
3. Validar escenario crítico end-to-end.
4. Demostrar MVP con evidencia en auditoría.

### Incremental Delivery

1. Entregar US1 (seguridad térmica automática).
2. Añadir US2 (observabilidad en tiempo real).
3. Añadir US3 (estabilidad e idempotencia robusta).
4. Cerrar con Polish y validación final reproducible.

### Completeness Check

- Todas las tareas cumplen formato checklist: `- [ ] T### [P?] [US?] Descripción con ruta`.
- Cada historia incluye criterio de prueba independiente.
- Todas las tareas de historia tienen etiqueta `[US#]`.
- Setup/Foundational/Polish no incluyen etiqueta de historia.
