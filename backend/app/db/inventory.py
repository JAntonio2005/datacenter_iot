from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


def resolve_rack_id(db: Session, zone: str, rack: str) -> int | None:
    sql = text(
        """
        SELECT r.id
        FROM racks r
        JOIN zonas z ON z.id = r.zona_id
        WHERE UPPER(z.codigo) = UPPER(:zone)
          AND UPPER(r.codigo) = UPPER(:rack)
        LIMIT 1
        """
    )
    return db.execute(sql, {"zone": zone, "rack": rack}).scalar_one_or_none()


def resolve_container_id(
    db: Session,
    *,
    rack_id: int,
    container_name: str | None,
    host: str | None,
    container_id: str | None,
) -> int | None:
    if not container_name:
        return None

    sql = text(
        """
        SELECT id
        FROM contenedores
        WHERE rack_id = :rack_id
          AND nombre_contenedor = :container_name
        LIMIT 1
        """
    )
    existing = db.execute(
        sql,
        {"rack_id": rack_id, "container_name": container_name},
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    insert_sql = text(
        """
        INSERT INTO contenedores(
            rack_id,
            contenedor_id,
            nombre_contenedor,
            host,
            rol,
            es_critico,
            estado
        ) VALUES (
            :rack_id,
            :contenedor_id,
            :nombre_contenedor,
            :host,
            :rol,
            :es_critico,
            'active'
        )
        ON CONFLICT (rack_id, nombre_contenedor)
        DO UPDATE SET
            contenedor_id = EXCLUDED.contenedor_id,
            host = COALESCE(EXCLUDED.host, contenedores.host)
        RETURNING id
        """
    )

    role = "critico" if container_name and "crit" in container_name.lower() else "normal"

    return db.execute(
        insert_sql,
        {
            "rack_id": rack_id,
            "contenedor_id": container_id,
            "nombre_contenedor": container_name,
            "host": host,
            "rol": role,
            "es_critico": role == "critico",
        },
    ).scalar_one()
