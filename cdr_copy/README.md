# cdr_copy

Модуль для копирования CDR/LU файлов из исходной папки в целевую на основе правил конфигурации.

## Установка

Установите зависимости:

```bash
pip install -r requirements.txt
```

## Использование

### Базовое использование

```bash
# Прямой вызов Python
python3 cdr_copy/cdr_copy.py <имя_задачи>

# С dry-run режимом
python3 cdr_copy/cdr_copy.py <имя_задачи> --dry-run

# Примеры
python3 cdr_copy/cdr_copy.py telna_cdr
python3 cdr_copy/cdr_copy.py telna_cdr --dry-run
```

### Конфигурационные файлы

Конфигурационные задачи хранятся в `cdr_copy/config/<имя_задачи>.env`

Для создания новой задачи:
1. Скопируйте шаблон `cdr_copy/config/task.env.example`
2. Переименуйте в `<имя_задачи>.env`
3. Заполните параметры

#### Пример конфигурации

```ini
# Обязательные параметры
from="/source/folder"
to="/target/folder"

# Опциональные фильтры
company="ClientName"

# Флаги структуры (yes/no)
by_company=no
flat=no
by_date=no

# Удобные флаги для быстрой фильтрации (yes/no)
yesterday=no
today=no

# Диапазоны дат (формат YYYYMMDD)
from_date="20260101"
to_date="20261231"
```

## Описание параметров

### Обязательные параметры

- **from** - Исходная папка с файлами
  - Должна существовать
  - Проверяется при запуске

- **to** - Целевая папка для копирования
  - Создаётся автоматически если не существует
  - Должна быть доступна для записи

### Опциональные фильтры

- **company** - Фильтрация по названию компании
  - Ищет подстроку в названии компании
  - Пример: `company="eData"` найдёт файлы с `LIVE_eData_Online_CDR_...`

### Флаги структуры

Флаги принимают значения `yes` или `no` и могут комбинироваться:

- **by_company** - Раскладывать файлы по папкам компаний
  - Извлекает компанию из имени файла
  - Заменяет подчёркивания на пробелы
  - Пример: `LIVE_Telna_Corp_CDR_...` → `Telna Corp/`
  - Значение: `yes` или `no`

- **by_date** - Раскладывать файлы по папкам дат
  - Извлекает дату из имени файла
  - Формат папки: YYYY-MM-DD
  - Пример: `2026-04-10/`
  - Значение: `yes` или `no`

- **flat** - Плоская структура из подпапок
  - Рекурсивно сканирует исходную папку
  - Копирует все файлы в целевую папку без сохранения структуры
  - Значение: `yes` или `no`

**Примеры комбинаций:**

| Флаги | Результат |
|-------|-----------|
| Все `no` | `to/filename.csv` |
| `by_company=yes` | `to/Telna Corp/filename.csv` |
| `by_date=yes` | `to/2026-04-10/filename.csv` |
| `by_company=yes by_date=yes` | `to/Telna Corp/2026-04-10/filename.csv` |
| `flat=yes` | `to/filename.csv` (из всех подпапок) |

### Флаги фильтрации по дате

Флаги принимают значения `yes` или `no`:

- **yesterday** - Только вчерашние файлы
  - Устанавливает from_date и to_date на вчерашний день
  - Значение: `yes` или `no`

- **today** - Только сегодняшние файлы
  - Устанавливает from_date и to_date на сегодняшний день
  - Значение: `yes` или `no`

**Важно:** Нельзя использовать `yesterday=yes` и `today=yes` одновременно.

### Диапазоны дат

- **from_date** - Игнорировать файлы до этой даты (формат YYYYMMDD)
- **to_date** - Игнорировать файлы после этой даты (формат YYYYMMDD)

## Примеры использования

### Пример 1: Простое копирование

Конфигурация `config/telna_cdr.env`:

```ini
from="/home/cdr_admin/incoming/telna"
to="/home/cdr_admin/outbound/telna"
```

Запуск:

```bash
python3 cdr_copy/cdr_copy.py telna_cdr
```

### Пример 2: Сортировка по компаниям

Конфигурация `config/all_clients.env`:

```ini
from="/home/cdr_admin/incoming"
to="/home/cdr_admin/processed"
by_company=yes
```

Результат:

```
/home/cdr_admin/processed/
├── Telna Corp/
│   └── file1.csv
├── Client X/
│   └── file2.csv
```

### Пример 3: Сортировка по датам

Конфигурация `config/daily_cdr.env`:

```ini
from="/home/cdr_admin/incoming"
to="/home/cdr_admin/archive"
by_date=yes
```

Результат:

