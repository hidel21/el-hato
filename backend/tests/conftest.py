"""Entorno de pruebas.

Los tests corren contra una base aparte, `ganaderia_pruebas`, que se crea sola
si no existe. Cada test arranca con las tablas vacias y arma sus propios datos.
"""

import os
import re
import uuid
from collections.abc import Iterator
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def _url_de_pruebas() -> str:
    """Saca la URL de pruebas del entorno o del .env, sin importar la app."""
    directa = os.environ.get("GAN_URL_BASE_DATOS_PRUEBAS")
    if directa:
        return directa

    archivo = RAIZ / ".env"
    if archivo.exists():
        for linea in archivo.read_text().splitlines():
            encontrado = re.match(r"^\s*GAN_URL_BASE_DATOS_PRUEBAS\s*=\s*(.+?)\s*$", linea)
            if encontrado:
                return encontrado.group(1).strip("\"'")
    return "postgresql+psycopg://ganaderia:ganaderia@localhost:5433/ganaderia_pruebas"


# Estas dos variables se fijan ANTES de importar nada de la aplicacion: el
# motor se construye al importar app.nucleo.base_datos.
URL_PRUEBAS = _url_de_pruebas()
os.environ["GAN_URL_BASE_DATOS"] = URL_PRUEBAS
os.environ["GAN_SEGUNDOS_DEBOUNCE_INVENTARIO"] = "0"  # sin hilos de fondo en los tests

import pytest  # noqa: E402
import sqlalchemy as sa  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from alembic import command  # noqa: E402
from app.main import app  # noqa: E402
from app.modelos import Animal, Finca, Grupo, Potrero, Usuario  # noqa: E402
from app.modelos.enumeraciones import (  # noqa: E402
    EstadoAnimal,
    EtapaGrupo,
    PropositoGrupo,
    RolUsuario,
    Sexo,
)
from app.nucleo.base_datos import Base, FabricaSesion, motor  # noqa: E402
from app.nucleo.seguridad import hashear_clave  # noqa: E402

CLAVE = "prueba1234"


def _crear_base_si_falta() -> None:
    url = sa.engine.make_url(URL_PRUEBAS)
    administrativo = sa.create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with administrativo.connect() as conexion:
        existe = conexion.execute(
            sa.text("SELECT 1 FROM pg_database WHERE datname = :nombre"), {"nombre": url.database}
        ).scalar()
        if not existe:
            conexion.execute(sa.text(f'CREATE DATABASE "{url.database}"'))
    administrativo.dispose()


@pytest.fixture(scope="session", autouse=True)
def esquema() -> Iterator[None]:
    """Crea la base de pruebas y le aplica la migracion desde cero."""
    _crear_base_si_falta()

    configuracion_alembic = Config(str(RAIZ / "backend" / "alembic.ini"))
    configuracion_alembic.set_main_option("script_location", str(RAIZ / "backend" / "alembic"))
    os.environ["GAN_URL_BASE_DATOS_ALEMBIC"] = URL_PRUEBAS

    command.downgrade(configuracion_alembic, "base")
    command.upgrade(configuracion_alembic, "head")
    yield


@pytest.fixture(autouse=True)
def tablas_limpias(esquema: None) -> Iterator[None]:
    """Cada test empieza con la base vacia."""
    nombres = ", ".join(f'"{tabla}"' for tabla in Base.metadata.tables)
    with motor.begin() as conexion:
        conexion.execute(sa.text(f"TRUNCATE {nombres} RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture
def sesion() -> Iterator[Session]:
    sesion = FabricaSesion()
    try:
        yield sesion
    finally:
        sesion.close()


@pytest.fixture
def cliente() -> Iterator[TestClient]:
    with TestClient(app) as cliente:
        yield cliente


def crear_finca(sesion: Session, nombre: str, sufijo: str) -> dict[str, object]:
    """Finca completa y usable: tres roles, un potrero, un grupo."""
    finca = Finca(nombre=nombre)
    sesion.add(finca)
    sesion.flush()

    clave = hashear_clave(CLAVE)
    usuarios = {}
    for rol in (RolUsuario.administrador, RolUsuario.veterinario, RolUsuario.capataz):
        usuario = Usuario(
            finca_id=finca.id,
            nombre_completo=f"{rol.value.capitalize()} de {nombre}",
            correo=f"{rol.value}-{sufijo}@ejemplo.com",
            clave_hash=clave,
            rol=rol,
        )
        sesion.add(usuario)
        usuarios[rol.value] = usuario

    potrero = Potrero(finca_id=finca.id, nombre=f"Potrero {sufijo}", hectareas=10)
    sesion.add(potrero)
    sesion.flush()

    grupo = Grupo(
        finca_id=finca.id,
        nombre=f"Grupo {sufijo}",
        etapa=EtapaGrupo.levante,
        proposito=PropositoGrupo.engorde,
        potrero_id=potrero.id,
    )
    sesion.add(grupo)
    sesion.commit()

    return {
        "finca": finca,
        "usuarios": usuarios,
        "potrero": potrero,
        "grupo": grupo,
        "sufijo": sufijo,
    }


def crear_animal(sesion: Session, finca_id: uuid.UUID, arete: str, **extra) -> Animal:
    animal = Animal(
        finca_id=finca_id,
        arete=arete,
        sexo=extra.pop("sexo", Sexo.hembra),
        estado=extra.pop("estado", EstadoAnimal.activo),
        **extra,
    )
    sesion.add(animal)
    sesion.commit()
    sesion.refresh(animal)
    return animal


def crear_potrero(sesion: Session, finca_id: uuid.UUID, nombre: str, **extra) -> Potrero:
    potrero = Potrero(
        finca_id=finca_id,
        nombre=nombre,
        hectareas=extra.pop("hectareas", 10),
        **extra,
    )
    sesion.add(potrero)
    sesion.commit()
    sesion.refresh(potrero)
    return potrero


def crear_grupo(sesion: Session, finca_id: uuid.UUID, nombre: str, **extra) -> Grupo:
    grupo = Grupo(
        finca_id=finca_id,
        nombre=nombre,
        etapa=extra.pop("etapa", EtapaGrupo.levante),
        proposito=extra.pop("proposito", PropositoGrupo.engorde),
        **extra,
    )
    sesion.add(grupo)
    sesion.commit()
    sesion.refresh(grupo)
    return grupo


def cabeceras(cliente: TestClient, correo: str) -> dict[str, str]:
    respuesta = cliente.post("/api/v1/auth/login", json={"correo": correo, "clave": CLAVE})
    assert respuesta.status_code == 200, respuesta.text
    return {"Authorization": f"Bearer {respuesta.json()['token_acceso']}"}


@pytest.fixture
def finca_a(sesion: Session) -> dict[str, object]:
    return crear_finca(sesion, "La Guacamaya", "a")


@pytest.fixture
def finca_b(sesion: Session) -> dict[str, object]:
    return crear_finca(sesion, "El Recuerdo", "b")
