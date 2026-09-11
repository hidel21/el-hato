"""Router de la version 1 de la API."""

from fastapi import APIRouter

from app.rutas.v1 import autenticacion

router_v1 = APIRouter(prefix="/api/v1")
router_v1.include_router(autenticacion.router)
