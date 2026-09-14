"""Entrada y salida de potreros, lotes y movimientos entre potreros."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modelos.enumeraciones import EtapaGrupo, PropositoGrupo, TipoPasto


def _limpiar(valor: str | None) -> str | None:
    if valor is None:
        return None
    return valor.strip() or None


# ----------------------------------------------------------------------
# Potreros
# ----------------------------------------------------------------------


class PotreroCrear(BaseModel):
    id: uuid.UUID | None = None
    nombre: str = Field(min_length=1, max_length=120)
    hectareas: Decimal = Field(gt=0, le=100000)
    tipo_pasto: TipoPasto | None = None
    capacidad_ugm_ha: Decimal | None = Field(default=None, gt=0, le=20)
    dias_descanso_recomendado: int = Field(default=30, ge=1, le=365)
    en_descanso: bool = False
    fecha_ultimo_ingreso: date | None = None
    observaciones: str | None = None

    device_id: str | None = Field(default=None, max_length=100)
    client_timestamp: datetime | None = None
    client_timestamp_raw: datetime | None = None

    @field_validator("nombre", "observaciones")
    @classmethod
    def limpiar(cls, valor: str | None) -> str | None:
        return _limpiar(valor)


class PotreroActualizar(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    hectareas: Decimal | None = Field(default=None, gt=0, le=100000)
    tipo_pasto: TipoPasto | None = None
    capacidad_ugm_ha: Decimal | None = Field(default=None, gt=0, le=20)
    dias_descanso_recomendado: int | None = Field(default=None, ge=1, le=365)
    en_descanso: bool | None = None
    fecha_ultimo_ingreso: date | None = None
    observaciones: str | None = None

    device_id: str | None = Field(default=None, max_length=100)
    client_timestamp: datetime | None = None
    client_timestamp_raw: datetime | None = None

    @field_validator("nombre", "observaciones")
    @classmethod
    def limpiar(cls, valor: str | None) -> str | None:
        return _limpiar(valor)


class PotreroSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    finca_id: uuid.UUID
    nombre: str
    hectareas: Decimal
    tipo_pasto: TipoPasto | None
    capacidad_ugm_ha: Decimal | None
    dias_descanso_recomendado: int
    en_descanso: bool
    fecha_ultimo_ingreso: date | None
    observaciones: str | None

    # Agregaciones de toda la finca: esto el dispositivo no lo puede derivar
    # solo, asi que lo calcula el servidor (decision 6). Los dias de ocupacion
    # si los deriva el cliente desde fecha_ultimo_ingreso.
    cantidad_animales: int = 0
    peso_total_kg: Decimal = Decimal("0")
    carga_ugm_ha: Decimal | None = None
    lotes: list[str] = Field(default_factory=list)

    is_deleted: bool
    version: int
    device_id: str | None
    client_timestamp: datetime | None
    created_at: datetime
    updated_at: datetime


# ----------------------------------------------------------------------
# Lotes (grupos)
# ----------------------------------------------------------------------


class GrupoCrear(BaseModel):
    id: uuid.UUID | None = None
    nombre: str = Field(min_length=1, max_length=120)
    etapa: EtapaGrupo
    proposito: PropositoGrupo
    potrero_id: uuid.UUID | None = None
    responsable_id: uuid.UUID | None = None
    descripcion: str | None = None

    device_id: str | None = Field(default=None, max_length=100)
    client_timestamp: datetime | None = None
    client_timestamp_raw: datetime | None = None

    @field_validator("nombre", "descripcion")
    @classmethod
    def limpiar(cls, valor: str | None) -> str | None:
        return _limpiar(valor)


class GrupoActualizar(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    etapa: EtapaGrupo | None = None
    proposito: PropositoGrupo | None = None
    potrero_id: uuid.UUID | None = None
    responsable_id: uuid.UUID | None = None
    descripcion: str | None = None

    device_id: str | None = Field(default=None, max_length=100)
    client_timestamp: datetime | None = None
    client_timestamp_raw: datetime | None = None

    @field_validator("nombre", "descripcion")
    @classmethod
    def limpiar(cls, valor: str | None) -> str | None:
        return _limpiar(valor)


class GrupoSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    finca_id: uuid.UUID
    nombre: str
    etapa: EtapaGrupo
    proposito: PropositoGrupo
    potrero_id: uuid.UUID | None
    potrero_nombre: str | None = None
    responsable_id: uuid.UUID | None
    responsable_nombre: str | None = None
    descripcion: str | None

    cantidad_animales: int = 0

    is_deleted: bool
    version: int
    device_id: str | None
    client_timestamp: datetime | None
    created_at: datetime
    updated_at: datetime


# ----------------------------------------------------------------------
# Movimientos entre potreros
# ----------------------------------------------------------------------


class MovimientoCrear(BaseModel):
    """Traslado de un lote completo o de un animal suelto.

    Va uno de los dos, nunca los dos ni ninguno: o se mueve el lote entero o se
    mueve un animal.
    """

    id: uuid.UUID | None = None
    potrero_destino_id: uuid.UUID
    grupo_id: uuid.UUID | None = None
    animal_id: uuid.UUID | None = None
    fecha_movimiento: date | None = None
    motivo: str | None = Field(default=None, max_length=160)
    observaciones: str | None = None

    device_id: str | None = Field(default=None, max_length=100)
    client_timestamp: datetime | None = None
    client_timestamp_raw: datetime | None = None

    @field_validator("motivo", "observaciones")
    @classmethod
    def limpiar(cls, valor: str | None) -> str | None:
        return _limpiar(valor)

    @model_validator(mode="after")
    def uno_u_otro(self) -> "MovimientoCrear":
        if bool(self.grupo_id) == bool(self.animal_id):
            raise ValueError("indica un lote o un animal, pero no los dos")
        return self


class MovimientoSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    finca_id: uuid.UUID
    potrero_origen_id: uuid.UUID | None
    potrero_origen_nombre: str | None = None
    potrero_destino_id: uuid.UUID
    potrero_destino_nombre: str | None = None
    grupo_id: uuid.UUID | None
    grupo_nombre: str | None = None
    animal_id: uuid.UUID | None
    animal_arete: str | None = None
    fecha_movimiento: date
    cantidad_animales: int
    responsable_id: uuid.UUID | None
    motivo: str | None
    observaciones: str | None

    is_deleted: bool
    version: int
    device_id: str | None
    client_timestamp: datetime | None
    created_at: datetime
    updated_at: datetime
