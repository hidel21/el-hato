"""Lotes: el grupo de animales que se maneja junto."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import cabeceras, crear_animal, crear_grupo, crear_potrero

RUTA = "/api/v1/grupos"


def test_el_listado_dice_cuantos_animales_tiene_cada_lote(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    potrero = crear_potrero(sesion, finca_a["finca"].id, "La Ceiba")
    vientres = crear_grupo(sesion, finca_a["finca"].id, "Vientres A", potrero_id=potrero.id)
    crear_grupo(sesion, finca_a["finca"].id, "Terneras 26")
    for numero in range(5):
        crear_animal(sesion, finca_a["finca"].id, f"C-{numero}", grupo_id=vientres.id)

    lotes = {
        g["nombre"]: g
        for g in cliente.get(RUTA, headers=cabeceras(cliente, "capataz-a@ejemplo.com")).json()[
            "datos"
        ]
    }

    assert lotes["Vientres A"]["cantidad_animales"] == 5
    assert lotes["Vientres A"]["potrero_nombre"] == "La Ceiba"
    assert lotes["Terneras 26"]["cantidad_animales"] == 0
    assert lotes["Terneras 26"]["potrero_nombre"] is None


def test_crear_y_editar_un_lote(cliente: TestClient, sesion: Session, finca_a: dict) -> None:
    potrero = crear_potrero(sesion, finca_a["finca"].id, "El Palmar")
    capataz = cabeceras(cliente, "capataz-a@ejemplo.com")

    alta = cliente.post(
        RUTA,
        json={
            "nombre": "Levante Norte",
            "etapa": "levante",
            "proposito": "engorde",
            "potrero_id": str(potrero.id),
        },
        headers=capataz,
    )
    assert alta.status_code == 201, alta.text
    assert alta.json()["potrero_nombre"] == "El Palmar"
    assert alta.json()["version"] == 1

    edicion = cliente.put(
        f"{RUTA}/{alta.json()['id']}",
        json={"descripcion": "Machos y hembras de levante."},
        headers=capataz,
    )
    assert edicion.status_code == 200
    assert edicion.json()["version"] == 2


def test_el_nombre_del_lote_no_se_repite_en_la_finca(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    """A diferencia del arete, un lote no se captura a la carrera: quien lo
    crea puede elegir otro nombre, asi que aqui si se rechaza."""
    crear_grupo(sesion, finca_a["finca"].id, "Vientres A")

    respuesta = cliente.post(
        RUTA,
        json={"nombre": "  vientres a  ", "etapa": "vientre", "proposito": "cria"},
        headers=cabeceras(cliente, "capataz-a@ejemplo.com"),
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["error"]["code"] == "nombre_repetido"
    assert "Vientres A" in respuesta.json()["error"]["message"]


def test_no_se_borra_un_lote_con_animales(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    grupo = crear_grupo(sesion, finca_a["finca"].id, "Vientres A")
    crear_animal(sesion, finca_a["finca"].id, "C-100", grupo_id=grupo.id)
    crear_animal(sesion, finca_a["finca"].id, "C-101", grupo_id=grupo.id)

    respuesta = cliente.delete(
        f"{RUTA}/{grupo.id}", headers=cabeceras(cliente, "administrador-a@ejemplo.com")
    )

    assert respuesta.status_code == 409
    assert "2 animales" in respuesta.json()["error"]["message"]
    sesion.refresh(grupo)
    assert grupo.is_deleted is False


def test_un_lote_vacio_si_se_borra_y_el_borrado_es_logico(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    grupo = crear_grupo(sesion, finca_a["finca"].id, "Descarte 25")
    administrador = cabeceras(cliente, "administrador-a@ejemplo.com")

    assert cliente.delete(f"{RUTA}/{grupo.id}", headers=administrador).status_code == 204
    assert cliente.get(f"{RUTA}/{grupo.id}", headers=administrador).status_code == 404

    sesion.refresh(grupo)
    assert grupo.is_deleted is True
    assert grupo.deleted_at is not None

    # El nombre queda libre otra vez: el indice unico es parcial.
    assert (
        cliente.post(
            RUTA,
            json={"nombre": "Descarte 25", "etapa": "descarte", "proposito": "manejo"},
            headers=administrador,
        ).status_code
        == 201
    )


def test_el_capataz_no_puede_borrar_un_lote(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    grupo = crear_grupo(sesion, finca_a["finca"].id, "Vientres A")

    respuesta = cliente.delete(
        f"{RUTA}/{grupo.id}", headers=cabeceras(cliente, "capataz-a@ejemplo.com")
    )

    assert respuesta.status_code == 403
    assert respuesta.json()["error"]["code"] == "sin_permiso"


def test_no_se_cuelga_un_lote_de_un_potrero_ajeno(
    cliente: TestClient, sesion: Session, finca_a: dict, finca_b: dict
) -> None:
    ajeno = crear_potrero(sesion, finca_b["finca"].id, "Ajeno")

    respuesta = cliente.post(
        RUTA,
        json={
            "nombre": "Colados",
            "etapa": "levante",
            "proposito": "engorde",
            "potrero_id": str(ajeno.id),
        },
        headers=cabeceras(cliente, "capataz-a@ejemplo.com"),
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["message"] == "Ese potrero no es de tu finca."


def test_no_se_ve_ni_se_edita_un_lote_de_otra_finca(
    cliente: TestClient, sesion: Session, finca_a: dict, finca_b: dict
) -> None:
    ajeno = crear_grupo(sesion, finca_b["finca"].id, "De la otra finca")
    de_a = cabeceras(cliente, "administrador-a@ejemplo.com")

    assert cliente.get(f"{RUTA}/{ajeno.id}", headers=de_a).status_code == 404
    edicion = cliente.put(f"{RUTA}/{ajeno.id}", json={"nombre": "Mio"}, headers=de_a)
    assert edicion.status_code == 404
    assert cliente.delete(f"{RUTA}/{ajeno.id}", headers=de_a).status_code == 404

    nombres = {g["nombre"] for g in cliente.get(RUTA, headers=de_a).json()["datos"]}
    assert "De la otra finca" not in nombres


def test_cambiar_el_potrero_del_lote_no_mueve_a_los_animales(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    """Para trasladar ganado esta el movimiento, que deja historico. Editar el
    lote solo cambia la etiqueta."""
    origen = crear_potrero(sesion, finca_a["finca"].id, "La Ceiba")
    destino = crear_potrero(sesion, finca_a["finca"].id, "El Palmar")
    grupo = crear_grupo(sesion, finca_a["finca"].id, "Levante", potrero_id=origen.id)
    animal = crear_animal(
        sesion, finca_a["finca"].id, "C-100", grupo_id=grupo.id, potrero_id=origen.id
    )

    cliente.put(
        f"{RUTA}/{grupo.id}",
        json={"potrero_id": str(destino.id)},
        headers=cabeceras(cliente, "capataz-a@ejemplo.com"),
    )

    sesion.refresh(animal)
    assert animal.potrero_id == origen.id
