#!/usr/bin/env python
"""Carga la finca demo «La Guacamaya» con datos verosimiles.

Se puede correr las veces que haga falta: si la finca ya existe, borra sus
datos y los vuelve a crear. Es un script de semilla, no logica de aplicacion:
aqui el borrado si es fisico.

    python scripts/seed.py
"""

import sys
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import sqlalchemy as sa

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.modelos import Animal, Finca, Grupo, Potrero, Usuario  # noqa: E402
from app.modelos.enumeraciones import (  # noqa: E402
    EstadoAnimal,
    EtapaGrupo,
    PropositoGrupo,
    RolUsuario,
    Sexo,
    TipoPasto,
)
from app.nucleo.base_datos import FabricaSesion  # noqa: E402
from app.nucleo.seguridad import hashear_clave  # noqa: E402

NOMBRE_FINCA = "Finca La Guacamaya"
CLAVE_DEMO = "demo1234"
HOY = date(2026, 9, 11)

USUARIOS = [
    ("Marta Rueda", "admin@laguacamaya.com", RolUsuario.administrador, "+57 310 555 0142"),
    ("Dr. Iván Peñaloza", "vet@laguacamaya.com", RolUsuario.veterinario, "+57 311 555 0198"),
    ("Rubén Salcedo", "capataz@laguacamaya.com", RolUsuario.capataz, "+57 312 555 0177"),
]

POTREROS = [
    ("La Ceiba", 42, TipoPasto.brachiaria, "1.6", 35, False),
    ("El Palmar", 38, TipoPasto.estrella, "1.8", 30, False),
    ("Buenavista", 35, TipoPasto.guinea, "1.5", 30, False),
    ("La Laguna", 33, TipoPasto.pasto_natural, "1.5", 30, True),
]

GRUPOS = [
    (
        "Vientres A",
        EtapaGrupo.vientre,
        PropositoGrupo.cria,
        "La Ceiba",
        "Vacas de segundo parto en adelante.",
    ),
    (
        "Levante Norte",
        EtapaGrupo.levante,
        PropositoGrupo.engorde,
        "El Palmar",
        "Machos y hembras de levante.",
    ),
    (
        "Terneras 26",
        EtapaGrupo.ternero,
        PropositoGrupo.cria,
        "El Palmar",
        "Camada del primer semestre de 2026.",
    ),
]

