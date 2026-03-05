# Feature Specification: SEDCM MVP

**Feature Branch**: `001-sedcm-mvp`
**Created**: 2026-03-04
**Status**: Draft
**Input**: User description: "SEDCM sistema distribuido con MQTT, PostgreSQL, WebSocket, histéresis y stop_critico"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Monitoreo y mitigación térmica automática (Priority: P1)

Como operador, quiero que el sistema detecte temperatura crítica por rack y detenga automáticamente el contenedor crítico correcto para mitigar riesgo.

**Why this priority**: Es la capacidad de seguridad principal del MVP.

**Independent Test**: Forzar temperatura >=45°C en un rack y verificar emisión de `stop_critico`, detención del contenedor crítico por labels y ACK persistido.

**Acceptance Scenarios**:

1. **Given** rack en estado Normal, **When** temp sube a >=45°C, **Then** backend publica `stop_critico` en tópico de comandos del rack.
2. **Given** edge recibe comando válido, **When** resuelve `dc.critical=true`, **Then** detiene el contenedor objetivo y publica ACK `ok|fail`.

---

### User Story 2 - Visibilidad operativa en tiempo real (Priority: P2)

Como operador, quiero visualizar estado por zona/rack, métricas recientes y eventos de auditoría en un dashboard en tiempo real.

**Why this priority**: Permite operación y validación del comportamiento de mitigación.

**Independent Test**: Publicar telemetría y eventos MQTT de prueba y verificar render de estados y feed de eventos por WebSocket.

**Acceptance Scenarios**:

1. **Given** backend recibe telemetría, **When** procesa y persiste, **Then** dashboard refleja estado y métricas en <=2s.
2. **Given** se ejecuta un comando y llega ACK, **When** se guarda auditoría, **Then** dashboard muestra evento correlacionado.

---

### User Story 3 - Estabilidad de estado e idempotencia (Priority: P3)

Como sistema, quiero evitar flapping e inconsistencias ante duplicados MQTT para mantener estados confiables.

**Why this priority**: Asegura robustez operativa bajo condiciones reales de mensajería.

**Independent Test**: Reenviar mensajes duplicados y oscilantes alrededor de umbral y validar que no hay transiciones espurias ni comandos duplicados efectivos.

**Acceptance Scenarios**:

1. **Given** temperatura alrededor de T1, **When** oscila dentro del margen, **Then** estado no flapea entre Normal/Warning.
2. **Given** comando con mismo `command_id`, **When** se reprocesa, **Then** no ejecuta acción destructiva duplicada.

### Edge Cases

- Telemetría con campos faltantes o tipos inválidos debe rechazarse y auditarse sin romper el consumidor.
- ACK tardío o duplicado debe consolidarse por `command_id`.
- Si no existe contenedor crítico por labels en el rack, edge publica ACK `fail` con detalles.
- Si WebSocket cae, cliente debe poder reconectar y recuperar snapshot de estado.

### Event Contracts & State Rules *(mandatory for event-driven features)*

- **Topics**:
  - Telemetría: `dc/telemetria/zona/{Z}/rack/{R}/host/{H}/contenedor/{C}`
  - Comandos: `dc/comandos/zona/{Z}/rack/{R}`
  - ACK/estado: `dc/eventos/zona/{Z}/rack/{R}`
- **Telemetry Contract**: `timestamp, zone, rack, host, container_id, container_name, cpu_pct, ram_mb, net_rx, net_tx, io_read, io_write, temp_c, hum_pct, power_w?`
- **Command Contract**: `command_id, timestamp, zone, rack, action=stop_critico, reason, correlation_id`
- **ACK Contract**: `command_id, timestamp, status(ok|fail), details`
- **Idempotency Strategy**: deduplicación por `command_id` y correlación por `correlation_id`.
- **State Transitions**: Normal, Warning, Critical, Recovery con reglas explícitas.
- **Hysteresis Parameters**: `T1=40`, `T2=45`, `Treset=42`, `margen_hist=1`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST desplegar entorno reproducible con un `docker compose up`.
- **FR-002**: System MUST ingerir telemetría MQTT y validar payload JSON.
- **FR-003**: System MUST persistir telemetría, estado actual y auditoría en PostgreSQL.
- **FR-004**: System MUST ejecutar reglas de estado con histéresis y publicar `stop_critico` al alcanzar Critical.
- **FR-005**: System MUST ejecutar stop del contenedor crítico por labels mediante Docker API local y emitir ACK.
- **FR-006**: System MUST exponer API/WebSocket para dashboard con estado por rack y feed de eventos.
- **FR-007**: System MUST definir logging auditable de operaciones críticas.
- **FR-008**: System MUST tolerar mensajes duplicados sin corrupción de estado.
- **FR-009**: System MUST provisionar exactamente 2 zonas (A, B), 3 racks por zona (A1-A3, B1-B3) y 3 contenedores por rack (1 crítico, 2 normales) con labels `dc.zone`, `dc.rack`, `dc.critical`.
- **FR-010**: System MUST combinar y correlacionar telemetría de cAdvisor y variables ambientales simuladas por `zone/rack/timestamp` antes de evaluación de reglas y exposición al dashboard.

### Key Entities *(include if feature involves data)*

- **TelemetrySample**: medición por contenedor/rack con timestamp y métricas de recurso/ambiente.
- **RackState**: estado actual del rack (Normal/Warning/Critical/Recovery) y metadatos de transición.
- **CommandEvent**: comando de mitigación emitido por backend con correlación.
- **AckEvent**: resultado de ejecución del edge con estado y detalles.
- **AuditLog**: registro inmutable de eventos relevantes para trazabilidad.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Tras `docker compose up`, en <=5 minutos se verifica: `backend` responde `GET /health` con HTTP 200, `postgres` acepta conexión SQL, `mosquitto` acepta conexión MQTT en `1883`, `dashboard` sirve HTTP 200 en `:5173`, y `edge-executor`/simuladores permanecen en estado `running` sin reinicios.
- **SC-002**: En evento `temp_c>=45`, backend publica comando en <2s desde recepción.
- **SC-003**: En >=95% de comandos `stop_critico` válidos, Edge detiene el contenedor crítico correcto y publica ACK auditable en <=3s desde recepción del comando.
- **SC-004**: Dashboard refleja estado y últimos eventos en tiempo real con latencia visual <=2s.
- **SC-005**: No hay flapping en oscilación alrededor de T1 dentro de `margen_hist`.
