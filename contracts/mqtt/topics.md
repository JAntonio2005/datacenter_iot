# MQTT Topics - SEDCM (v1)

## Telemetría
- `dc/telemetria/zona/{zone}/rack/{rack}/host/{host}/contenedor/{container}`
  - zone: A | B
  - rack: A1..A3 o B1..B3
  - QoS recomendado: 1
  - Producer: simulators / cadvisor-bridge
  - Consumer: backend

## Comandos
- `dc/comandos/zona/{zone}/rack/{rack}`
  - QoS recomendado: 1
  - Producer: backend
  - Consumer: edge-executor

## Eventos / ACK
- `dc/eventos/zona/{zone}/rack/{rack}`
  - QoS recomendado: 1
  - Producer: edge-executor
  - Consumer: backend