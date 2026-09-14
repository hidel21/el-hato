import { useEffect, useMemo, useState } from 'react'

import { useAnimalesParaSelector } from '../api/animales'
import { useCatalogoProductos, useCatalogoVacunas, useRegistrar } from '../api/modulos'
import { useLotes, usePotreros } from '../api/territorio'
import Hoja from '../armazon/Hoja'
import Boton from '../disenio/Boton'
import { AvisoError, CLASE_CAMPO, Campo, Desplegable } from '../paginas/campos'
import { ACCIONES } from './definiciones'

const ROTULO_DESTINO = {
  animal: 'Un animal',
  lote: 'Un lote',
  potrero: 'Un potrero',
  nada: 'La finca',
}

const CAMPO_DESTINO = {
  animal: 'animal_id',
  lote: 'grupo_id',
  potrero: 'potrero_id',
  nada: null,
}

/** Mete un valor en un objeto anidado: «cria.arete» -> {cria:{arete}}. */
function asignar(destino, ruta, valor) {
  const partes = ruta.split('.')
  let actual = destino
  for (const parte of partes.slice(0, -1)) {
    actual[parte] = actual[parte] ?? {}
    actual = actual[parte]
  }
  actual[partes.at(-1)] = valor
}

function valoresIniciales(accion) {
  const valores = {}
  for (const campo of accion.campos) {
    if (campo.tipo === 'destino') {
      valores.__destino = campo.opciones[0]
      continue
    }
    valores[campo.nombre] = campo.valor ?? ''
  }
  return valores
}

/**
 * Formulario de registro en campo, dibujado desde `definiciones.js`.
 *
 * Nueve acciones comparten esta pantalla porque comparten la forma: elegir a
 * quien, poner unos datos y guardar. Un formulario por accion serian nueve
 * archivos casi identicos y nueve sitios donde arreglar el mismo detalle.
 */
