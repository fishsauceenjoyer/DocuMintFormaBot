# 🔒 PD Audit — полнотекстовый поиск персональных данных

Автогенерировано скриптом `scripts/pd_audit_search.py` (Эпик 1, задача 1.1).

Просканировано файлов: **98**.

Ключевые слова: passport, passport_number, inn, snils, address,
registration, date_of_birth, place_of_birth, паспорт, инн, снилс,
адрес, регистрация, дата рождения.

## `config/loader.py`

### Ключевое слово: `passport_number` (1 совпадений)

- L54: `"passport_number",`

## `config/templates.yaml`

### Ключевое слово: `address` (1 совпадений)

- L51: `- id: address`

### Ключевое слово: `passport` (2 совпадений)

- L33: `passport:`
- L36: `name_en: "🛂 Foreign passport"`

### Ключевое слово: `passport_number` (2 совпадений)

- L19: `- id: passport_number`
- L21: `type: passport_number`

### Ключевое слово: `адрес` (1 совпадений)

- L52: `prompt: "🏠 Адрес проживания"`

### Ключевое слово: `дата рождения` (3 совпадений)

- L17: `prompt: "🎂 Дата рождения (ДД.ММ.ГГГГ)"`
- L45: `prompt: "🎂 Дата рождения (ДД.ММ.ГГГГ)"`
- L68: `prompt: "🎂 Дата рождения (ДД.ММ.ГГГГ)"`

### Ключевое слово: `паспорта` (1 совпадений)

- L20: `prompt: "🛂 Номер паспорта (серия и номер)"`

### Ключевое слово: `паспорте` (1 совпадений)

- L13: `prompt: "👤 ФИО (как в паспорте)"`

## `configs/base.yaml`

### Ключевое слово: `passport` (3 совпадений)

- L6: `# allowed countries, passport pattern, and routing keys.`
- L55: `# ── Passport number format (regex) ────────────`
- L61: `passport: "ROUTING_PASSPORT"`

### Ключевое слово: `адрес` (1 совпадений)

- L34: `usdt: "₿ USDT (TRC20): TXYZ... (адрес кошелька)"`

## `configs/services.yaml`

### Ключевое слово: `address` (1 совпадений)

- L67: `- id: address`

### Ключевое слово: `passport` (2 совпадений)

- L46: `- id: passport`
- L49: `en: "🛂 Foreign passport"`

### Ключевое слово: `passport_number` (2 совпадений)

- L31: `- id: passport_number`
- L33: `type: passport_number`

### Ключевое слово: `адрес` (1 совпадений)

- L68: `prompt: "🏠 Адрес проживания"`

### Ключевое слово: `дата рождения` (3 совпадений)

- L29: `prompt: "🎂 Дата рождения (ДД.ММ.ГГГГ)"`
- L61: `prompt: "🎂 Дата рождения (ДД.ММ.ГГГГ)"`
- L89: `prompt: "🎂 Дата рождения (ДД.ММ.ГГГГ)"`

### Ключевое слово: `паспорта` (1 совпадений)

- L32: `prompt: "🛂 Номер паспорта (серия и номер)"`

### Ключевое слово: `паспорте` (1 совпадений)

- L25: `prompt: "👤 ФИО (как в паспорте)"`

## `data/business_config.py`

### Ключевое слово: `passport` (1 совпадений)

- L50: `# Passport number format (regex)`

## `data/business_config_demo.py`

### Ключевое слово: `адрес` (1 совпадений)

- L181: `"usdt": "₿ USDT (TRC20): TXYZ... (адрес кошелька)",`

## `data/business_config_original.py`

### Ключевое слово: `address` (1 совпадений)

- L40: `"address",`

### Ключевое слово: `адрес` (1 совпадений)

- L41: `"🏠 Полный адрес проживания (индекс, город, улица, квартира)",`

### Ключевое слово: `дата рождения` (2 совпадений)

