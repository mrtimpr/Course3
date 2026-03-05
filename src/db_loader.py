from __future__ import annotations

from typing import Iterable

import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import execute_values

from src.api_hh import Employer, Vacancy
from src.config import DbConfig


class DataLoader:
    """Insert employers and vacancies into PostgreSQL."""

    def __init__(self, db: DbConfig) -> None:
        self._db = db

    def _connect(self) -> connection:
        return psycopg2.connect(
            host=self._db.host,
            port=self._db.port,
            user=self._db.user,
            password=self._db.password,
            dbname=self._db.dbname,
        )

    def upsert_companies(self, employers: Iterable[Employer]) -> None:
        rows = [(e.hh_id, e.name, e.alternate_url, e.open_vacancies) for e in employers]

        sql = """
        INSERT INTO companies (hh_id, name, alternate_url, open_vacancies)
        VALUES %s
        ON CONFLICT (hh_id) DO UPDATE
        SET name = EXCLUDED.name,
            alternate_url = EXCLUDED.alternate_url,
            open_vacancies = EXCLUDED.open_vacancies;
        """

        conn = self._connect()
        try:
            with conn:
                with conn.cursor() as cur:
                    execute_values(cur, sql, rows, page_size=200)
        finally:
            conn.close()

    def get_company_pk_map(self) -> dict[int, int]:
        """Return mapping: employer_hh_id -> companies.id (PK)."""
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, hh_id FROM companies;")
                rows = cur.fetchall()
            return {int(hh_id): int(pk) for pk, hh_id in rows}
        finally:
            conn.close()

    def upsert_vacancies(self, vacancies: Iterable[Vacancy]) -> None:
        pk_map = self.get_company_pk_map()

        # 1) Дедупликация по hh_id (берём последнюю версию вакансии)
        unique: dict[int, Vacancy] = {}
        for v in vacancies:
            unique[int(v.hh_id)] = v

        rows = []
        for v in unique.values():
            company_id = pk_map.get(int(v.employer_hh_id))
            if company_id is None:
                continue
            rows.append(
                (
                    int(v.hh_id),
                    int(company_id),
                    v.name,
                    v.alternate_url,
                    v.salary_from,
                    v.salary_to,
                    v.currency,
                    v.gross,
                    v.published_at,
                )
            )

        if not rows:
            return

        sql = """
        INSERT INTO vacancies (
            hh_id, company_id, name, alternate_url,
            salary_from, salary_to, currency, gross, published_at
        )
        VALUES %s
        ON CONFLICT (hh_id) DO UPDATE
        SET company_id = EXCLUDED.company_id,
            name = EXCLUDED.name,
            alternate_url = EXCLUDED.alternate_url,
            salary_from = EXCLUDED.salary_from,
            salary_to = EXCLUDED.salary_to,
            currency = EXCLUDED.currency,
            gross = EXCLUDED.gross,
            published_at = EXCLUDED.published_at;
        """

        conn = self._connect()
        try:
            with conn:
                with conn.cursor() as cur:
                    execute_values(cur, sql, rows, page_size=500)
        finally:
            conn.close()
