"""Motor, sesion y clase base declarativa."""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.nucleo.configuracion import configuracion

motor = create_engine(configuracion.url_base_datos, pool_pre_ping=True, future=True)

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
