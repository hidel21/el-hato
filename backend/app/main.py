"""Aplicacion FastAPI."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.nucleo.configuracion import configuracion
from app.nucleo.errores import registrar_manejadores
from app.nucleo.tiempo_servidor import TiempoServidorMiddleware, ahora_iso
from app.rutas.v1 import router_v1

DESCRIPCION = """
API del sistema de gestion ganadera.

Toda respuesta incluye la cabecera **X-Server-Time** en ISO 8601 con
milisegundos: es la referencia de reloj para los dispositivos de campo.

Los listados se paginan **por cursor**, nunca por offset, y aceptan
`updated_since` para el delta de sincronizacion.

Los errores salen siempre asi:

    {"error": {"code": "...", "message": "..."}}
"""

aplicacion = FastAPI(
    title=configuracion.nombre_aplicacion,
    description=DESCRIPCION,
    version="0.1.0",
    docs_url="/docs",
    redoc_url=None,
)

aplicacion.add_middleware(TiempoServidorMiddleware)
aplicacion.add_middleware(
    CORSMiddleware,
    allow_origins=configuracion.lista_origenes,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Server-Time"],
)

registrar_manejadores(aplicacion)
aplicacion.include_router(router_v1)


@aplicacion.get("/api/v1/salud", tags=["Servicio"], summary="Comprobar que la API responde")
def salud() -> dict[str, str]:
    return {"estado": "ok", "hora_servidor": ahora_iso()}


# Alias corto: uvicorn app.main:app
app = aplicacion
