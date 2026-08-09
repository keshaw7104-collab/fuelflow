from contextlib import contextmanager
from pathlib import Path

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.config import settings


pool: ConnectionPool | None = None


def open_pool() -> None:
    global pool
    if pool is None:
        settings.validate()
        pool = ConnectionPool(conninfo=settings.database_url, min_size=1, max_size=5, open=False, kwargs={"row_factory": dict_row})
        pool.open(wait=True)


def close_pool() -> None:
    global pool
    if pool is not None:
        pool.close()
        pool = None


@contextmanager
def connection():
    if pool is None:
        open_pool()
    assert pool is not None
    with pool.connection() as conn:
        yield conn


def run_migrations() -> None:
    sql_file = Path(__file__).resolve().parents[1] / "sql" / "schema.sql"
    with connection() as conn, conn.cursor() as cursor:
        cursor.execute(sql_file.read_text(encoding="utf-8"))
        conn.commit()
