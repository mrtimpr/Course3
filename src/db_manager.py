from __future__ import annotations

from dataclasses import dataclass

import psycopg2
from psycopg2.extensions import connection

from src.config import DbConfig


@dataclass(frozen=True)
class VacancyRow:
    company_name: str
    vacancy_name: str
    salary_from: int | None
    salary_to: int | None
    currency: str | None
    url: str | None


class DBManager:
    """Work with vacancies database using psycopg2."""

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

    def get_companies_and_vacancies_count(self) -> list[tuple[str, int]]:
        """
        Get all companies and number of vacancies for each (JOIN required by criteria).
        """
        sql = """
        SELECT c.name, COUNT(v.id) AS вакансий
        FROM companies c
        LEFT JOIN vacancies v ON v.company_id = c.id
        GROUP BY c.name
        ORDER BY вакансий DESC, c.name;
        """
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
                return [(name, int(cnt)) for name, cnt in cur.fetchall()]
        finally:
            conn.close()

    def get_all_vacancies(self) -> list[VacancyRow]:
        """
        Get all vacancies with company name, vacancy name, salary and URL (JOIN required by criteria).
        """
        sql = """
        SELECT c.name, v.name, v.salary_from, v.salary_to, v.currency, v.alternate_url
        FROM vacancies v
        JOIN companies c ON v.company_id = c.id
        ORDER BY c.name, v.name;
        """
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()
            return [
                VacancyRow(
                    company_name=r[0],
                    vacancy_name=r[1],
                    salary_from=r[2],
                    salary_to=r[3],
                    currency=r[4],
                    url=r[5],
                )
                for r in rows
            ]
        finally:
            conn.close()

    def get_avg_salary(self) -> float:
        """
        Get average salary across vacancies (AVG required by criteria).

        For vacancies with partial salary range:
        - if both from & to -> average of (from + to)/2
        - if only from -> from
        - if only to -> to
        """
        sql = """
        SELECT AVG(
            COALESCE(
                (salary_from + salary_to) / 2.0,
                salary_from::float,
                salary_to::float
            )
        )
        FROM vacancies
        WHERE salary_from IS NOT NULL OR salary_to IS NOT NULL;
        """
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
                val = cur.fetchone()[0]
                return float(val) if val is not None else 0.0
        finally:
            conn.close()

    def get_vacancies_with_higher_salary(self) -> list[VacancyRow]:
        """
        Get vacancies with salary higher than average (WHERE filter required by criteria).
        """
        sql = """
        WITH avg_sal AS (
            SELECT AVG(
                COALESCE(
                    (salary_from + salary_to) / 2.0,
                    salary_from::float,
                    salary_to::float
                )
            ) AS v
            FROM vacancies
            WHERE salary_from IS NOT NULL OR salary_to IS NOT NULL
        )
        SELECT c.name, v.name, v.salary_from, v.salary_to, v.currency, v.alternate_url
        FROM vacancies v
        JOIN companies c ON v.company_id = c.id
        CROSS JOIN avg_sal
        WHERE
            (v.salary_from IS NOT NULL OR v.salary_to IS NOT NULL)
            AND COALESCE(
                (v.salary_from + v.salary_to) / 2.0,
                v.salary_from::float,
                v.salary_to::float
            ) > avg_sal.v
        ORDER BY c.name, v.name;
        """
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()
            return [
                VacancyRow(
                    company_name=r[0],
                    vacancy_name=r[1],
                    salary_from=r[2],
                    salary_to=r[3],
                    currency=r[4],
                    url=r[5],
                )
                for r in rows
            ]
        finally:
            conn.close()

    def get_vacancies_with_keyword(self, keyword: str) -> list[VacancyRow]:
        """
        Get vacancies containing keyword in title (LIKE required by criteria).
        """
        sql = """
        SELECT c.name, v.name, v.salary_from, v.salary_to, v.currency, v.alternate_url
        FROM vacancies v
        JOIN companies c ON v.company_id = c.id
        WHERE v.name ILIKE %s
        ORDER BY c.name, v.name;
        """
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, (f"%{keyword}%",))
                rows = cur.fetchall()
            return [
                VacancyRow(
                    company_name=r[0],
                    vacancy_name=r[1],
                    salary_from=r[2],
                    salary_to=r[3],
                    currency=r[4],
                    url=r[5],
                )
                for r in rows
            ]
        finally:
            conn.close()
