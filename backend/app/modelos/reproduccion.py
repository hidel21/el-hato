"""Ciclo reproductivo completo: celo, servicio, diagnostico y parto.

Decision 5: sin la tabla partos no hay intervalo entre partos, que es el
indicador central de un hato de cria. El ciclo no termina en el diagnostico.
"""

import uuid
from datetime import date
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.modelos.base import ConIdentificador, DeFinca, Sincronizable
from app.modelos.enumeraciones import (
    DificultadParto,
    MetodoCelo,
    ResultadoParto,
    ResultadoPrenez,
    tipo_enum,
)
from app.nucleo.base_datos import Base


class Celo(ConIdentificador, Sincronizable, DeFinca, Base):
    __tablename__ = "celos"

    animal_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("animales.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fecha_celo: Mapped[date] = mapped_column(sa.Date, nullable=False)
    metodo: Mapped[MetodoCelo] = mapped_column(tipo_enum(MetodoCelo), nullable=False)
    intensidad: Mapped[str | None] = mapped_column(sa.String(20), nullable=True)
    responsable_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    observaciones: Mapped[str | None] = mapped_column(sa.Text, nullable=True)


class ServicioReproductivo(ConIdentificador, Sincronizable, DeFinca, Base):
    __tablename__ = "servicios_reproductivos"

    __table_args__ = (
        sa.Index(
            "idx_servicios_fecha_estimada_parto",
            "finca_id",
            "fecha_estimada_parto",
            postgresql_where=sa.text("is_deleted = false AND fecha_estimada_parto IS NOT NULL"),
        ),
    )

    animal_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("animales.id", ondelete="CASCADE"), nullable=False, index=True
    )
    celo_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("celos.id", ondelete="SET NULL"), nullable=True
    )
    tipo: Mapped[str] = mapped_column(sa.String(30), nullable=False)
    fecha_servicio: Mapped[date] = mapped_column(sa.Date, nullable=False)
    toro_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("animales.id", ondelete="SET NULL"), nullable=True
    )
    pajilla_codigo: Mapped[str | None] = mapped_column(sa.String(80), nullable=True)
    inseminador_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    fecha_estimada_parto: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
    costo: Mapped[Decimal | None] = mapped_column(sa.Numeric(12, 2), nullable=True)
    observaciones: Mapped[str | None] = mapped_column(sa.Text, nullable=True)


class DiagnosticoPrenez(ConIdentificador, Sincronizable, DeFinca, Base):
    __tablename__ = "diagnosticos_prenez"

    __table_args__ = (
        sa.Index(
            "idx_diagnosticos_fecha_estimada_parto",
            "finca_id",
            "fecha_estimada_parto",
            postgresql_where=sa.text("is_deleted = false AND fecha_estimada_parto IS NOT NULL"),
        ),
    )

    animal_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("animales.id", ondelete="CASCADE"), nullable=False, index=True
    )
    servicio_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("servicios_reproductivos.id", ondelete="SET NULL"), nullable=True
    )
    fecha_diagnostico: Mapped[date] = mapped_column(sa.Date, nullable=False)
    resultado: Mapped[ResultadoPrenez] = mapped_column(tipo_enum(ResultadoPrenez), nullable=False)
    metodo: Mapped[str | None] = mapped_column(sa.String(40), nullable=True)
    dias_gestacion: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    fecha_estimada_parto: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
    responsable_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    observaciones: Mapped[str | None] = mapped_column(sa.Text, nullable=True)


class Parto(ConIdentificador, Sincronizable, DeFinca, Base):
    __tablename__ = "partos"

    madre_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("animales.id", ondelete="CASCADE"), nullable=False, index=True
    )
    diagnostico_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("diagnosticos_prenez.id", ondelete="SET NULL"), nullable=True
    )
    cria_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("animales.id", ondelete="SET NULL"), nullable=True, index=True
    )
    fecha_parto: Mapped[date] = mapped_column(sa.Date, nullable=False)
    resultado: Mapped[ResultadoParto] = mapped_column(tipo_enum(ResultadoParto), nullable=False)
    dificultad: Mapped[DificultadParto] = mapped_column(
        tipo_enum(DificultadParto), nullable=False, server_default="normal"
    )
    peso_nacimiento_kg: Mapped[Decimal | None] = mapped_column(sa.Numeric(6, 2), nullable=True)
    responsable_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    observaciones: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
