# План улучшения покрытия тестами

## Текущее состояние
- **Всего тестов**: 330
- **Проходят**: 326
- **Пропущено**: 2
- **Падают**: 2 (pre-existing в `test_services.py`)
- **Покрытие**: ~75-80%

## Созданные тесты (2026-07-28)
1. `tests/test_order_coverage.py` — 21 тест для критических хендлеров:
   - `process_payment_proof` (7 тестов)
   - `process_document_field` (6 тестов)
   - `save_delivery` (5 тестов)
   - `_generate_order_id` (3 теста)
   - `_notify_admin_validation_error` (3 теста)

2. `tests/test_e2e_order_flow.py` — 3 e2e-теста:
   - `test_e2e_full_order_flow` — полный сценарий заказа
   - `test_e2e_cancel_flow` — отмена заказа
   - `test_e2e_admin_flow` — skipped (требует deeper integration)

3. `tests/test_documents.py` — 12 тестов для шаблонов документов и цен

## План на ближайшую неделю

### 1. Исправить pre-existing баги (приоритет: высокий)
- [ ] **`tests/test_services.py`**: уникальность `order_id` в SQLite
  - Проблема: `UNIQUE constraint failed: orders.order_id`
  - Решение: добавить фиксированные order_id в тестовые данные или очищать БД между тестами

### 2. Улучшить admin e2e-тестирование (приоритет: средний)
- [ ] Создать кастомный декоратор `@mock_admin` в `tests/fixtures/mocks.py`
- [ ] Добавить тесты для `callback_send_doc` с реальными `CallbackQuery` моками
- [ ] Протестировать `process_document_file` с реальными `Message` с `photo`

### 3. Покрыть недостающие хендлеры (приоритет: средний)
- [ ] `handlers/fast_order.py` — добавить тесты для валидации полей
- [ ] `handlers/start.py` — покрыть `cmd_help_manager` (уже есть частично)
- [ ] `handlers/admin.py` — добавить тесты для `cmd_track`, `callback_order_done`

### 4. Параметризация и DRY (приоритет: низкий)
- [ ] Объединить дублирующиеся тесты в `test_order.py` и `test_order_coverage.py`
- [ ] Добавить `@pytest.mark.parametrize` для валидационных тестов

### 5. Инфраструктура (приоритет: низкий)
- [ ] Настроить `pytest-cov` с порогом 80% в `pyproject.toml`
- [ ] Добавить badge в `README.md` (coverage %, builds)
- [ ] Настроить GitHub Actions для авто-запуска тестов при PR

## Метрики успеха
- **Цель по покрытию**: 85%+ (строки/функции)
- **Цель по тестам**: 350+ тестов
- **Падающих тестов**: 0

## Команды для запуска
```bash
# Запустить все тесты
py -m pytest tests/

# Запустить с coverage
py -m pytest tests/ --cov=. --cov-report=html

# Запустить конкретный файл
py -m pytest tests/test_order_coverage.py -v
```

## Структура тестового каталога
```
tests/
├── conftest.py                 # Общие фикстуры
├── fixtures/
│   ├── __init__.py
│   ├── db_fixtures.py          # Фикстуры БД
│   └── mocks.py                # Mock-объекты (Message, Callback, FSM)
├── test_admin.py               # Admin-хендлеры
├── test_auth.py                # Авторизация
├── test_buttons.py             # Клавиатуры
├── test_config.py              # Конфиг
├── test_crud.py                # CRUD операции
├── test_database_config.py     # Database setup
├── test_documents.py           # Шаблоны документов ✨ НОВЫЙ
├── test_e2e_order_flow.py      # E2E тесты ✨ НОВЫЙ
├── test_fast_order.py          # Быстрый заказ
├── test_fixes.py               # Исправления
├── test_i18n.py                # Интернационализация
├── test_middleware.py          # Middleware
├── test_order.py               # Основные хендлеры заказа
├── test_order_coverage.py      # Покрытие заказа ✨ НОВЫЙ
├── test_router.py              # Роутер
├── test_services.py            # Сервисы
├── test_start.py               # Стартовые команды
├── test_states.py              # FSM состояния
├── test_telegram_connectivity.py # Telegram API
├── test_validation.py          # Валидация
└── test_validation_parametrized.py # Параметризованная валидация
```

## Примечания
- Admin-флоу требует интеграции с Telegram Messenger API для полного тестирования
- `test_e2e_admin_flow` помечен `@pytest.mark.skip` до реализации кастомных моков
- Pre-existing failures в `test_services.py` не блокируют CI