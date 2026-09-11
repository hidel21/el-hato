"""Mixins compartidos por todas las tablas.

Las columnas de sincronizacion existen desde el primer dia aunque el motor de
sincronizacion sea Fase 2: son el contrato que esa fase va a consumir.
"""

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, declared_attr, mapped_column


class ConIdentificador:
    """PK UUID generada en el cliente cuando exista; gen_random_uuid() de respaldo."""

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=sa.text("gen_random_uuid()"),
    )


class ConMarcaTemporal:
    """Auditoria y borrado logico. El borrado fisico no existe en este sistema."""

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
        onupdate=sa.func.now(),
    )
    is_deleted: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.text("false")
    )
    deleted_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)


class Sincronizable(ConMarcaTemporal):
    """Todo lo que un dispositivo puede crear o editar sin señal.

    client_timestamp es la hora del dispositivo ya corregida con su desfase;
    client_timestamp_raw es la que el telefono reporto, y se guarda para auditar.
    """

    device_id: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    version: Mapped[int] = mapped_column(sa.Integer, nullable=False, server_default=sa.text("1"))
    client_timestamp: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    client_timestamp_raw: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )


class DeFinca:
    """Aislamiento multi-tenant. Ninguna tabla raiz se queda sin esta columna."""

    @declared_attr.directive
    def finca_id(cls) -> Mapped[uuid.UUID]:
        return mapped_column(
            sa.Uuid, sa.ForeignKey("fincas.id", ondelete="RESTRICT"), nullable=False, index=True
        )
