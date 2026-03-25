# Feature Specification: Normalizacion de base de datos SEDCM para inventario, telemetria y auditoria

**Feature Branch**: `002-normalizacion-bd`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "Normalizacion de base de datos SEDCM para inventario, telemetria y auditoria. Contexto, problema, objetivo, resultados esperados, fuera de alcance y criterios de aceptacion provistos por el usuario."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Inventario normalizado y consultable (Priority: P1)

Como operador, necesito consultar el inventario por zona, rack y contenedor usando entidades maestras, para asegurar integridad referencial y consultas consistentes.

**Why this priority**: Sin inventario normalizado no hay base para telemetria, reglas ni auditoria consistentes.

**Independent Test**: Se puede probar creando zonas, racks y contenedores y consultando el inventario sin depender de telemetria.

**Acceptance Scenarios**:

1. **Given** zonas y racks definidos, **When** consulto el inventario por zona, **Then** obtengo los racks y contenedores asociados con claves unicas.
2. **Given** un contenedor con rol critico, **When** consulto el inventario del rack, **Then** el contenedor aparece ligado al rack correcto.

---

### User Story 2 - Telemetria y estado ligados a entidades (Priority: P2)

Como operador, necesito que la telemetria y el estado de rack queden vinculados a las entidades del inventario, para trazabilidad y reglas consistentes.

**Why this priority**: La telemetria es el insumo principal del motor de reglas y debe quedar ligada a la jerarquia.

**Independent Test**: Se puede enviar telemetria con zone/rack y verificar que se resuelve a rack_id y opcionalmente a `contenedor_id_ref`.

**Acceptance Scenarios**:

1. **Given** un payload con zone/rack existentes, **When** ingresa telemetria, **Then** queda registrada con el rack correspondiente.
2. **Given** un payload con container_name conocido, **When** ingresa telemetria, **Then** queda ligada al contenedor correcto.

---

### User Story 3 - Migracion historica sin perdida (Priority: P3)

Como operador, necesito migrar o convivir con datos legacy sin perdida de historial, para mantener trazabilidad completa.

**Why this priority**: Permite continuidad operativa y auditoria completa durante la transicion.

**Independent Test**: Se puede migrar un conjunto de datos legacy y validar conteos y relaciones.

**Acceptance Scenarios**:

1. **Given** datos legacy existentes, **When** ejecuto la migracion, **Then** los registros quedan mapeados a zonas/racks/contenedores o marcados con motivo si no se pudo.

---

### Edge Cases

- **Payload incompleto**: se rechaza la persistencia, se registra evento `telemetry_rejected` con motivo y no se ejecuta el rules engine.
- **Rack desconocido (zone/rack no existente)**: se registra en auditoria como no mapeado y no se actualiza estado hasta resolver inventario.
- **container_id faltante**: se permite persistencia con `contenedor_id_ref = null` usando `container_name` cuando sea posible; si no hay match, se audita como parcial.
- **container_name duplicado en diferentes racks**: la resolucion se hace por par rack + nombre, y si sigue ambiguo se audita y no se enlaza contenedor.
- **Datos legacy con zone/rack inconsistentes (ej. vacios)**: se migran como no mapeados con marca de error en auditoria.
- **Estado de rack existente sin telemetria asociada**: se conserva estado actual y se marca para reconciliacion en backfill.

### Event Contracts & State Rules *(mandatory for event-driven features)*

- **Topics**: Telemetria en `dc/telemetria/zona/{zone}/rack/{rack}/host/{host}/contenedor/{container}`; comandos en `dc/comandos/zona/{zone}/rack/{rack}`; ACK en `dc/eventos/zona/{zone}/rack/{rack}`.
- **Telemetry Contract**: Mantener campos actuales (zone, rack, host, container_id, container_name, metricas) y validar tipos y rangos basicos.
- **Command Contract**: Mantener `command_id`, `action`, `reason`, `correlation_id` con semantica actual.
- **ACK Contract**: Mantener `status` ok|fail y `details` descriptivo.
- **Idempotency Strategy**: Duplicados de mensajes se detectan por id de mensaje o comando y no generan efectos repetidos.
- **State Transitions**: Normal, Warning, Critical, Recovery con reglas actuales.
- **Hysteresis Parameters**: T1=40, T2=45, Treset=42, margen_hist=1.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST definir entidades maestras para zonas, racks y contenedores con claves unicas y relaciones consistentes.
- **FR-002**: El sistema MUST persistir telemetria nueva ligada a un rack y, cuando sea posible, a un contenedor.
- **FR-003**: El sistema MUST mantener compatibilidad con payloads MQTT actuales sin cambios de formato.
- **FR-004**: El sistema MUST permitir migracion o convivencia temporal con datos legacy sin perdida de historial.
- **FR-005**: El sistema MUST mantener auditoria de eventos de negocio (ingesta, rechazo, transiciones, comandos y ACK).
- **FR-006**: El sistema MUST permitir consultar inventario por zona, rack y contenedor.
- **FR-007**: El sistema MUST aplicar idempotencia en la ingesta de eventos duplicados.
- **FR-008**: El sistema MUST conservar las reglas de negocio actuales con baseline explicito: T1=40, T2=45, Treset=42 y margen_hist=1.
- **FR-009**: El sistema MUST validar los payloads JSON de telemetria antes de persistirlos o usarlos en el rules engine.
- **FR-010**: El sistema MUST generar logs operativos en formato JSON estructurado para ingesta, reglas, comandos y auditoria.
- **FR-011**: El alcance MVP MUST contemplar 2 zonas, 3 racks por zona y 3 contenedores por rack (1 critico y 2 normales).
- **FR-012**: El sistema MUST mantener trazabilidad tecnica minima por `message_id`, `command_id` y `correlation_id` cuando aplique.
- **FR-013**: La convivencia temporal con tablas legacy MUST cerrarse cuando se cumplan SC-002 y SC-003, y cuando no existan errores criticos de mapeo abiertos en 2 ventanas consecutivas de 30 minutos cada una, verificadas con evidencia en auditoria y reporte de validacion en quickstart.

