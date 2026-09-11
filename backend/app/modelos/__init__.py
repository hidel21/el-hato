"""Importar este paquete deja todos los modelos registrados en Base.metadata."""

from app.modelos.animal import Animal
from app.modelos.operacion import Alerta, SyncQueue
from app.modelos.organizacion import Dispositivo, Finca, Usuario
from app.modelos.produccion import Gasto, Pesaje
from app.modelos.reproduccion import Celo, DiagnosticoPrenez, Parto, ServicioReproductivo
from app.modelos.sanidad import (
    Bano,
    BanoAnimal,
    CatalogoProductoBano,
    CatalogoVacuna,
    Vacunacion,
    VacunacionAnimal,
)
from app.modelos.territorio import Grupo, Potrero, PotreroMovimiento

__all__ = [
    "Alerta",
    "Animal",
    "Bano",
    "BanoAnimal",
    "CatalogoProductoBano",
    "CatalogoVacuna",
    "Celo",
    "DiagnosticoPrenez",
    "Dispositivo",
    "Finca",
    "Gasto",
    "Grupo",
    "Parto",
    "Pesaje",
    "Potrero",
    "PotreroMovimiento",
    "ServicioReproductivo",
    "SyncQueue",
    "Usuario",
    "Vacunacion",
    "VacunacionAnimal",
]
