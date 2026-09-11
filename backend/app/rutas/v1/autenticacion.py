"""Ingreso y refresco de sesion."""

from fastapi import APIRouter

from app.dependencias.sesion import SesionBD
from app.esquemas.autenticacion import RespuestaTokens, SolicitudIngreso, SolicitudRefresco
from app.servicios import autenticacion as servicio

router = APIRouter(prefix="/auth", tags=["Autenticacion"])


@router.post("/login", response_model=RespuestaTokens, summary="Entrar con correo y clave")
def login(datos: SolicitudIngreso, sesion: SesionBD) -> RespuestaTokens:
    """Publico. Devuelve token de acceso (30 minutos) y de refresco (14 dias)."""
    return servicio.ingresar(sesion, datos.correo, datos.clave)


@router.post("/refresh", response_model=RespuestaTokens, summary="Renovar la sesion")
def refresh(datos: SolicitudRefresco, sesion: SesionBD) -> RespuestaTokens:
    """Requiere un token de refresco vigente. Devuelve un par de tokens nuevo."""
    return servicio.refrescar(sesion, datos.token_refresco)
