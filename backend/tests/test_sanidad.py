"""Vacunacion y baños: la membresia se congela al aplicar (decision 8)."""

from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import cabeceras, crear_animal, crear_grupo, crear_potrero

VACUNAS = "/api/v1/catalogo-vacunas"
APLICAR = "/api/v1/vacunaciones"
PRODUCTOS = "/api/v1/catalogo-productos-bano"
BANOS = "/api/v1/banos"


def _vacuna(cliente, cabecera, **extra):
    cuerpo = {"nombre": "Aftosa", "enfermedad": "Fiebre aftosa", "dias_refuerzo": 180, **extra}
    return cliente.post(VACUNAS, json=cuerpo, headers=cabecera).json()


def _producto(cliente, cabecera, **extra):
    cuerpo = {
        "nombre": "Garrapaticida",
        "dias_carencia_carne": 21,
        "dias_carencia_leche": 3,
        "dias_reaplicacion": 30,
        **extra,
    }
    return cliente.post(PRODUCTOS, json=cuerpo, headers=cabecera).json()


def test_la_aplicacion_por_lote_congela_quienes_la_recibieron(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    """La regla del modulo. El lote cambia mañana; el registro sanitario no."""
    veterinario = cabeceras(cliente, "veterinario-a@ejemplo.com")
    grupo = crear_grupo(sesion, finca_a["finca"].id, "Levante Norte")
    animales = [
        crear_animal(sesion, finca_a["finca"].id, f"C-{n}", grupo_id=grupo.id) for n in range(3)
    ]
    vacuna = _vacuna(cliente, veterinario)

    aplicacion = cliente.post(
        APLICAR,
        json={"catalogo_vacuna_id": vacuna["id"], "grupo_id": str(grupo.id)},
        headers=veterinario,
    )
    assert aplicacion.status_code == 201, aplicacion.text
    assert aplicacion.json()["cantidad_animales"] == 3

    # Entra un animal nuevo al lote DESPUES de la aplicacion.
    crear_animal(sesion, finca_a["finca"].id, "C-nuevo", grupo_id=grupo.id)

    recibieron = cliente.get(
        f"{APLICAR}/{aplicacion.json()['id']}/animales", headers=veterinario
    ).json()
    assert {a["arete"] for a in recibieron} == {a.arete for a in animales}
    assert "C-nuevo" not in {a["arete"] for a in recibieron}


def test_la_proxima_dosis_sale_de_los_dias_de_refuerzo(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    veterinario = cabeceras(cliente, "veterinario-a@ejemplo.com")
    animal = crear_animal(sesion, finca_a["finca"].id, "C-100")
    vacuna = _vacuna(cliente, veterinario, dias_refuerzo=180)
    hoy = date.today()

    aplicacion = cliente.post(
        APLICAR,
        json={
            "catalogo_vacuna_id": vacuna["id"],
            "animal_id": str(animal.id),
            "fecha_aplicacion": str(hoy),
        },
        headers=veterinario,
    ).json()

    assert aplicacion["proxima_dosis_fecha"] == str(hoy + timedelta(days=180))


def test_el_historial_sanitario_de_un_animal_incluye_lo_aplicado_por_lote(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    veterinario = cabeceras(cliente, "veterinario-a@ejemplo.com")
    grupo = crear_grupo(sesion, finca_a["finca"].id, "Vientres A")
    animal = crear_animal(sesion, finca_a["finca"].id, "C-200", grupo_id=grupo.id)
    vacuna = _vacuna(cliente, veterinario)

    cliente.post(
        APLICAR,
        json={"catalogo_vacuna_id": vacuna["id"], "grupo_id": str(grupo.id)},
        headers=veterinario,
    )

    suyas = cliente.get(f"{APLICAR}?animal_id={animal.id}", headers=veterinario).json()
    assert len(suyas["datos"]) == 1
    assert suyas["datos"][0]["vacuna_nombre"] == "Aftosa"


def test_el_baño_calcula_la_carencia_de_carne_y_de_leche(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    """Sin carencia bien contada hay decomiso en frigorifico."""
    veterinario = cabeceras(cliente, "veterinario-a@ejemplo.com")
    potrero = crear_potrero(sesion, finca_a["finca"].id, "La Ceiba")
    crear_animal(sesion, finca_a["finca"].id, "C-300", potrero_id=potrero.id)
    producto = _producto(cliente, veterinario)
    hoy = date.today()

    bano = cliente.post(
        BANOS,
        json={
            "producto_id": producto["id"],
            "potrero_id": str(potrero.id),
            "fecha_bano": str(hoy),
        },
        headers=veterinario,
    ).json()

    assert bano["carencia_carne_hasta"] == str(hoy + timedelta(days=21))
    assert bano["carencia_leche_hasta"] == str(hoy + timedelta(days=3))
    assert bano["proxima_fecha"] == str(hoy + timedelta(days=30))
    assert bano["cantidad_animales"] == 1


def test_un_baño_va_a_un_lote_a_un_potrero_o_a_un_animal_pero_solo_uno(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    veterinario = cabeceras(cliente, "veterinario-a@ejemplo.com")
    grupo = crear_grupo(sesion, finca_a["finca"].id, "Levante")
    potrero = crear_potrero(sesion, finca_a["finca"].id, "La Ceiba")
    producto = _producto(cliente, veterinario)

    dos = cliente.post(
        BANOS,
        json={
            "producto_id": producto["id"],
            "grupo_id": str(grupo.id),
            "potrero_id": str(potrero.id),
        },
        headers=veterinario,
    )
    ninguno = cliente.post(BANOS, json={"producto_id": producto["id"]}, headers=veterinario)

    assert dos.status_code == 422
    assert ninguno.status_code == 422


def test_no_se_aplica_nada_donde_no_hay_animales(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    veterinario = cabeceras(cliente, "veterinario-a@ejemplo.com")
    grupo = crear_grupo(sesion, finca_a["finca"].id, "Vacio")
    vacuna = _vacuna(cliente, veterinario)

    respuesta = cliente.post(
        APLICAR,
        json={"catalogo_vacuna_id": vacuna["id"], "grupo_id": str(grupo.id)},
        headers=veterinario,
    )

    assert respuesta.status_code == 422
    assert "ningun animal" in respuesta.json()["error"]["message"]


def test_no_se_registra_una_aplicacion_en_el_futuro(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    veterinario = cabeceras(cliente, "veterinario-a@ejemplo.com")
    animal = crear_animal(sesion, finca_a["finca"].id, "C-400")
    vacuna = _vacuna(cliente, veterinario)

    respuesta = cliente.post(
        APLICAR,
        json={
            "catalogo_vacuna_id": vacuna["id"],
            "animal_id": str(animal.id),
            "fecha_aplicacion": str(date.today() + timedelta(days=1)),
        },
        headers=veterinario,
    )

    assert respuesta.status_code == 422


def test_el_capataz_no_toca_el_catalogo_pero_si_aplica(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    """En el potrero se aplica; el catalogo lo mantiene quien sabe de farmacos."""
    capataz = cabeceras(cliente, "capataz-a@ejemplo.com")
    veterinario = cabeceras(cliente, "veterinario-a@ejemplo.com")
    animal = crear_animal(sesion, finca_a["finca"].id, "C-500")
    vacuna = _vacuna(cliente, veterinario)

    alta_catalogo = cliente.post(VACUNAS, json={"nombre": "Otra"}, headers=capataz)
    aplicacion = cliente.post(
        APLICAR,
        json={"catalogo_vacuna_id": vacuna["id"], "animal_id": str(animal.id)},
        headers=capataz,
    )

    assert alta_catalogo.status_code == 403
    assert aplicacion.status_code == 201


def test_no_se_borra_del_catalogo_lo_que_ya_se_aplico(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    veterinario = cabeceras(cliente, "veterinario-a@ejemplo.com")
    administrador = cabeceras(cliente, "administrador-a@ejemplo.com")
    animal = crear_animal(sesion, finca_a["finca"].id, "C-600")
    vacuna = _vacuna(cliente, veterinario)
    cliente.post(
        APLICAR,
        json={"catalogo_vacuna_id": vacuna["id"], "animal_id": str(animal.id)},
        headers=veterinario,
    )

    respuesta = cliente.delete(f"{VACUNAS}/{vacuna['id']}", headers=administrador)

    assert respuesta.status_code == 409
    assert respuesta.json()["error"]["code"] == "catalogo_en_uso"
    assert "Desactivalo" in respuesta.json()["error"]["message"]


def test_los_vencimientos_se_pueden_pedir_por_fecha(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    veterinario = cabeceras(cliente, "veterinario-a@ejemplo.com")
    animal = crear_animal(sesion, finca_a["finca"].id, "C-700")
    pronto = _vacuna(cliente, veterinario, nombre="Pronto", dias_refuerzo=10)
    lejos = _vacuna(cliente, veterinario, nombre="Lejos", dias_refuerzo=300)
    for vacuna in (pronto, lejos):
        cliente.post(
            APLICAR,
            json={"catalogo_vacuna_id": vacuna["id"], "animal_id": str(animal.id)},
            headers=veterinario,
        )

    corte = date.today() + timedelta(days=30)
    vencen = cliente.get(f"{APLICAR}?vence_antes_de={corte}", headers=veterinario).json()

    assert [v["vacuna_nombre"] for v in vencen["datos"]] == ["Pronto"]


def test_no_se_aplica_a_un_animal_de_otra_finca(
    cliente: TestClient, sesion: Session, finca_a: dict, finca_b: dict
) -> None:
    veterinario = cabeceras(cliente, "veterinario-a@ejemplo.com")
    ajeno = crear_animal(sesion, finca_b["finca"].id, "B-100")
    vacuna = _vacuna(cliente, veterinario)

    respuesta = cliente.post(
        APLICAR,
        json={"catalogo_vacuna_id": vacuna["id"], "animal_id": str(ajeno.id)},
        headers=veterinario,
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["message"] == "Ese animal no esta en tu finca."


def test_el_catalogo_no_cruza_fincas(
    cliente: TestClient, sesion: Session, finca_a: dict, finca_b: dict
) -> None:
    _vacuna(cliente, cabeceras(cliente, "veterinario-a@ejemplo.com"), nombre="Solo de A")

    de_b = cliente.get(VACUNAS, headers=cabeceras(cliente, "veterinario-b@ejemplo.com")).json()

    assert de_b["datos"] == []
