from unittest.mock import MagicMock

from src.api_hh import HHApi


def _fake_response(json_data, status_code=200):
    r = MagicMock()
    r.status_code = status_code
    r.json.return_value = json_data
    r.raise_for_status.side_effect = None if status_code < 400 else Exception("HTTP error")
    return r


def test_get_employer_parsing(mocker):
    # Мокаем requests.Session так, чтобы api._session.get(...) вернул наш фейковый ответ
    session = MagicMock()
    session.get.return_value = _fake_response(
        {
            "id": "1455",
            "name": "HeadHunter",
            "alternate_url": "https://hh.ru/employer/1455",
            "open_vacancies": 123,
        }
    )
    mocker.patch("src.api_hh.requests.Session", return_value=session)

    api = HHApi(user_agent="Course3HH/1.0 (test@example.com)")
    emp = api.get_employer(1455)

    assert emp.hh_id == 1455
    assert emp.name == "HeadHunter"
    assert emp.alternate_url.endswith("/1455")
    assert emp.open_vacancies == 123

    session.get.assert_called_once()
    # проверим что URL корректный
    called_url = session.get.call_args[0][0]
    assert called_url == "https://api.hh.ru/employers/1455"


def test_get_vacancies_by_employer_pagination(mocker):
    session = MagicMock()

    # page 0 -> pages=2
    resp0 = _fake_response(
        {
            "pages": 2,
            "items": [
                {
                    "id": "1",
                    "name": "Python dev",
                    "alternate_url": "https://hh.ru/vacancy/1",
                    "published_at": "2024-01-01T00:00:00+03:00",
                    "employer": {"id": "10"},
                    "salary": {
                        "from": 100,
                        "to": 200,
                        "currency": "RUR",
                        "gross": True,
                    },
                }
            ],
        }
    )
    # page 1 -> last
    resp1 = _fake_response(
        {
            "pages": 2,
            "items": [
                {
                    "id": "2",
                    "name": "Data engineer",
                    "alternate_url": "https://hh.ru/vacancy/2",
                    "published_at": "2024-01-02T00:00:00+03:00",
                    "employer": {"id": "10"},
                    "salary": None,
                }
            ],
        }
    )

    session.get.side_effect = [resp0, resp1]
    mocker.patch("src.api_hh.requests.Session", return_value=session)

    api = HHApi(user_agent="Course3HH/1.0 (test@example.com)")
    vacs = api.get_vacancies_by_employer(employer_id=10, per_page=100)

    assert len(vacs) == 2
    assert vacs[0].hh_id == 1
    assert vacs[0].salary_from == 100
    assert vacs[0].salary_to == 200
    assert vacs[0].currency == "RUR"
    assert vacs[1].hh_id == 2
    assert vacs[1].salary_from is None
    assert vacs[1].salary_to is None

    assert session.get.call_count == 2

    # проверим параметры запросов page=0 и page=1
    params0 = session.get.call_args_list[0].kwargs["params"]
    params1 = session.get.call_args_list[1].kwargs["params"]
    assert params0["page"] == 0 and params0["employer_id"] == 10
    assert params1["page"] == 1 and params1["employer_id"] == 10
