"""Potreros: carga, descanso y movimientos de ganado."""

from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modelos.territorio import Grupo, Potrero
from tests.conftest import cabeceras, crear_animal, crear_grupo, crear_potrero

RUTA = "/api/v1/potreros"


def test_el_listado_trae_carga_y_animales(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    """La carga en UGM por hectarea es agregacion de finca: la calcula el
    servidor, no el dispositivo (decision 6)."""
    potrero = crear_potrero(sesion, finca_a["finca"].id, "La Ceiba", hectareas=10)
    grupo = crear_grupo(sesion, finca_a["finca"].id, "Vientres A", potrero_id=potrero.id)
    for numero in range(3):
        crear_animal(
            sesion,
            finca_a["finca"].id,
            f"C-{numero}",
            potrero_id=potrero.id,
            grupo_id=grupo.id,
            peso_actual_kg=Decimal("450"),
        )

    fila = next(
        p
        for p in cliente.get(RUTA, headers=cabeceras(cliente, "capataz-a@ejemplo.com")).json()[
            "datos"
        ]
        if p["nombre"] == "La Ceiba"
    )

    assert fila["cantidad_animales"] == 3
    assert Decimal(fila["peso_total_kg"]) == Decimal("1350")
    # 1350 kg / 450 kg por UGM / 10 ha = 0,30 UGM/ha
    assert Decimal(fila["carga_ugm_ha"]) == Decimal("0.30")
    assert fila["lotes"] == ["Vientres A"]


def test_mover_un_lote_arrastra_a_sus_animales(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    """La regla del modulo: el traslado es una sola transaccion que deja los
    dos potreros al dia."""
    origen = crear_potrero(sesion, finca_a["finca"].id, "La Ceiba")
    destino = crear_potrero(sesion, finca_a["finca"].id, "El Palmar")
    grupo = crear_grupo(sesion, finca_a["finca"].id, "Levante Norte", potrero_id=origen.id)
    animales = [
        crear_animal(sesion, finca_a["finca"].id, f"C-{n}", potrero_id=origen.id, grupo_id=grupo.id)
        for n in range(4)
    ]

    respuesta = cliente.post(
        f"{RUTA}/movimientos",
        json={
            "potrero_destino_id": str(destino.id),
            "grupo_id": str(grupo.id),
            "motivo": "Rotación por descanso",
        },
        headers=cabeceras(cliente, "capataz-a@ejemplo.com"),
    )

    assert respuesta.status_code == 201, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["cantidad_animales"] == 4
    assert cuerpo["potrero_origen_nombre"] == "La Ceiba"
    assert cuerpo["potrero_destino_nombre"] == "El Palmar"

    sesion.expire_all()
    for animal in animales:
        sesion.refresh(animal)
        assert animal.potrero_id == destino.id
        assert animal.version == 2

    sesion.refresh(grupo)
    assert grupo.potrero_id == destino.id

    # El destino recibe ganado, asi que deja de descansar y anota la fecha.
    sesion.refresh(destino)
    assert destino.en_descanso is False
    assert destino.fecha_ultimo_ingreso == date.fromisoformat(cuerpo["fecha_movimiento"])

    # El origen quedo vacio: empieza a descansar.
    sesion.refresh(origen)
    assert origen.en_descanso is True


def test_la_cantidad_movida_queda_congelada_en_el_historico(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    """El lote cambia al dia siguiente; el movimiento tiene que seguir
    diciendo cuantos se movieron ese dia."""
    origen = crear_potrero(sesion, finca_a["finca"].id, "La Ceiba")
    destino = crear_potrero(sesion, finca_a["finca"].id, "El Palmar")
    grupo = crear_grupo(sesion, finca_a["finca"].id, "Levante", potrero_id=origen.id)
    for numero in range(2):
        crear_animal(
            sesion, finca_a["finca"].id, f"C-{numero}", potrero_id=origen.id, grupo_id=grupo.id
        )

    capataz = cabeceras(cliente, "capataz-a@ejemplo.com")
    cliente.post(
        f"{RUTA}/movimientos",
        json={"potrero_destino_id": str(destino.id), "grupo_id": str(grupo.id)},
        headers=capataz,
    )
    # Despues del traslado entran dos animales mas al lote.
    for numero in range(2, 4):
        crear_animal(
            sesion, finca_a["finca"].id, f"C-{numero}", potrero_id=destino.id, grupo_id=grupo.id
        )

    historial = cliente.get(f"{RUTA}/movimientos", headers=capataz).json()["datos"]
    assert historial[0]["cantidad_animales"] == 2


def test_mover_al_mismo_potrero_no_hace_nada(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    potrero = crear_potrero(sesion, finca_a["finca"].id, "La Ceiba")
    grupo = crear_grupo(sesion, finca_a["finca"].id, "Levante", potrero_id=potrero.id)

    respuesta = cliente.post(
        f"{RUTA}/movimientos",
        json={"potrero_destino_id": str(potrero.id), "grupo_id": str(grupo.id)},
        headers=cabeceras(cliente, "capataz-a@ejemplo.com"),
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["error"]["code"] == "sin_movimiento"


def test_un_movimiento_lleva_lote_o_animal_pero_no_los_dos(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    destino = crear_potrero(sesion, finca_a["finca"].id, "El Palmar")
    grupo = crear_grupo(sesion, finca_a["finca"].id, "Levante")
    animal = crear_animal(sesion, finca_a["finca"].id, "C-100")
    capataz = cabeceras(cliente, "capataz-a@ejemplo.com")

    ambos = cliente.post(
        f"{RUTA}/movimientos",
        json={
            "potrero_destino_id": str(destino.id),
            "grupo_id": str(grupo.id),
            "animal_id": str(animal.id),
        },
        headers=capataz,
    )
    ninguno = cliente.post(
        f"{RUTA}/movimientos", json={"potrero_destino_id": str(destino.id)}, headers=capataz
    )

    assert ambos.status_code == 422
    assert ninguno.status_code == 422


def test_no_se_borra_un_potrero_con_ganado_dentro(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    potrero = crear_potrero(sesion, finca_a["finca"].id, "La Ceiba")
    crear_animal(sesion, finca_a["finca"].id, "C-100", potrero_id=potrero.id)

    respuesta = cliente.delete(
        f"{RUTA}/{potrero.id}", headers=cabeceras(cliente, "administrador-a@ejemplo.com")
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["error"]["code"] == "potrero_ocupado"
    assert "1 animal" in respuesta.json()["error"]["message"]

    sesion.refresh(potrero)
    assert potrero.is_deleted is False


def test_el_capataz_no_puede_borrar_un_potrero(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    potrero = crear_potrero(sesion, finca_a["finca"].id, "Vacio")

    respuesta = cliente.delete(
        f"{RUTA}/{potrero.id}", headers=cabeceras(cliente, "capataz-a@ejemplo.com")
    )

    assert respuesta.status_code == 403
    assert respuesta.json()["error"]["code"] == "sin_permiso"


def test_el_nombre_del_potrero_no_se_repite(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    crear_potrero(sesion, finca_a["finca"].id, "La Ceiba")

    respuesta = cliente.post(
        RUTA,
        json={"nombre": "la ceiba", "hectareas": "20"},
        headers=cabeceras(cliente, "capataz-a@ejemplo.com"),
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["error"]["code"] == "nombre_repetido"


def test_no_se_mueve_ganado_al_potrero_de_otra_finca(
    cliente: TestClient, sesion: Session, finca_a: dict, finca_b: dict
) -> None:
    ajeno = crear_potrero(sesion, finca_b["finca"].id, "Ajeno")
    grupo = crear_grupo(sesion, finca_a["finca"].id, "Levante")
    animal = crear_animal(sesion, finca_a["finca"].id, "C-100", grupo_id=grupo.id)

    respuesta = cliente.post(
        f"{RUTA}/movimientos",
        json={"potrero_destino_id": str(ajeno.id), "grupo_id": str(grupo.id)},
        headers=cabeceras(cliente, "capataz-a@ejemplo.com"),
    )

    assert respuesta.status_code == 404
    sesion.refresh(animal)
    assert animal.potrero_id is None


def test_el_listado_solo_trae_potreros_de_la_finca(
    cliente: TestClient, sesion: Session, finca_a: dict, finca_b: dict
) -> None:
    crear_potrero(sesion, finca_a["finca"].id, "De A")
    crear_potrero(sesion, finca_b["finca"].id, "De B")

    nombres = {
        p["nombre"]
        for p in cliente.get(RUTA, headers=cabeceras(cliente, "capataz-a@ejemplo.com")).json()[
            "datos"
        ]
    }

    assert "De A" in nombres
    assert "De B" not in nombres


def test_el_mismo_nombre_puede_existir_en_dos_fincas(
    cliente: TestClient, sesion: Session, finca_a: dict, finca_b: dict
) -> None:
    crear_potrero(sesion, finca_a["finca"].id, "La Ceiba")

    respuesta = cliente.post(
        RUTA,
        json={"nombre": "La Ceiba", "hectareas": "30"},
        headers=cabeceras(cliente, "capataz-b@ejemplo.com"),
    )

    assert respuesta.status_code == 201


def test_un_potrero_recien_creado_no_tiene_carga(cliente: TestClient, finca_a: dict) -> None:
    respuesta = cliente.post(
        RUTA,
        json={"nombre": "La Laguna", "hectareas": "33", "tipo_pasto": "pasto_natural"},
        headers=cabeceras(cliente, "capataz-a@ejemplo.com"),
    )

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["cantidad_animales"] == 0
    assert Decimal(cuerpo["carga_ugm_ha"]) == Decimal("0")
    assert cuerpo["dias_descanso_recomendado"] == 30


def test_los_modelos_no_se_tocan_solos(sesion: Session, finca_a: dict) -> None:
    """Guarda contra un descuido: crear un potrero no crea lotes ni al reves."""
    assert sesion.query(Potrero).filter_by(finca_id=finca_a["finca"].id).count() == 1
    assert sesion.query(Grupo).filter_by(finca_id=finca_a["finca"].id).count() == 1
