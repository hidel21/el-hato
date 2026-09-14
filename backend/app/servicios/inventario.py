"""Refresco de la vista materializada inventario_hato.

Decision 7: nunca se refresca dentro de la peticion. Refrescar en linea
convierte un alta de dos segundos en una de quince.

El debounce es por coalescencia, no por reinicio: la primera escritura agenda
un refresco dentro de 30 segundos y las que lleguen en esa ventana se suman al
mismo. Asi se garantiza como mucho un refresco cada 30 segundos y, a la vez,
que ninguna escritura se quede esperando indefinidamente, que es lo que pasa
con un debounce que reinicia el temporizador bajo escritura continua.
"""

import logging
import threading
from decimal import Decimal

import sqlalchemy as sa

from app.dependencias.acceso import AlcanceFinca
from app.esquemas.inventario import Corte, FilaInventario, Inventario
from app.modelos.enumeraciones import EstadoAnimal, EtapaGrupo, Sexo
from app.nucleo.base_datos import motor
from app.nucleo.configuracion import configuracion

registro = logging.getLogger(__name__)

SENTENCIA = sa.text("REFRESH MATERIALIZED VIEW CONCURRENTLY inventario_hato")

_candado = threading.Lock()
_temporizador: threading.Timer | None = None


def refrescar_ahora() -> None:
    """Refresca de inmediato. Lo usan el temporizador y las pruebas."""
    with motor.begin() as conexion:
        conexion.execute(SENTENCIA)


def _disparar() -> None:
    global _temporizador
    with _candado:
        _temporizador = None
    try:
        refrescar_ahora()
    except Exception:  # el refresco nunca debe tumbar el proceso
        registro.exception("No se pudo refrescar inventario_hato")


def agendar_refresco() -> bool:
    """Agenda el refresco. Devuelve True si agendo uno nuevo, False si ya habia.

    Con segundos_debounce_inventario en 0 no hace nada: asi corren los tests.
    """
    global _temporizador
    if configuracion.segundos_debounce_inventario <= 0:
        return False

    with _candado:
        if _temporizador is not None:
            return False
        _temporizador = threading.Timer(configuracion.segundos_debounce_inventario, _disparar)
        _temporizador.daemon = True
        _temporizador.start()
    return True


def cancelar_pendiente() -> None:
    """Cancela el refresco agendado. Para apagar limpio."""
    global _temporizador
    with _candado:
        if _temporizador is not None:
            _temporizador.cancel()
            _temporizador = None


# ----------------------------------------------------------------------
# Lectura
# ----------------------------------------------------------------------

ETIQUETAS_ETAPA = {
    EtapaGrupo.ternero: "Terneros y terneras",
    EtapaGrupo.destete: "Destete",
    EtapaGrupo.levante: "Levante",
    EtapaGrupo.engorde: "Engorde",
    EtapaGrupo.vientre: "Vientres",
    EtapaGrupo.toro: "Toros",
    EtapaGrupo.descarte: "Descarte",
}

ETIQUETAS_ESTADO = {
    EstadoAnimal.activo: "Activos",
    EstadoAnimal.en_engorde: "En engorde",
    EstadoAnimal.vendido: "Vendidos",
    EstadoAnimal.muerto: "Muertos",
    EstadoAnimal.descartado: "Descartados",
}

SIN_LOTE = "Sin lote"
SIN_POTRERO = "Sin potrero"

VISTA = sa.table(
    "inventario_hato",
    sa.column("finca_id"),
    sa.column("grupo_id"),
    sa.column("grupo_nombre"),
    sa.column("grupo_etapa"),
    sa.column("potrero_id"),
    sa.column("potrero_nombre"),
    sa.column("sexo"),
    sa.column("estado"),
    sa.column("cantidad"),
    sa.column("peso_total_kg"),
    sa.column("peso_promedio_kg"),
    sa.column("actualizado_en"),
)


def _cortar(conteos: dict[str, tuple[str, int]], total: int) -> list[Corte]:
    """Ordena de mayor a menor y calcula que parte del hato es cada uno."""
    cortes = [
        Corte(
            clave=clave,
            etiqueta=etiqueta,
            cantidad=cantidad,
            porcentaje=round(cantidad * 100 / total) if total else 0,
        )
        for clave, (etiqueta, cantidad) in conteos.items()
    ]
    return sorted(cortes, key=lambda corte: (-corte.cantidad, corte.etiqueta))


def leer(alcance: AlcanceFinca) -> Inventario:
    """El inventario del hato, leido de la vista materializada.

    No se recalcula aqui: la vista se refresca aparte, con debounce de 30
    segundos (decision 7). Por eso la respuesta dice cuando se recalculo.
    """
    filas = (
        alcance.sesion.execute(sa.select(VISTA).where(VISTA.c.finca_id == alcance.finca_id))
        .mappings()
        .all()
    )

    detalle: list[FilaInventario] = []
    total = 0
    hembras = 0
    machos = 0
    peso_total = Decimal("0")
    por_etapa: dict[str, tuple[str, int]] = {}
    por_potrero: dict[str, tuple[str, int]] = {}
    por_estado: dict[str, tuple[str, int]] = {}
    actualizado = None

    for fila in filas:
        cantidad = fila["cantidad"]
        total += cantidad
        peso_total += Decimal(fila["peso_total_kg"] or 0)
        if fila["sexo"] == Sexo.hembra.value:
            hembras += cantidad
        else:
            machos += cantidad

        etapa = fila["grupo_etapa"]
        clave_etapa = etapa or "sin_lote"
        etiqueta_etapa = ETIQUETAS_ETAPA.get(EtapaGrupo(etapa), etapa) if etapa else SIN_LOTE
        por_etapa[clave_etapa] = (etiqueta_etapa, por_etapa.get(clave_etapa, ("", 0))[1] + cantidad)

        clave_potrero = str(fila["potrero_id"]) if fila["potrero_id"] else "sin_potrero"
        etiqueta_potrero = fila["potrero_nombre"] or SIN_POTRERO
        por_potrero[clave_potrero] = (
            etiqueta_potrero,
            por_potrero.get(clave_potrero, ("", 0))[1] + cantidad,
        )

        estado = fila["estado"]
        etiqueta_estado = ETIQUETAS_ESTADO.get(EstadoAnimal(estado), estado)
        por_estado[estado] = (etiqueta_estado, por_estado.get(estado, ("", 0))[1] + cantidad)

        if fila["actualizado_en"] and (actualizado is None or fila["actualizado_en"] > actualizado):
            actualizado = fila["actualizado_en"]

        detalle.append(FilaInventario(**fila))

    return Inventario(
        total_animales=total,
        hembras=hembras,
        machos=machos,
        peso_total_kg=peso_total,
        peso_promedio_kg=round(peso_total / total, 2) if total else None,
        por_etapa=_cortar(por_etapa, total),
        por_potrero=_cortar(por_potrero, total),
        por_estado=_cortar(por_estado, total),
        actualizado_en=actualizado,
        filas=sorted(detalle, key=lambda f: (-f.cantidad, f.grupo_nombre or "")),
    )
