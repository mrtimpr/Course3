from __future__ import annotations

import psycopg2
from psycopg2.extensions import connection

from src.config import DbConfig


def _connect(db: DbConfig, dbname: str) -> connection:
    return psycopg2.connect(
        host=db.host,
        port=db.port,
        user=db.user,
        password=db.password,
        dbname=dbname,
    )


def create_database_if_not_exists(db: DbConfig) -> None:
    """Create target database (DB_NAME) if it doesn't exist."""
    conn = _connect(db, db.maintenance_db)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (db.dbname,))
            exists = cur.fetchone() is not None
            if not exists:
                cur.execute(f'CREATE DATABASE "{db.dbname}";')
    finally:
        conn.close()


def create_tables(db: DbConfig) -> None:
    """Create tables companies and vacancies with FK."""
    conn = _connect(db, db.dbname)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS companies (
                        id SERIAL PRIMARY KEY,
                        hh_id BIGINT UNIQUE NOT NULL,
                        name TEXT NOT NULL,
                        alternate_url TEXT,
                        open_vacancies INTEGER
                    );
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS vacancies (
                        id SERIAL PRIMARY KEY,
                        hh_id BIGINT UNIQUE NOT NULL,
                        company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
                        name TEXT NOT NULL,
                        alternate_url TEXT,
                        salary_from INTEGER,
                        salary_to INTEGER,
                        currency TEXT,
                        gross BOOLEAN,
                        published_at TIMESTAMPTZ
                    );
                    """
                )
    finally:
        conn.close()
