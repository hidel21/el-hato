"""Alertas y cola de sincronizacion del servidor."""

import uuid
from datetime import date, datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from app.modelos.base import ConIdentificador, ConMarcaTemporal, DeFinca, Sincronizable
from app.modelos.enumeraciones import EstadoAlerta, EstadoSync, OperacionSync, TipoAlerta, tipo_enum
from app.nucleo.base_datos import Base


class Alerta(ConIdentificador, Sincronizable, DeFinca, Base):
    """Decision 6: aqui vive el ESTADO de la alerta, no su calculo.

    Lo derivable de los datos (proxima dosis, fecha estimada de parto, dias de
    carencia, dias de ocupacion) lo calcula el cliente, que ya tiene los datos y
    funciona sin señal. Esta tabla guarda lo que debe viajar entre dispositivos
    y las alertas que exigen agregacion de toda la finca.
    """

    __tablename__ = "alertas"

    __table_args__ = (
        sa.Index(
            "idx_alertas_estado",
            "finca_id",
            "estado",
            "fecha_objetivo",
            postgresql_where=sa.text("is_deleted = false"),
        ),
    )

    tipo: Mapped[TipoAlerta] = mapped_column(tipo_enum(TipoAlerta), nullable=False)
    estado: Mapped[EstadoAlerta] = mapped_column(
        tipo_enum(EstadoAlerta), nullable=False, server_default="pendiente"
    )
    titulo: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    fecha_objetivo: Mapped[date | None] = mapped_column(sa.Date, nullable=True)

    animal_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("animales.id", ondelete="CASCADE"), nullable=True, index=True
    )
    grupo_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("grupos.id", ondelete="CASCADE"), nullable=True
    )
    potrero_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("potreros.id", ondelete="CASCADE"), nullable=True
    )
    # Apunta al registro que la origino sin obligar a una FK por cada tabla.
    referencia_tabla: Mapped[str | None] = mapped_column(sa.String(60), nullable=True)
    referencia_id: Mapped[uuid.UUID | None] = mapped_column(sa.Uuid, nullable=True)

    atendida_por_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    atendida_en: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)


class SyncQueue(ConIdentificador, ConMarcaTemporal, DeFinca, Base):
    """Bitacora de operaciones que el servidor recibe o debe entregar.

    Hoy solo existe la tabla: el motor que la consume es Fase 2.
    """

    __tablename__ = "sync_queue"

    __table_args__ = (sa.Index("idx_sync_queue_estado", "finca_id", "estado", "created_at"),)

    tabla: Mapped[str] = mapped_column(sa.String(60), nullable=False)
    registro_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, nullable=False)
    operacion: Mapped[OperacionSync] = mapped_column(tipo_enum(OperacionSync), nullable=False)
    estado: Mapped[EstadoSync] = mapped_column(
        tipo_enum(EstadoSync), nullable=False, server_default="pendiente"
    )
    contenido: Mapped[dict[str, Any] | None] = mapped_column(postgresql.JSONB, nullable=True)
    device_id: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    client_timestamp: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    client_timestamp_raw: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    intentos: Mapped[int] = mapped_column(sa.Integer, nullable=False, server_default=sa.text("0"))
    ultimo_error: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    procesado_en: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
