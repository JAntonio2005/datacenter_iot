<!--
Sync Impact Report
- Version change: N/A -> 1.0.0
- Modified principles:
	- Template Principle 1 -> I. Seguridad Térmica Primero
	- Template Principle 2 -> II. Arquitectura Desacoplada por Eventos
	- Template Principle 3 -> III. Trazabilidad y Auditoría Obligatorias
	- Template Principle 4 -> IV. Idempotencia y Tolerancia a Fallos
	- Template Principle 5 -> V. Histéresis y Estabilidad de Estado
- Added sections:
	- Restricciones Operativas del MVP
	- Flujo de Desarrollo y Quality Gates
- Removed sections:
	- None
- Templates requiring updates:
	- ✅ .specify/templates/plan-template.md
	- ✅ .specify/templates/spec-template.md
	- ✅ .specify/templates/tasks-template.md
	- ⚠ pending: .specify/templates/commands/*.md (directory not present)
	- ⚠ pending: README.md / docs/quickstart.md (files not present)
- Deferred TODOs:
	- None
-->

# SEDCM (Smart Edge Data Center Manager) Constitution

## Core Principles

### I. Seguridad Térmica Primero
Ante condición crítica de temperatura, el sistema MUST priorizar mitigación de riesgo
operativo sobre continuidad del contenedor crítico. Cuando la temperatura alcance o
supere T2, el backend MUST emitir `stop_critico` y el Edge Executor MUST intentar
detener el contenedor con `dc.critical=true` del rack objetivo usando la Docker API
local. Rationale: evita daño en cascada y alinea la operación con seguridad primero.

### II. Arquitectura Desacoplada por Eventos
Los módulos MUST comunicarse por MQTT y MUST NOT invocarse directamente entre sí,
excepto la relación Dashboard ↔ Backend por HTTP/WebSocket. Cada integración nueva
MUST definir topic, payload JSON versionado y manejo de errores/ACK explícito.
Rationale: reduce acoplamiento y permite evolución independiente de módulos.

### III. Trazabilidad y Auditoría Obligatorias
Todo evento relevante MUST registrarse con timestamp y correlación: telemetría
importante, transiciones de estado, alarmas, comandos y ACKs. El backend MUST
persistir evidencia en PostgreSQL y los logs operativos MUST ser estructurados en
JSON. Rationale: permite auditoría, depuración y validación reproducible de la demo.

### IV. Idempotencia y Tolerancia a Fallos
Consumidores MQTT MUST tolerar duplicados, retrasos y reentregas sin corromper el
estado. El procesamiento de comandos y ACKs MUST ser idempotente por `command_id`
o `correlation_id`, y los fallos transitorios MUST registrar reintentos sin generar
acciones destructivas repetidas. Rationale: MQTT es al menos una vez en escenarios
reales y el estado debe permanecer consistente.

### V. Histéresis y Estabilidad de Estado
El motor de reglas MUST aplicar histéresis para evitar flapping cerca de umbrales.
Estados y umbrales del MVP MUST respetar: T1=40°C, T2=45°C, Treset=42°C,
`margen_hist`=1°C (parametrizable). Una transición MUST requerir condiciones de
entrada/salida explícitas y observables. Rationale: asegura decisiones estables y
operación entendible para el equipo.

## Restricciones Operativas del MVP

- El alcance MVP MUST incluir 2 zonas (A, B), 3 racks por zona y 3 contenedores por
	rack (1 crítico y 2 normales), con labels `dc.zone`, `dc.rack`, `dc.critical`.
- La telemetría MUST combinar métricas de cAdvisor y variables ambientales simuladas
	(temperatura, humedad y energía cuando aplique).
- El backend MUST validar payloads JSON antes de persistencia o decisiones.
- La persistencia oficial del MVP MUST ser PostgreSQL para telemetría, estado actual
	y auditoría.
- El dashboard MUST reflejar estado por zona/rack, métricas recientes y eventos en
	tiempo real (WebSocket preferido; polling solo como contingencia documentada).
- Fuera de alcance actual: sensores físicos reales, HA multi-broker y hardening TLS
	completo si compromete la demo local.

## Flujo de Desarrollo y Quality Gates

- Toda especificación MUST declarar contratos de mensajes (telemetría, comandos, ACK)
	y reglas de transición de estado antes de implementación.
- Todo plan MUST pasar un Constitution Check con evidencia de: seguridad térmica,
	desacoplamiento por eventos, trazabilidad, idempotencia e histéresis.
- Toda lista de tareas MUST incluir pruebas/validaciones para lógica crítica:
	activación `stop_critico`, ACK de ejecución y prevención de flapping.
- Definition of Done de cada feature MUST incluir demo reproducible y evidencia de
	auditoría verificable.

## Governance

Esta constitución prevalece sobre prácticas locales de implementación en caso de
conflicto. Toda enmienda MUST incluir: motivo, impacto, artefactos sincronizados y
actualización del Sync Impact Report.

Política de versionado:
- MAJOR: eliminación o redefinición incompatible de principios/gobernanza.
- MINOR: adición de principio o expansión normativa sustantiva.
- PATCH: clarificaciones editoriales o mejoras no normativas.

Proceso de enmienda:
1. Propuesta documentada en la constitución.
2. Revisión de consistencia sobre `plan-template`, `spec-template`, `tasks-template`
	 y guías operativas existentes.
3. Actualización de versión y fecha `Last Amended` en formato ISO.

Revisión de cumplimiento:
- En planificación: validación explícita de Constitution Check.
- En ejecución: evidencia de pruebas/validaciones de reglas críticas.
- En cierre: confirmación de trazabilidad y criterios DoD de la feature.

**Version**: 1.0.0 | **Ratified**: 2026-03-04 | **Last Amended**: 2026-03-04
