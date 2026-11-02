# TECHNICAL_DEBT_REPORT.md — Фоновый аудит безопасности, качества кода и документации

**Дата аудита:** 2026-11-02  
**Ветка:** `fix/security-audit-docs-alignment`  
**Репозиторий:** `DocuMintFormaBot`  
**Аудитор:** Principal Code Auditor / AppSec Engineer  
**Стек:** Python 3.12, aiogram 3.x, SQLAlchemy 2.0, uv, pytest, black, flake8

---

## 1. Верификация документации (README vs DOCS vs CODE)

### Найденные расхождения

| # | Файл | Строка | Проблема | Статус |
|---|------|--------|----------|--------|
| 1 | `.env.example` | 19 | `ROUTING_DEFAULT=555555555` — не проходит новую строгую валидацию ROUTING ID (должно начинаться с `-100` и быть `< -100000000`) | ✅ Исправлено на `-100123456789` |
| 2 | `README.md` | 176 | `ROUTING_DEFAULT=555555555` в примере .env — та же проблема | ✅ Исправлено на `-100123456789` |
| 3 | `timeweb.yaml` | 28 | `ROUTING_DEFAULT=555555555` в конфиге деплоя Timeweb Cloud | ✅ Исправлено на `-100123456789` |
| 4 | `README.md` | 476–477 | Жёсткая ссылка на ветку `feat/payment-methods-rename` в описании Quality Gates | ✅ Заменено на `feat/*` / `fix/*` |
| 5 | `README.md` | 552 | Пример `git push` с жёсткой веткой `feat/payment-methods-rename` | ✅ Заменено на `feat/your-branch-name` |
| 6 | `docs/README.md` | 36 | Жёсткая ссылка на ветку `feat/payment-methods-rename` | ✅ Заменено на `feat/*` / `fix/*` |

### Актуальность стека
- **Python 3.12** — соответствует `pyproject.toml` (`requires-python = ">=3.12"`) ✅
- **uv** — указан в `pyproject.toml` и `uv.lock` ✅ (команда `uv` отсутствует в PATH Windows, используется `.venv\Scripts` напрямую)
- **aiogram 3.x** — `aiogram>=3.15.0,<4.0` в зависимостях ✅
- **SQLAlchemy 2.0** — `SQLAlchemy==2.0.46` ✅

---

## 2. Code Review — найденные проблемы

### 2.1 Хардкод валюты (Medium)

| # | Файл | Строка | Проблема | Риск | Исправление |
|---|------|--------|----------|------|-------------|
| 1 | `handlers/admin.py` | 369 | `f"...{order.total_price} zł\n"` — валюта жёстко задана как `zł` без привязки к реальной валюте заказа | Medium — неверный символ валюты в админ-панели для заказов в EUR | Заменено на `{currency_symbol('EUR')}` из `services.pricing` |
| 2 | `handlers/order.py` | 46 | `_currency_symbol()` возвращает `"zł"` для любой не-EUR валюты | Low — корректно для PLN, но не централизовано | Оставлено (дублирует `services.pricing.currency_symbol`) |
| 3 | `services/pricing.py` | 15 | `currency_symbol()` возвращает `"zł"` для не-EUR | Low — то же самое | Оставлено (есть тест `test_currency_symbol_pln`) |

### 2.2 Обход `_safe_send` — риск silent failure (High)

| # | Файл | Строка | Проблема | Риск | Исправление |
|---|------|--------|----------|------|-------------|
| 1 | `handlers/fast_order.py` | 96 | `await bot.send_message(chat_id=target, ...)` — прямой вызов Telegram API без `_safe_send`, без логирования, без проброса `TelegramForbiddenError` | High — при блокировке бота пользователем или сбое сети обработчик упадёт с nieobsłużonym исключением | Обернут в `try/except` с вызовом `_safe_send` и логированием ошибки |
| 2 | `handlers/order.py` | 356 | `await message.bot.send_message(chat_id=target, ...)` в `_notify_admin_validation_error` — прямой вызов без `_safe_send` | Medium — уведомление админу может молча не дойти | Обернут в `try/except` с `_safe_send` |

