"""Inventario del hato."""

from fastapi import APIRouter, Depends

from app.dependencias.acceso import Alcance, require_rol
from app.esquemas.inventario import Inventario
from app.modelos.enumeraciones import RolUsuario
from app.servicios import inventario as servicio

router = APIRouter(prefix="/inventario", tags=["Inventario"])

TODOS_LOS_ROLES = [RolUsuario.administrador, RolUsuario.veterinario, RolUsuario.capataz]


@router.get(
    "",
    response_model=Inventario,
    summary="Conteo del hato",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def leer_inventario(alcance: Alcance) -> Inventario:
    """Conteo por lote, etapa, potrero, sexo y estado.

    Sale de la vista materializada, que se refresca aparte con debounce de 30
    segundos: `actualizado_en` dice de cuando son los numeros.
    """
    return servicio.leer(alcance)