```
/home/cdr_admin/archive/
├── 2026-04-10/
│   └── file1.csv
├── 2026-04-11/
│   └── file2.csv
```

### Пример 4: Комбинированная сортировка

Конфигурация `config/organized.env`:

```ini
from="/home/cdr_admin/incoming"
to="/home/cdr_admin/organized"
by_company=yes
by_date=yes
```

Результат:

```
/home/cdr_admin/organized/
├── Telna Corp/
│   ├── 2026-04-10/
│   │   └── file1.csv
│   └── 2026-04-11/
│       └── file2.csv
└── Client X/
    └── 2026-04-10/
        └── file3.csv
```

### Пример 5: Плоская структура

Конфигурация `config/flat.env`:

```ini
from="/home/cdr_admin/incoming/telna"
to="/home/cdr_admin/flat"
flat=yes
```

Результат:

```
/home/cdr_admin/flat/
├── file1.csv (из /incoming/telna/subdir1/)
├── file2.csv (из /incoming/telna/subdir2/)
└── file3.csv (из /incoming/telna/)
```

### Пример 6: Фильтрация по компании

Конфигурация `config/edatA_only.env`:

```ini
from="/home/cdr_admin/incoming"
to="/home/cdr_admin/edata"
company="eData"
```

Скопирует только файлы с `eData` в названии компании.

### Пример 7: Вчерашние файлы

Конфигурация `config/yesterday.env`:

```ini
from="/home/cdr_admin/incoming"
to="/home/cdr_admin/yesterday"
yesterday=yes
```

Скопирует только файлы за вчерашний день.

### Пример 8: Диапазон дат

Конфигурация `config/q1_2026.env`:

```ini
from="/home/cdr_admin/incoming"
to="/home/cdr_admin/q1_2026"
from_date="20260101"
to_date="20260331"
```

Скопирует только файлы за Q1 2026.

## Dry-run режим

Режим предпросмотра без реального копирования:

```bash
python3 cdr_copy/cdr_copy.py telna_cdr --dry-run
```

Вывод:

```
2026-04-10 15:30:45 - DRY RUN MODE - no files will be copied
2026-04-10 15:30:46 - DRY RUN: Would copy /src/file.csv -> /dst/file.csv
2026-04-10 15:30:47 - DRY RUN: Would copy /src/file2.csv -> /dst/file2.csv
2026-04-10 15:30:48 - RUN SUMMARY: copied=0 skipped=0 errors=0 dry_run_skipped=2
```

## Логирование

Лог-файлы хранятся в `cdr_copy/logs/cdr_copy.log`.

### Формат логов

```
2026-04-10 15:30:45 - COPIED LIVE_Telna_CDR_20260410...
2026-04-10 15:30:46 - SKIPPED LIVE_Client_LU_... (exists)
2026-04-10 15:30:47 - ERROR LIVE_... : Permission denied
2026-04-10 15:30:48 - RUN SUMMARY: copied=10 skipped=5 errors=0
```

### Ротация логов

Для настройки ротации используйте logrotate:

```bash
# Установить конфигурацию logrotate
sudo cp cdr_copy.logrotate /etc/logrotate.d/cdr_copy
```

Конфигурация хранит 7 дней логов с сжатием.

## Обработка ошибок

### Валидация конфигурации

Модуль проверяет:

- Обязательные параметры (from, to)
- Существование исходной папки
- Возможность создания целевой папки
- Права на запись в целевую папку
- Формат дат (YYYYMMDD)
- Логику диапазона дат (from_date <= to_date)
- Несовместимые флаги (yesterday=yes и today=yes)

### Коды возврата

- **0** - Успешное выполнение
- **1** - Ошибка валидации или ошибки копирования

## Особенности

- **Атомарное копирование** - использует временные файлы для предотвращения частичной записи
- **Пропуск существующих файлов** - не перезаписывает файлы, которые уже существуют
- **Извлечение метаданных** - использует паттерны имён файлов для получения даты и компании
- **Гибкая фильтрация** - комбинации флагов для различных сценариев использования

## Формат имени файла

Модуль ожидает файлы в формате:

```
LIVE_{Company}_{Type}_{DateTime}_{N}_{EndDateTime}.csv
```

Примеры:

- `LIVE_eData_Online_CDR_20260323090000_1_20260323101228.csv`
- `LIVE_Telna_Corp_LU_20260407120000_1_20260407123456.csv`

## Интеграция

Модуль может использоваться в цепочках:

```
cdr_sync → cdr_copy → cdr_organize → cdr_load → cdr_publish
```

## Зависимости

- Python 3.8+
- python-dotenv==1.0.0
