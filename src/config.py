from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class DbConfig:
    """PostgreSQL connection settings."""

    host: str
    port: int
    user: str
    password: str
    dbname: str
    maintenance_db: str = "postgres"


@dataclass(frozen=True)
class AppConfig:
    """Application settings."""

    db: DbConfig
    hh_user_agent: str
    per_page: int = 100
    max_pages_per_company: int | None = None  # None -> all pages


def load_config() -> AppConfig:
    """Load configuration from environment variables (.env supported)."""
    load_dotenv()

    db = DbConfig(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        dbname=os.getenv("DB_NAME", "hh_vacancies"),
        maintenance_db=os.getenv("DB_MAINTENANCE_DB", "postgres"),
    )

    hh_user_agent = os.getenv("HH_USER_AGENT", "hh-postgres-project/1.0 (mailto:example@example.com)")
    per_page = int(os.getenv("HH_PER_PAGE", "100"))
    max_pages_raw = os.getenv("HH_MAX_PAGES", "").strip()
    max_pages = int(max_pages_raw) if max_pages_raw else None

    return AppConfig(
        db=db,
        hh_user_agent=hh_user_agent,
        per_page=per_page,
        max_pages_per_company=max_pages,
    )
