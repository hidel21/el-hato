"""Ciclo reproductivo. El ciclo no termina en el diagnostico (decision 5)."""

from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modelos.enumeraciones import Sexo
from app.servicios.reproduccion import DIAS_GESTACION
from tests.conftest import cabeceras, crear_animal

BASE = "/api/v1/reproduccion"
HOY = date.today()


def _vaca(sesion, finca, arete="C-100", **extra):
    return crear_animal(sesion, finca["finca"].id, arete, sexo=Sexo.hembra, **extra)


def _toro(sesion, finca, arete="T-001"):
    return crear_animal(sesion, finca["finca"].id, arete, sexo=Sexo.macho)


def test_el_servicio_calcula_la_fecha_estimada_de_parto(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    vaca = _vaca(sesion, finca_a)
    toro = _toro(sesion, finca_a)
    capataz = cabeceras(cliente, "capataz-a@ejemplo.com")
    fecha = HOY - timedelta(days=30)

    servicio = cliente.post(
        f"{BASE}/servicios",
        json={
            "animal_id": str(vaca.id),
            "toro_id": str(toro.id),
            "tipo": "monta_natural",
            "fecha_servicio": str(fecha),
        },
        headers=capataz,
    )

    assert servicio.status_code == 201, servicio.text
    assert servicio.json()["fecha_estimada_parto"] == str(fecha + timedelta(days=DIAS_GESTACION))
    assert servicio.json()["toro_arete"] == "T-001"


def test_el_parto_abre_la_ficha_del_ternero_con_su_genealogia(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    """La regla del modulo: el nacimiento se captura una sola vez."""
    vaca = _vaca(sesion, finca_a, "C-0412", raza="Brahman")
    toro = _toro(sesion, finca_a, "T-0031")
    capataz = cabeceras(cliente, "capataz-a@ejemplo.com")

    cliente.post(
        f"{BASE}/servicios",
        json={
            "animal_id": str(vaca.id),
            "toro_id": str(toro.id),
            "fecha_servicio": str(HOY - timedelta(days=284)),
        },
        headers=capataz,
    )

    parto = cliente.post(
        f"{BASE}/partos",
        json={
            "madre_id": str(vaca.id),
            "fecha_parto": str(HOY),
            "resultado": "vivo",
            "dificultad": "normal",
            "cria": {
                "arete": "C-1099",
                "nombre": "Canela",
                "sexo": "hembra",
                "peso_nacimiento_kg": "32.5",
            },
        },
        headers=capataz,
    )

    assert parto.status_code == 201, parto.text
    assert parto.json()["cria_arete"] == "C-1099"

    ficha = cliente.get(f"/api/v1/animales/{parto.json()['cria_id']}", headers=capataz).json()
    assert ficha["arete"] == "C-1099"
    assert ficha["madre_arete"] == "C-0412"
    assert ficha["padre_arete"] == "T-0031"
    assert ficha["raza"] == "Brahman"
    assert ficha["origen"] == "nacimiento"
    assert ficha["fecha_nacimiento"] == str(HOY)


def test_el_intervalo_entre_partos_es_el_indicador_del_hato(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    vaca = _vaca(sesion, finca_a)
    capataz = cabeceras(cliente, "capataz-a@ejemplo.com")

    for dias in (760, 380, 0):
        cliente.post(
            f"{BASE}/partos",
            json={"madre_id": str(vaca.id), "fecha_parto": str(HOY - timedelta(days=dias))},
            headers=capataz,
        )

    partos = cliente.get(f"{BASE}/partos?madre_id={vaca.id}", headers=capataz).json()["datos"]
    intervalos = [p["intervalo_partos_dias"] for p in partos]

    # El listado viene del mas reciente al mas viejo.
    assert intervalos == [380, 380, None]

    hoja = cliente.get(f"{BASE}/de-animal/{vaca.id}", headers=capataz).json()
    assert hoja["partos_totales"] == 3
    assert hoja["intervalo_promedio_dias"] == 380


def test_la_hoja_reproductiva_dice_en_que_punto_del_ciclo_esta(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    vaca = _vaca(sesion, finca_a)
    toro = _toro(sesion, finca_a)
    capataz = cabeceras(cliente, "capataz-a@ejemplo.com")
    veterinario = cabeceras(cliente, "veterinario-a@ejemplo.com")
    ruta = f"{BASE}/de-animal/{vaca.id}"

    assert cliente.get(ruta, headers=capataz).json()["estado"] == "sin_registros"

    cliente.post(
        f"{BASE}/celos",
        json={"animal_id": str(vaca.id), "fecha_celo": str(HOY - timedelta(days=60))},
        headers=capataz,
    )
    cliente.post(
        f"{BASE}/servicios",
        json={
            "animal_id": str(vaca.id),
            "toro_id": str(toro.id),
            "fecha_servicio": str(HOY - timedelta(days=59)),
        },
        headers=capataz,
    )
    assert cliente.get(ruta, headers=capataz).json()["estado"] == "en_servicio"

    cliente.post(
        f"{BASE}/diagnosticos",
        json={
            "animal_id": str(vaca.id),
            "resultado": "prenada",
            "metodo": "palpacion",
            "fecha_diagnostico": str(HOY - timedelta(days=15)),
        },
        headers=veterinario,
    )
    hoja = cliente.get(ruta, headers=capataz).json()

    assert hoja["estado"] == "prenada"
    assert hoja["descripcion_estado"] == "Preñada"
    # La fecha estimada la hereda del servicio, no la reinventa.
    assert hoja["fecha_estimada_parto"] == str(HOY - timedelta(days=59) + timedelta(days=283))
    assert [e["tipo"] for e in hoja["eventos"]] == ["celo", "servicio", "diagnostico"]


def test_los_dias_abiertos_cuentan_desde_el_ultimo_parto(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    """Cada dia abierto es dinero: la vaca come y no esta gestando."""
    vaca = _vaca(sesion, finca_a)
    capataz = cabeceras(cliente, "capataz-a@ejemplo.com")

    cliente.post(
        f"{BASE}/partos",
        json={"madre_id": str(vaca.id), "fecha_parto": str(HOY - timedelta(days=90))},
        headers=capataz,
    )
    hoja = cliente.get(f"{BASE}/de-animal/{vaca.id}", headers=capataz).json()
    assert hoja["estado"] == "parida"
    assert hoja["dias_abiertos"] == 90

    # Al volver a servirla, los dias abiertos se congelan en ese punto.
    cliente.post(
        f"{BASE}/servicios",
        json={"animal_id": str(vaca.id), "fecha_servicio": str(HOY - timedelta(days=30))},
        headers=capataz,
    )
    hoja = cliente.get(f"{BASE}/de-animal/{vaca.id}", headers=capataz).json()
    assert hoja["dias_abiertos"] == 60


def test_un_macho_no_entra_al_ciclo_reproductivo(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    toro = _toro(sesion, finca_a)

    respuesta = cliente.post(
        f"{BASE}/celos",
        json={"animal_id": str(toro.id)},
        headers=cabeceras(cliente, "capataz-a@ejemplo.com"),
    )

    assert respuesta.status_code == 422
    assert "es macho" in respuesta.json()["error"]["message"]


def test_una_hembra_no_puede_servir(cliente: TestClient, sesion: Session, finca_a: dict) -> None:
    vaca = _vaca(sesion, finca_a)
    otra = _vaca(sesion, finca_a, "C-200")

    respuesta = cliente.post(
        f"{BASE}/servicios",
        json={"animal_id": str(vaca.id), "toro_id": str(otra.id)},
        headers=cabeceras(cliente, "capataz-a@ejemplo.com"),
    )

    assert respuesta.status_code == 422
    assert "es hembra" in respuesta.json()["error"]["message"]


def test_solo_el_veterinario_diagnostica_prenez(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    vaca = _vaca(sesion, finca_a)

    respuesta = cliente.post(
        f"{BASE}/diagnosticos",
        json={"animal_id": str(vaca.id), "resultado": "prenada"},
        headers=cabeceras(cliente, "capataz-a@ejemplo.com"),
    )

    assert respuesta.status_code == 403


def test_no_se_abre_ficha_de_cria_si_no_nacio_viva(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    vaca = _vaca(sesion, finca_a)

    respuesta = cliente.post(
        f"{BASE}/partos",
        json={
            "madre_id": str(vaca.id),
            "resultado": "muerto",
            "cria": {"arete": "C-999", "sexo": "macho"},
        },
        headers=cabeceras(cliente, "capataz-a@ejemplo.com"),
    )

    assert respuesta.status_code == 422
    assert "nace viva" in respuesta.json()["error"]["message"]


def test_no_se_registra_nada_en_el_futuro(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    vaca = _vaca(sesion, finca_a)
    capataz = cabeceras(cliente, "capataz-a@ejemplo.com")

    respuesta = cliente.post(
        f"{BASE}/celos",
        json={"animal_id": str(vaca.id), "fecha_celo": str(HOY + timedelta(days=1))},
        headers=capataz,
    )

    assert respuesta.status_code == 422


def test_el_ciclo_no_cruza_fincas(
    cliente: TestClient, sesion: Session, finca_a: dict, finca_b: dict
) -> None:
    ajena = _vaca(sesion, finca_b, "B-100")
    de_a = cabeceras(cliente, "capataz-a@ejemplo.com")

    celo = cliente.post(f"{BASE}/celos", json={"animal_id": str(ajena.id)}, headers=de_a)
    hoja = cliente.get(f"{BASE}/de-animal/{ajena.id}", headers=de_a)

    assert celo.status_code == 422
    assert hoja.status_code == 404


def test_el_arete_repetido_de_una_cria_tampoco_se_rechaza(
    cliente: TestClient, sesion: Session, finca_a: dict
) -> None:
    """Decision 1 tambien aqui: el dato capturado en campo no se pierde."""
    vaca = _vaca(sesion, finca_a, "C-0412")
    crear_animal(sesion, finca_a["finca"].id, "C-777")
    capataz = cabeceras(cliente, "capataz-a@ejemplo.com")

    parto = cliente.post(
        f"{BASE}/partos",
        json={
            "madre_id": str(vaca.id),
            "cria": {"arete": "C-777", "sexo": "macho"},
        },
        headers=capataz,
    )

    assert parto.status_code == 201
    cria = cliente.get(f"/api/v1/animales/{parto.json()['cria_id']}", headers=capataz).json()
    assert cria["arete_duplicado"] is True
