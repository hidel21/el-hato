"""Salida del inventario del hato."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.modelos.enumeraciones import EstadoAnimal, EtapaGrupo, Sexo


class FilaInventario(BaseModel):
    """Un renglon de la vista materializada, tal como esta agrupada."""

    grupo_id: uuid.UUID | None
    grupo_nombre: str | None
    grupo_etapa: EtapaGrupo | None
    potrero_id: uuid.UUID | None
    potrero_nombre: str | None
    sexo: Sexo
    estado: EstadoAnimal
    cantidad: int
    peso_total_kg: Decimal
    peso_promedio_kg: Decimal | None


class Corte(BaseModel):
    """Un conteo por alguna dimension, con su parte del hato."""

    clave: str
    etiqueta: str
    cantidad: int
    porcentaje: int


class Inventario(BaseModel):
    total_animales: int
    hembras: int
    machos: int
    peso_total_kg: Decimal
    peso_promedio_kg: Decimal | None

    por_etapa: list[Corte]
    por_potrero: list[Corte]
    por_estado: list[Corte]

    # Cuando se recalculo la vista. Puede ir hasta 30 segundos por detras de la
    # ultima escritura: el refresco es con debounce (decision 7).
    actualizado_en: datetime | None
    filas: list[FilaInventario]
