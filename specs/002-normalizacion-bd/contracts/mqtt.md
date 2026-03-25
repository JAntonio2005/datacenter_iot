# MQTT Contracts - SEDCM (sin cambios de formato)

## Telemetria
- Topic: dc/telemetria/zona/{zone}/rack/{rack}/host/{host}/contenedor/{container}
- Campos: timestamp, zone, rack, host, container_id, container_name, cpu_pct, ram_mb, net_rx, net_tx, io_read, io_write, temp_c, hum_pct, power_w

## Comandos
- Topic: dc/comandos/zona/{zone}/rack/{rack}
- Campos: command_id, timestamp, zone, rack, action, reason, correlation_id

## ACK / Eventos
- Topic: dc/eventos/zona/{zone}/rack/{rack}
- Campos: command_id, timestamp, status, details