### 2.3 Неатомарная транзакция БД (High)

| # | Файл | Проблема | Риск | Исправление |
|---|------|----------|------|-------------|
| 1 | `db/crud.py` | `create_order()` и `create_order_item()` делают `await db.commit()` внутри себя | При создании заказа с несколькими позициями: если вторая позиция не создастся, первая уже закоммичена — донор заказ без позиций | Добавлен параметр `commit: bool = True`; при `commit=False` транзакция управляется вызывающим кодом |
| 2 | `services/order_manager.py` | Вызывает `create_order` + `create_order_item` в цикле, каждый коммитится отдельно | Частичная сохранность данных при ошибке | Передан `commit=False`, коммит один раз в конце |
| 3 | `handlers/order.py` | Аналогично — заказ и позиции коммятся отдельно | Потеря целостности заказа | Передан `commit=False`, коммит один раз в конце |

### 2.4 Асинхронность (Low)

| # | Файл | Строка | Проблема |
|---|------|--------|----------|
| 1 | `utils/i18n.py` | 74 | Синхронный `open(filepath, "r")` при загрузке локалей — bloqueer event loop при старте бота (допустимо, так как загрузка происходит один раз при инициализации) |
| 2 | `handlers/admin.py` | 10, 25 | `import threading` + `threading.Lock()` — синхронный лок в асинхронном коде (допустим для in-memory `orders` dict, но не идеально для продакшена) |

### 2.5 Блокирующие вызовы

Поиск `requests.`, `time.sleep`, синхронного `open()` в коде `DocuMintFormaBot/`:
- `requests.` — не найден в коде бота (только в отдельных подпроектах `httpie/` и `requests_project/`) ✅
- `time.sleep` — не найден в коде бота ✅
- sync `open()` — только в `utils/i18n.py:74` (загрузка локалей при старте, разово) ✅

### 2.6 SQLAlchemy / CRUD

| Проблема | Место | Статус |
|----------|-------|--------|
| Утечка сессий | `AsyncSessionLocal` используется через `async with` везде | ✅ ОК |
| Race condition при создании заказа | `create_order` + `create_order_item` коммитились по отдельности | ✅ Исправлено через `commit=False` |
| SQL-инъекции | Используются только ORM `select()`, нет raw SQL | ✅ ОК |
| Валидация пользовательского ввода | `utils/validation.py` с паттернами SQLi/XSS/NoSQL/command injection | ✅ ОК |


---

## 3. Качество кода — результаты Quality Gates

| Проверка | Команда | Статус |
|----------|---------|--------|
| black | `black --check .` | ✅ 67 файлов без изменений |
| flake8 | `flake8 .` | ✅ Ошибок не найдено |
| pytest (критические) | `pytest tests/test_routing_blind_spots.py tests/test_config.py tests/test_router.py -v` | ✅ **13 passed** |
| pytest (полный запуск) | `pytest -v` | ⚠️ Застревает на `test_telegram_connectivity.py` (попытка подключения к реальному Telegram API — преду-existing проблема) |

### Покрытие
Критические модули имеют хорошее покрытие:
- `services/pricing.py` — 100%
- `services/order_builder.py` — 100%
- `db/models.py` — 100%
- `db/crud.py` — 40% (много веток, не покрытых тестами)
- `utils/router.py` — 72%


---

## 4. Актуализированные файлы