export default function FormaRegistro({ accion, abierta, alCerrar, alGuardar, contexto = {} }) {
  const definicion = ACCIONES[accion] ?? null
  const registrar = useRegistrar(definicion?.ruta ?? '/animales')

  const [valores, setValores] = useState(() => (definicion ? valoresIniciales(definicion) : {}))
  const [errorApi, setErrorApi] = useState(null)

  const animales = useAnimalesParaSelector()
  const hembras = useAnimalesParaSelector('hembra')
  const machos = useAnimalesParaSelector('macho')
  const lotes = useLotes()
  const potreros = usePotreros()
  const vacunas = useCatalogoVacunas()
  const productos = useCatalogoProductos()

  useEffect(() => {
    if (abierta && definicion) {
      setValores({ ...valoresIniciales(definicion), ...contexto })
      setErrorApi(null)
    }
    // El contexto llega ya resuelto desde quien abre la hoja.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [abierta, accion])

  const opcionesDe = useMemo(
    () => ({
      animal: (animales.data ?? []).map((a) => ({
        valor: a.id,
        texto: `${a.arete}${a.nombre ? ` · ${a.nombre}` : ''}`,
      })),
      hembra: (hembras.data ?? []).map((a) => ({
        valor: a.id,
        texto: `${a.arete}${a.nombre ? ` · ${a.nombre}` : ''}`,
      })),
      toro: (machos.data ?? []).map((a) => ({
        valor: a.id,
        texto: `${a.arete}${a.nombre ? ` · ${a.nombre}` : ''}`,
      })),
      lote: (lotes.data ?? []).map((l) => ({
        valor: l.id,
        texto: `${l.nombre} · ${l.cantidad_animales} animales`,
      })),
      potrero: (potreros.data ?? []).map((p) => ({
        valor: p.id,
        texto: `${p.nombre} · ${p.cantidad_animales} animales`,
      })),
      'catalogo-vacunas': (vacunas.data ?? []).map((v) => ({ valor: v.id, texto: v.nombre })),
      'catalogo-productos': (productos.data ?? []).map((p) => ({ valor: p.id, texto: p.nombre })),
    }),
    [
      animales.data,
      hembras.data,
      machos.data,
      lotes.data,
      potreros.data,
      vacunas.data,
      productos.data,
    ]
  )

  if (!definicion) return null

  const poner = (nombre, valor) => setValores((previos) => ({ ...previos, [nombre]: valor }))

  const cerrar = () => {
    setErrorApi(null)
    alCerrar()
  }

  const enviar = async (evento) => {
    evento.preventDefault()
    setErrorApi(null)

    const cuerpo = {}
    for (const campo of definicion.campos) {
      if (campo.tipo === 'destino') {
        const clave = CAMPO_DESTINO[valores.__destino]
        const elegido = valores[clave]
        if (clave && !elegido) {
          return setErrorApi(`Elige ${ROTULO_DESTINO[valores.__destino].toLowerCase()}.`)
        }
        if (clave) cuerpo[clave] = elegido
        continue
      }

      const valor = valores[campo.nombre]
      if (campo.requerido && !valor) return setErrorApi(`Falta ${campo.rotulo.toLowerCase()}.`)
      if (valor === '' || valor === undefined || valor === null) continue
      asignar(cuerpo, campo.nombre, campo.mayusculas ? String(valor).toUpperCase() : valor)
    }

    // La cria solo se manda si le pusieron arete.
    if (cuerpo.cria && !cuerpo.cria.arete) delete cuerpo.cria

    try {
      const creado = await registrar.mutateAsync(cuerpo)
      cerrar()
      alGuardar?.(definicion, creado)
    } catch (error) {
      setErrorApi(error.message)
    }
  }

  const dibujar = (campo) => {
    const valor = valores[campo.nombre] ?? ''
    const comun = { value: valor, onChange: (e) => poner(campo.nombre, e.target.value) }

    if (campo.tipo === 'destino') {
      const destino = valores.__destino
      const clave = CAMPO_DESTINO[destino]
      return (
        <div key={campo.nombre} className="flex flex-col gap-2">
          <Campo rotulo={campo.rotulo} grupo>
            <div className="flex flex-wrap gap-2">
              {campo.opciones.map((opcion) => (
                <button
                  key={opcion}
                  type="button"
                  aria-pressed={destino === opcion}
                  onClick={() => poner('__destino', opcion)}
                  className={`min-h-[40px] flex-1 rounded-caja border px-3 text-[13.5px] peso-medio ${
                    destino === opcion
                      ? 'border-pasto bg-pasto text-white'
                      : 'border-borde bg-superficie text-tinta'
                  }`}
                >
                  {ROTULO_DESTINO[opcion]}
                </button>
              ))}
            </div>
          </Campo>
          {clave ? (
            <Desplegable
              vacio={`Elige ${ROTULO_DESTINO[destino].toLowerCase()}`}
              opciones={opcionesDe[destino]}
              value={valores[clave] ?? ''}
              onChange={(e) => poner(clave, e.target.value)}
            />
          ) : null}
        </div>
      )
    }

    const cuerpo = () => {
      switch (campo.tipo) {
        case 'animal':
        case 'hembra':
        case 'toro':
        case 'lote':
        case 'potrero':
        case 'catalogo-vacunas':
        case 'catalogo-productos':
          return (
            <Desplegable
              vacio={`Elige ${campo.rotulo.toLowerCase()}`}
              opciones={opcionesDe[campo.tipo]}
              {...comun}
            />
          )
        case 'opciones':
          return (
            <Desplegable
              vacio="Sin registrar"
              opciones={campo.opciones.map(([v, t]) => ({ valor: v, texto: t }))}
              {...comun}
            />
          )
        case 'fecha':
          return <input type="date" max={campo.valor} className={CLASE_CAMPO} {...comun} />
        case 'numero':
          return (
            <input
              type="number"
              step={campo.paso ?? '1'}
              inputMode="decimal"
              className={CLASE_CAMPO}
              {...comun}
            />
          )
        case 'nota':
          return (
            <textarea rows={2} className={`${CLASE_CAMPO} py-2.5 leading-relaxed`} {...comun} />
          )
        default:
          return (
            <input
              type="text"
              autoComplete="off"
              className={`${CLASE_CAMPO} ${campo.mayusculas ? 'uppercase' : ''}`}
              {...comun}
            />
          )
      }
    }

    return (
      <Campo key={campo.nombre} rotulo={campo.rotulo} ayuda={campo.ayuda}>
        {cuerpo()}
      </Campo>
    )
  }

  // Los campos marcados como «medio» se emparejan de dos en dos.
  const filas = []
  for (const campo of definicion.campos) {
    const ultima = filas.at(-1)
    if (campo.ancho === 'medio' && ultima?.length === 1 && ultima[0].ancho === 'medio') {
      ultima.push(campo)
    } else {
      filas.push([campo])
    }
  }

  return (
    <Hoja
      abierta={abierta}
      alCerrar={cerrar}
      titulo={definicion.titulo}
      descripcion={definicion.descripcion}
    >
      <form onSubmit={enviar} noValidate className="flex flex-col gap-3.5">
        {filas.map((fila, indice) =>
          fila.length === 2 ? (
            <div key={indice} className="grid grid-cols-2 gap-3">
              {fila.map(dibujar)}
            </div>
          ) : (
            dibujar(fila[0])
          )
        )}

        <AvisoError mensaje={errorApi} />

        <div className="mt-1 flex flex-col gap-2 rail:flex-row-reverse">
          <Boton type="submit" variante="amarillo" bloque disabled={registrar.isPending}>
            {registrar.isPending ? 'Guardando…' : 'Guardar'}
          </Boton>
          <Boton variante="suave" bloque onClick={cerrar}>
            Cancelar
          </Boton>
        </div>
      </form>
    </Hoja>
  )
}
