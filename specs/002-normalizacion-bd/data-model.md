# Data Model - Normalizacion SEDCM

## Entidades

## Coexistencia temporal
- Legacy durante migracion: `rack_state`, `telemetry_samples`, `audit_log`, `processed_message`.
- Normalizado objetivo: `estado_rack`, `muestras_telemetria`, `auditoria`, `mensaje_procesado`.
- Modo de escritura configurable por `DB_WRITE_MODE`: `legacy`, `dual`, `normalized`.

### Zona
- Fields: id (PK), codigo (unique), nombre
- Reglas: codigo obligatorio y unico (A, B)

### Rack
- Fields: id (PK), zona_id (FK), codigo, nombre, clave_rack (unique)
- Reglas: clave_rack = "{zona_codigo}:{rack_codigo}" o equivalente

### Contenedor
- Fields: id (PK), rack_id (FK), contenedor_id, nombre_contenedor, host, rol, es_critico, estado, creado_en
- Reglas: nombre_contenedor unico por rack; rol en {critico, normal, infraestructura}

### EstadoRack
- Fields: clave_rack (PK), rack_id (FK, unique), estado, actualizado_en
- Reglas: estado en {Normal, Warning, Critical, Recovery}

### Inventario API (proyecciones)
- ZoneSummary: zone, nombre
- RackSummary: zone, rack, state, temp_c, hum_pct, power_w
- ContainerSummary: rack, container_name, host, rol, es_critico

### MuestraTelemetria
- Fields: id (PK), rack_id (FK), contenedor_id_ref (FK opcional), marca_tiempo, host, cpu_pct, ram_mb, temp_c, hum_pct, power_w, net_rx, net_tx, io_read, io_write, payload, creado_en
- Reglas: marca_tiempo obligatorio; metricas >= 0 cuando apliquen

### Auditoria
- Fields: id (PK), rack_id (FK opcional), tipo_evento, id_correlacion, id_comando, detalles, creado_en
- Reglas: tipo_evento obligatorio; detalles JSON opcional

### MensajeProcesado
- Fields: id_mensaje (PK), fuente, visto_en
- Reglas: id_mensaje unico

## Relaciones
- Zona 1..N Rack
- Rack 1..N Contenedor
- Rack 1..N MuestraTelemetria
- Contenedor 0..N MuestraTelemetria
- Rack 1..1 EstadoRack
- Rack 0..N Auditoria

## Validaciones y reglas
- Zona/rack se resuelven desde payload MQTT (zone, rack)
- Contenedor se resuelve por nombre dentro del rack
- Si no hay match de contenedor, la telemetria se guarda con contenedor_id_ref null y se registra en auditoria

## State transitions (sin cambios)
- Normal -> Warning (temp_c >= 40)
- Warning -> Critical (temp_c >= 45)
- Critical -> Recovery (temp_c <= 42)
- Recovery -> Normal (temp_c < 39)
