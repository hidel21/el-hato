"""Entrada y salida de pesajes y gastos."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modelos.enumeraciones import CategoriaGasto

METODOS_PESAJE = ("bascula", "cinta", "estimado")


class PesajeCrear(BaseModel):
    id: uuid.UUID | None = None
    animal_id: uuid.UUID
    fecha_pesaje: date | None = None
    peso_kg: Decimal = Field(gt=0, le=2000)
    metodo: str | None = Field(default=None, max_length=40)
    observaciones: str | None = None

    device_id: str | None = Field(default=None, max_length=100)
    client_timestamp: datetime | None = None
    client_timestamp_raw: datetime | None = None

    @field_validator("metodo")
    @classmethod
    def metodo_conocido(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        limpio = valor.strip().lower()
        if limpio and limpio not in METODOS_PESAJE:
            raise ValueError(f"el metodo debe ser uno de: {', '.join(METODOS_PESAJE)}")
        return limpio or None


class PesajeActualizar(BaseModel):
    fecha_pesaje: date | None = None
    peso_kg: Decimal | None = Field(default=None, gt=0, le=2000)
    metodo: str | None = Field(default=None, max_length=40)
    observaciones: str | None = None

    device_id: str | None = Field(default=None, max_length=100)
    client_timestamp: datetime | None = None
    client_timestamp_raw: datetime | None = None


class PesajeSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    finca_id: uuid.UUID
    animal_id: uuid.UUID
    animal_arete: str | None = None
    animal_nombre: str | None = None
    fecha_pesaje: date
    peso_kg: Decimal
    metodo: str | None
    # Ganancia diaria de peso respecto al pesaje anterior. Es el numero por el
    # que se pregunta en una finca de engorde.
    ganancia_diaria_kg: Decimal | None
    diferencia_kg: Decimal | None = None
    dias_desde_anterior: int | None = None
    responsable_id: uuid.UUID | None
    observaciones: str | None

    is_deleted: bool
    version: int
    device_id: str | None
    client_timestamp: datetime | None
    created_at: datetime
    updated_at: datetime


# ----------------------------------------------------------------------
# Gastos
# ----------------------------------------------------------------------


class GastoCrear(BaseModel):
    id: uuid.UUID | None = None
    categoria: CategoriaGasto
    concepto: str = Field(min_length=1, max_length=200)
    monto: Decimal = Field(gt=0, le=Decimal("9999999999"))
    fecha_gasto: date | None = None
    animal_id: uuid.UUID | None = None
    grupo_id: uuid.UUID | None = None
    potrero_id: uuid.UUID | None = None
    proveedor: str | None = Field(default=None, max_length=140)
    comprobante: str | None = Field(default=None, max_length=120)
    observaciones: str | None = None

    device_id: str | None = Field(default=None, max_length=100)
    client_timestamp: datetime | None = None
    client_timestamp_raw: datetime | None = None

    @field_validator("concepto", "proveedor", "comprobante")
    @classmethod
    def limpiar(cls, valor: str | None) -> str | None:
        return valor.strip() or None if valor else None


class GastoActualizar(BaseModel):
    categoria: CategoriaGasto | None = None
    concepto: str | None = Field(default=None, min_length=1, max_length=200)
    monto: Decimal | None = Field(default=None, gt=0)
    fecha_gasto: date | None = None
    animal_id: uuid.UUID | None = None
    grupo_id: uuid.UUID | None = None
    potrero_id: uuid.UUID | None = None
    proveedor: str | None = Field(default=None, max_length=140)
    comprobante: str | None = Field(default=None, max_length=120)
    observaciones: str | None = None

    device_id: str | None = Field(default=None, max_length=100)
    client_timestamp: datetime | None = None
    client_timestamp_raw: datetime | None = None


class GastoSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    finca_id: uuid.UUID
    categoria: CategoriaGasto
    concepto: str
    monto: Decimal
    fecha_gasto: date
    animal_id: uuid.UUID | None
    animal_arete: str | None = None
    grupo_id: uuid.UUID | None
    grupo_nombre: str | None = None
    potrero_id: uuid.UUID | None
    proveedor: str | None
    comprobante: str | None
    responsable_id: uuid.UUID | None
    observaciones: str | None

    is_deleted: bool
    version: int
    device_id: str | None
    client_timestamp: datetime | None
    created_at: datetime
    updated_at: datetime


class ResumenGastos(BaseModel):
    """Lo que se gasto, partido por categoria. Agregacion de finca completa."""

    total: Decimal
    desde: date | None
    hasta: date | None
    por_categoria: dict[str, Decimal]
    cantidad: int
