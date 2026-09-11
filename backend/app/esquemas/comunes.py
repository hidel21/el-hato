"""Esquemas compartidos por todos los listados."""

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class Pagina(BaseModel, Generic[T]):
    """Sobre de todo listado. El cursor es opaco: no lo interpretes en el cliente."""

    model_config = ConfigDict(from_attributes=True)

    datos: list[T]
    cursor_siguiente: str | None = Field(
        default=None, description="Pasalo como ?cursor= para pedir la pagina siguiente."
    )
    hay_mas: bool = False


class DetalleError(BaseModel):
    code: str
    message: str


class RespuestaError(BaseModel):
    """Formato unico de error de toda la API."""

    error: DetalleError
