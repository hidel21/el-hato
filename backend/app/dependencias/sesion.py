"""Sesion de base de datos por peticion."""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.nucleo.base_datos import FabricaSesion


def obtener_sesion() -> Iterator[Session]:
    sesion = FabricaSesion()
    try:
        yield sesion
        sesion.commit()
    except Exception:
        sesion.rollback()
        raise
    finally:
        sesion.close()


SesionBD = Annotated[Session, Depends(obtener_sesion)]
