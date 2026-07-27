# Plintron cdr_copy — поддержка .cdr расширения

**Дата:** 2026-07-27

## Краткое описание задачи

При добавлении второго провайдера Plintron `cdr_sync` отработал корректно (скачал `.cdr` файлы), но `cdr_copy` отклонял все файлы с ошибкой "not a CSV file", т.к. проверка расширения была жёстко зашита на `.csv`.

## Итоги Research

- `should_process_file()` в `cdr_copy.py:180` проверяет только `.csv` расширение
- `CDRCopyConfig` не имел параметра для настройки расширений
- Файлы Plintron имеют расширение `.cdr`

## План

1. `config.py` — добавить поле `file_extensions` с дефолтом `['csv']`
2. `cdr_copy.py` — заменить жёсткую проверку на проверку по списку из конфига
3. `task.env.example` — добавить документацию параметра

## Что реализовано

- **`cdr_copy/config.py:27`** — новое поле `file_extensions: list[str] | None` в `CDRCopyConfig`
- **`cdr_copy/config.py:36-37`** — дефолт `['csv']` в `__post_init__`
- **`cdr_copy/config.py:60-61`** — загрузка `file_extensions` из `.env` (через запятую, с очисткой точек и пробелов)
- **`cdr_copy/cdr_copy.py:178-182`** — проверка расширения через `config.file_extensions`
- **`cdr_copy/config/task.env.example:14-22`** — документация нового параметра

## Результаты Validation

- Синтаксис Python: OK

## Проблемы и откаты

Нет

## Статус

Done