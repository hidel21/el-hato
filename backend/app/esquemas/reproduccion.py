"""Entrada y salida del ciclo reproductivo."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modelos.enumeraciones import (
    DificultadParto,
    MetodoCelo,
    ResultadoParto,
    ResultadoPrenez,
    Sexo,
)

TIPOS_SERVICIO = ("monta_natural", "inseminacion", "transferencia")
INTENSIDADES = ("baja", "media", "alta")


class _Sincronizable(BaseModel):
    device_id: str | None = Field(default=None, max_length=100)
    client_timestamp: datetime | None = None
    client_timestamp_raw: datetime | None = None


# ----------------------------------------------------------------------
# Celo
# ----------------------------------------------------------------------


class CeloCrear(_Sincronizable):
    id: uuid.UUID | None = None
    animal_id: uuid.UUID
    fecha_celo: date | None = None
    metodo: MetodoCelo = MetodoCelo.observacion
    intensidad: str | None = Field(default=None, max_length=20)
    observaciones: str | None = None

    @field_validator("intensidad")
    @classmethod
    def intensidad_conocida(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        limpio = valor.strip().lower()
        if limpio and limpio not in INTENSIDADES:
            raise ValueError(f"la intensidad debe ser: {', '.join(INTENSIDADES)}")
        return limpio or None


class CeloSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    finca_id: uuid.UUID
    animal_id: uuid.UUID
    animal_arete: str | None = None
    fecha_celo: date
    metodo: MetodoCelo
    intensidad: str | None
    responsable_id: uuid.UUID | None
    observaciones: str | None

    is_deleted: bool
    version: int
    device_id: str | None
    client_timestamp: datetime | None
    created_at: datetime
    updated_at: datetime


# ----------------------------------------------------------------------
# Servicio
# ----------------------------------------------------------------------


class ServicioCrear(_Sincronizable):
    id: uuid.UUID | None = None
    animal_id: uuid.UUID
    celo_id: uuid.UUID | None = None
    tipo: str = "monta_natural"
    fecha_servicio: date | None = None
    toro_id: uuid.UUID | None = None
    pajilla_codigo: str | None = Field(default=None, max_length=80)
    inseminador_id: uuid.UUID | None = None
    costo: Decimal | None = Field(default=None, ge=0)
    observaciones: str | None = None

    @field_validator("tipo")
    @classmethod
    def tipo_conocido(cls, valor: str) -> str:
        limpio = valor.strip().lower()
        if limpio not in TIPOS_SERVICIO:
            raise ValueError(f"el tipo debe ser: {', '.join(TIPOS_SERVICIO)}")
        return limpio


class ServicioSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    finca_id: uuid.UUID
    animal_id: uuid.UUID
    animal_arete: str | None = None
    celo_id: uuid.UUID | None
    tipo: str
    fecha_servicio: date
    toro_id: uuid.UUID | None
    toro_arete: str | None = None
    pajilla_codigo: str | None
    inseminador_id: uuid.UUID | None
    # fecha_servicio + 283 dias de gestacion. Es lo que deja al cliente avisar
    # del parto sin señal.
    fecha_estimada_parto: date | None
    costo: Decimal | None
    observaciones: str | None

    is_deleted: bool
    version: int
    device_id: str | None
    client_timestamp: datetime | None
    created_at: datetime
    updated_at: datetime


# ----------------------------------------------------------------------
# Diagnostico de preñez
# ----------------------------------------------------------------------


class DiagnosticoCrear(_Sincronizable):
    id: uuid.UUID | None = None
    animal_id: uuid.UUID
    servicio_id: uuid.UUID | None = None
    fecha_diagnostico: date | None = None
    resultado: ResultadoPrenez
    metodo: str | None = Field(default=None, max_length=40)
    dias_gestacion: int | None = Field(default=None, ge=1, le=300)
    observaciones: str | None = None


class DiagnosticoSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    finca_id: uuid.UUID
    animal_id: uuid.UUID
    animal_arete: str | None = None
    servicio_id: uuid.UUID | None
    fecha_diagnostico: date
    resultado: ResultadoPrenez
    metodo: str | None
    dias_gestacion: int | None
    fecha_estimada_parto: date | None
    responsable_id: uuid.UUID | None
    observaciones: str | None

    is_deleted: bool
    version: int
    device_id: str | None
    client_timestamp: datetime | None
    created_at: datetime
    updated_at: datetime


# ----------------------------------------------------------------------
# Parto
# ----------------------------------------------------------------------


class CriaNueva(BaseModel):
    """Los datos con los que se abre la ficha del ternero recien nacido."""

    arete: str = Field(min_length=1, max_length=40)
    nombre: str | None = Field(default=None, max_length=120)
    sexo: Sexo
    peso_nacimiento_kg: Decimal | None = Field(default=None, gt=0, le=100)

    @field_validator("arete")
    @classmethod
    def limpiar_arete(cls, valor: str) -> str:
        return valor.strip().upper()


class PartoCrear(_Sincronizable):
    id: uuid.UUID | None = None
    madre_id: uuid.UUID
    diagnostico_id: uuid.UUID | None = None
    fecha_parto: date | None = None
    resultado: ResultadoParto = ResultadoParto.vivo
    dificultad: DificultadParto = DificultadParto.normal
    peso_nacimiento_kg: Decimal | None = Field(default=None, gt=0, le=100)
    observaciones: str | None = None

    # Si viene, se abre la ficha del ternero y queda enlazada a la madre y al
    # toro del servicio. Es el atajo que evita capturar el nacimiento dos veces.
    cria: CriaNueva | None = None
    # O se enlaza una ficha que ya existe.
    cria_id: uuid.UUID | None = None


class PartoSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    finca_id: uuid.UUID
    madre_id: uuid.UUID
    madre_arete: str | None = None
    diagnostico_id: uuid.UUID | None
    cria_id: uuid.UUID | None
    cria_arete: str | None = None
    fecha_parto: date
    resultado: ResultadoParto
    dificultad: DificultadParto
    peso_nacimiento_kg: Decimal | None
    responsable_id: uuid.UUID | None
    observaciones: str | None

    # Dias desde el parto anterior de la misma madre. Es EL indicador de un
    # hato de cria: lo ideal esta entre 365 y 400 dias.
    intervalo_partos_dias: int | None = None

    is_deleted: bool
    version: int
    device_id: str | None
    client_timestamp: datetime | None
    created_at: datetime
    updated_at: datetime


# ----------------------------------------------------------------------
# Hoja reproductiva del animal
# ----------------------------------------------------------------------


class EventoReproductivo(BaseModel):
    """Un renglon de la linea de tiempo, sea del tipo que sea."""

    tipo: str
    fecha: date
    titulo: str
    detalle: str | None = None
    referencia_id: uuid.UUID


class HojaReproductiva(BaseModel):
    """Todo el historial reproductivo de una hembra, en una sola llamada."""

    animal_id: uuid.UUID
    arete: str
    # vacia | en_servicio | prenada | parida | sin_registros
    estado: str
    descripcion_estado: str

    ultimo_celo: date | None = None
    ultimo_servicio: date | None = None
    ultimo_diagnostico: ResultadoPrenez | None = None
    fecha_estimada_parto: date | None = None
    ultimo_parto: date | None = None
    dias_abiertos: int | None = None
    partos_totales: int = 0
    intervalo_promedio_dias: int | None = None

    eventos: list[EventoReproductivo]
