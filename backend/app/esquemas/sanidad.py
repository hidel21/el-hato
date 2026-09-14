"""Entrada y salida de vacunacion y baños sanitarios."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _limpiar(valor: str | None) -> str | None:
    return valor.strip() or None if valor else None


class _Sincronizable(BaseModel):
    device_id: str | None = Field(default=None, max_length=100)
    client_timestamp: datetime | None = None
    client_timestamp_raw: datetime | None = None


# ----------------------------------------------------------------------
# Catalogo de vacunas
# ----------------------------------------------------------------------


class VacunaCrear(_Sincronizable):
    id: uuid.UUID | None = None
    nombre: str = Field(min_length=1, max_length=140)
    enfermedad: str | None = Field(default=None, max_length=140)
    laboratorio: str | None = Field(default=None, max_length=140)
    via_aplicacion: str | None = Field(default=None, max_length=60)
    dosis_ml: Decimal | None = Field(default=None, gt=0, le=1000)
    # Cada cuantos dias toca el refuerzo. Es lo que deja al cliente calcular la
    # proxima dosis sin señal (decision 6).
    dias_refuerzo: int | None = Field(default=None, ge=1, le=3650)
    dias_carencia: int = Field(default=0, ge=0, le=365)
    obligatoria: bool = False
    activo: bool = True

    @field_validator("nombre", "enfermedad", "laboratorio", "via_aplicacion")
    @classmethod
    def limpiar(cls, valor: str | None) -> str | None:
        return _limpiar(valor)


class VacunaActualizar(_Sincronizable):
    nombre: str | None = Field(default=None, min_length=1, max_length=140)
    enfermedad: str | None = Field(default=None, max_length=140)
    laboratorio: str | None = Field(default=None, max_length=140)
    via_aplicacion: str | None = Field(default=None, max_length=60)
    dosis_ml: Decimal | None = Field(default=None, gt=0, le=1000)
    dias_refuerzo: int | None = Field(default=None, ge=1, le=3650)
    dias_carencia: int | None = Field(default=None, ge=0, le=365)
    obligatoria: bool | None = None
    activo: bool | None = None


class VacunaSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    finca_id: uuid.UUID
    nombre: str
    enfermedad: str | None
    laboratorio: str | None
    via_aplicacion: str | None
    dosis_ml: Decimal | None
    dias_refuerzo: int | None
    dias_carencia: int
    obligatoria: bool
    activo: bool

    is_deleted: bool
    version: int
    device_id: str | None
    client_timestamp: datetime | None
    created_at: datetime
    updated_at: datetime


# ----------------------------------------------------------------------
# Aplicaciones de vacuna
# ----------------------------------------------------------------------


class AplicacionBase(_Sincronizable):
    """Una aplicacion va a un animal o a un lote, nunca a los dos ni a ninguno."""

    id: uuid.UUID | None = None
    animal_id: uuid.UUID | None = None
    grupo_id: uuid.UUID | None = None
    observaciones: str | None = None

    @model_validator(mode="after")
    def uno_u_otro(self):
        if bool(self.animal_id) == bool(self.grupo_id):
            raise ValueError("indica un animal o un lote, pero no los dos")
        return self


class VacunacionCrear(AplicacionBase):
    catalogo_vacuna_id: uuid.UUID
    fecha_aplicacion: date | None = None
    # Si no viene, se calcula con los dias de refuerzo del catalogo.
    proxima_dosis_fecha: date | None = None
    dosis_ml: Decimal | None = Field(default=None, gt=0, le=1000)
    lote_producto: str | None = Field(default=None, max_length=80)
    costo_total: Decimal | None = Field(default=None, ge=0)


class VacunacionSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    finca_id: uuid.UUID
    catalogo_vacuna_id: uuid.UUID
    vacuna_nombre: str | None = None
    enfermedad: str | None = None
    animal_id: uuid.UUID | None
    animal_arete: str | None = None
    grupo_id: uuid.UUID | None
    grupo_nombre: str | None = None
    fecha_aplicacion: date
    proxima_dosis_fecha: date | None
    dosis_ml: Decimal | None
    lote_producto: str | None
    cantidad_animales: int
    costo_total: Decimal | None
    responsable_id: uuid.UUID | None
    observaciones: str | None

    is_deleted: bool
    version: int
    device_id: str | None
    client_timestamp: datetime | None
    created_at: datetime
    updated_at: datetime


# ----------------------------------------------------------------------
# Catalogo de productos de baño
# ----------------------------------------------------------------------


class ProductoBanoCrear(_Sincronizable):
    id: uuid.UUID | None = None
    nombre: str = Field(min_length=1, max_length=140)
    principio_activo: str | None = Field(default=None, max_length=140)
    laboratorio: str | None = Field(default=None, max_length=140)
    tipo: str | None = Field(default=None, max_length=60)
    dosis_por_litro_ml: Decimal | None = Field(default=None, gt=0, le=10000)
    # Dias que hay que esperar antes de mandar el animal a sacrificio o de
    # aprovechar su leche. Es lo que evita un decomiso.
    dias_carencia_carne: int = Field(default=0, ge=0, le=365)
    dias_carencia_leche: int = Field(default=0, ge=0, le=365)
    dias_reaplicacion: int | None = Field(default=None, ge=1, le=365)
    activo: bool = True

    @field_validator("nombre", "principio_activo", "laboratorio", "tipo")
    @classmethod
    def limpiar(cls, valor: str | None) -> str | None:
        return _limpiar(valor)


class ProductoBanoActualizar(_Sincronizable):
    nombre: str | None = Field(default=None, min_length=1, max_length=140)
    principio_activo: str | None = Field(default=None, max_length=140)
    laboratorio: str | None = Field(default=None, max_length=140)
    tipo: str | None = Field(default=None, max_length=60)
    dosis_por_litro_ml: Decimal | None = Field(default=None, gt=0, le=10000)
    dias_carencia_carne: int | None = Field(default=None, ge=0, le=365)
    dias_carencia_leche: int | None = Field(default=None, ge=0, le=365)
    dias_reaplicacion: int | None = Field(default=None, ge=1, le=365)
    activo: bool | None = None


class ProductoBanoSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    finca_id: uuid.UUID
    nombre: str
    principio_activo: str | None
    laboratorio: str | None
    tipo: str | None
    dosis_por_litro_ml: Decimal | None
    dias_carencia_carne: int
    dias_carencia_leche: int
    dias_reaplicacion: int | None
    activo: bool

    is_deleted: bool
    version: int
    device_id: str | None
    client_timestamp: datetime | None
    created_at: datetime
    updated_at: datetime


# ----------------------------------------------------------------------
# Baños
# ----------------------------------------------------------------------


class BanoCrear(_Sincronizable):
    """Un baño se aplica a un lote, a un potrero entero o a un animal."""

    id: uuid.UUID | None = None
    producto_id: uuid.UUID
    grupo_id: uuid.UUID | None = None
    potrero_id: uuid.UUID | None = None
    animal_id: uuid.UUID | None = None
    fecha_bano: date | None = None
    proxima_fecha: date | None = None
    metodo: str | None = Field(default=None, max_length=40)
    dosis_total_ml: Decimal | None = Field(default=None, ge=0)
    litros_agua: Decimal | None = Field(default=None, ge=0)
    costo_total: Decimal | None = Field(default=None, ge=0)
    observaciones: str | None = None

    @model_validator(mode="after")
    def a_quien(self):
        elegidos = [bool(self.grupo_id), bool(self.potrero_id), bool(self.animal_id)]
        if sum(elegidos) != 1:
            raise ValueError("indica un lote, un potrero o un animal: solo uno")
        return self


class BanoSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    finca_id: uuid.UUID
    producto_id: uuid.UUID
    producto_nombre: str | None = None
    grupo_id: uuid.UUID | None
    grupo_nombre: str | None = None
    potrero_id: uuid.UUID | None
    potrero_nombre: str | None = None
    fecha_bano: date
    proxima_fecha: date | None
    metodo: str | None
    dosis_total_ml: Decimal | None
    litros_agua: Decimal | None
    cantidad_animales: int
    costo_total: Decimal | None
    responsable_id: uuid.UUID | None
    observaciones: str | None

    # Hasta cuando no se puede vender la carne ni aprovechar la leche.
    carencia_carne_hasta: date | None = None
    carencia_leche_hasta: date | None = None

    is_deleted: bool
    version: int
    device_id: str | None
    client_timestamp: datetime | None
    created_at: datetime
    updated_at: datetime


class AnimalAplicado(BaseModel):
    """Un animal que recibio la aplicacion, congelado en ese momento."""

    model_config = ConfigDict(from_attributes=True)

    animal_id: uuid.UUID
    arete: str
    nombre: str | None
