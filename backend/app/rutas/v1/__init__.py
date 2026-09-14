"""Router de la version 1 de la API."""

from fastapi import APIRouter

from app.rutas.v1 import (
    animales,
    autenticacion,
    grupos,
    inventario,
    pesajes,
    potreros,
)

router_v1 = APIRouter(prefix="/api/v1")
router_v1.include_router(autenticacion.router)
router_v1.include_router(animales.router)
router_v1.include_router(grupos.router)
router_v1.include_router(potreros.router)
router_v1.include_router(pesajes.router)
router_v1.include_router(inventario.router)
