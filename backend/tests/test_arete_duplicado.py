"""Decision 1: el servidor nunca rechaza un arete ya capturado en campo."""

import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modelos.animal import Animal
from app.modelos.enumeraciones import EstadoAlerta, TipoAlerta
from app.modelos.operacion import Alerta
from tests.conftest import cabeceras, crear_animal


def test_el_arete_repetido_entra_marcado_y_genera_alerta(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    finca = finca_a["finca"]
    crear_animal(sesion, finca.id, "C-0412")

    capataz = cabeceras(cliente, "capataz-a@ejemplo.com")
    respuesta = cliente.post(
        "/api/v1/animales",
        json={"arete": "C-0412", "sexo": "macho", "nombre": "El otro"},
        headers=capataz,
    )

    # No se rechaza: el trabajo hecho en el potrero no se pierde.
    assert respuesta.status_code == 201, respuesta.text
    assert respuesta.json()["arete_duplicado"] is True

    # Y queda una alerta para que una persona resuelva el choque.
    alerta = sesion.execute(
        sa.select(Alerta).where(Alerta.finca_id == finca.id, Alerta.tipo == TipoAlerta.otro)
    ).scalar_one()
    assert alerta.estado == EstadoAlerta.pendiente
    assert "C-0412" in alerta.titulo
    assert alerta.referencia_tabla == "animales"


def test_el_primero_conserva_el_arete_sin_marca(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    capataz = cabeceras(cliente, "capataz-a@ejemplo.com")

    primero = cliente.post(
        "/api/v1/animales", json={"arete": "C-777", "sexo": "hembra"}, headers=capataz
    )
    segundo = cliente.post(
        "/api/v1/animales", json={"arete": "C-777", "sexo": "hembra"}, headers=capataz
    )

    assert primero.json()["arete_duplicado"] is False
    assert segundo.json()["arete_duplicado"] is True

    # El indice unico parcial deja pasar al duplicado justamente porque
    # arete_duplicado = true lo saca del indice.
    canonicos = sesion.execute(
        sa.select(sa.func.count())
        .select_from(Animal)
        .where(
            Animal.finca_id == finca_a["finca"].id,
            Animal.arete == "C-777",
            Animal.arete_duplicado.is_(False),
            Animal.is_deleted.is_(False),
        )
    ).scalar_one()
    assert canonicos == 1


def test_un_arete_liberado_por_borrado_vuelve_a_estar_libre(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    animal = crear_animal(sesion, finca_a["finca"].id, "C-500")

    administrador = cabeceras(cliente, "administrador-a@ejemplo.com")
    assert cliente.delete(f"/api/v1/animales/{animal.id}", headers=administrador).status_code == 204

    respuesta = cliente.post(
        "/api/v1/animales", json={"arete": "C-500", "sexo": "hembra"}, headers=administrador
    )
    assert respuesta.status_code == 201
    assert respuesta.json()["arete_duplicado"] is False
