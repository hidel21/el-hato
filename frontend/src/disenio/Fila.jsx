/**
 * Una fila de lista. Es el ladrillo de casi toda la aplicacion: caravana a la
 * izquierda, titulo y meta en el centro, cifra a la derecha.
 *
 * Con `onClick` se vuelve un boton de 52 px de alto; sin el, un div.
 *
 * OJO: si la fila lleva algo interactivo dentro —un boton, un enlace— NO le
 * pases `onClick`. Un boton dentro de otro boton es HTML invalido y el
 * navegador se come el clic interior.
 */
const MARCAS = {
  vencido: 'bg-vencido',
  pronto: 'bg-pronto',
  ok: 'bg-ok',
  neutro: 'bg-borde',
}

export default function Fila({
  marca,
  izquierda,
  titulo,
  meta,
  derecha,
  onClick,
  activa = false,
  className = '',
}) {
  const Elemento = onClick ? 'button' : 'div'
  return (
    <Elemento
      {...(onClick ? { type: 'button', onClick } : {})}
      className={`flex w-full min-h-tap items-center gap-3 px-3.5 py-3 text-left ${
        onClick ? 'hover:bg-[#FAFBF7]' : ''
      } ${activa ? 'bg-[#F2F6F0]' : ''} ${className}`}
    >
      {marca ? <i className={`w-1 self-stretch rounded-sm ${MARCAS[marca]}`} /> : null}
      {izquierda}
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2 text-[15px] peso-medio">{titulo}</div>
        {meta ? <div className="mt-px truncate text-[13px] text-hierro">{meta}</div> : null}
      </div>
      {derecha ? <div className="flex-none text-right">{derecha}</div> : null}
    </Elemento>
  )
}
