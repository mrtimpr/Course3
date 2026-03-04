from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

import requests


@dataclass(frozen=True)
class Employer:
    """Employer entity (minimal fields for DB)."""

    hh_id: int
    name: str
    alternate_url: str | None
    open_vacancies: int | None


@dataclass(frozen=True)
class Vacancy:
    """Vacancy entity (minimal fields for DB)."""

    hh_id: int
    employer_hh_id: int
    name: str
    alternate_url: str | None
    salary_from: int | None
    salary_to: int | None
    currency: str | None
    gross: bool | None
    published_at: str | None


class HHApi:
    """
    HeadHunter public API client.

    Note: HH API requires User-Agent / HH-User-Agent header. :contentReference[oaicite:2]{index=2}
    Base URL: https://api.hh.ru/ :contentReference[oaicite:3]{index=3}
    """

    BASE_URL = "https://api.hh.ru"

    def __init__(self, user_agent: str, timeout: float = 30.0) -> None:
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": user_agent,
                # Duplicate header sometimes helps when some clients can't set User-Agent
                "HH-User-Agent": user_agent,
            }
        )

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.BASE_URL}{path}"
        resp = self._session.get(url, params=params, timeout=self._timeout)

        if resp.status_code >= 400:
            # покажет {"errors":[{"type":"bad_user_agent","value":"..."}]}
            raise requests.HTTPError(
                f"{resp.status_code} {resp.reason} for {resp.url}\nResponse: {resp.text}",
                response=resp,
            )

        return cast(dict[str, Any], resp.json())

    def get_employer(self, employer_id: int) -> Employer:
        """Fetch employer info by employer_id."""
        data = self._get(f"/employers/{employer_id}")
        return Employer(
            hh_id=int(data["id"]),
            name=data.get("name", ""),
            alternate_url=data.get("alternate_url"),
            open_vacancies=data.get("open_vacancies"),
        )

    def get_vacancies_by_employer(
        self,
        employer_id: int,
        per_page: int = 100,
        max_pages: int | None = None,
    ) -> list[Vacancy]:
        """
        Fetch vacancies for one employer via vacancy search with pagination.

        We store only fields needed for the project: title, salary, link, company id.
        """
        result: list[Vacancy] = []
        page = 0

        while True:
            if max_pages is not None and page >= max_pages:
                break

            data = self._get(
                "/vacancies",
                params={
                    "employer_id": employer_id,
                    "page": page,
                    "per_page": per_page,
                },
            )

            items = data.get("items", [])
            for it in items:
                salary = it.get("salary")
                result.append(
                    Vacancy(
                        hh_id=int(it["id"]),
                        employer_hh_id=int(it["employer"]["id"]),
                        name=it.get("name", ""),
                        alternate_url=it.get("alternate_url"),
                        salary_from=(salary.get("from") if salary else None),
                        salary_to=(salary.get("to") if salary else None),
                        currency=(salary.get("currency") if salary else None),
                        gross=(salary.get("gross") if salary else None),
                        published_at=it.get("published_at"),
                    )
                )

            pages_total = data.get("pages", 0)
            page += 1
            if page >= pages_total:
                break

        return result
