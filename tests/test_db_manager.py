from src.config import DbConfig
from src.db_manager import DBManager, VacancyRow


def test_get_companies_and_vacancies_count(pg_mocks, mocker):
    conn, cur = pg_mocks
    mocker.patch("src.db_manager.psycopg2.connect", return_value=conn)

    cur.fetchall.return_value = [("A", 2), ("B", 0)]

    db = DbConfig(host="127.0.0.1", port=5432, user="u", password="p", dbname="target")
    m = DBManager(db)

    res = m.get_companies_and_vacancies_count()
    assert res == [("A", 2), ("B", 0)]

    sql = cur.execute.call_args[0][0]
    assert "JOIN" in sql.upper()  # критерий про JOIN


def test_get_all_vacancies(pg_mocks, mocker):
    conn, cur = pg_mocks
    mocker.patch("src.db_manager.psycopg2.connect", return_value=conn)

    cur.fetchall.return_value = [
        ("A", "V1", 100, 200, "RUR", "url1"),
        ("B", "V2", None, None, None, "url2"),
    ]

    db = DbConfig(host="127.0.0.1", port=5432, user="u", password="p", dbname="target")
    m = DBManager(db)

    res = m.get_all_vacancies()
    assert res[0] == VacancyRow("A", "V1", 100, 200, "RUR", "url1")
    assert res[1] == VacancyRow("B", "V2", None, None, None, "url2")

    sql = cur.execute.call_args[0][0]
    assert "JOIN" in sql.upper()


def test_get_avg_salary(pg_mocks, mocker):
    conn, cur = pg_mocks
    mocker.patch("src.db_manager.psycopg2.connect", return_value=conn)

    cur.fetchone.return_value = (150.0,)

    db = DbConfig(host="127.0.0.1", port=5432, user="u", password="p", dbname="target")
    m = DBManager(db)

    assert m.get_avg_salary() == 150.0
    sql = cur.execute.call_args[0][0]
    assert "AVG" in sql.upper()


def test_get_vacancies_with_higher_salary(pg_mocks, mocker):
    conn, cur = pg_mocks
    mocker.patch("src.db_manager.psycopg2.connect", return_value=conn)

    cur.fetchall.return_value = [
        ("A", "V1", 200, 300, "RUR", "url1"),
    ]

    db = DbConfig(host="127.0.0.1", port=5432, user="u", password="p", dbname="target")
    m = DBManager(db)

    res = m.get_vacancies_with_higher_salary()
    assert res == [VacancyRow("A", "V1", 200, 300, "RUR", "url1")]

    sql = cur.execute.call_args[0][0].upper()
    assert "WHERE" in sql
    assert "AVG" in sql  # критерий про среднюю и фильтрацию


def test_get_vacancies_with_keyword_uses_ilike(pg_mocks, mocker):
    conn, cur = pg_mocks
    mocker.patch("src.db_manager.psycopg2.connect", return_value=conn)

    cur.fetchall.return_value = [("A", "Python dev", None, None, None, "url")]

    db = DbConfig(host="127.0.0.1", port=5432, user="u", password="p", dbname="target")
    m = DBManager(db)

    res = m.get_vacancies_with_keyword("python")
    assert res[0].vacancy_name == "Python dev"

    sql, params = cur.execute.call_args[0][0], cur.execute.call_args[0][1]
    assert "ILIKE" in sql.upper()
    assert params == ("%python%",)
