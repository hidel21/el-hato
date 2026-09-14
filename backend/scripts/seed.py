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

from app.modelos import (  # noqa: E402
    Animal,
    Bano,
    BanoAnimal,
    CatalogoProductoBano,
    CatalogoVacuna,
    Finca,
    Grupo,
    Pesaje,
    Potrero,
    Usuario,
    Vacunacion,
    VacunacionAnimal,
)
from app.modelos.enumeraciones import (  # noqa: E402
    EstadoAnimal,
    EtapaGrupo,
    PropositoGrupo,
    RolUsuario,
    Sexo,
    TipoPasto,
)
from app.nucleo.base_datos import Base, FabricaSesion  # noqa: E402
from app.nucleo.seguridad import hashear_clave  # noqa: E402
from app.servicios import inventario  # noqa: E402

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
    """Borra todo lo de una finca, en orden seguro.

    No enumera las tablas a mano: recorre las que llevan finca_id en el orden
    inverso al de dependencias. Asi cada modulo nuevo queda cubierto sin volver
    a tocar este script, que es justo lo que fallo cuando aparecieron los
    movimientos entre potreros.
    """
    # Las autorreferencias van primero: un animal apunta a su madre y su padre.
    sesion.execute(
        sa.update(Animal).where(Animal.finca_id == finca_id).values(madre_id=None, padre_id=None)
    )

    for tabla in reversed(Base.metadata.sorted_tables):
        if tabla.name != "fincas" and "finca_id" in tabla.c:
            sesion.execute(sa.delete(tabla).where(tabla.c.finca_id == finca_id))

    sesion.execute(sa.delete(Finca).where(Finca.id == finca_id))
    sesion.flush()


# Cuanto gana al dia cada etapa, mas o menos. Un ternero gana rapido, un toro
# adulto ya casi no se mueve de peso.
GANANCIA_POR_ETAPA = {
    "ternero": Decimal("0.62"),
    "levante": Decimal("0.74"),
    "vientre": Decimal("0.22"),
    "toro": Decimal("0.06"),
}


def etapa_de(arete: str, grupo: str | None) -> str:
    if arete.startswith("T-"):
        return "toro"
    if grupo == "Terneras 26":
        return "ternero"
    if grupo == "Levante Norte":
        return "levante"
    return "vientre"


def sembrar_pesajes(sesion, finca_id, animales_creados: dict, usuarios_por_rol: dict) -> None:
    """Cinco pesajes por animal, hacia atras desde su peso actual.

    Sin historico no hay grafica ni ganancia diaria, y la ficha de un animal se
    ve muerta. Los pesos se reconstruyen restando la ganancia de su etapa, asi
    que las cifras cuadran con lo que muestra la ficha.
    """
    capataz = usuarios_por_rol[RolUsuario.capataz]
    fechas = [HOY - timedelta(days=dias) for dias in (182, 140, 96, 51, 3)]

    for arete, _n, _s, _r, _nac, _e, grupo, _p, peso_texto, *_resto in ANIMALES:
        animal = animales_creados[arete]
        ganancia = GANANCIA_POR_ETAPA[etapa_de(arete, grupo)]
        peso_final = Decimal(peso_texto)

        anterior = None
        for indice, fecha in enumerate(fechas):
            dias_atras = (fechas[-1] - fecha).days
            peso = (peso_final - ganancia * dias_atras).quantize(Decimal("0.1"))
            if peso <= 0:
                continue

            registro = Pesaje(
                finca_id=finca_id,
                animal_id=animal.id,
                fecha_pesaje=fecha,
                peso_kg=peso,
                metodo="bascula" if indice % 2 == 0 else "cinta",
                responsable_id=capataz.id,
            )
            if anterior is not None:
                dias = (fecha - anterior[0]).days
                registro.ganancia_diaria_kg = round((peso - anterior[1]) / Decimal(dias), 3)
            sesion.add(registro)
            anterior = (fecha, peso)

        # El ultimo pesaje manda sobre el peso de la ficha.
        if anterior is not None:
            animal.peso_actual_kg = anterior[1]


# nombre, enfermedad, laboratorio, dias de refuerzo, dias de carencia, obligatoria
VACUNAS = [
    ("Aftosa", "Fiebre aftosa", "Vecol", 180, 0, True),
    ("Carbón sintomático", "Carbón sintomático", "Zoetis", 365, 0, True),
    ("Brucelosis", "Brucelosis bovina", "Vecol", None, 0, True),
    ("Triple bovina", "Rinotraqueítis, diarrea viral y parainfluenza", "MSD", 365, 0, False),
]

# nombre, principio activo, tipo, carencia carne, carencia leche, reaplicacion
PRODUCTOS_BANO = [
    ("Garrapaticida Amitraz", "Amitraz 12,5%", "garrapaticida", 21, 3, 30),
    ("Mosquicida Cipermetrina", "Cipermetrina 15%", "mosquicida", 14, 2, 45),
]


