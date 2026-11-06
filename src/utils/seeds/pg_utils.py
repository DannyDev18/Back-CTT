from sqlalchemy import text
from sqlmodel import Session


def sync_pk_sequence(session: Session, table: str, column: str = "id") -> None:
    """
    Alinea la secuencia SERIAL de PostgreSQL con el MAX(id) de la tabla.

    Los seeds insertan filas con id explícito; en PostgreSQL eso NO avanza la
    secuencia, y el siguiente INSERT sin id (p. ej. crear un usuario desde la
    API) colisionaría con un id ya usado. No hace nada en otros motores
    (los tests usan SQLite).
    """
    if session.get_bind().dialect.name != "postgresql":
        return
    session.execute(
        text(
            f"SELECT setval(pg_get_serial_sequence('{table}', '{column}'), "
            f"COALESCE((SELECT MAX({column}) FROM {table}), 1), "
            f"(SELECT COUNT(*) > 0 FROM {table}))"
        )
    )
    session.commit()
