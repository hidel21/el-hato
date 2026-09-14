"""Gastos y estado de alertas."""

from datetime import date, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import cabeceras, crear_animal, crear_grupo

GASTOS = "/api/v1/gastos"
ALERTAS = "/api/v1/alertas"
HOY = date.today()


def test_el_costo_acumulado_de_un_animal(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    """Saber cuanto costo criarlo es la mitad de saber si dio plata."""
    animal = crear_animal(sesion, finca_a["finca"].id, "C-100")
    otro = crear_animal(sesion, finca_a["finca"].id, "C-200")
    capataz = cabeceras(cliente, "capataz-a@ejemplo.com")

    for categoria, concepto, monto, quien in [
        ("veterinario", "Revisión de preñez", "18.00", animal),
        ("medicamento", "Vitamina AD3E", "6.50", animal),
        ("alimento", "Sal mineralizada", "12.00", animal),
        ("alimento", "Suplemento", "40.00", otro),
    ]:
        cliente.post(
            GASTOS,
            json={
                "categoria": categoria,
                "concepto": concepto,
                "monto": monto,
                "animal_id": str(quien.id),
            },
            headers=capataz,
        )

    resumen = cliente.get(f"{GASTOS}/resumen?animal_id={animal.id}", headers=capataz).json()

    assert Decimal(resumen["total"]) == Decimal("36.50")
    assert resumen["cantidad"] == 3
    assert Decimal(resumen["por_categoria"]["veterinario"]) == Decimal("18.00")


def test_el_resumen_se_puede_acotar_por_fecha(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    capataz = cabeceras(cliente, "capataz-a@ejemplo.com")
    for dias, monto in [(200, "500.00"), (10, "80.00")]:
        cliente.post(
            GASTOS,
            json={
                "categoria": "insumo",
                "concepto": "Compra",
                "monto": monto,
                "fecha_gasto": str(HOY - timedelta(days=dias)),
            },
            headers=capataz,
        )

    reciente = cliente.get(
        f"{GASTOS}/resumen?desde={HOY - timedelta(days=30)}", headers=capataz
    ).json()

    assert Decimal(reciente["total"]) == Decimal("80.00")


def test_un_gasto_puede_ir_a_un_lote(cliente: TestClient, sesion: Session, finca_a: dict) -> None:
    grupo = crear_grupo(sesion, finca_a["finca"].id, "Levante Norte")
    capataz = cabeceras(cliente, "capataz-a@ejemplo.com")

    gasto = cliente.post(
        GASTOS,
        json={
            "categoria": "alimento",
            "concepto": "Melaza",
            "monto": "220.00",
            "grupo_id": str(grupo.id),
        },
        headers=capataz,
    )

    assert gasto.status_code == 201
    assert gasto.json()["grupo_nombre"] == "Levante Norte"


def test_no_se_registra_un_gasto_en_el_futuro(cliente: TestClient, finca_a: dict) -> None:
    respuesta = cliente.post(
        GASTOS,
        json={
            "categoria": "insumo",
            "concepto": "Adelanto",
            "monto": "10.00",
            "fecha_gasto": str(HOY + timedelta(days=2)),
        },
        headers=cabeceras(cliente, "capataz-a@ejemplo.com"),
    )

    assert respuesta.status_code == 422


def test_los_gastos_no_cruzan_fincas(
    cliente: TestClient, sesion: Session, finca_a: dict, finca_b: dict
) -> None:
    ajeno = crear_animal(sesion, finca_b["finca"].id, "B-100")

    respuesta = cliente.post(
        GASTOS,
        json={
            "categoria": "insumo",
            "concepto": "Colado",
            "monto": "10.00",
            "animal_id": str(ajeno.id),
        },
        headers=cabeceras(cliente, "capataz-a@ejemplo.com"),
    )

    assert respuesta.status_code == 422


def test_marcar_atendida_una_alerta_derivada_no_la_duplica(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    """El cliente calcula el vencimiento; aqui solo se guarda que ya se atendio.

    Si dos dispositivos la marcan, tiene que quedar una sola fila.
    """
    animal = crear_animal(sesion, finca_a["finca"].id, "C-300")
    capataz = cabeceras(cliente, "capataz-a@ejemplo.com")
    referencia = str(animal.id)

    cuerpo = {
        "tipo": "vacunacion",
        "titulo": "Refuerzo de aftosa",
        "estado": "atendida",
        "animal_id": str(animal.id),
        "referencia_tabla": "vacunaciones",
        "referencia_id": referencia,
    }
    primera = cliente.post(ALERTAS, json=cuerpo, headers=capataz).json()
    segunda = cliente.post(ALERTAS, json=cuerpo, headers=capataz).json()

    assert primera["id"] == segunda["id"]
    assert segunda["estado"] == "atendida"
    assert segunda["atendida_por_nombre"] is not None

    listado = cliente.get(f"{ALERTAS}?referencia_tabla=vacunaciones", headers=capataz).json()
    assert len(listado["datos"]) == 1


def test_atender_y_reabrir_una_alerta(cliente: TestClient, sesion: Session, finca_a: dict) -> None:
    capataz = cabeceras(cliente, "capataz-a@ejemplo.com")
    alerta = cliente.post(
        ALERTAS,
        json={"tipo": "otro", "titulo": "Revisar la cerca del Palmar"},
        headers=capataz,
    ).json()

    atendida = cliente.put(
        f"{ALERTAS}/{alerta['id']}", json={"estado": "atendida"}, headers=capataz
    ).json()
    assert atendida["atendida_en"] is not None

    reabierta = cliente.put(
        f"{ALERTAS}/{alerta['id']}", json={"estado": "pendiente"}, headers=capataz
    ).json()
    assert reabierta["atendida_en"] is None
    assert reabierta["atendida_por_id"] is None


def test_solo_abiertas_deja_fuera_lo_resuelto(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    capataz = cabeceras(cliente, "capataz-a@ejemplo.com")
    abierta = cliente.post(
        ALERTAS, json={"tipo": "otro", "titulo": "Pendiente"}, headers=capataz
    ).json()
    cerrada = cliente.post(
        ALERTAS, json={"tipo": "otro", "titulo": "Hecha", "estado": "atendida"}, headers=capataz
    ).json()

    abiertas = cliente.get(f"{ALERTAS}?solo_abiertas=true", headers=capataz).json()
    ids = {a["id"] for a in abiertas["datos"]}

    assert abierta["id"] in ids
    assert cerrada["id"] not in ids


def test_las_alertas_no_cruzan_fincas(
    cliente: TestClient, sesion: Session, finca_a: dict, finca_b: dict
) -> None:
    cliente.post(
        ALERTAS,
        json={"tipo": "otro", "titulo": "Solo de A"},
        headers=cabeceras(cliente, "capataz-a@ejemplo.com"),
    )

    de_b = cliente.get(ALERTAS, headers=cabeceras(cliente, "capataz-b@ejemplo.com")).json()

    assert de_b["datos"] == []
