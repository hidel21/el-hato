"""Paginacion por cursor. Nunca offset.

Dos modos, y el cursor lleva dentro cual es para que no se mezclen:

- «reciente»: orden (created_at DESC, id DESC). Lo ultimo dado de alta primero,
  que es lo que el capataz espera ver.
- «delta»: se activa con ?updated_since=. Orden (updated_at ASC, id ASC), que es
  lo que necesita la sincronizacion para no saltarse registros.
"""

import base64
import binascii
import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, TypeVar

import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase

from app.nucleo.errores import DatosInvalidos

MODO_RECIENTE = "reciente"
MODO_DELTA = "delta"

LIMITE_POR_DEFECTO = 50
LIMITE_MAXIMO = 200

M = TypeVar("M", bound=DeclarativeBase)


@dataclass(frozen=True)
class Cursor:
    modo: str
    marca: datetime
    identificador: uuid.UUID

    def codificar(self) -> str:
        crudo = json.dumps(
            {"m": self.modo, "t": self.marca.isoformat(), "i": str(self.identificador)},
            separators=(",", ":"),
        )
        return base64.urlsafe_b64encode(crudo.encode()).decode().rstrip("=")


def decodificar_cursor(texto: str, modo_esperado: str) -> Cursor:
    try:
        relleno = "=" * (-len(texto) % 4)
        contenido: dict[str, Any] = json.loads(base64.urlsafe_b64decode(texto + relleno))
        cursor = Cursor(
            modo=contenido["m"],
            marca=datetime.fromisoformat(contenido["t"]),
            identificador=uuid.UUID(contenido["i"]),
        )
    except (KeyError, ValueError, binascii.Error, json.JSONDecodeError) as error:
        raise DatosInvalidos("El cursor no es valido. Pide la primera pagina otra vez.") from error

    if cursor.modo != modo_esperado:
        raise DatosInvalidos(
            "Ese cursor es de otro orden de listado. Pide la primera pagina otra vez."
        )
    return cursor


def limite_valido(limite: int | None) -> int:
    if limite is None:
        return LIMITE_POR_DEFECTO
    if limite < 1:
        raise DatosInvalidos("El limite tiene que ser al menos 1.")
    return min(limite, LIMITE_MAXIMO)


def aplicar_orden_y_cursor(
    consulta: sa.Select, modelo: type[M], modo: str, cursor: Cursor | None
) -> sa.Select:
    """Ordena y recorta por keyset. La comparacion de tuplas usa el indice."""
    if modo == MODO_DELTA:
        columna = modelo.updated_at
        consulta = consulta.order_by(columna.asc(), modelo.id.asc())
        if cursor is not None:
            consulta = consulta.where(
                sa.tuple_(columna, modelo.id) > sa.tuple_(cursor.marca, cursor.identificador)
            )
    else:
        columna = modelo.created_at
        consulta = consulta.order_by(columna.desc(), modelo.id.desc())
        if cursor is not None:
            consulta = consulta.where(
                sa.tuple_(columna, modelo.id) < sa.tuple_(cursor.marca, cursor.identificador)
            )
    return consulta


def armar_pagina(filas: list[M], limite: int, modo: str) -> tuple[list[M], str | None]:
    """Recibe limite+1 filas y devuelve la pagina mas el cursor de la siguiente."""
    hay_mas = len(filas) > limite
    pagina = filas[:limite]
    if not hay_mas or not pagina:
        return pagina, None

    ultima = pagina[-1]
    marca = ultima.updated_at if modo == MODO_DELTA else ultima.created_at
    return pagina, Cursor(modo=modo, marca=marca, identificador=ultima.id).codificar()
