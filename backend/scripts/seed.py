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
    Celo,
    DiagnosticoPrenez,
    Finca,
    Gasto,
    Grupo,
    Parto,
    Pesaje,
    Potrero,
    ServicioReproductivo,
    Usuario,
    Vacunacion,
    VacunacionAnimal,
)
from app.modelos.enumeraciones import (  # noqa: E402
    CategoriaGasto,
    DificultadParto,
    EstadoAnimal,
    EtapaGrupo,
    MetodoCelo,
    PropositoGrupo,
    ResultadoParto,
    ResultadoPrenez,
    RolUsuario,
    Sexo,
    TipoPasto,
)
from app.nucleo.base_datos import Base, FabricaSesion  # noqa: E402
from app.nucleo.seguridad import hashear_clave  # noqa: E402
from app.servicios import inventario  # noqa: E402

NOMBRE_FINCA = "Finca La Guacamaya"
CLAVE_DEMO = "demo1234"
# La demo se siembra siempre «hoy»: las fechas relativas cuelgan de aqui. Si se
# clava una fecha, a la semana la finca demo se ve abandonada.
HOY = date.today()

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


def marca(fecha: date, hora: int = 8) -> datetime:
    """Momento de captura verosimil: el hecho se anota el dia que ocurre.

    Sin esto todo nace con la fecha de la siembra y la pantalla de «lo que
    registraste hoy» muestra medio año de historia.
    """
    return datetime(fecha.year, fecha.month, fecha.day, hora, 30, tzinfo=UTC)


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
    fechas = [HOY - timedelta(days=dias) for dias in (182, 140, 96, 51, 0)]

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
                created_at=marca(fecha, 7 + indice),
                updated_at=marca(fecha, 7 + indice),
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
            created_at=marca(fecha),
            updated_at=marca(fecha),
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
            created_at=marca(fecha),
            updated_at=marca(fecha),
        )
        sesion.add(registro)
        sesion.flush()
        sesion.add_all(
            [BanoAnimal(finca_id=finca_id, bano_id=registro.id, animal_id=a.id) for a in objetivo]
        )


def sembrar_reproduccion(sesion, finca_id, creados: dict, usuarios: dict) -> None:
    """Un ciclo completo por vientre, en distintos puntos del calendario.

    Una hembra preñada con parto encima, una vacia que hay que revisar y una
    que ya pario: son los tres casos que se ven a diario en una finca de cria.
    """
    capataz = usuarios[RolUsuario.capataz]
    veterinario = usuarios[RolUsuario.veterinario]
    toro = creados["T-0031"]
    otro_toro = creados["T-0044"]

    # arete, dias del celo, tipo, toro, dias del diagnostico, resultado, dias del parto
    CICLOS = [
        ("C-0412", 300, "inseminacion", None, 240, ResultadoPrenez.prenada, None),
        ("C-0503", 70, "monta_natural", toro, 26, ResultadoPrenez.vacia, None),
        ("C-0688", 268, "inseminacion", None, 205, ResultadoPrenez.prenada, None),
        ("C-0188", 640, "monta_natural", otro_toro, 580, ResultadoPrenez.prenada, 357),
        ("C-0729", 420, "monta_natural", toro, 360, ResultadoPrenez.prenada, 137),
    ]

    for arete, dias_celo, tipo, reproductor, dias_dx, resultado, dias_parto in CICLOS:
        madre = creados[arete]
        fecha_celo = HOY - timedelta(days=dias_celo)

        celo = Celo(
            finca_id=finca_id,
            animal_id=madre.id,
            fecha_celo=fecha_celo,
            metodo=MetodoCelo.observacion,
            intensidad="alta",
            responsable_id=capataz.id,
            created_at=marca(fecha_celo),
            updated_at=marca(fecha_celo),
        )
        sesion.add(celo)
        sesion.flush()

        fecha_servicio = fecha_celo + timedelta(days=1)
        servicio = ServicioReproductivo(
            finca_id=finca_id,
            animal_id=madre.id,
            celo_id=celo.id,
            tipo=tipo,
            fecha_servicio=fecha_servicio,
            toro_id=reproductor.id if reproductor else None,
            pajilla_codigo=None if reproductor else "PAJ-2026-114",
            inseminador_id=veterinario.id,
            fecha_estimada_parto=fecha_servicio + timedelta(days=283),
            costo=Decimal("18.00") if reproductor is None else None,
            created_at=marca(fecha_servicio),
            updated_at=marca(fecha_servicio),
        )
        sesion.add(servicio)
        sesion.flush()

        diagnostico = DiagnosticoPrenez(
            finca_id=finca_id,
            animal_id=madre.id,
            servicio_id=servicio.id,
            fecha_diagnostico=HOY - timedelta(days=dias_dx),
            resultado=resultado,
            metodo="palpación",
            fecha_estimada_parto=(
                servicio.fecha_estimada_parto if resultado == ResultadoPrenez.prenada else None
            ),
            responsable_id=veterinario.id,
            created_at=marca(HOY - timedelta(days=dias_dx)),
            updated_at=marca(HOY - timedelta(days=dias_dx)),
        )
        sesion.add(diagnostico)
        sesion.flush()

        if dias_parto is None:
            continue

        cria = creados.get("C-1033") if arete == "C-0188" else None
        sesion.add(
            Parto(
                finca_id=finca_id,
                madre_id=madre.id,
                diagnostico_id=diagnostico.id,
                cria_id=cria.id if cria else None,
                fecha_parto=HOY - timedelta(days=dias_parto),
                resultado=ResultadoParto.vivo,
                dificultad=DificultadParto.normal,
                peso_nacimiento_kg=Decimal("32.0"),
                responsable_id=capataz.id,
                created_at=marca(HOY - timedelta(days=dias_parto)),
                updated_at=marca(HOY - timedelta(days=dias_parto)),
            )
        )

    # Un parto mas viejo de la misma madre, para que haya intervalo que medir.
    sesion.add(
        Parto(
            finca_id=finca_id,
            madre_id=creados["C-0188"].id,
            fecha_parto=HOY - timedelta(days=357 + 372),
            resultado=ResultadoParto.vivo,
            dificultad=DificultadParto.asistido,
            peso_nacimiento_kg=Decimal("29.5"),
            responsable_id=capataz.id,
        )
    )