# arete, nombre, sexo, raza, nacimiento, estado, grupo, potrero, peso, madre, padre, obs
ANIMALES = [
    (
        "T-0031",
        "Rayo",
        Sexo.macho,
        "Brahman",
        date(2019, 6, 30),
        EstadoAnimal.activo,
        None,
        "La Ceiba",
        "812.0",
        None,
        None,
        "Reproductor principal. Evaluacion andrologica al dia.",
    ),
    (
        "T-0044",
        "Trueno",
        Sexo.macho,
        "Nelore",
        date(2020, 2, 14),
        EstadoAnimal.activo,
        None,
        "Buenavista",
        "774.5",
        None,
        None,
        "Reproductor de reemplazo.",
    ),
    (
        "C-0188",
        "Lucera",
        Sexo.hembra,
        "Brahman",
        date(2018, 3, 22),
        EstadoAnimal.activo,
        "Vientres A",
        "La Ceiba",
        "503.0",
        None,
        None,
        "Seis partos. Buena madre.",
    ),
    (
        "C-0412",
        "Estrella",
        Sexo.hembra,
        "Brahman",
        date(2021, 4, 8),
        EstadoAnimal.activo,
        "Vientres A",
        "La Ceiba",
        "472.0",
        "C-0188",
        "T-0031",
        "Marca en oreja izquierda. Tercer parto.",
    ),
    (
        "C-0503",
        "Perla",
        Sexo.hembra,
        "Gyr",
        date(2020, 11, 14),
        EstadoAnimal.activo,
        "Vientres A",
        "Buenavista",
        "494.0",
        None,
        None,
        "No repite celo desde julio. Revisar.",
    ),
    (
        "C-0688",
        "Manchada",
        Sexo.hembra,
        "Brahman",
        date(2022, 8, 21),
        EstadoAnimal.activo,
        "Vientres A",
        "Buenavista",
        "441.0",
        "C-0188",
        "T-0044",
        "Primer parto esperado.",
    ),
    (
        "C-0729",
        "Azabache",
        Sexo.hembra,
        "Gyr",
        date(2022, 1, 30),
        EstadoAnimal.activo,
        "Vientres A",
        "La Ceiba",
        "458.5",
        "C-0188",
        "T-0031",
        "Temperamento nervioso en la manga.",
    ),
    (
        "C-0871",
        "Nube",
        Sexo.hembra,
        "Gyr x Holstein",
        date(2023, 9, 2),
        EstadoAnimal.en_engorde,
        "Levante Norte",
        "El Palmar",
        "418.0",
        "C-0503",
        "T-0044",
        "Buena conversion. Candidata a vientre.",
    ),
    (
        "C-0925",
        "Lucero",
        Sexo.macho,
        "Nelore",
        date(2024, 3, 11),
        EstadoAnimal.en_engorde,
        "Levante Norte",
        "El Palmar",
        "386.0",
        "C-0503",
        "T-0031",
        "Salida prevista a los 460 kg.",
    ),
    (
        "C-0944",
        "Carbón",
        Sexo.macho,
        "Brahman",
        date(2024, 5, 19),
        EstadoAnimal.en_engorde,
        "Levante Norte",
        "El Palmar",
        "352.0",
        "C-0412",
        "T-0044",
        "Ganancia pareja desde el destete.",
    ),
    (
        "C-0961",
        "Tormenta",
        Sexo.hembra,
        "Brahman",
        date(2024, 7, 4),
        EstadoAnimal.en_engorde,
        "Levante Norte",
        "El Palmar",
        "338.0",
        "C-0729",
        "T-0044",
        None,
    ),
    (
        "C-1002",
        "Melao",
        Sexo.macho,
        "Gyr x Holstein",
        date(2025, 10, 27),
        EstadoAnimal.activo,
        "Levante Norte",
        "El Palmar",
        "214.0",
        "C-0688",
        "T-0031",
        "Destetado en agosto.",
    ),
    (
        "C-1033",
        "Canela",
        Sexo.hembra,
        "Brahman",
        date(2026, 2, 19),
        EstadoAnimal.activo,
        "Terneras 26",
        "El Palmar",
        "96.0",
        "C-0412",
        "T-0031",
        "Nacida sin asistencia.",
    ),
    (
        "C-1041",
        "Lluvia",
        Sexo.hembra,
        "Gyr",
        date(2026, 3, 6),
        EstadoAnimal.activo,
        "Terneras 26",
        "El Palmar",
        "88.5",
        "C-0503",
        "T-0031",
        None,
    ),
    (
        "C-1058",
        "Trigo",
        Sexo.macho,
        "Brahman",
        date(2026, 4, 22),
        EstadoAnimal.activo,
        "Terneras 26",
        "El Palmar",
        "74.0",
        "C-0729",
        "T-0044",
        "Mellizo. El hermano no sobrevivio.",
    ),
]


def limpiar_finca(sesion, finca_id: uuid.UUID) -> None:
    """Borra en orden inverso a las dependencias."""
    sesion.execute(
        sa.update(Animal).where(Animal.finca_id == finca_id).values(madre_id=None, padre_id=None)
    )
    for modelo in (Animal, Grupo, Potrero, Usuario):
        sesion.execute(sa.delete(modelo).where(modelo.finca_id == finca_id))
    sesion.execute(sa.delete(Finca).where(Finca.id == finca_id))
    sesion.flush()