### Non-Functional Requirements

- **NFR-001 (Calidad de validacion)**: El 100% de payloads invalidos debe quedar registrado como `telemetry_rejected` con motivo y sin ejecucion de reglas; el 100% de payloads validos debe continuar al flujo normal.
- **NFR-002 (Observabilidad)**: Los logs JSON estructurados deben incluir como minimo `ts`, `level`, `event_type`, `zone`, `rack`, `message_id`, `command_id`, `correlation_id` cuando existan.
- **NFR-003 (Verificacion de compatibilidad MQTT)**: La compatibilidad de contratos MQTT definidos en FR-003 debe validarse con pruebas de regresion de contratos para telemetria/comando/ACK.
- **NFR-004 (Disponibilidad en migracion)**: La disponibilidad durante migracion debe medirse de forma reproducible segun el metodo definido para SC-003.

### Terminologia Canonica

- `container_id`: identificador recibido en payload MQTT.
- `contenedor_id_ref`: llave foranea opcional en tabla `muestras_telemetria` hacia `contenedores.id`.

### Definicion de Error Critico de Mapeo

Para FR-013, un error critico de mapeo es cualquier caso que impida persistir telemetria valida en tablas normalizadas por falta de correspondencia de `zone/rack` o inconsistencia de FK obligatoria. No se considera critico cuando solo falta asociacion de contenedor y la fila puede persistirse con `contenedor_id_ref = null` y auditoria de motivo.

### Key Entities *(include if feature involves data)*

- **Zona**: Unidad logica que agrupa racks, identificada por codigo y nombre.
- **Rack**: Unidad fisica o logica dentro de una zona, con codigo y clave unica.
- **Contenedor**: Activo Docker asociado a un rack, con rol y marca de criticidad.
- **MuestraTelemetria**: Registro historico de metricas y ambiente asociado a un rack y opcionalmente a un contenedor.
- **EstadoRack**: Ultimo estado conocido de un rack basado en reglas de temperatura.
- **Auditoria**: Registro de eventos y decisiones del sistema con trazabilidad.
- **MensajeProcesado**: Registro para idempotencia de eventos duplicados.

## Assumptions

- El inventario inicial puede derivarse de datos legacy y/o configuracion existente.
- Los payloads actuales contienen informacion suficiente para resolver zona y rack.
- La migracion puede ejecutarse con una ventana de mantenimiento de maximo 60 segundos acumulados (alineada con SC-003) o en modo conviviente.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% de la telemetria nueva queda ligada a un rack valido; al menos 95% queda ligada a un contenedor cuando `container_name` existe en inventario, medido sobre una ventana minima de 24 horas y muestra minima de 1,000 mensajes, con formula `mensajes_contenedor_enlazado / mensajes_con_container_name_en_inventario`.
- **SC-002**: 99.9% de los registros legacy migrados quedan relacionados con zona y rack; los restantes quedan marcados con motivo de no mapeo.
- **SC-003**: La ingesta de telemetria no se detiene por mas de 1 minuto acumulado durante la migracion.
- **SC-004**: En una corrida completa de inventario (ejecucion de consulta de validacion sobre el 100% de `zonas` activas y sus `racks` asociados en tablas maestras), la fuente de verdad de racks esperados MUST ser `zonas` + `racks`. El mecanismo de comprobacion MUST usar una consulta de comparacion entre (a) pares esperados `zona_codigo + rack_codigo` desde tablas maestras activas y (b) pares observados y campos en la respuesta/consulta de inventario (`zone`, `rack`, `state`). Formula de pass/fail: `cobertura = pares_observados_validos / pares_esperados`; PASS si `cobertura = 1.0` y `campos_obligatorios_presentes = 100%`; FAIL en cualquier otro caso.
