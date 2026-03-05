from src.config import DbConfig
from src.db_init import create_database_if_not_exists, create_tables


def test_create_database_if_not_exists_creates(pg_mocks, mocker):
    conn, cur = pg_mocks
    mocker.patch("src.db_init.psycopg2.connect", return_value=conn)

    # БД не существует
    cur.fetchone.return_value = None

    db = DbConfig(
        host="127.0.0.1",
        port=5432,
        user="u",
        password="p",
        dbname="target",
        maintenance_db="postgres",
    )
    create_database_if_not_exists(db)

    # SELECT pg_database был
    assert cur.execute.call_args_list[0][0][0].startswith("SELECT 1 FROM pg_database")
    # CREATE DATABASE был
    assert "CREATE DATABASE" in cur.execute.call_args_list[1][0][0]


def test_create_database_if_not_exists_skips_when_exists(pg_mocks, mocker):
    conn, cur = pg_mocks
    mocker.patch("src.db_init.psycopg2.connect", return_value=conn)

    # БД существует
    cur.fetchone.return_value = (1,)

    db = DbConfig(
        host="127.0.0.1",
        port=5432,
        user="u",
        password="p",
        dbname="target",
        maintenance_db="postgres",
    )
    create_database_if_not_exists(db)

    # Должен быть только SELECT, без CREATE
    executed_sql = [c[0][0] for c in cur.execute.call_args_list]
    assert any(s.startswith("SELECT 1 FROM pg_database") for s in executed_sql)
    assert not any("CREATE DATABASE" in s for s in executed_sql)


def test_create_tables_executes(pg_mocks, mocker):
    conn, cur = pg_mocks
    mocker.patch("src.db_init.psycopg2.connect", return_value=conn)

    db = DbConfig(
        host="127.0.0.1",
        port=5432,
        user="u",
        password="p",
        dbname="target",
        maintenance_db="postgres",
    )
    create_tables(db)

    executed_sql = [c[0][0] for c in cur.execute.call_args_list]
    assert any("CREATE TABLE IF NOT EXISTS companies" in s for s in executed_sql)
    assert any("CREATE TABLE IF NOT EXISTS vacancies" in s for s in executed_sql)
    assert any("REFERENCES companies" in s for s in executed_sql)
