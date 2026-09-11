"""Quien eres, que puedes hacer y que datos puedes ver.

El aislamiento multi-tenant vive aqui y solo aqui. Un endpoint que arme su
propio select() sin pasar por AlcanceFinca es un agujero de seguridad.
"""

import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Annotated, TypeVar

import sqlalchemy as sa
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import DeclarativeBase, Session

from app.dependencias.sesion import SesionBD
from app.modelos.enumeraciones import RolUsuario
from app.modelos.organizacion import Usuario
from app.nucleo.errores import NoAutenticado, SinPermiso
from app.nucleo.seguridad import TIPO_ACCESO, decodificar_token

esquema_bearer = HTTPBearer(auto_error=False, description="Token de acceso")

M = TypeVar("M", bound=DeclarativeBase)


def obtener_usuario_actual(
    sesion: SesionBD,
    credenciales: Annotated[HTTPAuthorizationCredentials | None, Depends(esquema_bearer)],
) -> Usuario:
    if credenciales is None:
        raise NoAutenticado()

    contenido = decodificar_token(credenciales.credentials, TIPO_ACCESO)
    usuario = sesion.get(Usuario, uuid.UUID(contenido["sub"]))

    if usuario is None or usuario.is_deleted or not usuario.activo:
        raise NoAutenticado("Tu usuario ya no esta activo.")
    # El token dice de que finca es la sesion; si no coincide, el token es viejo.
    if str(usuario.finca_id) != contenido.get("finca_id"):
        raise NoAutenticado("Tu sesion quedo desactualizada. Vuelve a entrar.")
    return usuario


UsuarioActual = Annotated[Usuario, Depends(obtener_usuario_actual)]


def require_rol(roles: Sequence[RolUsuario | str]) -> Callable[[Usuario], Usuario]:
    """Dependencia de control de acceso. Se escribe una vez y se reutiliza.

    @router.delete("/{id}", dependencies=[Depends(require_rol(["administrador"]))])
    """
    permitidos = {RolUsuario(rol) for rol in roles}

    def verificar(usuario: UsuarioActual) -> Usuario:
        if usuario.rol not in permitidos:
            raise SinPermiso(
                "Esta accion es solo para: " + ", ".join(sorted(rol.value for rol in permitidos))
            )
        return usuario

    return verificar


@dataclass
class AlcanceFinca:
    """Todo lo que se consulta pasa por aqui, ya acotado a la finca del token."""

    sesion: Session
    usuario: Usuario

    @property
    def finca_id(self) -> uuid.UUID:
        return self.usuario.finca_id

    def consultar(self, modelo: type[M], incluir_borrados: bool = False) -> sa.Select:
        consulta = sa.select(modelo).where(modelo.finca_id == self.finca_id)
        if not incluir_borrados:
            consulta = consulta.where(modelo.is_deleted.is_(False))
        return consulta

    def obtener(
        self, modelo: type[M], identificador: uuid.UUID, incluir_borrados: bool = False
    ) -> M | None:
        consulta = self.consultar(modelo, incluir_borrados).where(modelo.id == identificador)
        return self.sesion.execute(consulta).scalar_one_or_none()


def obtener_alcance(sesion: SesionBD, usuario: UsuarioActual) -> AlcanceFinca:
    return AlcanceFinca(sesion=sesion, usuario=usuario)


Alcance = Annotated[AlcanceFinca, Depends(obtener_alcance)]
