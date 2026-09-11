"""Cabecera X-Server-Time en toda respuesta.

Decision 2: el reloj del telefono no es confiable y la resolucion de conflictos
sera Last Write Wins por timestamp. El dispositivo mide su desfase contra esta
cabecera y corrige client_timestamp antes de enviar.
"""

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

CABECERA = "X-Server-Time"


def ahora_iso() -> str:
    """ISO 8601 en UTC con milisegundos: 2026-09-11T15:04:05.123Z"""
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class TiempoServidorMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, peticion: Request, siguiente: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        respuesta = await siguiente(peticion)
        respuesta.headers[CABECERA] = ahora_iso()
        return respuesta
