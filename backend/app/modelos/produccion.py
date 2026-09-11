"""Pesajes y gastos."""

import uuid
from datetime import date
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.modelos.base import ConIdentificador, DeFinca, Sincronizable
from app.modelos.enumeraciones import CategoriaGasto, tipo_enum
from app.nucleo.base_datos import Base


class Pesaje(ConIdentificador, Sincronizable, DeFinca, Base):
    __tablename__ = "pesajes"

    __table_args__ = (
        sa.Index(
            "idx_pesajes_animal_fecha",
            "animal_id",
            "fecha_pesaje",
            postgresql_where=sa.text("is_deleted = false"),
        ),
    )

    animal_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("animales.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fecha_pesaje: Mapped[date] = mapped_column(sa.Date, nullable=False)
    peso_kg: Mapped[Decimal] = mapped_column(sa.Numeric(7, 2), nullable=False)
    metodo: Mapped[str | None] = mapped_column(sa.String(40), nullable=True)
    # Se guarda calculada para no recorrer el historico en cada listado.
    ganancia_diaria_kg: Mapped[Decimal | None] = mapped_column(sa.Numeric(6, 3), nullable=True)
    responsable_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    observaciones: Mapped[str | None] = mapped_column(sa.Text, nullable=True)


class Gasto(ConIdentificador, Sincronizable, DeFinca, Base):
    __tablename__ = "gastos"

    categoria: Mapped[CategoriaGasto] = mapped_column(tipo_enum(CategoriaGasto), nullable=False)
    concepto: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    monto: Mapped[Decimal] = mapped_column(sa.Numeric(12, 2), nullable=False)
    fecha_gasto: Mapped[date] = mapped_column(sa.Date, nullable=False)
    animal_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("animales.id", ondelete="SET NULL"), nullable=True, index=True
    )
    grupo_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("grupos.id", ondelete="SET NULL"), nullable=True, index=True
    )
    potrero_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("potreros.id", ondelete="SET NULL"), nullable=True
    )
    proveedor: Mapped[str | None] = mapped_column(sa.String(140), nullable=True)
    comprobante: Mapped[str | None] = mapped_column(sa.String(120), nullable=True)
    responsable_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    observaciones: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
