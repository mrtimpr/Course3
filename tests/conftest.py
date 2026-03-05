from unittest.mock import MagicMock

import pytest


@pytest.fixture
def pg_mocks() -> tuple[MagicMock, MagicMock]:
    """
    Возвращает (conn, cur) — моки соединения и курсора psycopg2,
    уже настроенные под контекстные менеджеры:
      with conn:
      with conn.cursor() as cur:
    """
    conn = MagicMock(name="conn")
    cur = MagicMock(name="cursor")

    # connection as context manager
    conn.__enter__.return_value = conn
    conn.__exit__.return_value = False

    # cursor as context manager
    conn.cursor.return_value.__enter__.return_value = cur
    conn.cursor.return_value.__exit__.return_value = False

    return conn, cur
