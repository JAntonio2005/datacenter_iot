---

description: "Task list for Normalizacion de base de datos SEDCM"
---

# Tasks: Normalizacion de base de datos SEDCM

**Input**: Design documents from `/specs/002-normalizacion-bd/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 [FR-004][SC-002] Review legacy schema and mapping targets in backend/app/db/models.py and backend/app/db/migrations/0001_initial.sql

---

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T002 [FR-001][FR-011] Create normalized schema migration in backend/app/db/migrations/0002_normalizacion.sql
- [X] T003 [FR-004][SC-002] Create backfill migration (legacy to normalized) in backend/app/db/migrations/0003_backfill_normalizacion.sql
- [X] T003a [FR-004] Implement dual-write/cutover mode toggle for telemetry and audit writes in backend/app/mqtt/telemetry_consumer.py and backend/app/services/audit_service.py
- [X] T003b [FR-004][FR-013] Add integration validation for cutover mode transitions (`legacy` -> `dual` -> `normalized`) in backend/tests/integration/test_cutover_modes.py
- [X] T004 [P] [FR-001] Update SQLAlchemy models for normalized tables in backend/app/db/models.py
- [X] T005 [P] [FR-006] Add inventory lookup helpers in backend/app/db/inventory.py
- [X] T006 [P] [FR-005][FR-012] Extend AuditService to accept rack_id resolution in backend/app/services/audit_service.py
- [X] T006a [P] [FR-010] Enforce structured JSON logging fields in backend/app/core/logging.py and backend/app/services/audit_service.py
- [X] T006b [P] [NFR-002] Add integration validation for required JSON log fields in backend/tests/integration/test_structured_logging_fields.py
- [X] T006c [P] [NFR-002] Add per-flow log validation for ingestion/rules/command_emitted/edge_ack in backend/tests/integration/test_structured_logging_event_flows.py
- [X] T007 [P] [FR-006] Add inventory service for zone/rack/container queries in backend/app/services/inventory_service.py
- [X] T007a [P] [FR-007] Add idempotency checks for duplicate telemetry messages in backend/app/mqtt/telemetry_consumer.py

**Checkpoint**: Normalized schema and helpers exist; ready for story implementation.

---

## Phase 3: User Story 1 - Inventario normalizado y consultable (Priority: P1)

**Goal**: Expose inventory by zone, rack, and container using normalized entities.

**Independent Test**: Create zones/racks/containers and retrieve them via inventory endpoints.

### Implementation

- [X] T008 [P] [US1][FR-006] Add inventory response schemas in backend/app/api/schemas.py
- [X] T009 [US1][FR-006][SC-004] Implement inventory endpoints in backend/app/api/routes.py
- [X] T010 [US1][FR-006][SC-004] Wire inventory queries using inventory_service in backend/app/services/inventory_service.py
- [X] T010a [US1][FR-006][SC-004] Add reproducible inventory coverage validation (expected vs observed pairs and required fields) in backend/tests/integration/test_inventory_sc004_validation.py with pass/fail report formula (`cobertura = pares_observados_validos / pares_esperados`, PASS only when cobertura=1.0 and required fields=100%)

**Checkpoint**: Inventory endpoints return zones, racks, and containers from normalized tables.

---

## Phase 4: User Story 2 - Telemetria y estado ligados a entidades (Priority: P2)

**Goal**: Persist telemetry and rack state using FK relationships while keeping MQTT payloads unchanged.

**Independent Test**: Send telemetry with zone/rack and verify records store rack_id and optional contenedor_id_ref.

### Implementation

- [X] T011 [US2][FR-002][SC-001] Update telemetry ingestion to resolve rack_id and contenedor_id_ref in backend/app/mqtt/telemetry_consumer.py
- [X] T011a [US2][FR-009] Validate telemetry payload schema and required fields before persistence in backend/app/mqtt/telemetry_consumer.py
- [X] T011b [US2][FR-009] Reject/log invalid payloads as telemetry_rejected and skip DB insert in backend/app/mqtt/telemetry_consumer.py
- [X] T011c [US2][FR-009] Prevent rules engine execution for invalid payloads in backend/app/mqtt/telemetry_consumer.py
- [X] T011d [US2][FR-009][NFR-001] Add integration tests for payload incompleto, rack desconocido y container_id faltante in backend/tests/integration/test_payload_edge_cases.py
- [X] T011e [US2][NFR-001] Add positive-flow integration test (payload valido -> persistencia + rules engine) in backend/tests/integration/test_valid_payload_flow.py
- [X] T012 [US2][FR-008] Update rules engine to read/write estado_rack via rack_id in backend/app/rules/engine.py
- [X] T013 [US2][FR-002][SC-001] Update rack queries to use normalized tables in backend/app/api/routes.py
- [X] T014 [US2][FR-006] Update rack API schemas if needed for normalized lookups in backend/app/api/schemas.py
- [X] T015 [US2][FR-005][FR-012] Update ack consumer to resolve rack_id when auditing in backend/app/mqtt/ack_consumer.py
- [X] T015a [US2][FR-008] Add integration test for stop_critico emission on Critical transition in backend/tests/integration/test_stop_critico_emission.py
- [X] T015b [US2][FR-005][FR-007][FR-012] Add integration test for ACK correlation and edge_ack persistence in backend/tests/integration/test_ack_correlation.py
- [X] T015c [US2][FR-008] Add integration test for anti-flapping with hysteresis thresholds in backend/tests/integration/test_hysteresis_antiflapping.py
- [X] T015d [US2][FR-003][NFR-003] Add contract regression tests for MQTT telemetry/command/ack payload compatibility in backend/tests/contract/test_mqtt_contract_regression.py

**Checkpoint**: Telemetry and state updates use normalized relationships without changing MQTT payloads.

---

## Phase 5: User Story 3 - Migracion historica sin perdida (Priority: P3)

**Goal**: Migrate legacy data into normalized tables and preserve history.

**Independent Test**: Run backfill and verify counts and sample records map to zones/racks/containers.

### Implementation

- [X] T016 [US3][FR-004][SC-002] Add legacy-to-normalized mapping queries in backend/app/db/migrations/0003_backfill_normalizacion.sql
- [X] T017 [US3][FR-004][FR-005] Add audit markers for unmapped legacy rows in backend/app/db/migrations/0003_backfill_normalizacion.sql
- [X] T018 [US3][FR-004][SC-002] Document migration validation steps in specs/002-normalizacion-bd/quickstart.md
- [X] T018a [US3][SC-003][NFR-004] Add reproducible downtime measurement procedure and script usage in specs/002-normalizacion-bd/quickstart.md and scripts/migration/measure_downtime.ps1
- [X] T018b [US3][FR-004] Validate backfill edge cases: duplicate container_name y registros legacy sin zone/rack in backend/tests/integration/test_backfill_edge_cases.py
- [X] T018c [US3][SC-001] Add reproducible SC-001 measurement query/report (24h window, min 1000 messages) in scripts/migration/measure_container_link_rate.sql

**Checkpoint**: Legacy data is migrated or flagged with reasons for non-mapping.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T019 [P] [FR-001][FR-002] Update data-model references if schema changes during implementation in specs/002-normalizacion-bd/data-model.md
- [X] T020 [P] [FR-004][FR-009][FR-013] Update migration contract notes with coexistence exit criteria (2x30 min windows + evidence source) and critical mapping-error taxonomy in specs/002-normalizacion-bd/contracts/migration.md
- [X] T020a [FR-013] Add executable validation task/script for coexistence closure criteria in scripts/migration/validate_coexistence_exit.ps1
- [X] T021 [P] [FR-005][FR-012] Add task-to-requirement traceability notes in specs/002-normalizacion-bd/quickstart.md
- [X] T022 [FR-005][FR-012] Add Definition of Done evidence checklist (reproducible demo + verifiable audit trail) in specs/002-normalizacion-bd/quickstart.md

---

## Dependencies & Execution Order

- Phase 1 must complete before Phase 2.
- Phase 2 blocks all user stories.
- Phases 3-5 can proceed after Phase 2; prioritize P1 then P2 then P3.
- Phase 6 can run after any story, but ideally after Phases 3-5.

## Parallel Execution Examples

- Phase 2: T004, T005, T006, and T007 can run in parallel.
- US1: T008 can run in parallel with T010 once service scaffolding exists.
- US2: T011 and T012 can proceed in parallel if model updates are done.
- Polish: T019 and T020 can run in parallel.

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup
2. Phase 2: Foundational
3. Phase 3: User Story 1
4. Validate inventory endpoints

### Incremental Delivery

1. Complete Phase 1-2
2. Deliver US1 (inventory)
3. Deliver US2 (telemetry/state normalization)
4. Deliver US3 (legacy migration)
5. Polish documentation

## Traceability Matrix (Spec -> Tasks)

- **FR-001**: T002, T004, T019
- **FR-002**: T011, T013, T019
- **FR-003**: T015d
- **FR-004**: T001, T003, T003a, T003b, T016, T017, T018, T018b, T020
- **FR-005**: T006, T015, T015b, T017, T021, T022
- **FR-006**: T005, T007, T008, T009, T010, T010a, T014
- **FR-007**: T007a, T015b
- **FR-008**: T012, T015a, T015c
- **FR-009**: T011a, T011b, T011c, T011d, T020
- **FR-010**: T006a
- **FR-011**: T002
- **FR-012**: T006, T015, T015b, T021, T022
- **FR-013**: T003b, T020, T020a
- **NFR-001**: T011a, T011b, T011c, T011d, T011e
- **NFR-002**: T006a, T006b, T006c
- **NFR-003**: T015d
- **NFR-004**: T018a
- **SC-001**: T011, T013, T018c
- **SC-002**: T001, T003, T016, T018
- **SC-003**: T018a
- **SC-004**: T009, T010, T010a
- **Constitution-DoD**: T022
