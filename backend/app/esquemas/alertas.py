"""Entrada y salida de alertas.

Decision 6: lo derivable de los datos —proxima dosis, parto estimado, dias de
carencia, dias de ocupacion— lo calcula el CLIENTE, que ya tiene los datos y
funciona sin señal. Aqui solo vive el estado, que es lo que si tiene que viajar
entre dispositivos, y las alertas que nadie puede derivar solo.
"""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modelos.enumeraciones import EstadoAlerta, TipoAlerta


class AlertaCrear(BaseModel):
    """Sirve para dos cosas.

    Una: anotar un pendiente a mano («revisar la cerca del Palmar»).

    Dos, y es la importante: dejar constancia de que una alerta **derivada** ya
    se atendio. El cliente calcula «a C-0412 le toca refuerzo», la persona la
    marca, y se guarda aqui apuntando al registro que la origino. Asi el resto
    de dispositivos dejan de mostrarla.
    """

    id: uuid.UUID | None = None
    tipo: TipoAlerta
    titulo: str = Field(min_length=1, max_length=200)
    descripcion: str | None = None
    estado: EstadoAlerta = EstadoAlerta.pendiente
    fecha_objetivo: date | None = None

    animal_id: uuid.UUID | None = None
    grupo_id: uuid.UUID | None = None
    potrero_id: uuid.UUID | None = None
    referencia_tabla: str | None = Field(default=None, max_length=60)
    referencia_id: uuid.UUID | None = None

    device_id: str | None = Field(default=None, max_length=100)
    client_timestamp: datetime | None = None
    client_timestamp_raw: datetime | None = None

    @field_validator("titulo", "descripcion", "referencia_tabla")
    @classmethod
    def limpiar(cls, valor: str | None) -> str | None:
        return valor.strip() or None if valor else None


class AlertaActualizar(BaseModel):
    estado: EstadoAlerta | None = None
    titulo: str | None = Field(default=None, min_length=1, max_length=200)
    descripcion: str | None = None
    fecha_objetivo: date | None = None

    device_id: str | None = Field(default=None, max_length=100)
    client_timestamp: datetime | None = None
    client_timestamp_raw: datetime | None = None


class AlertaSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    finca_id: uuid.UUID
    tipo: TipoAlerta
    estado: EstadoAlerta
    titulo: str
    descripcion: str | None
    fecha_objetivo: date | None

    animal_id: uuid.UUID | None
    animal_arete: str | None = None
    grupo_id: uuid.UUID | None
    potrero_id: uuid.UUID | None
    referencia_tabla: str | None
    referencia_id: uuid.UUID | None

    atendida_por_id: uuid.UUID | None
    atendida_por_nombre: str | None = None
    atendida_en: datetime | None

    is_deleted: bool
    version: int
    device_id: str | None
    client_timestamp: datetime | None
    created_at: datetime
    updated_at: datetime
