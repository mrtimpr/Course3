from src.config import load_config


def test_load_config_defaults(monkeypatch):
    # очищаем переменные окружения
    for k in [
        "DB_HOST",
        "DB_PORT",
        "DB_USER",
        "DB_PASSWORD",
        "DB_NAME",
        "DB_MAINTENANCE_DB",
        "HH_USER_AGENT",
        "HH_PER_PAGE",
        "HH_MAX_PAGES",
    ]:
        monkeypatch.delenv(k, raising=False)

    cfg = load_config()

    assert cfg.db.host == "localhost"
    assert cfg.db.port == 5432
    assert cfg.db.user == "postgres"
    assert cfg.db.dbname == "hh_vacancies"
    assert isinstance(cfg.hh_user_agent, str) and len(cfg.hh_user_agent) > 0
    assert cfg.per_page == 100
    assert cfg.max_pages_per_company is None


def test_load_config_from_env(monkeypatch):
    monkeypatch.setenv("DB_HOST", "127.0.0.1")
    monkeypatch.setenv("DB_PORT", "5544")
    monkeypatch.setenv("DB_USER", "u1")
    monkeypatch.setenv("DB_PASSWORD", "p1")
    monkeypatch.setenv("DB_NAME", "db1")
    monkeypatch.setenv("DB_MAINTENANCE_DB", "postgres")
    monkeypatch.setenv("HH_USER_AGENT", "Course3HH/1.0 (test@example.com)")
    monkeypatch.setenv("HH_PER_PAGE", "50")
    monkeypatch.setenv("HH_MAX_PAGES", "2")

    cfg = load_config()

    assert cfg.db.host == "127.0.0.1"
    assert cfg.db.port == 5544
    assert cfg.db.user == "u1"
    assert cfg.db.password == "p1"
    assert cfg.db.dbname == "db1"
    assert cfg.hh_user_agent.startswith("Course3HH/1.0")
    assert cfg.per_page == 50
    assert cfg.max_pages_per_company == 2