GASTOS_DEMO = [
    (CategoriaGasto.veterinario, "Revisión de preñez", "18.00", 26, "C-0503"),
    (CategoriaGasto.medicamento, "Vitamina AD3E", "6.50", 40, "C-0412"),
    (CategoriaGasto.veterinario, "Evaluación andrológica", "75.00", 95, "T-0031"),
    (CategoriaGasto.medicamento, "Desparasitante", "5.00", 61, "C-1033"),
    (CategoriaGasto.alimento, "Sal mineralizada, 6 bultos", "186.00", 12, None),
    (CategoriaGasto.alimento, "Suplemento proteico", "240.00", 33, None),
    (CategoriaGasto.mano_obra, "Jornales de cerca", "320.00", 21, None),
    (CategoriaGasto.transporte, "Flete a subasta", "150.00", 8, None),
    (CategoriaGasto.insumo, "Cuerda y grapas", "48.00", 54, None),
    (CategoriaGasto.mantenimiento, "Arreglo del bebedero", "95.00", 70, None),
]


def sembrar_gastos(sesion, finca_id, creados: dict, grupos: dict, usuarios: dict) -> None:
    administrador = usuarios[RolUsuario.administrador]
    for categoria, concepto, monto, dias, arete in GASTOS_DEMO:
        sesion.add(
            Gasto(
                finca_id=finca_id,
                categoria=categoria,
                concepto=concepto,
                monto=Decimal(monto),
                fecha_gasto=HOY - timedelta(days=dias),
                animal_id=creados[arete].id if arete else None,
                grupo_id=None if arete else grupos["Levante Norte"].id,
                proveedor="Agroinsumos del Sinú",
                responsable_id=administrador.id,
                created_at=marca(HOY - timedelta(days=dias)),
                updated_at=marca(HOY - timedelta(days=dias)),
            )
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
        sembrar_reproduccion(sesion, finca.id, creados, usuarios_por_rol)
        sembrar_gastos(sesion, finca.id, creados, grupos, usuarios_por_rol)
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
        print(f"  5 ciclos reproductivos y {len(GASTOS_DEMO)} gastos.")
    except Exception:
        sesion.rollback()
        raise
    finally:
        sesion.close()


if __name__ == "__main__":
    sembrar()
