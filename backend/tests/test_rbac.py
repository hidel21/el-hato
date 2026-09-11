"""El control de acceso por rol vive en una sola dependencia reutilizable."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import cabeceras, crear_animal


def test_el_capataz_no_puede_borrar(cliente: TestClient, sesion: Session, finca_a: dict) -> None:
    animal = crear_animal(sesion, finca_a["finca"].id, "C-100")
    capataz = cabeceras(cliente, "capataz-a@ejemplo.com")

    respuesta = cliente.delete(f"/api/v1/animales/{animal.id}", headers=capataz)

    assert respuesta.status_code == 403
    assert respuesta.json() == {
        "error": {"code": "sin_permiso", "message": "Esta accion es solo para: administrador"}
    }


def test_el_veterinario_tampoco_puede_borrar(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    animal = crear_animal(sesion, finca_a["finca"].id, "C-101")
    veterinario = cabeceras(cliente, "veterinario-a@ejemplo.com")

    assert cliente.delete(f"/api/v1/animales/{animal.id}", headers=veterinario).status_code == 403


def test_el_administrador_borra_y_el_borrado_es_logico(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    animal = crear_animal(sesion, finca_a["finca"].id, "C-102")
    administrador = cabeceras(cliente, "administrador-a@ejemplo.com")

    assert cliente.delete(f"/api/v1/animales/{animal.id}", headers=administrador).status_code == 204

    sesion.expire_all()
    assert cliente.get(f"/api/v1/animales/{animal.id}", headers=administrador).status_code == 404

    # La ficha sigue en la base: is_deleted, nunca DELETE.
    sesion.refresh(animal)
    assert animal.is_deleted is True
    assert animal.deleted_at is not None


def test_el_capataz_si_puede_listar_y_dar_de_alta(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    capataz = cabeceras(cliente, "capataz-a@ejemplo.com")

    assert cliente.get("/api/v1/animales", headers=capataz).status_code == 200
    alta = cliente.post(
        "/api/v1/animales", json={"arete": "C-200", "sexo": "hembra"}, headers=capataz
    )
    assert alta.status_code == 201


def test_sin_token_no_se_entra(cliente: TestClient, finca_a: dict) -> None:
    respuesta = cliente.get("/api/v1/animales")

    assert respuesta.status_code == 401
    assert respuesta.json()["error"]["code"] == "no_autenticado"
