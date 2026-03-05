# HH.ru API + PostgreSQL (Компании и вакансии)

Учебный проект: получить данные о работодателях и их вакансиях через публичный API hh.ru, спроектировать таблицы в PostgreSQL, загрузить данные и реализовать класс `DBManager` для запросов к БД.

## Возможности

- Получение данных о работодателях и вакансиях через API hh.ru (`requests`)
- Автоматическое создание базы данных и таблиц в PostgreSQL (`psycopg2`)
- Загрузка в БД:
  - `companies` — выбранные работодатели (минимум 10)
  - `vacancies` — вакансии этих работодателей
- Запросы к БД через класс `DBManager`:
  - список компаний и количество вакансий
  - список всех вакансий (компания, название, зарплата, ссылка)
  - средняя зарплата
  - вакансии с зарплатой выше средней
  - поиск вакансий по ключевому слову
- Консольный интерфейс (меню) в `main.py`
- Набор unit-тестов (`pytest`), проверка типизации (`mypy`), линтер (`flake8`)

---

## Структура проекта


Course3/
data/
employers.json # список employer_id (минимум 10)
src/
init.py
api_hh.py # клиент hh.ru API
config.py # загрузка конфигурации из .env
db_init.py # создание БД и таблиц
db_loader.py # загрузка данных в БД (upsert)
db_manager.py # DBManager (SQL-запросы)
file_store.py # чтение/запись JSON
tests/
init.py
conftest.py
test_api_hh.py
test_config.py
test_db_init.py
test_db_loader.py
test_db_manager.py
test_file_store.py
.env # локальные секреты (НЕ коммитить)
.env.example # пример настроек окружения
.flake8 # настройки flake8
.gitignore
main.py # точка входа: создание БД/таблиц, загрузка, меню
requirements.txt
pyproject.toml # (если используете)
poetry.toml # (если используете)
README.md

---

## Требования

- Python 3.10+ (у вас может быть 3.14 — это ок)
- PostgreSQL 13+ (должен быть установлен и запущен)
- Доступ в интернет для запросов к hh.ru API

---

## Подготовка PostgreSQL

1. Убедитесь, что PostgreSQL запущен и порт открыт (обычно `5432`).
2. Проверьте, что вы знаете пользователя/пароль (часто `postgres`).

> Совет для Windows: если возникают проблемы с `localhost (::1)`, используйте `DB_HOST=127.0.0.1` в `.env`.

---

## Настройка окружения

### Вариант A: через `pip` и виртуальное окружение

**Windows (PowerShell):**

#### powershell
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
#### Linux/macOS:
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
#### Вариант B: через Poetry (если используете)

Если проект у вас уже настроен под Poetry:
```
poetry install
poetry shell
```
### Настройка .env

Скопируйте пример и заполните значения:
```
cp .env.example .env
```
Пример .env:
```
DB_HOST=127.0.0.1
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=hh_vacancies
DB_MAINTENANCE_DB=postgres

# Важно: hh.ru ожидает корректный User-Agent (не пустой)
HH_USER_AGENT=Course3HH/1.0 (you@example.com)

HH_PER_PAGE=100
# Можно ограничить количество страниц, чтобы не тянуть слишком много вакансий:
# HH_MAX_PAGES=2
```
### Выбор компаний (data/employers.json)

В файле data/employers.json хранится список работодателей, по которым будут собираться вакансии.

Пример:
```
{
  "employers": [
    { "hh_id": 1455, "label": "HeadHunter" },
    { "hh_id": 3529, "label": "Сбер" }
  ]
}
```
Требование проекта — минимум 10 компаний.

Как найти hh_id:

- Откройте страницу работодателя на hh.ru — в URL будет /employer/<id>

## Запуск проекта
```
python main.py
```
Что происходит при запуске:

1. Создаётся БД (если не существует)

2. Создаются таблицы companies и vacancies

3. Загружаются работодатели из data/employers.json

4. Загружаются вакансии по каждому работодателю

5. Открывается консольное меню

### Консольное меню (пример)

- 1 — Компании и количество вакансий

- 2 — Все вакансии

- 3 — Средняя зарплата

- 4 — Вакансии с зарплатой выше средней

- 5 — Поиск вакансий по ключевому слову

- 0 — Выход

## Схема БД (кратко)
companies
- id (PK)
- hh_id (UNIQUE)
- name
- alternate_url
- open_vacancies
- 
vacancies
- id (PK)
- hh_id (UNIQUE)
- company_id (FK → companies.id)
- name
- alternate_url
- salary_from, salary_to, currency, gross
- published_at

## Тесты

Установите dev-зависимости (если они отдельно):
```
pip install pytest pytest-mock
```
Запуск:
```
pytest -q
```
### Проверка стиля и типизации

#### flake8
```
flake8 .
```
#### mypy

Если ругается на отсутствующие stubs:
```
pip install types-requests types-psycopg2
```
Запуск:
```
mypy .
```

### Частые проблемы
1) 400 Bad Request от hh.ru

Обычно причина — некорректный/пустой HH_USER_AGENT.
Проверьте .env и задайте нормальное значение:
Course3HH/1.0 (you@example.com).

2) Ошибка подключения к Postgres

Проверьте, что сервер запущен и порт верный

Проверьте пароль в .env

На Windows часто помогает DB_HOST=127.0.0.1 вместо localhost

3) ON CONFLICT DO UPDATE cannot affect row a second time

Это значит, что в одной пачке вставки были дубли по vacancies.hh_id.
В проекте предусмотрена дедупликация по hh_id перед вставкой.

## Авторы и лицензия

Проект разработан в учебных целях.
Лицензия: MIT.