- L37: `Field("birth_date", "🎂 Дата рождения (ДД.ММ.ГГГГ)", "date"),`
- L93: `Field("birth_date", "🎂 Дата рождения", "date"),`

### Ключевое слово: `паспорта` (1 совпадений)

- L38: `Field("pesel", "🆔 PESEL или серия/номер паспорта", "text"),`

## `db/crud.py`

### Ключевое слово: `address` (1 совпадений)

- L238: `delivery_paczkomat=delivery.get("address") if delivery else None,`

## `db/models.py`

### Ключевое слово: `passport` (1 совпадений)

- L99: `code: Unique type code (e.g. ``"visa"``, ``"passport"``).`

## `docs/BUSINESS_CONFIG_GUIDE.md`

### Ключевое слово: `address` (1 совпадений)

- L72: `| `email` | Email address | — |`

### Ключевое слово: `passport` (2 совпадений)

- L27: `| `PASSPORT_NUMBER_PATTERN` | `str` | Regex for passport number format |`
- L75: `| `passport_number` | Passport number (A-Z, 0-9, -./) | — |`

### Ключевое слово: `passport_number` (1 совпадений)

- L75: `| `passport_number` | Passport number (A-Z, 0-9, -./) | — |`

## `fsm/states.py`

### Ключевое слово: `адрес` (1 совпадений)

- L21: `5. filling_delivery — ввод данных для доставки (ФИО, телефон, адрес)`

## `handlers/order.py`

### Ключевое слово: `address` (1 совпадений)

- L633: `"address": truncate_for_storage(`

## `locales/en.json`

### Ключевое слово: `address` (2 совпадений)

- L9: `"delivery_prompt": "🚚 **Delivery**\n\nEnter delivery details in one message:\n\nFull name:\nPhone number:\nEmail:\nDelivery address or parcel locker number",`
- L10: `"delivery_format_error": "❌ Please enter details in the correct format:\n\nFull name:\nPhone number:\nEmail:\nDelivery address",`

## `pyproject.toml`

### Ключевое слово: `passport` (1 совпадений)

- L4: `description = "Telegram bot for document ordering (visa, passport, apostille)"`

## `README.md`

### Ключевое слово: `address` (1 совпадений)

- L22: `- 🚚 **Delivery / pickup** — enter courier address or choose self-pickup`

### Ключевое слово: `passport` (2 совпадений)

- L201: `| 🛂 Foreign passport                   | 200  | 45   |`
- L212: `| `data/business_config.py` | **Active** — demo "consular services" (visa, passport, etc.) |`

### Ключевое слово: `registration` (1 совпадений)

- L73: `│   ├── middleware.py         # Logging / user registration middleware`

## `scripts/pd_audit_search.py`

### Ключевое слово: `address` (2 совпадений)

- L24: `r"address|registration)\b",`
- L102: `"Ключевые слова: passport, passport_number, inn, snils, address,",`

### Ключевое слово: `date_of_birth` (2 совпадений)

- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"`
- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",`

### Ключевое слово: `inn` (3 совпадений)

- L21: `# "running" matching "inn").`
- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"`
- L102: `"Ключевые слова: passport, passport_number, inn, snils, address,",`

### Ключевое слово: `passport` (2 совпадений)

- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"`
- L102: `"Ключевые слова: passport, passport_number, inn, snils, address,",`

### Ключевое слово: `passport_number` (2 совпадений)

- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"`
- L102: `"Ключевые слова: passport, passport_number, inn, snils, address,",`

### Ключевое слово: `place_of_birth` (2 совпадений)

- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"`
- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",`

### Ключевое слово: `registration` (2 совпадений)

- L24: `r"address|registration)\b",`
- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",`

### Ключевое слово: `snils` (2 совпадений)

- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"`
- L102: `"Ключевые слова: passport, passport_number, inn, snils, address,",`

