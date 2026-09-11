"""Paginacion por cursor: sin offset, sin repetidos, sin saltos."""

from datetime import UTC, datetime, timedelta
from urllib.parse import quote

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import cabeceras, crear_animal


def _sembrar(sesion: Session, finca_id, cantidad: int) -> None:
    """Altas separadas en el tiempo, como pasaria en la finca."""
    momento = datetime.now(UTC) - timedelta(hours=cantidad)
    for numero in range(cantidad):
        crear_animal(
            sesion,
            finca_id,
            f"C-{numero:04d}",
            created_at=momento + timedelta(hours=numero),
            updated_at=momento + timedelta(hours=numero),
        )


def test_recorre_todo_sin_repetir_ni_saltar(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    _sembrar(sesion, finca_a["finca"].id, 12)
    capataz = cabeceras(cliente, "capataz-a@ejemplo.com")

    vistos: list[str] = []
    cursor = None
    paginas = 0

    while True:
        consulta = "/api/v1/animales?limite=5" + (f"&cursor={cursor}" if cursor else "")
        cuerpo = cliente.get(consulta, headers=capataz).json()
        vistos.extend(animal["arete"] for animal in cuerpo["datos"])
        paginas += 1
        cursor = cuerpo["cursor_siguiente"]
        if not cursor:
            break
        assert paginas < 10, "el cursor no termina"

    assert paginas == 3
    assert len(vistos) == 12
    assert len(set(vistos)) == 12
    # Orden: lo ultimo dado de alta primero.
    assert vistos[0] == "C-0011"
    assert vistos[-1] == "C-0000"


def test_la_ultima_pagina_no_trae_cursor(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    _sembrar(sesion, finca_a["finca"].id, 3)
    capataz = cabeceras(cliente, "capataz-a@ejemplo.com")

    cuerpo = cliente.get("/api/v1/animales?limite=10", headers=capataz).json()

    assert len(cuerpo["datos"]) == 3
    assert cuerpo["cursor_siguiente"] is None
    assert cuerpo["hay_mas"] is False


def test_un_cursor_roto_se_rechaza_con_mensaje_util(cliente: TestClient, finca_a: dict) -> None:
    capataz = cabeceras(cliente, "capataz-a@ejemplo.com")

    respuesta = cliente.get("/api/v1/animales?cursor=esto-no-es-un-cursor", headers=capataz)

    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["code"] == "datos_invalidos"


def test_el_cursor_de_un_modo_no_sirve_en_el_otro(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    """Decision 11: el modo va dentro del cursor para que no se mezclen."""
    _sembrar(sesion, finca_a["finca"].id, 6)
    capataz = cabeceras(cliente, "capataz-a@ejemplo.com")

    normal = cliente.get("/api/v1/animales?limite=2", headers=capataz).json()
    ayer = quote((datetime.now(UTC) - timedelta(days=1)).isoformat())

    mezclado = cliente.get(
        f"/api/v1/animales?limite=2&updated_since={ayer}&cursor={normal['cursor_siguiente']}",
        headers=capataz,
    )

    assert mezclado.status_code == 422
    assert "primera pagina" in mezclado.json()["error"]["message"]


def test_updated_since_entrega_el_delta_incluidos_los_borrados(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    """El contrato que consumira la sincronizacion de la Fase 2."""
    _sembrar(sesion, finca_a["finca"].id, 4)
    administrador = cabeceras(cliente, "administrador-a@ejemplo.com")

    corte = quote(datetime.now(UTC).isoformat())
    nuevo = cliente.post(
        "/api/v1/animales", json={"arete": "C-9999", "sexo": "hembra"}, headers=administrador
    ).json()
    listado = cliente.get("/api/v1/animales?limite=50", headers=administrador).json()
    borrado = next(a for a in listado["datos"] if a["arete"] == "C-0000")
    cliente.delete(f"/api/v1/animales/{borrado['id']}", headers=administrador)

    delta = cliente.get(f"/api/v1/animales?updated_since={corte}", headers=administrador).json()
    aretes = {animal["arete"]: animal for animal in delta["datos"]}

    assert aretes.keys() == {"C-9999", "C-0000"}
    assert aretes["C-9999"]["id"] == nuevo["id"]
    # Un borrado tambien es un cambio que el dispositivo necesita conocer.
    assert aretes["C-0000"]["is_deleted"] is True
