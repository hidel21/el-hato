"""Plantilla de tests. Los cuatro minimos de todo modulo."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import cabeceras, crear_animal

RUTA = "/api/v1/RUTA"


def test_el_camino_feliz(cliente: TestClient, sesion: Session, finca_a: dict) -> None:
    animal = crear_animal(sesion, finca_a["finca"].id, "C-100")
    capataz = cabeceras(cliente, "capataz-a@ejemplo.com")

    alta = cliente.post(RUTA, json={"animal_id": str(animal.id)}, headers=capataz)
    assert alta.status_code == 201, alta.text

    listado = cliente.get(RUTA, headers=capataz).json()
    assert len(listado["datos"]) == 1


def test_el_capataz_no_puede_borrar(cliente: TestClient, sesion: Session, finca_a: dict) -> None:
    capataz = cabeceras(cliente, "capataz-a@ejemplo.com")
    creado = cliente.post(RUTA, json={}, headers=capataz).json()

    respuesta = cliente.delete(f"{RUTA}/{creado['id']}", headers=capataz)

    assert respuesta.status_code == 403
    assert respuesta.json()["error"]["code"] == "sin_permiso"


def test_no_se_ve_lo_de_otra_finca(
    cliente: TestClient, sesion: Session, finca_a: dict, finca_b: dict
) -> None:
    de_b = cabeceras(cliente, "capataz-b@ejemplo.com")
    ajeno = cliente.post(RUTA, json={}, headers=cabeceras(cliente, "capataz-a@ejemplo.com")).json()

    # 404 y no 403: desde la otra finca ese registro no existe.
    assert cliente.get(f"{RUTA}/{ajeno['id']}", headers=de_b).status_code == 404
    assert cliente.get(RUTA, headers=de_b).json()["datos"] == []


def test_la_regla_propia_del_dominio(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    """Cada modulo tiene una regla que lo define. Esta es la de vacunacion:
    una aplicacion por lote materializa la membresia en el momento.

    Cambiala por la que corresponda: la carencia de un baño, el intervalo entre
    partos, los dias de ocupacion de un potrero.
    """
    animal = crear_animal(sesion, finca_a["finca"].id, "C-100", grupo_id=finca_a["grupo"].id)
    veterinario = cabeceras(cliente, "veterinario-a@ejemplo.com")

    aplicacion = cliente.post(
        RUTA, json={"grupo_id": str(finca_a["grupo"].id)}, headers=veterinario
    ).json()

    assert aplicacion["cantidad_animales"] == 1
    detalle = cliente.get(f"{RUTA}/{aplicacion['id']}/animales", headers=veterinario).json()
    assert [fila["animal_id"] for fila in detalle["datos"]] == [str(animal.id)]
