"""Configuracion leida del entorno. Prefijo GAN_ para no chocar con nada mas."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

RAIZ = Path(__file__).resolve().parents[3]


class Configuracion(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="GAN_",
        env_file=(RAIZ / ".env", RAIZ / "backend" / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    nombre_aplicacion: str = "Hato"
    url_base_datos: str = "postgresql+psycopg://ganaderia:ganaderia@localhost:5433/ganaderia"
    url_base_datos_pruebas: str = (
        "postgresql+psycopg://ganaderia:ganaderia@localhost:5433/ganaderia_pruebas"
    )

    clave_secreta: str = "clave-de-desarrollo-no-usar-en-produccion"
    algoritmo_jwt: str = "HS256"
    minutos_token_acceso: int = 30
    dias_token_refresco: int = 14

    origenes_permitidos: str = "http://localhost:5173"

    @property
    def lista_origenes(self) -> list[str]:
        return [origen.strip() for origen in self.origenes_permitidos.split(",") if origen.strip()]


@lru_cache
def obtener_configuracion() -> Configuracion:
    return Configuracion()


configuracion = obtener_configuracion()
