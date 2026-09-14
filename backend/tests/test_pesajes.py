"""Control de peso: la ganancia diaria es el numero del modulo."""

from datetime import date, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import cabeceras, crear_animal

RUTA = "/api/v1/pesajes"


def _pesar(cliente, cabecera, animal_id, fecha, peso):
    return cliente.post(
        RUTA,
        json={"animal_id": str(animal_id), "fecha_pesaje": str(fecha), "peso_kg": str(peso)},
        headers=cabecera,
    )


def test_la_ganancia_diaria_se_calcula_contra_el_pesaje_anterior(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    """La regla del modulo: 30 kg en 60 dias son 0,5 kg por dia."""
    animal = crear_animal(sesion, finca_a["finca"].id, "C-100")
    capataz = cabeceras(cliente, "capataz-a@ejemplo.com")
    hoy = date.today()

    primero = _pesar(cliente, capataz, animal.id, hoy - timedelta(days=60), 300)
    segundo = _pesar(cliente, capataz, animal.id, hoy, 330)

    assert primero.status_code == 201, primero.text
    # El primero no tiene con que compararse.
    assert primero.json()["ganancia_diaria_kg"] is None
    assert Decimal(segundo.json()["ganancia_diaria_kg"]) == Decimal("0.500")
    assert Decimal(segundo.json()["diferencia_kg"]) == Decimal("30.00")
    assert segundo.json()["dias_desde_anterior"] == 60


def test_el_peso_del_animal_queda_al_dia(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    animal = crear_animal(sesion, finca_a["finca"].id, "C-101")
    capataz = cabeceras(cliente, "capataz-a@ejemplo.com")
    hoy = date.today()

    _pesar(cliente, capataz, animal.id, hoy - timedelta(days=30), 280)
    _pesar(cliente, capataz, animal.id, hoy, 315.5)

    sesion.refresh(animal)
    assert animal.peso_actual_kg == Decimal("315.50")

    ficha = cliente.get(f"/api/v1/animales/{animal.id}", headers=capataz).json()
    assert Decimal(ficha["peso_actual_kg"]) == Decimal("315.50")


def test_un_pesaje_con_fecha_vieja_recalcula_los_posteriores(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    """Pasa a diario: se anota en papel y se captura al final del dia."""
    animal = crear_animal(sesion, finca_a["finca"].id, "C-102")
    capataz = cabeceras(cliente, "capataz-a@ejemplo.com")
    hoy = date.today()

    _pesar(cliente, capataz, animal.id, hoy - timedelta(days=100), 200)
    ultimo = _pesar(cliente, capataz, animal.id, hoy, 300).json()
    # 100 kg en 100 dias
    assert Decimal(ultimo["ganancia_diaria_kg"]) == Decimal("1.000")

    # Aparece un pesaje intermedio que nadie habia capturado.
    _pesar(cliente, capataz, animal.id, hoy - timedelta(days=50), 260)

    corregido = cliente.get(f"{RUTA}/{ultimo['id']}", headers=capataz).json()
    # Ahora el ultimo se compara contra el intermedio: 40 kg en 50 dias.
    assert Decimal(corregido["ganancia_diaria_kg"]) == Decimal("0.800")


def test_el_historial_sale_del_mas_viejo_al_mas_nuevo(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    animal = crear_animal(sesion, finca_a["finca"].id, "C-103")
    capataz = cabeceras(cliente, "capataz-a@ejemplo.com")
    hoy = date.today()
    for dias, peso in [(90, 210), (60, 240), (30, 275), (0, 300)]:
        _pesar(cliente, capataz, animal.id, hoy - timedelta(days=dias), peso)

    historial = cliente.get(f"{RUTA}/de-animal/{animal.id}", headers=capataz).json()

    assert [float(p["peso_kg"]) for p in historial] == [210, 240, 275, 300]
    assert historial[0]["diferencia_kg"] is None
    assert Decimal(historial[-1]["diferencia_kg"]) == Decimal("25.00")


def test_no_se_pesa_en_el_futuro_ni_antes_de_nacer(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    animal = crear_animal(
        sesion, finca_a["finca"].id, "C-104", fecha_nacimiento=date.today() - timedelta(days=10)
    )
    capataz = cabeceras(cliente, "capataz-a@ejemplo.com")

    futuro = _pesar(cliente, capataz, animal.id, date.today() + timedelta(days=1), 100)
    antes = _pesar(cliente, capataz, animal.id, date.today() - timedelta(days=40), 100)

    assert futuro.status_code == 422
    assert "futuro" in futuro.json()["error"]["message"]
    assert antes.status_code == 422
    assert "nacimiento" in antes.json()["error"]["message"]


def test_borrar_un_pesaje_devuelve_el_peso_anterior_al_animal(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    animal = crear_animal(sesion, finca_a["finca"].id, "C-105")
    capataz = cabeceras(cliente, "capataz-a@ejemplo.com")
    administrador = cabeceras(cliente, "administrador-a@ejemplo.com")
    hoy = date.today()

    _pesar(cliente, capataz, animal.id, hoy - timedelta(days=30), 280)
    ultimo = _pesar(cliente, capataz, animal.id, hoy, 310).json()

    assert cliente.delete(f"{RUTA}/{ultimo['id']}", headers=administrador).status_code == 204

    sesion.refresh(animal)
    assert animal.peso_actual_kg == Decimal("280.00")


def test_el_capataz_no_puede_borrar_pesajes(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    animal = crear_animal(sesion, finca_a["finca"].id, "C-106")
    capataz = cabeceras(cliente, "capataz-a@ejemplo.com")
    pesaje = _pesar(cliente, capataz, animal.id, date.today(), 250).json()

    respuesta = cliente.delete(f"{RUTA}/{pesaje['id']}", headers=capataz)

    assert respuesta.status_code == 403


def test_no_se_pesa_un_animal_de_otra_finca(
    cliente: TestClient, sesion: Session, finca_a: dict, finca_b: dict
) -> None:
    ajeno = crear_animal(sesion, finca_b["finca"].id, "B-100")

    capataz = cabeceras(cliente, "capataz-a@ejemplo.com")
    respuesta = _pesar(cliente, capataz, ajeno.id, date.today(), 300)

    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["message"] == "Ese animal no esta en tu finca."


def test_el_historial_de_un_animal_ajeno_no_se_ve(
    cliente: TestClient, sesion: Session, finca_a: dict, finca_b: dict
) -> None:
    ajeno = crear_animal(sesion, finca_b["finca"].id, "B-101")

    respuesta = cliente.get(
        f"{RUTA}/de-animal/{ajeno.id}", headers=cabeceras(cliente, "capataz-a@ejemplo.com")
    )

    assert respuesta.status_code == 404
