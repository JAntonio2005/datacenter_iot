# Research - Normalizacion de base de datos SEDCM

## Decision 1: Estrategia de migracion incremental con tablas nuevas
- Decision: Crear tablas normalizadas en paralelo y migrar datos legacy con backfill.
- Rationale: Minimiza riesgo y permite convivencia temporal sin frenar la ingesta.
- Alternatives considered: Migracion in-place de tablas actuales (rechazada por alto riesgo de downtime).

## Decision 2: Resolucion de inventario desde payloads actuales
- Decision: Mantener payloads MQTT actuales y resolver zone/rack/contendedor a IDs internos.
- Rationale: Evita cambios en productores y mantiene compatibilidad con simuladores y edge.
- Alternatives considered: Cambiar contratos MQTT para enviar IDs (fuera de alcance).

## Decision 3: Idempotencia y auditoria preservadas
- Decision: Mantener processed_message y audit_log con relacion a entidades nuevas.
- Rationale: Cumple con trazabilidad e idempotencia existentes sin perder historial.
- Alternatives considered: Resetear auditoria durante migracion (rechazado por perdida de trazabilidad).

## Decision 4: Mapeo de contenedores por nombre y labels
- Decision: Usar container_name + rack para asociar contenedor; si no hay match, registrar en auditoria.
- Rationale: Los payloads actuales no garantizan IDs estables; el nombre es el dato mas disponible.
- Alternatives considered: Requerir container_id estable (no garantizado en todos los simuladores).
