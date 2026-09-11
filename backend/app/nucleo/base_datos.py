"""Motor, sesion y clase base declarativa."""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.nucleo.configuracion import configuracion

motor = create_engine(
    configuracion.url_base_datos,
    pool_pre_ping=True,
    future=True,
    # Sin sentencias preparadas del lado del servidor. Con ellas, cualquier
    # cambio de esquema con la API encendida —un `make reiniciar-base`, por
    # ejemplo— deja las conexiones del pool con planes viejos y Postgres
    # responde «cached plan must not change result type» hasta reiniciar.
    # A esta escala la diferencia de rendimiento no se nota, y ademas es lo que
    # exige PgBouncer en modo transaccion, que es adonde va a ir esto.
    connect_args={"prepare_threshold": None},
)

FabricaSesion = sessionmaker(bind=motor, autocommit=False, autoflush=False, class_=Session)


class Base(DeclarativeBase):
    """Todas las tablas heredan de aqui."""


def obtener_sesion() -> Iterator[Session]:
    sesion = FabricaSesion()
    try:
        yield sesion
        sesion.commit()
    except Exception:
        sesion.rollback()
        raise
    finally:
        sesion.close()