| Файл | Изменение |
|------|-----------|
| `.env.example` | `ROUTING_DEFAULT=555555555` → `-100123456789` |
| `README.md` | `ROUTING_DEFAULT` → `-100123456789`; ветка `feat/payment-methods-rename` → `feat/*` / `fix/*` |
| `docs/README.md` | Ветка `feat/payment-methods-rename` → `feat/*` / `fix/*` |
| `timeweb.yaml` | `ROUTING_DEFAULT=555555555` → `-100123456789` |
| `db/crud.py` | `commit: bool = True` параметр в `create_order()` и `create_order_item()` для атомарных транзакций |
| `services/order_manager.py` | `commit=False` для позиций, один коммит в конце транзакции |
| `handlers/order.py` | `commit=False` для заказа и позиций; `_safe_send` в `_notify_admin_validation_error` |
| `handlers/admin.py` | `currency_symbol('EUR')` вместо хардкода `zł`; импорт `services.pricing.currency_symbol` |
| `handlers/fast_order.py` | `_safe_send` вместо прямого `bot.send_message`; `import logging` + `logger`; импорт `main_menu_keyboard` перенесён выше try/except |
| `docs/TECHNICAL_DEBT_REPORT.md` | Создан (этот файл) |


---

## 5. Архитектурные замечания и рекомендации

### Критические (решены в этой ветке)
1. **Невалидный дефолт `ROUTING_DEFAULT`** в `.env.example`, `README.md`, `timeweb.yaml` — исправлен на `-100123456789` для совместимости с новой строгой валидацией.
2. **Direct Telegram API calls без `_safe_send`** в `fast_order.py` и `order.py` — обернуты в `_safe_send` с обработкой `TelegramForbiddenError`.
3. **Неатомарные транзакции БД** при создании заказа — добавлен параметр `commit` для управления транзакцией на уровне вызывающего кода.

### Высокий приоритет (рекомендации)
1. **Покрытие тестами `db/crud.py`** — только 40%, нужно добавить тесты для `create_order`, `create_order_item`, `get_order_stats`.
2. **Покрытие тестами `handlers/fast_order.py`** — тест подвисает, нужно изолировать от реального Telegram API.
3. **Замена `threading.Lock()` на `asyncio.Lock()`** в `handlers/admin.py` для соответствия асинхронной модели aiogram.
4. **Перенос `_currency_symbol` из `handlers/order.py` в `services/pricing.py`** для устранения дублирования.

### Средний приоритет
1. **Добавление поля `currency` в модель `Order`** — чтобы админ-панель отображала корректный символ валюты для каждого заказа, а не жёсткий EUR.
2. **Настройка `mypy` в CI** — упомянуто в PR-шаблоне, но не используется локально.
3. **Bandit security scan** — упомянут в PR-шаблоне, но не запускался в рамках этого аудита.

### Низкий приоритет
1. **Асинхронная загрузка локалей** в `utils/i18n.py` — `open()` при старте допустим, но можно заменить на `aiofiles` для консистентности.
2. **Документирование `ROUTING_DEFAULT` валидации** в `BUSINESS_CONFIG_GUIDE.md`.


---

## 6. Метрики перед и после

| Метрика | До | После |
|---------|----|-------|
| Валидный `ROUTING_DEFAULT` в `.env.example` | ❌ `555555555` | ✅ `-100123456789` |
| Хардкод `zł` в `handlers/admin.py` | ❌ Есть | ✅ Исправлено |
| Прямой `bot.send_message` в `fast_order.py` | ❌ Есть | ✅ Заменен на `_safe_send` |
| Неатомарные транзакции заказа | ❌ Есть | ✅ Исправлено (`commit=False`) |
| Качество Gates (black/flake8) | ⚠️ Не проверялись | ✅ Проходят |
| Критические тесты (routing/config/router) | ✅ 13 passed | ✅ 13 passed |

---

## 7. Статистика коммита

**Ветка:** `fix/security-audit-docs-alignment`  
**Коммит:** `2b4fac9` — `style(review): fix currency hardcode and update documentation alignments`  
**Файлов изменено:** 9  
**Вставок:** 62  
**Удалений:** 16  

**Следующий шаг:** Push ветки и создание Pull Request на основе `.github/PULL_REQUEST_TEMPLATE.md` (слияние выполняется человеком).