def sembrar_sanidad(sesion, finca_id, grupos: dict, animales_creados: dict, usuarios: dict) -> None:
    """Catalogos y unas cuantas aplicaciones, con su membresia congelada.

    Sin esto la pantalla de sanidad nace vacia y no se entiende para que sirve.
    """
    veterinario = usuarios[RolUsuario.veterinario]

    catalogo_vacunas: dict[str, CatalogoVacuna] = {}
    for nombre, enfermedad, laboratorio, refuerzo, carencia, obligatoria in VACUNAS:
        vacuna = CatalogoVacuna(
            finca_id=finca_id,
            nombre=nombre,
            enfermedad=enfermedad,
            laboratorio=laboratorio,
            via_aplicacion="subcutánea",
            dosis_ml=Decimal("5.00"),
            dias_refuerzo=refuerzo,
            dias_carencia=carencia,
            obligatoria=obligatoria,
        )
        sesion.add(vacuna)
        catalogo_vacunas[nombre] = vacuna

    catalogo_banos: dict[str, CatalogoProductoBano] = {}
    for nombre, activo, tipo, carne, leche, reaplicacion in PRODUCTOS_BANO:
        producto = CatalogoProductoBano(
            finca_id=finca_id,
            nombre=nombre,
            principio_activo=activo,
            laboratorio="Agrovet",
            tipo=tipo,
            dosis_por_litro_ml=Decimal("2.00"),
            dias_carencia_carne=carne,
            dias_carencia_leche=leche,
            dias_reaplicacion=reaplicacion,
        )
        sesion.add(producto)
        catalogo_banos[nombre] = producto
    sesion.flush()

    def animales_de(grupo_nombre: str) -> list:
        objetivo = grupos[grupo_nombre].id
        return [a for a in animales_creados.values() if a.grupo_id == objetivo]

    # Aftosa al hato completo hace cuatro meses: el refuerzo ya esta encima.
    aplicaciones = [
        ("Aftosa", None, HOY - timedelta(days=124)),
        ("Carbón sintomático", "Levante Norte", HOY - timedelta(days=61)),
        ("Triple bovina", "Vientres A", HOY - timedelta(days=38)),
    ]
    for nombre_vacuna, grupo_nombre, fecha in aplicaciones:
        vacuna = catalogo_vacunas[nombre_vacuna]
        objetivo = animales_de(grupo_nombre) if grupo_nombre else list(animales_creados.values())
        registro = Vacunacion(
            finca_id=finca_id,
            catalogo_vacuna_id=vacuna.id,
            grupo_id=grupos[grupo_nombre].id if grupo_nombre else None,
            fecha_aplicacion=fecha,
            proxima_dosis_fecha=(
                fecha + timedelta(days=vacuna.dias_refuerzo) if vacuna.dias_refuerzo else None
            ),
            dosis_ml=vacuna.dosis_ml,
            lote_producto=f"L-{fecha.year}{fecha.month:02d}",
            cantidad_animales=len(objetivo),
            costo_total=Decimal("1.80") * len(objetivo),
            responsable_id=veterinario.id,
        )
        sesion.add(registro)
        sesion.flush()
        sesion.add_all(
            [
                VacunacionAnimal(finca_id=finca_id, vacunacion_id=registro.id, animal_id=a.id)
                for a in objetivo
            ]
        )

    # Baño garrapaticida al levante, ya vencido; y uno reciente a los vientres.
    for nombre_producto, grupo_nombre, dias in [
        ("Garrapaticida Amitraz", "Levante Norte", 44),
        ("Garrapaticida Amitraz", "Vientres A", 12),
    ]:
        producto = catalogo_banos[nombre_producto]
        objetivo = animales_de(grupo_nombre)
        if not objetivo:
            continue
        fecha = HOY - timedelta(days=dias)
        registro = Bano(
            finca_id=finca_id,
            producto_id=producto.id,
            grupo_id=grupos[grupo_nombre].id,
            fecha_bano=fecha,
            proxima_fecha=fecha + timedelta(days=producto.dias_reaplicacion),
            metodo="aspersión",
            dosis_total_ml=Decimal("2.00") * 400,
            litros_agua=Decimal("400"),
            cantidad_animales=len(objetivo),
            costo_total=Decimal("0.90") * len(objetivo),
            responsable_id=veterinario.id,
        )
        sesion.add(registro)
        sesion.flush()
        sesion.add_all(
            [BanoAnimal(finca_id=finca_id, bano_id=registro.id, animal_id=a.id) for a in objetivo]
        )


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
        usuarios_por_rol: dict[RolUsuario, Usuario] = {}
        for nombre, correo, rol, telefono in USUARIOS:
            usuario = Usuario(
                finca_id=finca.id,
                nombre_completo=nombre,
                correo=correo,
                clave_hash=clave,
                rol=rol,
                telefono=telefono,
                activo=True,
            )
            sesion.add(usuario)
            usuarios_por_rol[rol] = usuario
        sesion.flush()

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

        sembrar_pesajes(sesion, finca.id, creados, usuarios_por_rol)
        sembrar_sanidad(sesion, finca.id, grupos, creados, usuarios_por_rol)
        sesion.commit()

        # La vista de inventario se refresca con debounce y nadie va a escribir
        # justo despues de sembrar: se refresca aqui para que la pantalla de
        # inventario tenga datos desde el primer arranque.
        inventario.refrescar_ahora()

        print(f"Finca «{finca.nombre}» lista.")
        print(f"  {len(USUARIOS)} usuarios, clave «{CLAVE_DEMO}» para los tres:")
        for _, correo, rol, _ in USUARIOS:
            print(f"    {correo:32} {rol.value}")
        print(f"  {len(POTREROS)} potreros, {len(GRUPOS)} grupos, {len(ANIMALES)} animales.")
        print(f"  {len(VACUNAS)} vacunas y {len(PRODUCTOS_BANO)} productos en catalogo.")
    except Exception:
        sesion.rollback()
        raise
    finally:
        sesion.close()


if __name__ == "__main__":
    sembrar()
