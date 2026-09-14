/**
 * Que se puede registrar en campo, y con que campos.
 *
 * Nueve acciones con la misma forma: elegir a quien, poner unos datos y
 * guardar. En vez de nueve formularios casi iguales, la forma se describe aqui
 * y `FormaRegistro` la dibuja.
 */

export const HOY = new Date().toISOString().slice(0, 10)

export const ACCIONES = {
  pesaje: {
    texto: 'Pesaje',
    ayuda: 'Calcula la ganancia sola',
    icono: 'pesaje',
    ruta: '/pesajes',
    titulo: 'Registrar pesaje',
    descripcion: 'La ganancia diaria se calcula contra el pesaje anterior.',
    campos: [
      { nombre: 'animal_id', tipo: 'animal', rotulo: 'Animal', requerido: true },
      {
        nombre: 'peso_kg',
        tipo: 'numero',
        rotulo: 'Peso (kg)',
        requerido: true,
        paso: '0.5',
        ancho: 'medio',
      },
      { nombre: 'fecha_pesaje', tipo: 'fecha', rotulo: 'Cuándo', ancho: 'medio', valor: HOY },
      {
        nombre: 'metodo',
        tipo: 'opciones',
        rotulo: 'Cómo',
        opciones: [
          ['bascula', 'Báscula'],
          ['cinta', 'Cinta'],
          ['estimado', 'A ojo'],
        ],
      },
      { nombre: 'observaciones', tipo: 'nota', rotulo: 'Notas' },
    ],
  },

  vacuna: {
    texto: 'Vacuna',
    ayuda: 'Individual o por lote',
    icono: 'vacuna',
    ruta: '/vacunaciones',
    titulo: 'Aplicar vacuna',
    descripcion: 'Si la aplicas a un lote, se guarda qué animales la recibieron.',
    campos: [
      {
        nombre: 'catalogo_vacuna_id',
        tipo: 'catalogo-vacunas',
        rotulo: 'Vacuna',
        requerido: true,
      },
      { nombre: '__destino', tipo: 'destino', rotulo: 'A quién', opciones: ['animal', 'lote'] },
      { nombre: 'fecha_aplicacion', tipo: 'fecha', rotulo: 'Cuándo', ancho: 'medio', valor: HOY },
      { nombre: 'dosis_ml', tipo: 'numero', rotulo: 'Dosis (ml)', paso: '0.5', ancho: 'medio' },
      { nombre: 'lote_producto', tipo: 'texto', rotulo: 'Lote del frasco', ancho: 'medio' },
      {
        nombre: 'costo_total',
        tipo: 'numero',
        rotulo: 'Costo total',
        paso: '0.01',
        ancho: 'medio',
      },
      { nombre: 'observaciones', tipo: 'nota', rotulo: 'Notas' },
    ],
  },

  bano: {
    texto: 'Baño',
    ayuda: 'Marca la carencia',
    icono: 'bano',
    ruta: '/banos',
    titulo: 'Registrar baño',
    descripcion: 'Se calcula la carencia de carne y de leche, y la próxima aplicación.',
    campos: [
      { nombre: 'producto_id', tipo: 'catalogo-productos', rotulo: 'Producto', requerido: true },
      {
        nombre: '__destino',
        tipo: 'destino',
        rotulo: 'A quién',
        opciones: ['lote', 'potrero', 'animal'],
      },
      { nombre: 'fecha_bano', tipo: 'fecha', rotulo: 'Cuándo', ancho: 'medio', valor: HOY },
      {
        nombre: 'metodo',
        tipo: 'opciones',
        rotulo: 'Cómo',
        ancho: 'medio',
        opciones: [
          ['inmersión', 'Inmersión'],
          ['aspersión', 'Aspersión'],
          ['derrame', 'Derrame'],
        ],
      },
      { nombre: 'litros_agua', tipo: 'numero', rotulo: 'Litros de agua', ancho: 'medio' },
      {
        nombre: 'costo_total',
        tipo: 'numero',
        rotulo: 'Costo total',
        paso: '0.01',
        ancho: 'medio',
      },
      { nombre: 'observaciones', tipo: 'nota', rotulo: 'Notas' },
    ],
  },

  celo: {
    texto: 'Celo',
    ayuda: 'Abre el servicio después',
    icono: 'celo',
    ruta: '/reproduccion/celos',
    titulo: 'Registrar celo',
    descripcion: 'Anótalo apenas lo veas: de aquí sale el servicio.',
    campos: [
      { nombre: 'animal_id', tipo: 'hembra', rotulo: 'Vaca', requerido: true },
      { nombre: 'fecha_celo', tipo: 'fecha', rotulo: 'Cuándo', ancho: 'medio', valor: HOY },
      {
        nombre: 'intensidad',
        tipo: 'opciones',
        rotulo: 'Intensidad',
        ancho: 'medio',
        opciones: [
          ['baja', 'Baja'],
          ['media', 'Media'],
          ['alta', 'Alta'],
        ],
      },
      {
        nombre: 'metodo',
        tipo: 'opciones',
        rotulo: 'Cómo lo viste',
        valor: 'observacion',
        opciones: [
          ['observacion', 'Observación'],
          ['parche', 'Parche'],
          ['podometro', 'Podómetro'],
          ['monta_registrada', 'Monta registrada'],
          ['otro', 'Otro'],
        ],
      },
      { nombre: 'observaciones', tipo: 'nota', rotulo: 'Notas' },
    ],
  },

  servicio: {
    texto: 'Servicio',
    ayuda: 'Monta o inseminación',
    icono: 'servicio',
    ruta: '/reproduccion/servicios',
    titulo: 'Registrar servicio',
    descripcion: 'La fecha probable de parto se calcula sola, a 283 días.',
    campos: [
      { nombre: 'animal_id', tipo: 'hembra', rotulo: 'Vaca', requerido: true },
      {
        nombre: 'tipo',
        tipo: 'opciones',
        rotulo: 'Tipo',
        valor: 'monta_natural',
        requerido: true,
        opciones: [
          ['monta_natural', 'Monta natural'],
          ['inseminacion', 'Inseminación'],
          ['transferencia', 'Transferencia'],
        ],
      },
      { nombre: 'toro_id', tipo: 'toro', rotulo: 'Toro' },
      { nombre: 'pajilla_codigo', tipo: 'texto', rotulo: 'Pajilla', ancho: 'medio' },
      { nombre: 'fecha_servicio', tipo: 'fecha', rotulo: 'Cuándo', ancho: 'medio', valor: HOY },
      { nombre: 'costo', tipo: 'numero', rotulo: 'Costo', paso: '0.01' },
      { nombre: 'observaciones', tipo: 'nota', rotulo: 'Notas' },
    ],
  },

  diagnostico: {
    texto: 'Diagnóstico',
    ayuda: 'Palpación de preñez',
    icono: 'diagnostico',
    ruta: '/reproduccion/diagnosticos',
    titulo: 'Diagnóstico de preñez',
    descripcion: 'Se enlaza solo con el último servicio de esa vaca.',
    soloRoles: ['administrador', 'veterinario'],
    campos: [
      { nombre: 'animal_id', tipo: 'hembra', rotulo: 'Vaca', requerido: true },
      {
        nombre: 'resultado',
        tipo: 'opciones',
        rotulo: 'Resultado',
        requerido: true,
        opciones: [
          ['prenada', 'Preñada'],
          ['vacia', 'Vacía'],
          ['dudoso', 'Dudoso'],
        ],
      },
      {
        nombre: 'metodo',
        tipo: 'opciones',
        rotulo: 'Cómo',
        ancho: 'medio',
        opciones: [
          ['palpación', 'Palpación'],
          ['ecografía', 'Ecografía'],
          ['sangre', 'Sangre'],
        ],
      },
      {
        nombre: 'fecha_diagnostico',
        tipo: 'fecha',
        rotulo: 'Cuándo',
        ancho: 'medio',
        valor: HOY,
      },
      { nombre: 'dias_gestacion', tipo: 'numero', rotulo: 'Días de gestación' },
      { nombre: 'observaciones', tipo: 'nota', rotulo: 'Notas' },
    ],
  },

  nacimiento: {
    texto: 'Nacimiento',
    ayuda: 'Crea la ficha del ternero',
    icono: 'nacimiento',
    ruta: '/reproduccion/partos',
    titulo: 'Registrar nacimiento',
    descripcion: 'Con el arete de la cría se abre su ficha, con la genealogía puesta.',
    campos: [
      { nombre: 'madre_id', tipo: 'hembra', rotulo: 'Madre', requerido: true },
      { nombre: 'fecha_parto', tipo: 'fecha', rotulo: 'Cuándo', ancho: 'medio', valor: HOY },
      {
        nombre: 'resultado',
        tipo: 'opciones',
        rotulo: 'Resultado',
        ancho: 'medio',
        valor: 'vivo',
        requerido: true,
        opciones: [
          ['vivo', 'Nació vivo'],
          ['muerto', 'Nació muerto'],
          ['aborto', 'Aborto'],
          ['gemelar', 'Gemelar'],
        ],
      },
      {
        nombre: 'dificultad',
        tipo: 'opciones',
        rotulo: 'Dificultad',
        valor: 'normal',
        opciones: [
          ['normal', 'Normal'],
          ['asistido', 'Asistido'],
          ['cesarea', 'Cesárea'],
          ['distocia', 'Distocia'],
        ],
      },
      { nombre: 'cria.arete', tipo: 'texto', rotulo: 'Arete de la cría', mayusculas: true },
      {
        nombre: 'cria.sexo',
        tipo: 'opciones',
        rotulo: 'Sexo de la cría',
        ancho: 'medio',
        valor: 'hembra',
        opciones: [
          ['hembra', 'Hembra'],
          ['macho', 'Macho'],
        ],
      },
      {
        nombre: 'cria.peso_nacimiento_kg',
        tipo: 'numero',
        rotulo: 'Peso al nacer',
        paso: '0.5',
        ancho: 'medio',
      },
      { nombre: 'cria.nombre', tipo: 'texto', rotulo: 'Nombre de la cría' },
      { nombre: 'observaciones', tipo: 'nota', rotulo: 'Notas' },
    ],
  },

  gasto: {
    texto: 'Gasto',
    ayuda: 'Por animal o por lote',
    icono: 'gasto',
    ruta: '/gastos',
    titulo: 'Registrar gasto',
    descripcion: 'Si lo cargas a un animal, cuenta en su costo de crianza.',
    campos: [
      {
        nombre: 'categoria',
        tipo: 'opciones',
        rotulo: 'Categoría',
        requerido: true,
        opciones: [
          ['alimento', 'Alimento'],
          ['medicamento', 'Medicamento'],
          ['veterinario', 'Veterinario'],
          ['mano_obra', 'Mano de obra'],
          ['insumo', 'Insumo'],
          ['transporte', 'Transporte'],
          ['mantenimiento', 'Mantenimiento'],
          ['otro', 'Otro'],
        ],
      },
      { nombre: 'concepto', tipo: 'texto', rotulo: 'En qué', requerido: true },
      {
        nombre: 'monto',
        tipo: 'numero',
        rotulo: 'Cuánto',
        requerido: true,
        paso: '0.01',
        ancho: 'medio',
      },
      { nombre: 'fecha_gasto', tipo: 'fecha', rotulo: 'Cuándo', ancho: 'medio', valor: HOY },
      {
        nombre: '__destino',
        tipo: 'destino',
        rotulo: 'Cargarlo a',
        opciones: ['nada', 'animal', 'lote', 'potrero'],
      },
      { nombre: 'proveedor', tipo: 'texto', rotulo: 'Proveedor' },
      { nombre: 'observaciones', tipo: 'nota', rotulo: 'Notas' },
    ],
  },
}

/** Lo que se ofrece en la hoja del boton amarillo, en este orden. */
export const ORDEN_HOJA = [
  'pesaje',
  'vacuna',
  'celo',
  'servicio',
  'bano',
  'gasto',
  'diagnostico',
  'nacimiento',
]
