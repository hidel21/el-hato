"""Esquema inicial completo: 21 tablas, 15 enums y la vista de inventario.

Revision ID: 0001_esquema_inicial
Revises:
Create Date: 2026-09-11 10:36:55.029785-05:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001_esquema_inicial"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


# Los tipos enum de Postgres no se crean ni se borran solos junto con las tablas:
# se manejan explicitamente aqui para que el downgrade deje la base limpia.
ENUMS: list[tuple[str, list[str]]] = [
    (
        "potrero_tipo_pasto_enum",
        [
            "brachiaria",
            "estrella",
            "guinea",
            "kikuyo",
            "angleton",
            "pasto_natural",
            "mezcla",
            "otro",
        ],
    ),
    ("sync_operation_enum", ["insert", "update", "delete"]),
    ("sync_status_enum", ["pendiente", "enviando", "enviado", "error"]),
    ("user_role_enum", ["administrador", "veterinario", "capataz"]),
    (
        "grupo_etapa_enum",
        ["ternero", "destete", "levante", "engorde", "vientre", "toro", "descarte"],
    ),
    ("grupo_proposito_enum", ["cria", "levante", "engorde", "leche", "doble_proposito", "manejo"]),
    ("sexo_enum", ["hembra", "macho"]),
    ("animal_estado_enum", ["activo", "vendido", "muerto", "descartado", "en_engorde"]),
    (
        "alerta_tipo_enum",
        ["vacunacion", "bano", "parto", "celo", "peso", "rotacion", "inventario", "otro"],
    ),
    ("alerta_estado_enum", ["pendiente", "vencida", "atendida", "descartada"]),
    ("celo_metodo_enum", ["observacion", "parche", "podometro", "monta_registrada", "otro"]),
    (
        "gasto_categoria_enum",
        [
            "alimento",
            "medicamento",
            "veterinario",
            "mano_obra",
            "insumo",
            "transporte",
            "mantenimiento",
            "otro",
        ],
    ),
    ("prenez_resultado_enum", ["prenada", "vacia", "dudoso"]),
    ("parto_resultado_enum", ["vivo", "muerto", "aborto", "gemelar"]),
    ("parto_dificultad_enum", ["normal", "asistido", "cesarea", "distocia"]),
]


def upgrade() -> None:
    # pgcrypto da gen_random_uuid() como respaldo de las PK generadas en el cliente.
    # pg_trgm da la busqueda por arete parecido.
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    for nombre, valores in ENUMS:
        postgresql.ENUM(*valores, name=nombre).create(op.get_bind(), checkfirst=False)
    op.create_table(
        "fincas",
        sa.Column("nombre", sa.String(length=150), nullable=False),
        sa.Column("codigo", sa.String(length=30), nullable=True),
        sa.Column("municipio", sa.String(length=120), nullable=True),
        sa.Column("departamento", sa.String(length=120), nullable=True),
        sa.Column("pais", sa.String(length=80), server_default="Colombia", nullable=False),
        sa.Column("hectareas", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column(
            "zona_horaria", sa.String(length=60), server_default="America/Bogota", nullable=False
        ),
        sa.Column("moneda", sa.String(length=3), server_default="COP", nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "catalogo_productos_bano",
        sa.Column("nombre", sa.String(length=140), nullable=False),
        sa.Column("principio_activo", sa.String(length=140), nullable=True),
        sa.Column("laboratorio", sa.String(length=140), nullable=True),
        sa.Column("tipo", sa.String(length=60), nullable=True),
        sa.Column("dosis_por_litro_ml", sa.Numeric(precision=7, scale=2), nullable=True),
        sa.Column("dias_carencia_carne", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("dias_carencia_leche", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("dias_reaplicacion", sa.Integer(), nullable=True),
        sa.Column("activo", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("device_id", sa.String(length=100), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("client_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("client_timestamp_raw", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finca_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["finca_id"], ["fincas.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_catalogo_productos_bano_finca_id"),
        "catalogo_productos_bano",
        ["finca_id"],
        unique=False,
    )
    op.create_table(
        "catalogo_vacunas",
        sa.Column("nombre", sa.String(length=140), nullable=False),
        sa.Column("enfermedad", sa.String(length=140), nullable=True),
        sa.Column("laboratorio", sa.String(length=140), nullable=True),
        sa.Column("via_aplicacion", sa.String(length=60), nullable=True),
        sa.Column("dosis_ml", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("dias_refuerzo", sa.Integer(), nullable=True),
        sa.Column("dias_carencia", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("obligatoria", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("activo", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("device_id", sa.String(length=100), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("client_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("client_timestamp_raw", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finca_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["finca_id"], ["fincas.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_catalogo_vacunas_finca_id"), "catalogo_vacunas", ["finca_id"], unique=False
    )
    op.create_table(
        "potreros",
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("hectareas", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column(
            "tipo_pasto",
            postgresql.ENUM(name="potrero_tipo_pasto_enum", create_type=False),
            nullable=True,
        ),
        sa.Column("capacidad_ugm_ha", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column(
            "dias_descanso_recomendado", sa.Integer(), server_default=sa.text("30"), nullable=False
        ),
        sa.Column("en_descanso", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("fecha_ultimo_ingreso", sa.Date(), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("device_id", sa.String(length=100), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("client_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("client_timestamp_raw", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finca_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["finca_id"], ["fincas.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_potreros_finca_id"), "potreros", ["finca_id"], unique=False)
    op.create_table(
        "sync_queue",
        sa.Column("tabla", sa.String(length=60), nullable=False),
        sa.Column("registro_id", sa.Uuid(), nullable=False),
        sa.Column(
            "operacion",
            postgresql.ENUM(name="sync_operation_enum", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "estado",
            postgresql.ENUM(name="sync_status_enum", create_type=False),
            server_default="pendiente",
            nullable=False,
        ),
        sa.Column("contenido", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("device_id", sa.String(length=100), nullable=True),
        sa.Column("client_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("client_timestamp_raw", sa.DateTime(timezone=True), nullable=True),
        sa.Column("intentos", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("ultimo_error", sa.Text(), nullable=True),
        sa.Column("procesado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finca_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["finca_id"], ["fincas.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sync_queue_finca_id"), "sync_queue", ["finca_id"], unique=False)
    op.create_table(
        "usuarios",
        sa.Column("nombre_completo", sa.String(length=150), nullable=False),
        sa.Column("correo", sa.String(length=180), nullable=False),
        sa.Column("clave_hash", sa.String(length=255), nullable=False),
        sa.Column("rol", postgresql.ENUM(name="user_role_enum", create_type=False), nullable=False),
        sa.Column("telefono", sa.String(length=30), nullable=True),
        sa.Column("activo", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("ultimo_acceso", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finca_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["finca_id"], ["fincas.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_usuarios_finca_id"), "usuarios", ["finca_id"], unique=False)
    op.create_table(
        "dispositivos",
        sa.Column("usuario_id", sa.Uuid(), nullable=True),
        sa.Column("identificador", sa.String(length=100), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=True),
        sa.Column("plataforma", sa.String(length=40), nullable=True),
        sa.Column("desfase_reloj_ms", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("ultima_sincronizacion", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finca_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["finca_id"], ["fincas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_dispositivos_finca_id"), "dispositivos", ["finca_id"], unique=False)
    op.create_index(
        op.f("ix_dispositivos_usuario_id"), "dispositivos", ["usuario_id"], unique=False
    )
    op.create_table(
        "grupos",
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column(
            "etapa", postgresql.ENUM(name="grupo_etapa_enum", create_type=False), nullable=False
        ),
        sa.Column(
            "proposito",
            postgresql.ENUM(name="grupo_proposito_enum", create_type=False),
            nullable=False,
        ),
        sa.Column("potrero_id", sa.Uuid(), nullable=True),
        sa.Column("responsable_id", sa.Uuid(), nullable=True),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("device_id", sa.String(length=100), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("client_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("client_timestamp_raw", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finca_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["finca_id"], ["fincas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["potrero_id"], ["potreros.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["responsable_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_grupos_finca_id"), "grupos", ["finca_id"], unique=False)
    op.create_index(op.f("ix_grupos_potrero_id"), "grupos", ["potrero_id"], unique=False)
    op.create_table(
        "animales",
        sa.Column("arete", sa.String(length=40), nullable=False),
        sa.Column("arete_duplicado", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=True),
        sa.Column("sexo", postgresql.ENUM(name="sexo_enum", create_type=False), nullable=False),
        sa.Column("raza", sa.String(length=80), nullable=True),
        sa.Column("fecha_nacimiento", sa.Date(), nullable=True),
        sa.Column(
            "estado",
            postgresql.ENUM(name="animal_estado_enum", create_type=False),
            server_default="activo",
            nullable=False,
        ),
        sa.Column("grupo_id", sa.Uuid(), nullable=True),
        sa.Column("potrero_id", sa.Uuid(), nullable=True),
        sa.Column("madre_id", sa.Uuid(), nullable=True),
        sa.Column("padre_id", sa.Uuid(), nullable=True),
        sa.Column("peso_nacimiento_kg", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("peso_actual_kg", sa.Numeric(precision=7, scale=2), nullable=True),
        sa.Column("fecha_ingreso", sa.Date(), nullable=True),
        sa.Column("origen", sa.String(length=60), nullable=True),
        sa.Column("fecha_salida", sa.Date(), nullable=True),
        sa.Column("motivo_salida", sa.String(length=160), nullable=True),
        sa.Column("valor_compra", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("foto_url", sa.String(length=500), nullable=True),
        sa.Column("foto_local_id", sa.String(length=100), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("device_id", sa.String(length=100), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("client_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("client_timestamp_raw", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finca_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["finca_id"], ["fincas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["grupo_id"], ["grupos.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["madre_id"], ["animales.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["padre_id"], ["animales.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["potrero_id"], ["potreros.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_animales_finca_id"), "animales", ["finca_id"], unique=False)
    op.create_index(op.f("ix_animales_grupo_id"), "animales", ["grupo_id"], unique=False)
    op.create_index(op.f("ix_animales_madre_id"), "animales", ["madre_id"], unique=False)
    op.create_index(op.f("ix_animales_padre_id"), "animales", ["padre_id"], unique=False)
    op.create_index(op.f("ix_animales_potrero_id"), "animales", ["potrero_id"], unique=False)
    op.create_table(
        "banos",
        sa.Column("producto_id", sa.Uuid(), nullable=False),
        sa.Column("grupo_id", sa.Uuid(), nullable=True),
        sa.Column("potrero_id", sa.Uuid(), nullable=True),
        sa.Column("fecha_bano", sa.Date(), nullable=False),
        sa.Column("proxima_fecha", sa.Date(), nullable=True),
        sa.Column("metodo", sa.String(length=40), nullable=True),
        sa.Column("dosis_total_ml", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("litros_agua", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("cantidad_animales", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("costo_total", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("responsable_id", sa.Uuid(), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("device_id", sa.String(length=100), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("client_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("client_timestamp_raw", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finca_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["finca_id"], ["fincas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["grupo_id"], ["grupos.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["potrero_id"], ["potreros.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["producto_id"], ["catalogo_productos_bano.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["responsable_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_banos_finca_id"), "banos", ["finca_id"], unique=False)
    op.create_index(op.f("ix_banos_grupo_id"), "banos", ["grupo_id"], unique=False)
    op.create_index(op.f("ix_banos_potrero_id"), "banos", ["potrero_id"], unique=False)
    op.create_table(
        "alertas",
        sa.Column(
            "tipo", postgresql.ENUM(name="alerta_tipo_enum", create_type=False), nullable=False
        ),
        sa.Column(
            "estado",
            postgresql.ENUM(name="alerta_estado_enum", create_type=False),
            server_default="pendiente",
            nullable=False,
        ),
        sa.Column("titulo", sa.String(length=200), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("fecha_objetivo", sa.Date(), nullable=True),
        sa.Column("animal_id", sa.Uuid(), nullable=True),
        sa.Column("grupo_id", sa.Uuid(), nullable=True),
        sa.Column("potrero_id", sa.Uuid(), nullable=True),
        sa.Column("referencia_tabla", sa.String(length=60), nullable=True),
        sa.Column("referencia_id", sa.Uuid(), nullable=True),
        sa.Column("atendida_por_id", sa.Uuid(), nullable=True),
        sa.Column("atendida_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("device_id", sa.String(length=100), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("client_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("client_timestamp_raw", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finca_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["animal_id"], ["animales.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["atendida_por_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["finca_id"], ["fincas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["grupo_id"], ["grupos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["potrero_id"], ["potreros.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_alertas_animal_id"), "alertas", ["animal_id"], unique=False)
    op.create_index(op.f("ix_alertas_finca_id"), "alertas", ["finca_id"], unique=False)
    op.create_table(
        "bano_animales",
        sa.Column("bano_id", sa.Uuid(), nullable=False),
        sa.Column("animal_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("device_id", sa.String(length=100), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("client_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("client_timestamp_raw", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finca_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["animal_id"], ["animales.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["bano_id"], ["banos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["finca_id"], ["fincas.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_bano_animales_animal_id"), "bano_animales", ["animal_id"], unique=False
    )
    op.create_index(op.f("ix_bano_animales_bano_id"), "bano_animales", ["bano_id"], unique=False)
    op.create_index(op.f("ix_bano_animales_finca_id"), "bano_animales", ["finca_id"], unique=False)
    op.create_table(
        "celos",
        sa.Column("animal_id", sa.Uuid(), nullable=False),
        sa.Column("fecha_celo", sa.Date(), nullable=False),
        sa.Column(
            "metodo", postgresql.ENUM(name="celo_metodo_enum", create_type=False), nullable=False
        ),
        sa.Column("intensidad", sa.String(length=20), nullable=True),
        sa.Column("responsable_id", sa.Uuid(), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("device_id", sa.String(length=100), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("client_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("client_timestamp_raw", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finca_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["animal_id"], ["animales.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["finca_id"], ["fincas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["responsable_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_celos_animal_id"), "celos", ["animal_id"], unique=False)
    op.create_index(op.f("ix_celos_finca_id"), "celos", ["finca_id"], unique=False)
    op.create_table(
        "gastos",
        sa.Column(
            "categoria",
            postgresql.ENUM(name="gasto_categoria_enum", create_type=False),
            nullable=False,
        ),
        sa.Column("concepto", sa.String(length=200), nullable=False),
        sa.Column("monto", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("fecha_gasto", sa.Date(), nullable=False),
        sa.Column("animal_id", sa.Uuid(), nullable=True),
        sa.Column("grupo_id", sa.Uuid(), nullable=True),
        sa.Column("potrero_id", sa.Uuid(), nullable=True),
        sa.Column("proveedor", sa.String(length=140), nullable=True),
        sa.Column("comprobante", sa.String(length=120), nullable=True),
        sa.Column("responsable_id", sa.Uuid(), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("device_id", sa.String(length=100), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("client_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("client_timestamp_raw", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finca_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["animal_id"], ["animales.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["finca_id"], ["fincas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["grupo_id"], ["grupos.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["potrero_id"], ["potreros.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["responsable_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_gastos_animal_id"), "gastos", ["animal_id"], unique=False)
    op.create_index(op.f("ix_gastos_finca_id"), "gastos", ["finca_id"], unique=False)
    op.create_index(op.f("ix_gastos_grupo_id"), "gastos", ["grupo_id"], unique=False)
    op.create_table(
        "pesajes",
        sa.Column("animal_id", sa.Uuid(), nullable=False),
        sa.Column("fecha_pesaje", sa.Date(), nullable=False),
        sa.Column("peso_kg", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column("metodo", sa.String(length=40), nullable=True),
        sa.Column("ganancia_diaria_kg", sa.Numeric(precision=6, scale=3), nullable=True),
        sa.Column("responsable_id", sa.Uuid(), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("device_id", sa.String(length=100), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("client_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("client_timestamp_raw", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finca_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["animal_id"], ["animales.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["finca_id"], ["fincas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["responsable_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_pesajes_animal_id"), "pesajes", ["animal_id"], unique=False)
    op.create_index(op.f("ix_pesajes_finca_id"), "pesajes", ["finca_id"], unique=False)
    op.create_table(
        "potrero_movimientos",
        sa.Column("potrero_origen_id", sa.Uuid(), nullable=True),
        sa.Column("potrero_destino_id", sa.Uuid(), nullable=False),
        sa.Column("grupo_id", sa.Uuid(), nullable=True),
        sa.Column("animal_id", sa.Uuid(), nullable=True),
        sa.Column("fecha_movimiento", sa.Date(), nullable=False),
        sa.Column("cantidad_animales", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("responsable_id", sa.Uuid(), nullable=True),
        sa.Column("motivo", sa.String(length=160), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("device_id", sa.String(length=100), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("client_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("client_timestamp_raw", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finca_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["animal_id"], ["animales.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["finca_id"], ["fincas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["grupo_id"], ["grupos.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["potrero_destino_id"], ["potreros.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["potrero_origen_id"], ["potreros.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["responsable_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_potrero_movimientos_animal_id"), "potrero_movimientos", ["animal_id"], unique=False
    )
    op.create_index(
        op.f("ix_potrero_movimientos_finca_id"), "potrero_movimientos", ["finca_id"], unique=False
    )
    op.create_index(
        op.f("ix_potrero_movimientos_grupo_id"), "potrero_movimientos", ["grupo_id"], unique=False
    )
    op.create_index(
        op.f("ix_potrero_movimientos_potrero_destino_id"),
        "potrero_movimientos",
        ["potrero_destino_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_potrero_movimientos_potrero_origen_id"),
        "potrero_movimientos",
        ["potrero_origen_id"],
        unique=False,
    )
    op.create_table(
        "vacunaciones",
        sa.Column("catalogo_vacuna_id", sa.Uuid(), nullable=False),
        sa.Column("animal_id", sa.Uuid(), nullable=True),
        sa.Column("grupo_id", sa.Uuid(), nullable=True),
        sa.Column("fecha_aplicacion", sa.Date(), nullable=False),
        sa.Column("proxima_dosis_fecha", sa.Date(), nullable=True),
        sa.Column("dosis_ml", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("lote_producto", sa.String(length=80), nullable=True),
        sa.Column("cantidad_animales", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("costo_total", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("responsable_id", sa.Uuid(), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("device_id", sa.String(length=100), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("client_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("client_timestamp_raw", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finca_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["animal_id"], ["animales.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["catalogo_vacuna_id"], ["catalogo_vacunas.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["finca_id"], ["fincas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["grupo_id"], ["grupos.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["responsable_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_vacunaciones_animal_id"), "vacunaciones", ["animal_id"], unique=False)
    op.create_index(op.f("ix_vacunaciones_finca_id"), "vacunaciones", ["finca_id"], unique=False)
    op.create_index(op.f("ix_vacunaciones_grupo_id"), "vacunaciones", ["grupo_id"], unique=False)
    op.create_table(
        "servicios_reproductivos",
        sa.Column("animal_id", sa.Uuid(), nullable=False),
        sa.Column("celo_id", sa.Uuid(), nullable=True),
        sa.Column("tipo", sa.String(length=30), nullable=False),
        sa.Column("fecha_servicio", sa.Date(), nullable=False),
        sa.Column("toro_id", sa.Uuid(), nullable=True),
        sa.Column("pajilla_codigo", sa.String(length=80), nullable=True),
        sa.Column("inseminador_id", sa.Uuid(), nullable=True),
        sa.Column("fecha_estimada_parto", sa.Date(), nullable=True),
        sa.Column("costo", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("device_id", sa.String(length=100), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("client_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("client_timestamp_raw", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finca_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["animal_id"], ["animales.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["celo_id"], ["celos.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["finca_id"], ["fincas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["inseminador_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["toro_id"], ["animales.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_servicios_reproductivos_animal_id"),
        "servicios_reproductivos",
        ["animal_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servicios_reproductivos_finca_id"),
        "servicios_reproductivos",
        ["finca_id"],
        unique=False,
    )
    op.create_table(
        "vacunacion_animales",
        sa.Column("vacunacion_id", sa.Uuid(), nullable=False),
        sa.Column("animal_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("device_id", sa.String(length=100), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("client_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("client_timestamp_raw", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finca_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["animal_id"], ["animales.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["finca_id"], ["fincas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["vacunacion_id"], ["vacunaciones.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_vacunacion_animales_animal_id"), "vacunacion_animales", ["animal_id"], unique=False
    )
    op.create_index(
        op.f("ix_vacunacion_animales_finca_id"), "vacunacion_animales", ["finca_id"], unique=False
    )
    op.create_index(
        op.f("ix_vacunacion_animales_vacunacion_id"),
        "vacunacion_animales",
        ["vacunacion_id"],
        unique=False,
    )
    op.create_table(
        "diagnosticos_prenez",
        sa.Column("animal_id", sa.Uuid(), nullable=False),
        sa.Column("servicio_id", sa.Uuid(), nullable=True),
        sa.Column("fecha_diagnostico", sa.Date(), nullable=False),
        sa.Column(
            "resultado",
            postgresql.ENUM(name="prenez_resultado_enum", create_type=False),
            nullable=False,
        ),
        sa.Column("metodo", sa.String(length=40), nullable=True),
        sa.Column("dias_gestacion", sa.Integer(), nullable=True),
        sa.Column("fecha_estimada_parto", sa.Date(), nullable=True),
        sa.Column("responsable_id", sa.Uuid(), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("device_id", sa.String(length=100), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("client_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("client_timestamp_raw", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finca_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["animal_id"], ["animales.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["finca_id"], ["fincas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["responsable_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["servicio_id"], ["servicios_reproductivos.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_diagnosticos_prenez_animal_id"), "diagnosticos_prenez", ["animal_id"], unique=False
    )
    op.create_index(
        op.f("ix_diagnosticos_prenez_finca_id"), "diagnosticos_prenez", ["finca_id"], unique=False
    )
    op.create_table(
        "partos",
        sa.Column("madre_id", sa.Uuid(), nullable=False),
        sa.Column("diagnostico_id", sa.Uuid(), nullable=True),
        sa.Column("cria_id", sa.Uuid(), nullable=True),
        sa.Column("fecha_parto", sa.Date(), nullable=False),
        sa.Column(
            "resultado",
            postgresql.ENUM(name="parto_resultado_enum", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "dificultad",
            postgresql.ENUM(name="parto_dificultad_enum", create_type=False),
            server_default="normal",
            nullable=False,
        ),
        sa.Column("peso_nacimiento_kg", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("responsable_id", sa.Uuid(), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("device_id", sa.String(length=100), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("client_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("client_timestamp_raw", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finca_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["cria_id"], ["animales.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["diagnostico_id"], ["diagnosticos_prenez.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["finca_id"], ["fincas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["madre_id"], ["animales.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["responsable_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_partos_cria_id"), "partos", ["cria_id"], unique=False)
    op.create_index(op.f("ix_partos_finca_id"), "partos", ["finca_id"], unique=False)
    op.create_index(op.f("ix_partos_madre_id"), "partos", ["madre_id"], unique=False)

    # ------------------------------------------------------------------
    # Indices que Alembic no deduce de los modelos
    # ------------------------------------------------------------------

    # Decision 1: un arete canonico por finca. Los marcados como duplicado
    # quedan FUERA del indice, por eso el servidor puede aceptarlos igual.
    op.execute(
        "CREATE UNIQUE INDEX idx_animales_arete_unico ON animales (finca_id, arete) "
        "WHERE is_deleted = false AND arete_duplicado = false"
    )
    # Busqueda por arete parecido: el capataz teclea 412 y encuentra C-0412.
    op.execute(
        "CREATE INDEX idx_animales_arete_busqueda ON animales USING gin (arete gin_trgm_ops)"
    )
    # Orden del listado por cursor y delta de sincronizacion.
    op.execute(
        "CREATE INDEX idx_animales_listado ON animales (finca_id, created_at, id) "
        "WHERE is_deleted = false"
    )
    op.execute("CREATE INDEX idx_animales_actualizados ON animales (finca_id, updated_at, id)")

    # Identidad unica mientras el registro viva.
    op.execute(
        "CREATE UNIQUE INDEX idx_usuarios_correo_unico ON usuarios (correo) WHERE is_deleted = false"
    )
    op.execute(
        "CREATE UNIQUE INDEX idx_grupos_nombre_unico ON grupos (finca_id, nombre) "
        "WHERE is_deleted = false"
    )
    op.execute(
        "CREATE UNIQUE INDEX idx_dispositivos_identificador_unico "
        "ON dispositivos (finca_id, identificador) WHERE is_deleted = false"
    )
    # Decision 8: un animal no puede aparecer dos veces en la misma aplicacion.
    op.execute(
        "CREATE UNIQUE INDEX idx_vacunacion_animales_unico "
        "ON vacunacion_animales (vacunacion_id, animal_id) WHERE is_deleted = false"
    )
    op.execute(
        "CREATE UNIQUE INDEX idx_bano_animales_unico "
        "ON bano_animales (bano_id, animal_id) WHERE is_deleted = false"
    )

    # Indices parciales de vencimiento. El cliente deriva la alerta; el servidor
    # solo necesita responder rapido por fecha.
    op.execute(
        "CREATE INDEX idx_vacunaciones_proxima_dosis ON vacunaciones (finca_id, proxima_dosis_fecha) "
        "WHERE is_deleted = false AND proxima_dosis_fecha IS NOT NULL"
    )
    op.execute(
        "CREATE INDEX idx_banos_proxima_fecha ON banos (finca_id, proxima_fecha) "
        "WHERE is_deleted = false AND proxima_fecha IS NOT NULL"
    )
    op.execute(
        "CREATE INDEX idx_servicios_fecha_estimada_parto "
        "ON servicios_reproductivos (finca_id, fecha_estimada_parto) "
        "WHERE is_deleted = false AND fecha_estimada_parto IS NOT NULL"
    )
    op.execute(
        "CREATE INDEX idx_diagnosticos_fecha_estimada_parto "
        "ON diagnosticos_prenez (finca_id, fecha_estimada_parto) "
        "WHERE is_deleted = false AND fecha_estimada_parto IS NOT NULL"
    )
    op.execute(
        "CREATE INDEX idx_pesajes_animal_fecha ON pesajes (animal_id, fecha_pesaje) "
        "WHERE is_deleted = false"
    )
    op.execute(
        "CREATE INDEX idx_alertas_estado ON alertas (finca_id, estado, fecha_objetivo) "
        "WHERE is_deleted = false"
    )
    op.execute("CREATE INDEX idx_sync_queue_estado ON sync_queue (finca_id, estado, created_at)")

    # ------------------------------------------------------------------
    # Decision 7: vista materializada de inventario.
    # Se refresca con debounce de 30 segundos, nunca dentro de la peticion.
    # ------------------------------------------------------------------
    op.execute(
        """
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
    )
    # Sin indice unico no se puede refrescar CONCURRENTLY, y un refresco que
    # bloquea lecturas es un refresco que tumba la pantalla de inventario.
    op.execute(
        "CREATE UNIQUE INDEX idx_inventario_hato_unico ON inventario_hato "
        "(finca_id, grupo_id, potrero_id, sexo, estado)"
    )
    op.execute("CREATE INDEX idx_inventario_hato_finca ON inventario_hato (finca_id)")


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS inventario_hato")
    op.drop_index(op.f("ix_partos_madre_id"), table_name="partos")
    op.drop_index(op.f("ix_partos_finca_id"), table_name="partos")
    op.drop_index(op.f("ix_partos_cria_id"), table_name="partos")
    op.drop_table("partos")
    op.drop_index(op.f("ix_diagnosticos_prenez_finca_id"), table_name="diagnosticos_prenez")
    op.drop_index(op.f("ix_diagnosticos_prenez_animal_id"), table_name="diagnosticos_prenez")
    op.drop_table("diagnosticos_prenez")
    op.drop_index(op.f("ix_vacunacion_animales_vacunacion_id"), table_name="vacunacion_animales")
    op.drop_index(op.f("ix_vacunacion_animales_finca_id"), table_name="vacunacion_animales")
    op.drop_index(op.f("ix_vacunacion_animales_animal_id"), table_name="vacunacion_animales")
    op.drop_table("vacunacion_animales")
    op.drop_index(op.f("ix_servicios_reproductivos_finca_id"), table_name="servicios_reproductivos")
    op.drop_index(
        op.f("ix_servicios_reproductivos_animal_id"), table_name="servicios_reproductivos"
    )
    op.drop_table("servicios_reproductivos")
    op.drop_index(op.f("ix_vacunaciones_grupo_id"), table_name="vacunaciones")
    op.drop_index(op.f("ix_vacunaciones_finca_id"), table_name="vacunaciones")
    op.drop_index(op.f("ix_vacunaciones_animal_id"), table_name="vacunaciones")
    op.drop_table("vacunaciones")
    op.drop_index(
        op.f("ix_potrero_movimientos_potrero_origen_id"), table_name="potrero_movimientos"
    )
    op.drop_index(
        op.f("ix_potrero_movimientos_potrero_destino_id"), table_name="potrero_movimientos"
    )
    op.drop_index(op.f("ix_potrero_movimientos_grupo_id"), table_name="potrero_movimientos")
    op.drop_index(op.f("ix_potrero_movimientos_finca_id"), table_name="potrero_movimientos")
    op.drop_index(op.f("ix_potrero_movimientos_animal_id"), table_name="potrero_movimientos")
    op.drop_table("potrero_movimientos")
    op.drop_index(op.f("ix_pesajes_finca_id"), table_name="pesajes")
    op.drop_index(op.f("ix_pesajes_animal_id"), table_name="pesajes")
    op.drop_table("pesajes")
    op.drop_index(op.f("ix_gastos_grupo_id"), table_name="gastos")
    op.drop_index(op.f("ix_gastos_finca_id"), table_name="gastos")
    op.drop_index(op.f("ix_gastos_animal_id"), table_name="gastos")
    op.drop_table("gastos")
    op.drop_index(op.f("ix_celos_finca_id"), table_name="celos")
    op.drop_index(op.f("ix_celos_animal_id"), table_name="celos")
    op.drop_table("celos")
    op.drop_index(op.f("ix_bano_animales_finca_id"), table_name="bano_animales")
    op.drop_index(op.f("ix_bano_animales_bano_id"), table_name="bano_animales")
    op.drop_index(op.f("ix_bano_animales_animal_id"), table_name="bano_animales")
    op.drop_table("bano_animales")
    op.drop_index(op.f("ix_alertas_finca_id"), table_name="alertas")
    op.drop_index(op.f("ix_alertas_animal_id"), table_name="alertas")
    op.drop_table("alertas")
    op.drop_index(op.f("ix_banos_potrero_id"), table_name="banos")
    op.drop_index(op.f("ix_banos_grupo_id"), table_name="banos")
    op.drop_index(op.f("ix_banos_finca_id"), table_name="banos")
    op.drop_table("banos")
    op.drop_index(op.f("ix_animales_potrero_id"), table_name="animales")
    op.drop_index(op.f("ix_animales_padre_id"), table_name="animales")
    op.drop_index(op.f("ix_animales_madre_id"), table_name="animales")
    op.drop_index(op.f("ix_animales_grupo_id"), table_name="animales")
    op.drop_index(op.f("ix_animales_finca_id"), table_name="animales")
    op.drop_table("animales")
    op.drop_index(op.f("ix_grupos_potrero_id"), table_name="grupos")
    op.drop_index(op.f("ix_grupos_finca_id"), table_name="grupos")
    op.drop_table("grupos")
    op.drop_index(op.f("ix_dispositivos_usuario_id"), table_name="dispositivos")
    op.drop_index(op.f("ix_dispositivos_finca_id"), table_name="dispositivos")
    op.drop_table("dispositivos")
    op.drop_index(op.f("ix_usuarios_finca_id"), table_name="usuarios")
    op.drop_table("usuarios")
    op.drop_index(op.f("ix_sync_queue_finca_id"), table_name="sync_queue")
    op.drop_table("sync_queue")
    op.drop_index(op.f("ix_potreros_finca_id"), table_name="potreros")
    op.drop_table("potreros")
    op.drop_index(op.f("ix_catalogo_vacunas_finca_id"), table_name="catalogo_vacunas")
    op.drop_table("catalogo_vacunas")
    op.drop_index(op.f("ix_catalogo_productos_bano_finca_id"), table_name="catalogo_productos_bano")
    op.drop_table("catalogo_productos_bano")
    op.drop_table("fincas")

    for nombre, _ in reversed(ENUMS):
        op.execute(f"DROP TYPE IF EXISTS {nombre}")

    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
    op.execute("DROP EXTENSION IF EXISTS pgcrypto")
