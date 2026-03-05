from src.api_hh import Employer, Vacancy
from src.config import DbConfig
from src.db_loader import DataLoader


def test_upsert_companies_calls_execute_values(pg_mocks, mocker):
    conn, cur = pg_mocks
    mocker.patch("src.db_loader.psycopg2.connect", return_value=conn)

    ev = mocker.patch("src.db_loader.execute_values")

    db = DbConfig(host="127.0.0.1", port=5432, user="u", password="p", dbname="target")
    loader = DataLoader(db)

    employers = [
        Employer(hh_id=1, name="A", alternate_url="u1", open_vacancies=10),
        Employer(hh_id=2, name="B", alternate_url="u2", open_vacancies=20),
    ]
    loader.upsert_companies(employers)

    ev.assert_called_once()
    args, kwargs = ev.call_args
    assert args[0] == cur  # cursor
    rows = args[2]
    assert rows == [(1, "A", "u1", 10), (2, "B", "u2", 20)]


def test_upsert_vacancies_deduplicates_and_maps(pg_mocks, mocker):
    conn, cur = pg_mocks
    mocker.patch("src.db_loader.psycopg2.connect", return_value=conn)
    ev = mocker.patch("src.db_loader.execute_values")

    db = DbConfig(host="127.0.0.1", port=5432, user="u", password="p", dbname="target")
    loader = DataLoader(db)

    # Маппинг hh employer -> PK companies.id
    mocker.patch.object(loader, "get_company_pk_map", return_value={10: 100})

    vacs = [
        Vacancy(
            hh_id=1,
            employer_hh_id=10,
            name="V1",
            alternate_url="url1",
            salary_from=100,
            salary_to=200,
            currency="RUR",
            gross=True,
            published_at="2024-01-01T00:00:00+03:00",
        ),
        # Дубликат по hh_id=1 (должен “перезаписаться” и остаться один)
        Vacancy(
            hh_id=1,
            employer_hh_id=10,
            name="V1 NEW",
            alternate_url="url1n",
            salary_from=150,
            salary_to=250,
            currency="RUR",
            gross=False,
            published_at="2024-01-02T00:00:00+03:00",
        ),
        # Вакансия с неизвестной компанией (должна быть пропущена)
        Vacancy(
            hh_id=2,
            employer_hh_id=999,
            name="V2",
            alternate_url="url2",
            salary_from=None,
            salary_to=None,
            currency=None,
            gross=None,
            published_at=None,
        ),
    ]

    loader.upsert_vacancies(vacs)

    ev.assert_called_once()
    rows = ev.call_args[0][2]

    # Должна остаться только 1 строка (hh_id=1) и company_id=100
    assert len(rows) == 1
    assert rows[0][0] == 1  # hh_id
    assert rows[0][1] == 100  # company_id
    assert rows[0][2] == "V1 NEW"
    assert rows[0][3] == "url1n"
    assert rows[0][4] == 150
    assert rows[0][5] == 250
