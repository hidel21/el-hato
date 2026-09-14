"""Inventario del hato, leido de la vista materializada."""

from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modelos.enumeraciones import EtapaGrupo, Sexo
from app.servicios import inventario
from tests.conftest import cabeceras, crear_animal, crear_grupo, crear_potrero

RUTA = "/api/v1/inventario"


def test_cuenta_el_hato_por_etapa_sexo_y_potrero(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    potrero = crear_potrero(sesion, finca_a["finca"].id, "La Ceiba")
    vientres = crear_grupo(
        sesion, finca_a["finca"].id, "Vientres A", etapa=EtapaGrupo.vientre, potrero_id=potrero.id
    )
    terneros = crear_grupo(
        sesion, finca_a["finca"].id, "Terneras 26", etapa=EtapaGrupo.ternero, potrero_id=potrero.id
    )
    for numero in range(3):
        crear_animal(
            sesion,
            finca_a["finca"].id,
            f"V-{numero}",
            grupo_id=vientres.id,
            potrero_id=potrero.id,
            sexo=Sexo.hembra,
            peso_actual_kg=Decimal("450"),
        )
    crear_animal(
        sesion,
        finca_a["finca"].id,
        "T-1",
        grupo_id=terneros.id,
        potrero_id=potrero.id,
        sexo=Sexo.macho,
        peso_actual_kg=Decimal("90"),
    )
    # La vista no se refresca sola dentro de la peticion (decision 7).
    inventario.refrescar_ahora()

    cuerpo = cliente.get(RUTA, headers=cabeceras(cliente, "capataz-a@ejemplo.com")).json()

    assert cuerpo["total_animales"] == 4
    assert cuerpo["hembras"] == 3
    assert cuerpo["machos"] == 1
    assert Decimal(cuerpo["peso_total_kg"]) == Decimal("1440")

    etapas = {c["clave"]: c for c in cuerpo["por_etapa"]}
    assert etapas["vientre"]["cantidad"] == 3
    assert etapas["vientre"]["etiqueta"] == "Vientres"
    assert etapas["vientre"]["porcentaje"] == 75
    assert etapas["ternero"]["cantidad"] == 1

    potreros = {c["etiqueta"]: c["cantidad"] for c in cuerpo["por_potrero"]}
    assert potreros["La Ceiba"] == 4


def test_los_animales_sin_lote_se_cuentan_aparte(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    crear_animal(sesion, finca_a["finca"].id, "S-1")
    inventario.refrescar_ahora()

    cuerpo = cliente.get(RUTA, headers=cabeceras(cliente, "capataz-a@ejemplo.com")).json()

    etapas = {c["clave"]: c["etiqueta"] for c in cuerpo["por_etapa"]}
    assert etapas["sin_lote"] == "Sin lote"


def test_el_inventario_no_cruza_fincas(
    cliente: TestClient, sesion: Session, finca_a: dict, finca_b: dict
) -> None:
    crear_animal(sesion, finca_a["finca"].id, "A-1")
    for numero in range(4):
        crear_animal(sesion, finca_b["finca"].id, f"B-{numero}")
    inventario.refrescar_ahora()

    de_a = cliente.get(RUTA, headers=cabeceras(cliente, "capataz-a@ejemplo.com")).json()
    de_b = cliente.get(RUTA, headers=cabeceras(cliente, "capataz-b@ejemplo.com")).json()

    assert de_a["total_animales"] == 1
    assert de_b["total_animales"] == 4


def test_un_hato_vacio_no_rompe_los_porcentajes(cliente: TestClient, finca_a: dict) -> None:
    inventario.refrescar_ahora()

    cuerpo = cliente.get(RUTA, headers=cabeceras(cliente, "capataz-a@ejemplo.com")).json()

    assert cuerpo["total_animales"] == 0
    assert cuerpo["por_etapa"] == []
    assert cuerpo["peso_promedio_kg"] is None


def test_los_animales_borrados_no_cuentan(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    animal = crear_animal(sesion, finca_a["finca"].id, "C-1")
    crear_animal(sesion, finca_a["finca"].id, "C-2")
    administrador = cabeceras(cliente, "administrador-a@ejemplo.com")
    cliente.delete(f"/api/v1/animales/{animal.id}", headers=administrador)
    inventario.refrescar_ahora()

    cuerpo = cliente.get(RUTA, headers=administrador).json()

    assert cuerpo["total_animales"] == 1
