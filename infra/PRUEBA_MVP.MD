# 1. Levantar stack
docker compose up -d --build

# 2. Verificar servicios principales
docker compose ps

# 3. Escuchar comandos
docker exec -it sedcm-mosquitto sh -c "mosquitto_sub -t 'dc/comandos/#' -v"

# 4. Escuchar eventos / ACK
docker exec -it sedcm-mosquitto sh -c "mosquitto_sub -t 'dc/eventos/#' -v"

# 5. Forzar condición crítica en A2
docker exec -it sedcm-mosquitto sh -c "mosquitto_pub -h localhost -t 'dc/telemetria/zona/A/rack/A2/host/env-sim/contenedor/environment-simulator' -m '{\"timestamp\":\"2026-03-12T05:15:00Z\",\"zone\":\"A\",\"rack\":\"A2\",\"host\":\"env-sim\",\"container_id\":\"env-A-A2\",\"container_name\":\"environment-simulator\",\"cpu_pct\":1.0,\"ram_mb\":10.0,\"net_rx\":0,\"net_tx\":0,\"io_read\":0,\"io_write\":0,\"temp_c\":55.0,\"hum_pct\":50.0,\"power_w\":150.0}'"

# 6. Verificar estado del rack
docker exec -it sedcm-postgres psql -U sedcm -d sedcm -c "
SELECT zone, rack, state, updated_at
FROM rack_state
ORDER BY zone, rack;"

# 7. Ver auditoría
docker exec -it sedcm-postgres psql -U sedcm -d sedcm -c "
SELECT created_at, event_type, zone, rack, details
FROM audit_log
ORDER BY created_at DESC
LIMIT 30;"

# 8. Verificar que el contenedor crítico cayó
docker ps -a --format "table {{.Names}}\t{{.Status}}" | grep sedcm-critico-a2