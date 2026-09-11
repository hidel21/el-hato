"""Vacunaciones y baños, con sus catalogos y sus tablas puente.

Decision 8: una aplicacion por lote materializa la membresia en el momento,
porque el grupo cambia al dia siguiente y la trazabilidad se perderia.
"""

import uuid
from datetime import date
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.modelos.base import ConIdentificador, DeFinca, Sincronizable
from app.nucleo.base_datos import Base


class CatalogoVacuna(ConIdentificador, Sincronizable, DeFinca, Base):
    """Decision 4: sincronizable, porque un veterinario crea entradas sin señal."""

    __tablename__ = "catalogo_vacunas"

    nombre: Mapped[str] = mapped_column(sa.String(140), nullable=False)
    enfermedad: Mapped[str | None] = mapped_column(sa.String(140), nullable=True)
    laboratorio: Mapped[str | None] = mapped_column(sa.String(140), nullable=True)
    via_aplicacion: Mapped[str | None] = mapped_column(sa.String(60), nullable=True)
    dosis_ml: Mapped[Decimal | None] = mapped_column(sa.Numeric(6, 2), nullable=True)
    dias_refuerzo: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    dias_carencia: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default=sa.text("0")
    )
    obligatoria: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.text("false")
    )
    activo: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.text("true"))


class Vacunacion(ConIdentificador, Sincronizable, DeFinca, Base):
    __tablename__ = "vacunaciones"

    __table_args__ = (
        sa.Index(
            "idx_vacunaciones_proxima_dosis",
            "finca_id",
            "proxima_dosis_fecha",
            postgresql_where=sa.text("is_deleted = false AND proxima_dosis_fecha IS NOT NULL"),
        ),
    )

    catalogo_vacuna_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("catalogo_vacunas.id", ondelete="RESTRICT"), nullable=False
    )
    animal_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("animales.id", ondelete="SET NULL"), nullable=True, index=True
    )
    grupo_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("grupos.id", ondelete="SET NULL"), nullable=True, index=True
    )
    fecha_aplicacion: Mapped[date] = mapped_column(sa.Date, nullable=False)
    proxima_dosis_fecha: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
    dosis_ml: Mapped[Decimal | None] = mapped_column(sa.Numeric(6, 2), nullable=True)
    lote_producto: Mapped[str | None] = mapped_column(sa.String(80), nullable=True)
    cantidad_animales: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default=sa.text("1")
    )
    costo_total: Mapped[Decimal | None] = mapped_column(sa.Numeric(12, 2), nullable=True)
    responsable_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    observaciones: Mapped[str | None] = mapped_column(sa.Text, nullable=True)


class VacunacionAnimal(ConIdentificador, Sincronizable, DeFinca, Base):
    __tablename__ = "vacunacion_animales"

    __table_args__ = (
        sa.Index(
            "idx_vacunacion_animales_unico",
            "vacunacion_id",
            "animal_id",
            unique=True,
            postgresql_where=sa.text("is_deleted = false"),
        ),
    )

    vacunacion_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("vacunaciones.id", ondelete="CASCADE"), nullable=False, index=True
    )
    animal_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("animales.id", ondelete="CASCADE"), nullable=False, index=True
    )


class CatalogoProductoBano(ConIdentificador, Sincronizable, DeFinca, Base):
    """Decision 4: sincronizable por el mismo motivo que el catalogo de vacunas."""

    __tablename__ = "catalogo_productos_bano"

    nombre: Mapped[str] = mapped_column(sa.String(140), nullable=False)
    principio_activo: Mapped[str | None] = mapped_column(sa.String(140), nullable=True)
    laboratorio: Mapped[str | None] = mapped_column(sa.String(140), nullable=True)
    tipo: Mapped[str | None] = mapped_column(sa.String(60), nullable=True)
    dosis_por_litro_ml: Mapped[Decimal | None] = mapped_column(sa.Numeric(7, 2), nullable=True)
    dias_carencia_carne: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default=sa.text("0")
    )
    dias_carencia_leche: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default=sa.text("0")
    )
    dias_reaplicacion: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    activo: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.text("true"))


class Bano(ConIdentificador, Sincronizable, DeFinca, Base):
    __tablename__ = "banos"

    __table_args__ = (
        sa.Index(
            "idx_banos_proxima_fecha",
            "finca_id",
            "proxima_fecha",
            postgresql_where=sa.text("is_deleted = false AND proxima_fecha IS NOT NULL"),
        ),
    )

    producto_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("catalogo_productos_bano.id", ondelete="RESTRICT"), nullable=False
    )
    grupo_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("grupos.id", ondelete="SET NULL"), nullable=True, index=True
    )
    potrero_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("potreros.id", ondelete="SET NULL"), nullable=True, index=True
    )
    fecha_bano: Mapped[date] = mapped_column(sa.Date, nullable=False)
    proxima_fecha: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
    metodo: Mapped[str | None] = mapped_column(sa.String(40), nullable=True)
    dosis_total_ml: Mapped[Decimal | None] = mapped_column(sa.Numeric(10, 2), nullable=True)
    litros_agua: Mapped[Decimal | None] = mapped_column(sa.Numeric(10, 2), nullable=True)
    cantidad_animales: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default=sa.text("0")
    )
    costo_total: Mapped[Decimal | None] = mapped_column(sa.Numeric(12, 2), nullable=True)
    responsable_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    observaciones: Mapped[str | None] = mapped_column(sa.Text, nullable=True)


class BanoAnimal(ConIdentificador, Sincronizable, DeFinca, Base):
    __tablename__ = "bano_animales"

    __table_args__ = (
        sa.Index(
            "idx_bano_animales_unico",
            "bano_id",
            "animal_id",
            unique=True,
            postgresql_where=sa.text("is_deleted = false"),
        ),
    )

    bano_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("banos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    animal_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("animales.id", ondelete="CASCADE"), nullable=False, index=True
    )