### Ключевое слово: `адрес` (2 совпадений)

- L28: `r"\b(паспорт\w*|инн\b|снилс\w*|адрес\w*|регистраци\w*|дата\s+рождения)\b",`
- L104: `"адрес, регистрация, дата рождения.",`

### Ключевое слово: `дата рождения` (1 совпадений)

- L104: `"адрес, регистрация, дата рождения.",`

### Ключевое слово: `инн` (2 совпадений)

- L28: `r"\b(паспорт\w*|инн\b|снилс\w*|адрес\w*|регистраци\w*|дата\s+рождения)\b",`
- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",`

### Ключевое слово: `паспорт` (2 совпадений)

- L28: `r"\b(паспорт\w*|инн\b|снилс\w*|адрес\w*|регистраци\w*|дата\s+рождения)\b",`
- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",`

### Ключевое слово: `регистраци` (1 совпадений)

- L28: `r"\b(паспорт\w*|инн\b|снилс\w*|адрес\w*|регистраци\w*|дата\s+рождения)\b",`

### Ключевое слово: `регистрация` (1 совпадений)

- L104: `"адрес, регистрация, дата рождения.",`

### Ключевое слово: `снилс` (2 совпадений)

- L28: `r"\b(паспорт\w*|инн\b|снилс\w*|адрес\w*|регистраци\w*|дата\s+рождения)\b",`
- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",`

## `services/order_builder.py`

### Ключевое слово: `address` (2 совпадений)

- L54: `text += f"  Address: {delivery.get('address', '-')}\n\n"`
- L54: `text += f"  Address: {delivery.get('address', '-')}\n\n"`

## `templates/fields.py`

### Ключевое слово: `passport_number` (1 совпадений)

- L51: `"passport_number": "буквы A-Z, цифры 0-9, дефис, точка, слеш. Длина 3-30",`

## `tests/conftest.py`

### Ключевое слово: `address` (1 совпадений)

- L79: `# Try connecting to the first resolved address`

## `tests/test_business_config.py`

### Ключевое слово: `passport` (6 совпадений)

- L98: `assert "passport" in ROUTING_KEYS`
- L164: `assert "passport" in codes`
- L191: `assert get_price_pln("passport") == 200`
- L219: `assert get_price_eur("passport") == 45`
- L227: `"""Verify valid passport numbers match the pattern."""`
- L240: `"""Verify invalid passport numbers don't match the pattern."""`

## `tests/test_buttons.py`

### Ключевое слово: `passport` (4 совпадений)

- L20: `docs = [("visa", "Visa application"), ("passport", "Foreign passport")]`
- L20: `docs = [("visa", "Visa application"), ("passport", "Foreign passport")]`
- L30: `docs = [("visa", "Visa"), ("passport", "Passport")]`
- L30: `docs = [("visa", "Visa"), ("passport", "Passport")]`

## `tests/test_crud.py`

### Ключевое слово: `address` (1 совпадений)

- L127: `"address": "Test St 1",`

### Ключевое слово: `passport` (2 совпадений)

- L102: `assert len(types) >= 4  # visa, passport, criminal_record_check, apostille`
- L105: `assert "passport" in codes`

## `tests/test_documents.py`

### Ключевое слово: `passport` (4 совпадений)

- L43: `"""Verify 'passport' is in the list."""`
- L47: `assert "passport" in codes`
- L77: `"""Verify get_template('passport') returns a dict."""`
- L80: `template = get_template("passport")`

## `tests/test_fast_order.py`

### Ключевое слово: `passport` (2 совпадений)

- L160: `message = MockMessage(text="Test order: passport", chat_id=123)`
- L171: `assert "Test order: passport" in message.bot._mock_message_sent["text"]`

## `tests/test_order.py`

### Ключевое слово: `passport` (4 совпадений)

