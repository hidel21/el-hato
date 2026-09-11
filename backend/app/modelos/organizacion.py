"""Fincas, usuarios y dispositivos.

fincas y usuarios NO son sincronizables: en el cliente son de solo lectura
(decision 4). Si llevan marca temporal y borrado logico.
"""

import uuid
from datetime import datetime
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.modelos.base import ConIdentificador, ConMarcaTemporal, DeFinca
from app.modelos.enumeraciones import RolUsuario, tipo_enum
from app.nucleo.base_datos import Base


class Finca(ConIdentificador, ConMarcaTemporal, Base):
    __tablename__ = "fincas"

    nombre: Mapped[str] = mapped_column(sa.String(150), nullable=False)
    codigo: Mapped[str | None] = mapped_column(sa.String(30), nullable=True)
    municipio: Mapped[str | None] = mapped_column(sa.String(120), nullable=True)
    departamento: Mapped[str | None] = mapped_column(sa.String(120), nullable=True)
    pais: Mapped[str] = mapped_column(sa.String(80), nullable=False, server_default="Colombia")
    hectareas: Mapped[Decimal | None] = mapped_column(sa.Numeric(10, 2), nullable=True)
    zona_horaria: Mapped[str] = mapped_column(
        sa.String(60), nullable=False, server_default="America/Bogota"
    )
    moneda: Mapped[str] = mapped_column(sa.String(3), nullable=False, server_default="COP")


class Usuario(ConIdentificador, ConMarcaTemporal, DeFinca, Base):
    __tablename__ = "usuarios"

    __table_args__ = (
        sa.Index(
            "idx_usuarios_correo_unico",
            "correo",
            unique=True,
            postgresql_where=sa.text("is_deleted = false"),
        ),
    )

    nombre_completo: Mapped[str] = mapped_column(sa.String(150), nullable=False)
    correo: Mapped[str] = mapped_column(sa.String(180), nullable=False)
    clave_hash: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    rol: Mapped[RolUsuario] = mapped_column(tipo_enum(RolUsuario), nullable=False)
    telefono: Mapped[str | None] = mapped_column(sa.String(30), nullable=True)
    activo: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.text("true"))
    ultimo_acceso: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )


class Dispositivo(ConIdentificador, ConMarcaTemporal, DeFinca, Base):
    """Telefono o tablet registrado. desfase_reloj_ms es la correccion de la decision 2."""

    __tablename__ = "dispositivos"

    __table_args__ = (
        sa.Index(
            "idx_dispositivos_identificador_unico",
            "finca_id",
            "identificador",
            unique=True,
            postgresql_where=sa.text("is_deleted = false"),
        ),
    )

    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True
    )
    identificador: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    nombre: Mapped[str | None] = mapped_column(sa.String(120), nullable=True)
    plataforma: Mapped[str | None] = mapped_column(sa.String(40), nullable=True)
    desfase_reloj_ms: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default=sa.text("0")
    )
    ultima_sincronizacion: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
