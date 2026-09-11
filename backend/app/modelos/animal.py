"""La ficha del animal: el centro del sistema."""

import uuid
from datetime import date
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modelos.base import ConIdentificador, DeFinca, Sincronizable
from app.modelos.enumeraciones import EstadoAnimal, Sexo, tipo_enum
from app.nucleo.base_datos import Base


class Animal(ConIdentificador, Sincronizable, DeFinca, Base):
    __tablename__ = "animales"

    __table_args__ = (
        # Decision 1: el arete es unico por finca solo entre los NO duplicados.
        sa.Index(
            "idx_animales_arete_unico",
            "finca_id",
            "arete",
            unique=True,
            postgresql_where=sa.text("is_deleted = false AND arete_duplicado = false"),
        ),
        # Busqueda por parecido: el capataz teclea 412 y encuentra C-0412.
        sa.Index(
            "idx_animales_arete_busqueda",
            "arete",
            postgresql_using="gin",
            postgresql_ops={"arete": "gin_trgm_ops"},
        ),
        # Orden del listado por cursor. Postgres recorre el btree al reves sin ayuda.
        sa.Index(
            "idx_animales_listado",
            "finca_id",
            "created_at",
            "id",
            postgresql_where=sa.text("is_deleted = false"),
        ),
        # Delta de sincronizacion: ?updated_since=
        sa.Index("idx_animales_actualizados", "finca_id", "updated_at", "id"),
    )

    arete: Mapped[str] = mapped_column(sa.String(40), nullable=False)
    # Decision 1: el servidor nunca rechaza un arete capturado en campo.
    # El duplicado entra marcado y queda fuera del indice unico parcial.
    arete_duplicado: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.text("false")
    )
    nombre: Mapped[str | None] = mapped_column(sa.String(120), nullable=True)
    sexo: Mapped[Sexo] = mapped_column(tipo_enum(Sexo), nullable=False)
    raza: Mapped[str | None] = mapped_column(sa.String(80), nullable=True)
    fecha_nacimiento: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
    estado: Mapped[EstadoAnimal] = mapped_column(
        tipo_enum(EstadoAnimal), nullable=False, server_default="activo"
    )

    grupo_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("grupos.id", ondelete="SET NULL"), nullable=True, index=True
    )
    potrero_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("potreros.id", ondelete="SET NULL"), nullable=True, index=True
    )
    madre_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("animales.id", ondelete="SET NULL"), nullable=True, index=True
    )
    padre_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("animales.id", ondelete="SET NULL"), nullable=True, index=True
    )

    peso_nacimiento_kg: Mapped[Decimal | None] = mapped_column(sa.Numeric(6, 2), nullable=True)
    peso_actual_kg: Mapped[Decimal | None] = mapped_column(sa.Numeric(7, 2), nullable=True)
    fecha_ingreso: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
    origen: Mapped[str | None] = mapped_column(sa.String(60), nullable=True)
    fecha_salida: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
    motivo_salida: Mapped[str | None] = mapped_column(sa.String(160), nullable=True)
    valor_compra: Mapped[Decimal | None] = mapped_column(sa.Numeric(12, 2), nullable=True)

    foto_url: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    # Decision 3: sin conexion la URL no sirve. Este id apunta al binario del dispositivo.
    foto_local_id: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)

    observaciones: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    # Cargadas con la ficha para no disparar una consulta por fila en el listado.
    grupo = relationship("Grupo", lazy="joined", foreign_keys=[grupo_id])
    potrero = relationship("Potrero", lazy="joined", foreign_keys=[potrero_id])
    madre = relationship(
        "Animal", lazy="joined", foreign_keys=[madre_id], remote_side="Animal.id", join_depth=1
    )
    padre = relationship(
        "Animal", lazy="joined", foreign_keys=[padre_id], remote_side="Animal.id", join_depth=1
    )
