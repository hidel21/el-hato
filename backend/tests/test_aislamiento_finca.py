"""Multi-tenant: ninguna consulta puede cruzar la frontera de la finca.

El filtro vive en la dependencia AlcanceFinca, no en cada endpoint. Estos tests
son los que lo mantienen honesto.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import cabeceras, crear_animal


def test_el_listado_solo_trae_la_finca_del_token(
    cliente: TestClient, sesion: Session, finca_a: dict, finca_b: dict
) -> None:
    crear_animal(sesion, finca_a["finca"].id, "A-001")
    crear_animal(sesion, finca_a["finca"].id, "A-002")
    crear_animal(sesion, finca_b["finca"].id, "B-001")

    de_a = cliente.get("/api/v1/animales", headers=cabeceras(cliente, "capataz-a@ejemplo.com"))
    de_b = cliente.get("/api/v1/animales", headers=cabeceras(cliente, "capataz-b@ejemplo.com"))

    assert {a["arete"] for a in de_a.json()["datos"]} == {"A-001", "A-002"}
    assert {a["arete"] for a in de_b.json()["datos"]} == {"B-001"}


def test_no_se_puede_leer_una_ficha_ajena(
    cliente: TestClient, sesion: Session, finca_a: dict, finca_b: dict
) -> None:
    ajeno = crear_animal(sesion, finca_b["finca"].id, "B-002")
    de_a = cabeceras(cliente, "capataz-a@ejemplo.com")

    # 404 y no 403: desde la otra finca ese animal sencillamente no existe.
    assert cliente.get(f"/api/v1/animales/{ajeno.id}", headers=de_a).status_code == 404
    assert cliente.get(f"/api/v1/animales/{ajeno.id}/genealogia", headers=de_a).status_code == 404


def test_no_se_puede_editar_ni_borrar_una_ficha_ajena(
    cliente: TestClient, sesion: Session, finca_a: dict, finca_b: dict
) -> None:
    ajeno = crear_animal(sesion, finca_b["finca"].id, "B-003")
    administrador_de_a = cabeceras(cliente, "administrador-a@ejemplo.com")

    edicion = cliente.put(
        f"/api/v1/animales/{ajeno.id}", json={"nombre": "Secuestrada"}, headers=administrador_de_a
    )
    borrado = cliente.delete(f"/api/v1/animales/{ajeno.id}", headers=administrador_de_a)

    assert edicion.status_code == 404
    assert borrado.status_code == 404

    sesion.refresh(ajeno)
    assert ajeno.nombre is None
    assert ajeno.is_deleted is False


def test_no_se_puede_colgar_una_ficha_de_un_grupo_ajeno(
    cliente: TestClient, sesion: Session, finca_a: dict, finca_b: dict
) -> None:
    capataz_de_a = cabeceras(cliente, "capataz-a@ejemplo.com")

    respuesta = cliente.post(
        "/api/v1/animales",
        json={"arete": "A-010", "sexo": "hembra", "grupo_id": str(finca_b["grupo"].id)},
        headers=capataz_de_a,
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["message"] == "El grupo no es de tu finca."


def test_el_mismo_arete_puede_existir_en_dos_fincas(
    cliente: TestClient, sesion: Session, finca_a: dict, finca_b: dict
) -> None:
    """El arete es unico por finca, no en todo el sistema."""
    crear_animal(sesion, finca_a["finca"].id, "C-0412")

    respuesta = cliente.post(
        "/api/v1/animales",
        json={"arete": "C-0412", "sexo": "hembra"},
        headers=cabeceras(cliente, "capataz-b@ejemplo.com"),
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["arete_duplicado"] is False


def test_la_genealogia_no_cruza_fincas(
    cliente: TestClient, sesion: Session, finca_a: dict, finca_b: dict
) -> None:
    madre_ajena = crear_animal(sesion, finca_b["finca"].id, "B-MADRE")
    hija = crear_animal(sesion, finca_a["finca"].id, "A-HIJA")
    # Se fuerza el enlace por debajo de la API, que es la unica forma de que exista.
    hija.madre_id = madre_ajena.id
    sesion.commit()

    arbol = cliente.get(
        f"/api/v1/animales/{hija.id}/genealogia",
        headers=cabeceras(cliente, "capataz-a@ejemplo.com"),
    ).json()

    assert arbol["animal"]["arete"] == "A-HIJA"
    assert arbol["animal"]["madre"] is None
