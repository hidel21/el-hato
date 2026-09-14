"""Router de la version 1 de la API."""

from fastapi import APIRouter

from app.rutas.v1 import (
    alertas,
    animales,
    autenticacion,
    gastos,
    grupos,
    inventario,
    pesajes,
    potreros,
    reproduccion,
    sanidad,
)

router_v1 = APIRouter(prefix="/api/v1")
router_v1.include_router(autenticacion.router)
router_v1.include_router(animales.router)
router_v1.include_router(grupos.router)
router_v1.include_router(potreros.router)
router_v1.include_router(pesajes.router)
router_v1.include_router(inventario.router)
router_v1.include_router(sanidad.router_vacunas)
router_v1.include_router(sanidad.router_vacunaciones)
router_v1.include_router(sanidad.router_productos)
router_v1.include_router(sanidad.router_banos)
router_v1.include_router(reproduccion.router)
router_v1.include_router(gastos.router)
router_v1.include_router(alertas.router)
