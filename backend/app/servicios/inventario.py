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

import sqlalchemy as sa

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
