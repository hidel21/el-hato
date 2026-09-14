"""La vista de inventario tambien agrupa por etapa del lote.

La pantalla de inventario cuenta el hato por etapa —vientres, levante,
terneros—, y la etapa vive en el lote, no en el animal. Sin ella en la vista
habria que cruzar con grupos en cada lectura.

Revision ID: 0002_inventario_por_etapa
Revises: 0001_esquema_inicial
Create Date: 2026-09-14
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002_inventario_por_etapa"
down_revision: str | None = "0001_esquema_inicial"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


VISTA_NUEVA = """
CREATE MATERIALIZED VIEW inventario_hato AS
SELECT
    a.finca_id,
    a.grupo_id,
    g.nombre                                  AS grupo_nombre,
    g.etapa                                   AS grupo_etapa,
    a.potrero_id,
    p.nombre                                  AS potrero_nombre,
    a.sexo,
    a.estado,
    count(*)                                  AS cantidad,
    coalesce(sum(a.peso_actual_kg), 0)        AS peso_total_kg,
    round(avg(a.peso_actual_kg), 2)           AS peso_promedio_kg,
    max(a.updated_at)                         AS actualizado_en
FROM animales a
LEFT JOIN grupos   g ON g.id = a.grupo_id
LEFT JOIN potreros p ON p.id = a.potrero_id
WHERE a.is_deleted = false
GROUP BY a.finca_id, a.grupo_id, g.nombre, g.etapa, a.potrero_id, p.nombre, a.sexo, a.estado
WITH DATA
"""

VISTA_VIEJA = """
CREATE MATERIALIZED VIEW inventario_hato AS
SELECT
    a.finca_id,
    a.grupo_id,
    g.nombre                                  AS grupo_nombre,
    a.potrero_id,
    p.nombre                                  AS potrero_nombre,
    a.sexo,
    a.estado,
    count(*)                                  AS cantidad,
    coalesce(sum(a.peso_actual_kg), 0)        AS peso_total_kg,
    round(avg(a.peso_actual_kg), 2)           AS peso_promedio_kg,
    max(a.updated_at)                         AS actualizado_en
FROM animales a
LEFT JOIN grupos   g ON g.id = a.grupo_id
LEFT JOIN potreros p ON p.id = a.potrero_id
WHERE a.is_deleted = false
GROUP BY a.finca_id, a.grupo_id, g.nombre, a.potrero_id, p.nombre, a.sexo, a.estado
WITH DATA
"""

# Sin indice unico no se puede refrescar CONCURRENTLY, y un refresco que
# bloquea lecturas tumba la pantalla de inventario.
INDICES = [
    "CREATE UNIQUE INDEX idx_inventario_hato_unico ON inventario_hato "
    "(finca_id, grupo_id, potrero_id, sexo, estado)",
    "CREATE INDEX idx_inventario_hato_finca ON inventario_hato (finca_id)",
]


def _rehacer(sentencia: str) -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS inventario_hato")
    op.execute(sentencia)
    for indice in INDICES:
        op.execute(indice)


def upgrade() -> None:
    _rehacer(VISTA_NUEVA)


def downgrade() -> None:
    _rehacer(VISTA_VIEJA)
