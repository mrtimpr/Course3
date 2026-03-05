from __future__ import annotations

from src.api_hh import HHApi
from src.config import load_config
from src.db_init import create_database_if_not_exists, create_tables
from src.db_loader import DataLoader
from src.db_manager import DBManager
from src.file_store import read_json


def format_salary(s_from: int | None, s_to: int | None, cur: str | None) -> str:
    if s_from is None and s_to is None:
        return "не указана"
    if s_from is not None and s_to is not None:
        return f"{s_from}–{s_to} {cur or ''}".strip()
    return f"{s_from or s_to} {cur or ''}".strip()


def load_data() -> None:
    cfg = load_config()

    # 1) Create DB + tables
    create_database_if_not_exists(cfg.db)
    create_tables(cfg.db)

    # 2) Read employers list
    payload = read_json("data/employers.json")
    employer_ids = sorted({int(x["hh_id"]) for x in payload.get("employers", [])})
    if len(employer_ids) < 10:
        raise ValueError("Нужно указать минимум 10 компаний в data/employers.json")

    # 3) Fetch from HH
    api = HHApi(user_agent=cfg.hh_user_agent)
    employers = [api.get_employer(eid) for eid in employer_ids]

    all_vacancies = []
    for eid in employer_ids:
        all_vacancies.extend(
            api.get_vacancies_by_employer(
                employer_id=eid,
                per_page=cfg.per_page,
                max_pages=cfg.max_pages_per_company,
            )
        )

    # 4) Load into DB
    loader = DataLoader(cfg.db)
    loader.upsert_companies(employers)
    loader.upsert_vacancies(all_vacancies)


def run_cli() -> None:
    cfg = load_config()
    dbm = DBManager(cfg.db)

    menu = (
        "\nВыберите действие:\n"
        "1 — Компании и количество вакансий\n"
        "2 — Все вакансии\n"
        "3 — Средняя зарплата\n"
        "4 — Вакансии с зарплатой выше средней\n"
        "5 — Поиск вакансий по ключевому слову\n"
        "0 — Выход\n"
        "> "
    )

    while True:
        choice = input(menu).strip()

        if choice == "0":
            break

        if choice == "1":
            company_rows = dbm.get_companies_and_vacancies_count()
            for name, cnt in company_rows:
                print(f"{name}: {cnt}")
            continue

        if choice == "2":
            vacancy_rows = dbm.get_all_vacancies()
            for r in vacancy_rows:
                print(
                    f"[{r.company_name}] {r.vacancy_name} | "
                    f"{format_salary(r.salary_from, r.salary_to, r.currency)} | {r.url}"
                )
            continue

        if choice == "3":
            avg = dbm.get_avg_salary()
            print(f"Средняя зарплата по вакансиям: {avg:.2f}")
            continue

        if choice == "4":
            high_rows = dbm.get_vacancies_with_higher_salary()
            for r in high_rows:
                print(
                    f"[{r.company_name}] {r.vacancy_name} | "
                    f"{format_salary(r.salary_from, r.salary_to, r.currency)} | {r.url}"
                )
            continue

        if choice == "5":
            kw = input("Введите ключевое слово (например, python): ").strip()
            kw_rows = dbm.get_vacancies_with_keyword(kw)
            for r in kw_rows:
                print(
                    f"[{r.company_name}] {r.vacancy_name} | "
                    f"{format_salary(r.salary_from, r.salary_to, r.currency)} | {r.url}"
                )
            continue

        print("Неизвестный пункт меню.")


def main() -> None:
    load_data()
    run_cli()


if __name__ == "__main__":
    main()
