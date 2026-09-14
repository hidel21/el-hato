"""Potreros, grupos y movimientos entre potreros."""

import uuid
from datetime import date
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modelos.base import ConIdentificador, DeFinca, Sincronizable
from app.modelos.enumeraciones import EtapaGrupo, PropositoGrupo, TipoPasto, tipo_enum
from app.nucleo.base_datos import Base


class Potrero(ConIdentificador, Sincronizable, DeFinca, Base):
    __tablename__ = "potreros"

    nombre: Mapped[str] = mapped_column(sa.String(120), nullable=False)
    hectareas: Mapped[Decimal] = mapped_column(sa.Numeric(10, 2), nullable=False)
    tipo_pasto: Mapped[TipoPasto | None] = mapped_column(tipo_enum(TipoPasto), nullable=True)
    capacidad_ugm_ha: Mapped[Decimal | None] = mapped_column(sa.Numeric(5, 2), nullable=True)
    dias_descanso_recomendado: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default=sa.text("30")
    )
    en_descanso: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.text("false")
    )
    fecha_ultimo_ingreso: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
    observaciones: Mapped[str | None] = mapped_column(sa.Text, nullable=True)


class Grupo(ConIdentificador, Sincronizable, DeFinca, Base):
    __tablename__ = "grupos"

    __table_args__ = (
        sa.Index(
            "idx_grupos_nombre_unico",
            "finca_id",
            "nombre",
            unique=True,
            postgresql_where=sa.text("is_deleted = false"),
        ),
    )

    nombre: Mapped[str] = mapped_column(sa.String(120), nullable=False)
    etapa: Mapped[EtapaGrupo] = mapped_column(tipo_enum(EtapaGrupo), nullable=False)
    proposito: Mapped[PropositoGrupo] = mapped_column(tipo_enum(PropositoGrupo), nullable=False)
    potrero_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("potreros.id", ondelete="SET NULL"), nullable=True, index=True
    )
    responsable_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    descripcion: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    potrero = relationship("Potrero", lazy="joined", foreign_keys=[potrero_id])
    responsable = relationship("Usuario", lazy="joined", foreign_keys=[responsable_id])


class PotreroMovimiento(ConIdentificador, Sincronizable, DeFinca, Base):
    """Un traslado de un grupo o de un animal suelto entre potreros."""

    __tablename__ = "potrero_movimientos"

    potrero_origen_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("potreros.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    potrero_destino_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("potreros.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    grupo_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("grupos.id", ondelete="SET NULL"), nullable=True, index=True
    )
    animal_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("animales.id", ondelete="SET NULL"), nullable=True, index=True
    )
    fecha_movimiento: Mapped[date] = mapped_column(sa.Date, nullable=False)
    cantidad_animales: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default=sa.text("0")
    )
    responsable_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    motivo: Mapped[str | None] = mapped_column(sa.String(160), nullable=True)
    observaciones: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    # Cargados con la fila: el historial de movimientos siempre se lee con los
    # nombres, y sin esto seria una consulta por renglon.
    potrero_origen = relationship("Potrero", lazy="joined", foreign_keys=[potrero_origen_id])
    potrero_destino = relationship("Potrero", lazy="joined", foreign_keys=[potrero_destino_id])
    grupo = relationship("Grupo", lazy="joined", foreign_keys=[grupo_id])
    animal = relationship("Animal", lazy="joined", foreign_keys=[animal_id])
