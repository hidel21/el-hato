"""Ingreso y refresco de sesion."""

import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.esquemas.autenticacion import RespuestaTokens, UsuarioPublico
from app.modelos.organizacion import Finca, Usuario
from app.nucleo.configuracion import configuracion
from app.nucleo.errores import ErrorAPI, NoAutenticado
from app.nucleo.seguridad import (
    TIPO_REFRESCO,
    crear_token_acceso,
    crear_token_refresco,
    decodificar_token,
    verificar_clave,
)


def _armar_respuesta(sesion: Session, usuario: Usuario) -> RespuestaTokens:
    finca = sesion.get(Finca, usuario.finca_id)
    publico = UsuarioPublico.model_validate(usuario)
    publico.finca_nombre = finca.nombre if finca else None

    return RespuestaTokens(
        token_acceso=crear_token_acceso(usuario.id, usuario.finca_id, usuario.rol.value),
        token_refresco=crear_token_refresco(usuario.id, usuario.finca_id, usuario.rol.value),
        expira_en_segundos=configuracion.minutos_token_acceso * 60,
        usuario=publico,
    )


def ingresar(sesion: Session, correo: str, clave: str) -> RespuestaTokens:
    consulta = sa.select(Usuario).where(
        sa.func.lower(Usuario.correo) == correo.lower(),
        Usuario.is_deleted.is_(False),
    )
    usuario = sesion.execute(consulta).scalar_one_or_none()

    # Mismo mensaje si el correo no existe o si la clave no coincide: no se le
    # dice a nadie que correos estan registrados.
    generico = ErrorAPI("credenciales_invalidas", "El correo o la clave no coinciden.", 401)
    if usuario is None or not verificar_clave(clave, usuario.clave_hash):
        raise generico
    if not usuario.activo:
        raise ErrorAPI("usuario_inactivo", "Tu usuario esta desactivado.", 403)

    usuario.ultimo_acceso = datetime.now(UTC)
    sesion.flush()
    return _armar_respuesta(sesion, usuario)


def refrescar(sesion: Session, token_refresco: str) -> RespuestaTokens:
    contenido = decodificar_token(token_refresco, TIPO_REFRESCO)
    usuario = sesion.get(Usuario, uuid.UUID(contenido["sub"]))

    if usuario is None or usuario.is_deleted or not usuario.activo:
        raise NoAutenticado("Tu usuario ya no esta activo.")
    return _armar_respuesta(sesion, usuario)
