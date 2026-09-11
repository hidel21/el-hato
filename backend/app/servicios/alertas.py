"""Alertas que genera el servidor.

Decision 6: lo derivable de los datos (proxima dosis, fecha estimada de parto,
dias de carencia, dias de ocupacion de un potrero) lo calcula el cliente, que
ya tiene los datos en el dispositivo y funciona sin señal.

Aqui solo vive lo que el cliente no puede saber solo: los conflictos que
aparecen al juntar el trabajo de varios dispositivos, y las alertas que exigen
agregacion de toda la finca.
"""

import uuid

from sqlalchemy.orm import Session

from app.modelos.animal import Animal
from app.modelos.enumeraciones import EstadoAlerta, TipoAlerta
from app.modelos.operacion import Alerta


def alertar_arete_duplicado(sesion: Session, nuevo: Animal, existente_id: uuid.UUID) -> Alerta:
    """Decision 1: el registro entra igual y una persona resuelve el choque.

    Pasa cuando dos capataces sin señal dan de alta el mismo arete. Rechazar el
    segundo significaria perder trabajo hecho en el potrero.
    """
    alerta = Alerta(
        finca_id=nuevo.finca_id,
        tipo=TipoAlerta.otro,
        estado=EstadoAlerta.pendiente,
        titulo=f"Arete repetido: {nuevo.arete}",
        descripcion=(
            f"Se registro otro animal con el arete {nuevo.arete}. "
            "Revisa cual ficha se queda con el arete y corrige la otra."
        ),
        animal_id=nuevo.id,
        referencia_tabla="animales",
        referencia_id=existente_id,
        device_id=nuevo.device_id,
    )
    sesion.add(alerta)
    return alerta