def sembrar() -> None:
    sesion = FabricaSesion()
    try:
        existente = sesion.execute(
            sa.select(Finca).where(Finca.nombre == NOMBRE_FINCA)
        ).scalar_one_or_none()
        if existente is not None:
            print(f"La finca «{NOMBRE_FINCA}» ya existia: se recrea desde cero.")
            limpiar_finca(sesion, existente.id)

        finca = Finca(
            nombre=NOMBRE_FINCA,
            codigo="LGY-001",
            municipio="Montería",
            departamento="Córdoba",
            pais="Colombia",
            hectareas=Decimal("148.00"),
        )
        sesion.add(finca)
        sesion.flush()

        clave = hashear_clave(CLAVE_DEMO)
        for nombre, correo, rol, telefono in USUARIOS:
            sesion.add(
                Usuario(
                    finca_id=finca.id,
                    nombre_completo=nombre,
                    correo=correo,
                    clave_hash=clave,
                    rol=rol,
                    telefono=telefono,
                    activo=True,
                )
            )

        potreros: dict[str, Potrero] = {}
        for nombre, hectareas, pasto, capacidad, descanso, en_descanso in POTREROS:
            potrero = Potrero(
                finca_id=finca.id,
                nombre=nombre,
                hectareas=Decimal(str(hectareas)),
                tipo_pasto=pasto,
                capacidad_ugm_ha=Decimal(capacidad),
                dias_descanso_recomendado=descanso,
                en_descanso=en_descanso,
                fecha_ultimo_ingreso=None if en_descanso else HOY - timedelta(days=12),
            )
            sesion.add(potrero)
            potreros[nombre] = potrero
        sesion.flush()

        grupos: dict[str, Grupo] = {}
        for nombre, etapa, proposito, potrero_nombre, descripcion in GRUPOS:
            grupo = Grupo(
                finca_id=finca.id,
                nombre=nombre,
                etapa=etapa,
                proposito=proposito,
                potrero_id=potreros[potrero_nombre].id,
                descripcion=descripcion,
            )
            sesion.add(grupo)
            grupos[nombre] = grupo
        sesion.flush()

        # Las fichas se separan en el tiempo para que el listado por cursor
        # muestre primero la ultima dada de alta, como en la finca real.
        alta = datetime.now(UTC) - timedelta(hours=len(ANIMALES))
        creados: dict[str, Animal] = {}
        # Dos pasadas: primero las fichas, despues la genealogia, porque una
        # cria puede aparecer antes que su madre en la lista.
        for (
            arete,
            nombre,
            sexo,
            raza,
            nacimiento,
            estado,
            grupo,
            potrero,
            peso,
            _,
            _,
            obs,
        ) in ANIMALES:
            animal = Animal(
                finca_id=finca.id,
                arete=arete,
                nombre=nombre,
                sexo=sexo,
                raza=raza,
                fecha_nacimiento=nacimiento,
                estado=estado,
                grupo_id=grupos[grupo].id if grupo else None,
                potrero_id=potreros[potrero].id,
                peso_actual_kg=Decimal(peso),
                fecha_ingreso=nacimiento,
                origen="nacimiento",
                observaciones=obs,
                created_at=alta,
                updated_at=alta,
            )
            alta += timedelta(hours=1)
            sesion.add(animal)
            creados[arete] = animal
        sesion.flush()

        for arete, *_, madre, padre, _obs in ANIMALES:
            if madre:
                creados[arete].madre_id = creados[madre].id
            if padre:
                creados[arete].padre_id = creados[padre].id

        sesion.commit()

        print(f"Finca «{finca.nombre}» lista.")
        print(f"  {len(USUARIOS)} usuarios, clave «{CLAVE_DEMO}» para los tres:")
        for _, correo, rol, _ in USUARIOS:
            print(f"    {correo:32} {rol.value}")
        print(f"  {len(POTREROS)} potreros, {len(GRUPOS)} grupos, {len(ANIMALES)} animales.")
    except Exception:
        sesion.rollback()
        raise
    finally:
        sesion.close()


if __name__ == "__main__":
    sembrar()
