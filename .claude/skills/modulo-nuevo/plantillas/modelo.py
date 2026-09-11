"""Plantilla de modelo. Los mixins traen todo lo comun."""

import uuid
from datetime import date
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modelos.base import ConIdentificador, DeFinca, Sincronizable
from app.nucleo.base_datos import Base


class Modelo(ConIdentificador, Sincronizable, DeFinca, Base):
    """ConIdentificador da la PK UUID.
    Sincronizable da created_at, updated_at, is_deleted, deleted_at,
    device_id, version, client_timestamp y client_timestamp_raw.
    DeFinca da finca_id con su indice.
    """

    __tablename__ = "tabla"

    # Los indices parciales y de busqueda van aqui, no solo en la migracion:
    # asi alembic check detecta la deriva.
    __table_args__ = (
        sa.Index(
            "idx_tabla_vencimiento",
            "finca_id",
            "proxima_fecha",
            postgresql_where=sa.text("is_deleted = false AND proxima_fecha IS NOT NULL"),
        ),
    )

    animal_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("animales.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fecha: Mapped[date] = mapped_column(sa.Date, nullable=False)
    proxima_fecha: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
    cantidad: Mapped[Decimal | None] = mapped_column(sa.Numeric(10, 2), nullable=True)
    responsable_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    observaciones: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    # Cargada con la fila para no disparar una consulta por registro en el listado.
    animal = relationship("Animal", lazy="joined", foreign_keys=[animal_id])
