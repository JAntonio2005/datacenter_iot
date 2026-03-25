# REST Contracts - SEDCM

## GET /racks
- Descripcion: resumen por rack con estado y ultimas metricas
- Respuesta: lista de rack summaries

## GET /racks/{zone}/{rack}
- Descripcion: detalle de rack, ambiente y contenedores
- Respuesta: rack detail

## (Opcional) Inventario
- GET /inventory/zones
- GET /inventory/zones/{zone}/racks
- GET /inventory/racks/{rack}/containers
