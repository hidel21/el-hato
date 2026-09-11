"""Entrada y salida de la autenticacion."""

import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modelos.enumeraciones import RolUsuario


class SolicitudIngreso(BaseModel):
    correo: EmailStr
    clave: str = Field(min_length=6, max_length=128)


class SolicitudRefresco(BaseModel):
    token_refresco: str


class UsuarioPublico(BaseModel):
    """Lo que la interfaz necesita para saludar y decidir que mostrar."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nombre_completo: str
    correo: str
    rol: RolUsuario
    finca_id: uuid.UUID
    finca_nombre: str | None = None


class RespuestaTokens(BaseModel):
    token_acceso: str
    token_refresco: str
    tipo_token: str = "bearer"
    expira_en_segundos: int
    usuario: UsuarioPublico
