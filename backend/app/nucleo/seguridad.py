"""Hash de claves con Argon2 y emision de tokens JWT.

Acceso: 30 minutos. Refresco: 14 dias.
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.nucleo.configuracion import configuracion
from app.nucleo.errores import NoAutenticado

contexto_claves = CryptContext(schemes=["argon2"], deprecated="auto")

TIPO_ACCESO = "acceso"
TIPO_REFRESCO = "refresco"


def hashear_clave(clave: str) -> str:
    return contexto_claves.hash(clave)


def verificar_clave(clave: str, hash_guardado: str) -> bool:
    try:
        return contexto_claves.verify(clave, hash_guardado)
    except ValueError:
        return False


def _crear_token(
    usuario_id: uuid.UUID, finca_id: uuid.UUID, rol: str, tipo: str, duracion: timedelta
) -> str:
    ahora = datetime.now(UTC)
    contenido = {
        "sub": str(usuario_id),
        "finca_id": str(finca_id),
        "rol": rol,
        "tipo": tipo,
        "iat": int(ahora.timestamp()),
        "exp": int((ahora + duracion).timestamp()),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(contenido, configuracion.clave_secreta, algorithm=configuracion.algoritmo_jwt)


def crear_token_acceso(usuario_id: uuid.UUID, finca_id: uuid.UUID, rol: str) -> str:
    return _crear_token(
        usuario_id,
        finca_id,
        rol,
        TIPO_ACCESO,
        timedelta(minutes=configuracion.minutos_token_acceso),
    )


def crear_token_refresco(usuario_id: uuid.UUID, finca_id: uuid.UUID, rol: str) -> str:
    return _crear_token(
        usuario_id,
        finca_id,
        rol,
        TIPO_REFRESCO,
        timedelta(days=configuracion.dias_token_refresco),
    )


def decodificar_token(token: str, tipo_esperado: str) -> dict[str, Any]:
    try:
        contenido = jwt.decode(
            token, configuracion.clave_secreta, algorithms=[configuracion.algoritmo_jwt]
        )
    except JWTError as error:
        raise NoAutenticado("Tu sesion no es valida o ya vencio.") from error

    if contenido.get("tipo") != tipo_esperado:
        raise NoAutenticado("Ese token no sirve para esta operacion.")
    return contenido