- L59: `"""Test selecting a "Foreign passport" document.`
- L69: `# The English name is "Foreign passport"`
- L70: `assert "Foreign passport" in edited_text`
- L71: `# Passport price is 45 EUR`

## `tests/test_order_coverage.py`

### Ключевое слово: `address` (5 совпадений)

- L6: `- save_delivery (delivery address input)`
- L446: `"""Tests for delivery address input handler."""`
- L498: `assert session["delivery"]["address"] == "Main Street 1, Warsaw"`
- L527: `"""Verify missing address line defaults to '-'."""`
- L539: `assert session["delivery"]["address"] == "-"`

## `tests/test_security.py`

### Ключевое слово: `address` (3 совпадений)

- L153: `"address": "St (1)",`
- L232: `"address": truncate_for_storage(raw_lines[3]),`
- L239: `assert delivery["address"] == "St (1), Apt#2"`

## `tests/test_services.py`

### Ключевое слово: `address` (2 совпадений)

- L104: `"address": "Street 1",`
- L132: `"address": "Main 1",`

### Ключевое слово: `passport` (1 совпадений)

- L95: `"type": "passport",`

## `tests/test_start.py`

### Ключевое слово: `passport` (2 совпадений)

- L112: `("passport", "Foreign passport"),`
- L112: `("passport", "Foreign passport"),`

## `tests/test_telegram_connectivity.py`

### Ключевое слово: `address` (1 совпадений)

- L51: `"""Verify that ``api.telegram.org`` resolves to at least one IP address.`

## `tests/test_validation.py`

### Ключевое слово: `passport` (3 совпадений)

- L444: `f = Field("passport", "Number", "passport_number")`
- L643: `result = validate_field_value(value, "passport_number", field_name="passport")`
- L657: `result = validate_field_value(value, "passport_number", field_name="passport")`

### Ключевое слово: `passport_number` (14 совпадений)

- L315: `"FB363261", "passport_number", field_name="passport_number"`
- L315: `"FB363261", "passport_number", field_name="passport_number"`
- L322: `"AB-123.45 / 678", "passport_number", field_name="passport_number"`
- L322: `"AB-123.45 / 678", "passport_number", field_name="passport_number"`
- L329: `"AB", "passport_number", field_name="passport_number"`
- L329: `"AB", "passport_number", field_name="passport_number"`
- L336: `"AB@123", "passport_number", field_name="passport_number"`
- L336: `"AB@123", "passport_number", field_name="passport_number"`
- L342: `"fb363261", "passport_number", field_name="passport_number"`
- L342: `"fb363261", "passport_number", field_name="passport_number"`
- L444: `f = Field("passport", "Number", "passport_number")`
- L623: `"""Equivalence classes and boundary values for ``passport_number`` fields."""`
- L643: `result = validate_field_value(value, "passport_number", field_name="passport")`
- L657: `result = validate_field_value(value, "passport_number", field_name="passport")`

## `utils/middleware.py`

### Ключевое слово: `регистрации` (2 совпадений)

- L24: `Middleware для автоматической регистрации пользователей.`
- L30: `Позволяет избежать дублирования кода регистрации в каждом хендлере`

### Ключевое слово: `регистрация` (1 совпадений)

- L5: `- RegistrationMiddleware: автоматическая регистрация пользователей`

## `utils/router.py`

### Ключевое слово: `address` (2 совпадений)

- L179: `text += f"  Address: {_escape_markdown(delivery.get('address', '-'))}\n\n"`
- L179: `text += f"  Address: {_escape_markdown(delivery.get('address', '-'))}\n\n"`

## `utils/validation.py`

### Ключевое слово: `passport_number` (1 совпадений)

- L299: `elif field_type == "passport_number":`

### Ключевое слово: `паспорта` (1 совпадений)

- L306: `"❌ Неверный формат номера паспорта. "`

## 📊 Итоговая статистика

- Файлов с совпадениями: **34**
- Всего совпадений: **142**
