"""Entrada y salida del modulo de Animales."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modelos.enumeraciones import EstadoAnimal, Sexo


class AnimalCrear(BaseModel):
    """Alta de ficha.

    El id es opcional: si el dispositivo ya lo genero sin señal, se respeta.
    El arete nunca se rechaza por duplicado (decision 1).
    """

    id: uuid.UUID | None = None
    arete: str = Field(min_length=1, max_length=40)
    nombre: str | None = Field(default=None, max_length=120)
    sexo: Sexo
    raza: str | None = Field(default=None, max_length=80)
    fecha_nacimiento: date | None = None
    estado: EstadoAnimal = EstadoAnimal.activo

    grupo_id: uuid.UUID | None = None
    potrero_id: uuid.UUID | None = None
    madre_id: uuid.UUID | None = None
    padre_id: uuid.UUID | None = None

    peso_nacimiento_kg: Decimal | None = Field(default=None, ge=0, le=200)
    peso_actual_kg: Decimal | None = Field(default=None, ge=0, le=2000)
    fecha_ingreso: date | None = None
    origen: str | None = Field(default=None, max_length=60)
    valor_compra: Decimal | None = Field(default=None, ge=0)

    foto_url: str | None = Field(default=None, max_length=500)
    foto_local_id: str | None = Field(default=None, max_length=100)
    observaciones: str | None = None

    # Marcas del dispositivo (decision 2). Hoy se guardan tal cual; la
    # correccion de reloj la aplica la Fase 2.
    device_id: str | None = Field(default=None, max_length=100)
    client_timestamp: datetime | None = None
    client_timestamp_raw: datetime | None = None

    @field_validator("arete")
    @classmethod
    def limpiar_arete(cls, valor: str) -> str:
        limpio = valor.strip().upper()
        if not limpio:
            raise ValueError("el arete no puede quedar vacio")
        return limpio

    @field_validator("nombre", "raza", "origen")
    @classmethod
    def limpiar_texto(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        limpio = valor.strip()
        return limpio or None


class AnimalActualizar(BaseModel):
    """Edicion parcial: solo viaja lo que cambia."""

    arete: str | None = Field(default=None, min_length=1, max_length=40)
    nombre: str | None = Field(default=None, max_length=120)
    sexo: Sexo | None = None
    raza: str | None = Field(default=None, max_length=80)
    fecha_nacimiento: date | None = None
    estado: EstadoAnimal | None = None

    grupo_id: uuid.UUID | None = None
    potrero_id: uuid.UUID | None = None
    madre_id: uuid.UUID | None = None
    padre_id: uuid.UUID | None = None

    peso_nacimiento_kg: Decimal | None = Field(default=None, ge=0, le=200)
    peso_actual_kg: Decimal | None = Field(default=None, ge=0, le=2000)
    fecha_ingreso: date | None = None
    fecha_salida: date | None = None
    motivo_salida: str | None = Field(default=None, max_length=160)
    origen: str | None = Field(default=None, max_length=60)
    valor_compra: Decimal | None = Field(default=None, ge=0)

    foto_url: str | None = Field(default=None, max_length=500)
    foto_local_id: str | None = Field(default=None, max_length=100)
    observaciones: str | None = None

    device_id: str | None = Field(default=None, max_length=100)
    client_timestamp: datetime | None = None
    client_timestamp_raw: datetime | None = None

    @field_validator("arete")
    @classmethod
    def limpiar_arete(cls, valor: str | None) -> str | None:
        return valor.strip().upper() if valor else valor


class AnimalSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    finca_id: uuid.UUID
    arete: str
    arete_duplicado: bool
    nombre: str | None
    sexo: Sexo
    raza: str | None
    fecha_nacimiento: date | None
    estado: EstadoAnimal

    grupo_id: uuid.UUID | None
    grupo_nombre: str | None = None
    potrero_id: uuid.UUID | None
    potrero_nombre: str | None = None
    madre_id: uuid.UUID | None
    madre_arete: str | None = None
    padre_id: uuid.UUID | None
    padre_arete: str | None = None

    peso_nacimiento_kg: Decimal | None
    peso_actual_kg: Decimal | None
    fecha_ingreso: date | None
    fecha_salida: date | None
    motivo_salida: str | None
    origen: str | None
    valor_compra: Decimal | None

    foto_url: str | None
    foto_local_id: str | None
    observaciones: str | None

    is_deleted: bool
    version: int
    device_id: str | None
    client_timestamp: datetime | None
    created_at: datetime
    updated_at: datetime


class NodoGenealogia(BaseModel):
    """Un ancestro y, colgando de el, sus propios padres."""

    id: uuid.UUID
    arete: str
    nombre: str | None
    sexo: Sexo
    raza: str | None
    fecha_nacimiento: date | None
    madre: "NodoGenealogia | None" = None
    padre: "NodoGenealogia | None" = None


class RespuestaGenealogia(BaseModel):
    animal: NodoGenealogia
    niveles: int = Field(description="Generaciones de ancestros incluidas.")
