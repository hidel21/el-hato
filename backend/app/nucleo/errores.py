"""Errores con un unico formato de salida.

Todo error de la API responde asi, sin excepciones:

    {"error": {"code": "...", "message": "..."}}
"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as HTTPExceptionStarlette


class ErrorAPI(Exception):
    """Error de dominio. Lo levantan los servicios; lo traduce el manejador."""

    def __init__(self, codigo: str, mensaje: str, estado: int = status.HTTP_400_BAD_REQUEST):
        self.codigo = codigo
        self.mensaje = mensaje
        self.estado = estado
        super().__init__(mensaje)


class NoEncontrado(ErrorAPI):
    def __init__(self, mensaje: str = "No encontramos lo que buscabas."):
        super().__init__("no_encontrado", mensaje, status.HTTP_404_NOT_FOUND)


class SinPermiso(ErrorAPI):
    def __init__(self, mensaje: str = "Tu rol no puede hacer esta accion."):
        super().__init__("sin_permiso", mensaje, status.HTTP_403_FORBIDDEN)


class NoAutenticado(ErrorAPI):
    def __init__(self, mensaje: str = "Necesitas iniciar sesion."):
        super().__init__("no_autenticado", mensaje, status.HTTP_401_UNAUTHORIZED)


class DatosInvalidos(ErrorAPI):
    def __init__(self, mensaje: str):
        super().__init__("datos_invalidos", mensaje, status.HTTP_422_UNPROCESSABLE_ENTITY)


def cuerpo_error(codigo: str, mensaje: str) -> dict[str, dict[str, str]]:
    return {"error": {"code": codigo, "message": mensaje}}


# Codigos por estado HTTP, para traducir las excepciones que no son nuestras.
CODIGOS_POR_ESTADO = {
    400: "peticion_invalida",
    401: "no_autenticado",
    403: "sin_permiso",
    404: "no_encontrado",
    405: "metodo_no_permitido",
    409: "conflicto",
    422: "datos_invalidos",
}


def registrar_manejadores(aplicacion: FastAPI) -> None:
    @aplicacion.exception_handler(ErrorAPI)
    async def _error_api(_: Request, exc: ErrorAPI) -> JSONResponse:
        return JSONResponse(status_code=exc.estado, content=cuerpo_error(exc.codigo, exc.mensaje))

    @aplicacion.exception_handler(HTTPExceptionStarlette)
    async def _error_http(_: Request, exc: HTTPExceptionStarlette) -> JSONResponse:
        codigo = CODIGOS_POR_ESTADO.get(exc.status_code, "error")
        return JSONResponse(
            status_code=exc.status_code,
            content=cuerpo_error(codigo, str(exc.detail)),
            headers=getattr(exc, "headers", None),
        )

    @aplicacion.exception_handler(RequestValidationError)
    async def _error_validacion(_: Request, exc: RequestValidationError) -> JSONResponse:
        detalles = []
        for fallo in exc.errors():
            campo = ".".join(str(parte) for parte in fallo["loc"] if parte != "body")
            detalles.append(f"{campo}: {fallo['msg']}" if campo else fallo["msg"])
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=cuerpo_error("datos_invalidos", "; ".join(detalles)),
        )

    @aplicacion.exception_handler(Exception)
    async def _error_interno(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=cuerpo_error("error_interno", "Algo fallo de nuestro lado."),
        )
