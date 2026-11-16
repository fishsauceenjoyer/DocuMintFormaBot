# 🔒 PD Audit — полнотекстовый поиск персональных данных

Автогенерировано скриптом `scripts/pd_audit_search.py` (Эпик 1, задача 1.1).

Просканировано файлов: **99**.

Ключевые слова: passport, passport_number, inn, snils, address,
registration, date_of_birth, place_of_birth, паспорт, инн, снилс,
адрес, регистрация, дата рождения.

## `configs/base.yaml`

### Ключевое слово: `адрес` (1 совпадений)

- L38: `usdt: "₿ USDT (TRC20): TXYZ... (адрес кошелька)"`

## `data/business_config_demo.py`

### Ключевое слово: `адрес` (1 совпадений)

- L181: `"usdt": "₿ USDT (TRC20): TXYZ... (адрес кошелька)",`

## `db/crud.py`

### Ключевое слово: `address` (1 совпадений)

- L238: `delivery_paczkomat=delivery.get("address") if delivery else None,`

## `docs/BUSINESS_CONFIG_GUIDE.md`

### Ключевое слово: `address` (1 совпадений)

- L71: `| `email` | Email address | — |`

## `docs/cleanup_illegal_services.md`

### Ключевое слово: `address` (2 совпадений)

- L81: `> Telegram-аккаунте), «адрес доставки» (`delivery_paczkomat`/`delivery.get("address")`)`
- L82: `> и «IP address» в тестах коннективности **не являются** персональными данными`

### Ключевое слово: `date_of_birth` (1 совпадений)

- L64: ``date_of_birth`) из таблиц `orders`, `users`, `document_types`, если они существуют.`

### Ключевое слово: `inn` (1 совпадений)

- L63: `удаляет legacy-колонки (`passport_number`, `inn`, `snils`, `registration_address`,`

### Ключевое слово: `passport` (1 совпадений)

- L38: `- **`config_runtime.py`** — комментарий про `ROUTING_VISA/PASSPORT` заменён на постерный.`

### Ключевое слово: `passport_number` (1 совпадений)

- L63: `удаляет legacy-колонки (`passport_number`, `inn`, `snils`, `registration_address`,`

### Ключевое слово: `snils` (1 совпадений)

- L63: `удаляет legacy-колонки (`passport_number`, `inn`, `snils`, `registration_address`,`

### Ключевое слово: `адрес` (1 совпадений)

- L81: `> Telegram-аккаунте), «адрес доставки» (`delivery_paczkomat`/`delivery.get("address")`)`

### Ключевое слово: `адреса` (2 совпадений)

- L8: `удостоверяющие личность, идентификаторы, даты рождения, адреса регистрации и т.п.)`
- L16: `(документы, удостоверяющие личность, номера, даты рождения, адреса проживания,`

### Ключевое слово: `регистрации` (1 совпадений)

- L8: `удостоверяющие личность, идентификаторы, даты рождения, адреса регистрации и т.п.)`

### Ключевое слово: `регистрация` (1 совпадений)

- L80: `> **Замечание:** термины `RegistrationMiddleware` (регистрация *пользователя* в`

## `docs/PD_AUDIT.md`

### Ключевое слово: `address` (57 совпадений)

- L7: `Ключевые слова: passport, passport_number, inn, snils, address,`
- L19: `### Ключевое слово: `address` (1 совпадений)`
- L21: `- L51: `- id: address``
- L65: `### Ключевое слово: `address` (1 совпадений)`
- L67: `- L67: `- id: address``
- L111: `### Ключевое слово: `address` (1 совпадений)`
- L113: `- L40: `"address",``
- L130: `### Ключевое слово: `address` (1 совпадений)`
- L132: `- L238: `delivery_paczkomat=delivery.get("address") if delivery else None,``
- L142: `### Ключевое слово: `address` (1 совпадений)`
- L144: `- L72: `| `email` | Email address | — |``
- L163: `### Ключевое слово: `address` (1 совпадений)`
- L165: `- L633: `"address": truncate_for_storage(``
- L169: `### Ключевое слово: `address` (2 совпадений)`
- L171: `- L9: `"delivery_prompt": "🚚 **Delivery**\n\nEnter delivery details in one message:\n\nFull name:\nPhone number:\nEmail:\nDelivery address or parcel locker numb…`
- L172: `- L10: `"delivery_format_error": "❌ Please enter details in the correct format:\n\nFull name:\nPhone number:\nEmail:\nDelivery address",``
- L182: `### Ключевое слово: `address` (1 совпадений)`
- L184: `- L22: `- 🚚 **Delivery / pickup** — enter courier address or choose self-pickup``
- L197: `### Ключевое слово: `address` (2 совпадений)`
- L199: `- L24: `r"address|registration)\b",``
- L200: `- L102: `"Ключевые слова: passport, passport_number, inn, snils, address,",``
- L211: `- L102: `"Ключевые слова: passport, passport_number, inn, snils, address,",``
- L216: `- L102: `"Ключевые слова: passport, passport_number, inn, snils, address,",``
- L221: `- L102: `"Ключевые слова: passport, passport_number, inn, snils, address,",``
- L230: `- L24: `r"address|registration)\b",``
- L236: `- L102: `"Ключевые слова: passport, passport_number, inn, snils, address,",``
- L272: `### Ключевое слово: `address` (2 совпадений)`
- L274: `- L54: `text += f"  Address: {delivery.get('address', '-')}\n\n"``
- L274: `- L54: `text += f"  Address: {delivery.get('address', '-')}\n\n"``
- L275: `- L54: `text += f"  Address: {delivery.get('address', '-')}\n\n"``
- L275: `- L54: `text += f"  Address: {delivery.get('address', '-')}\n\n"``
- L285: `### Ключевое слово: `address` (1 совпадений)`
- L287: `- L79: `# Try connecting to the first resolved address``
- L311: `### Ключевое слово: `address` (1 совпадений)`
- L313: `- L127: `"address": "Test St 1",``
- L347: `### Ключевое слово: `address` (5 совпадений)`
- L349: `- L6: `- save_delivery (delivery address input)``
- L350: `- L446: `"""Tests for delivery address input handler."""``
- L351: `- L498: `assert session["delivery"]["address"] == "Main Street 1, Warsaw"``
- L352: `- L527: `"""Verify missing address line defaults to '-'."""``
- L353: `- L539: `assert session["delivery"]["address"] == "-"``
- L357: `### Ключевое слово: `address` (3 совпадений)`
- L359: `- L153: `"address": "St (1)",``
- L360: `- L232: `"address": truncate_for_storage(raw_lines[3]),``
- L361: `- L239: `assert delivery["address"] == "St (1), Apt#2"``
- L365: `### Ключевое слово: `address` (2 совпадений)`
- L367: `- L104: `"address": "Street 1",``
- L368: `- L132: `"address": "Main 1",``
- L383: `### Ключевое слово: `address` (1 совпадений)`
- L385: `- L51: `"""Verify that ``api.telegram.org`` resolves to at least one IP address.``
- … и ещё 7 совпадений

### Ключевое слово: `date_of_birth` (14 совпадений)

- L8: `registration, date_of_birth, place_of_birth, паспорт, инн, снилс,`
- L202: `### Ключевое слово: `date_of_birth` (2 совпадений)`
- L204: `- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"``
- L205: `- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",``
- L210: `- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"``
- L215: `- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"``
- L220: `- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"``
- L225: `- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"``
- L226: `- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",``
- L231: `- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",``
- L235: `- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"``
- L250: `- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",``
- L255: `- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",``
- L268: `- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",``

### Ключевое слово: `inn` (15 совпадений)

- L7: `Ключевые слова: passport, passport_number, inn, snils, address,`
- L200: `- L102: `"Ключевые слова: passport, passport_number, inn, snils, address,",``
- L204: `- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"``
- L207: `### Ключевое слово: `inn` (3 совпадений)`
- L209: `- L21: `# "running" matching "inn").``
- L210: `- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"``
- L211: `- L102: `"Ключевые слова: passport, passport_number, inn, snils, address,",``
- L215: `- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"``
- L216: `- L102: `"Ключевые слова: passport, passport_number, inn, snils, address,",``
- L220: `- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"``
- L221: `- L102: `"Ключевые слова: passport, passport_number, inn, snils, address,",``
- L225: `- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"``
- L235: `- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"``
- L236: `- L102: `"Ключевые слова: passport, passport_number, inn, snils, address,",``
- L459: `- Хардкод callback_data с `passport`, `inn`, `address` — **не найдено**.`

### Ключевое слово: `passport` (84 совпадений)

- L7: `Ключевые слова: passport, passport_number, inn, snils, address,`
- L23: `### Ключевое слово: `passport` (2 совпадений)`
- L25: `- L33: `passport:``
- L26: `- L36: `name_en: "🛂 Foreign passport"``
- L53: `### Ключевое слово: `passport` (3 совпадений)`
- L55: `- L6: `# allowed countries, passport pattern, and routing keys.``
- L56: `- L55: `# ── Passport number format (regex) ────────────``
- L57: `- L61: `passport: "ROUTING_PASSPORT"``
- L69: `### Ключевое слово: `passport` (2 совпадений)`
- L71: `- L46: `- id: passport``
- L72: `- L49: `en: "🛂 Foreign passport"``
- L99: `### Ключевое слово: `passport` (1 совпадений)`
- L101: `- L50: `# Passport number format (regex)``
- L136: `### Ключевое слово: `passport` (1 совпадений)`
- L138: `- L99: `code: Unique type code (e.g. ``"visa"``, ``"passport"``).``
- L146: `### Ключевое слово: `passport` (2 совпадений)`
- L148: `- L27: `| `PASSPORT_NUMBER_PATTERN` | `str` | Regex for passport number format |``
- L149: `- L75: `| `passport_number` | Passport number (A-Z, 0-9, -./) | — |``
- L153: `- L75: `| `passport_number` | Passport number (A-Z, 0-9, -./) | — |``
- L176: `### Ключевое слово: `passport` (1 совпадений)`
- L178: `- L4: `description = "Telegram bot for document ordering (visa, passport, apostille)"``
- L186: `### Ключевое слово: `passport` (2 совпадений)`
- L188: `- L201: `| 🛂 Foreign passport                   | 200  | 45   |``
- L189: `- L212: `| `data/business_config.py` | **Active** — demo "consular services" (visa, passport, etc.) |``
- L200: `- L102: `"Ключевые слова: passport, passport_number, inn, snils, address,",``
- L204: `- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"``
- L210: `- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"``
- L211: `- L102: `"Ключевые слова: passport, passport_number, inn, snils, address,",``
- L213: `### Ключевое слово: `passport` (2 совпадений)`
- L215: `- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"``
- L216: `- L102: `"Ключевые слова: passport, passport_number, inn, snils, address,",``
- L220: `- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"``
- L221: `- L102: `"Ключевые слова: passport, passport_number, inn, snils, address,",``
- L225: `- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"``
- L235: `- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"``
- L236: `- L102: `"Ключевые слова: passport, passport_number, inn, snils, address,",``
- L291: `### Ключевое слово: `passport` (6 совпадений)`
- L293: `- L98: `assert "passport" in ROUTING_KEYS``
- L294: `- L164: `assert "passport" in codes``
- L295: `- L191: `assert get_price_pln("passport") == 200``
- L296: `- L219: `assert get_price_eur("passport") == 45``
- L297: `- L227: `"""Verify valid passport numbers match the pattern."""``
- L298: `- L240: `"""Verify invalid passport numbers don't match the pattern."""``
- L302: `### Ключевое слово: `passport` (4 совпадений)`
- L304: `- L20: `docs = [("visa", "Visa application"), ("passport", "Foreign passport")]``
- L304: `- L20: `docs = [("visa", "Visa application"), ("passport", "Foreign passport")]``
- L305: `- L20: `docs = [("visa", "Visa application"), ("passport", "Foreign passport")]``
- L305: `- L20: `docs = [("visa", "Visa application"), ("passport", "Foreign passport")]``
- L306: `- L30: `docs = [("visa", "Visa"), ("passport", "Passport")]``
- L306: `- L30: `docs = [("visa", "Visa"), ("passport", "Passport")]``
- … и ещё 34 совпадений

### Ключевое слово: `passport_number` (56 совпадений)

- L7: `Ключевые слова: passport, passport_number, inn, snils, address,`
- L13: `### Ключевое слово: `passport_number` (1 совпадений)`
- L15: `- L54: `"passport_number",``
- L28: `### Ключевое слово: `passport_number` (2 совпадений)`
- L30: `- L19: `- id: passport_number``
- L31: `- L21: `type: passport_number``
- L74: `### Ключевое слово: `passport_number` (2 совпадений)`
- L76: `- L31: `- id: passport_number``
- L77: `- L33: `type: passport_number``
- L149: `- L75: `| `passport_number` | Passport number (A-Z, 0-9, -./) | — |``
- L151: `### Ключевое слово: `passport_number` (1 совпадений)`
- L153: `- L75: `| `passport_number` | Passport number (A-Z, 0-9, -./) | — |``
- L200: `- L102: `"Ключевые слова: passport, passport_number, inn, snils, address,",``
- L204: `- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"``
- L210: `- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"``
- L211: `- L102: `"Ключевые слова: passport, passport_number, inn, snils, address,",``
- L215: `- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"``
- L216: `- L102: `"Ключевые слова: passport, passport_number, inn, snils, address,",``
- L218: `### Ключевое слово: `passport_number` (2 совпадений)`
- L220: `- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"``
- L221: `- L102: `"Ключевые слова: passport, passport_number, inn, snils, address,",``
- L225: `- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"``
- L235: `- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"``
- L236: `- L102: `"Ключевые слова: passport, passport_number, inn, snils, address,",``
- L279: `### Ключевое слово: `passport_number` (1 совпадений)`
- L281: `- L51: `"passport_number": "буквы A-Z, цифры 0-9, дефис, точка, слеш. Длина 3-30",``
- L391: `- L444: `f = Field("passport", "Number", "passport_number")``
- L392: `- L643: `result = validate_field_value(value, "passport_number", field_name="passport")``
- L393: `- L657: `result = validate_field_value(value, "passport_number", field_name="passport")``
- L395: `### Ключевое слово: `passport_number` (14 совпадений)`
- L397: `- L315: `"FB363261", "passport_number", field_name="passport_number"``
- L397: `- L315: `"FB363261", "passport_number", field_name="passport_number"``
- L398: `- L315: `"FB363261", "passport_number", field_name="passport_number"``
- L398: `- L315: `"FB363261", "passport_number", field_name="passport_number"``
- L399: `- L322: `"AB-123.45 / 678", "passport_number", field_name="passport_number"``
- L399: `- L322: `"AB-123.45 / 678", "passport_number", field_name="passport_number"``
- L400: `- L322: `"AB-123.45 / 678", "passport_number", field_name="passport_number"``
- L400: `- L322: `"AB-123.45 / 678", "passport_number", field_name="passport_number"``
- L401: `- L329: `"AB", "passport_number", field_name="passport_number"``
- L401: `- L329: `"AB", "passport_number", field_name="passport_number"``
- L402: `- L329: `"AB", "passport_number", field_name="passport_number"``
- L402: `- L329: `"AB", "passport_number", field_name="passport_number"``
- L403: `- L336: `"AB@123", "passport_number", field_name="passport_number"``
- L403: `- L336: `"AB@123", "passport_number", field_name="passport_number"``
- L404: `- L336: `"AB@123", "passport_number", field_name="passport_number"``
- L404: `- L336: `"AB@123", "passport_number", field_name="passport_number"``
- L405: `- L342: `"fb363261", "passport_number", field_name="passport_number"``
- L405: `- L342: `"fb363261", "passport_number", field_name="passport_number"``
- L406: `- L342: `"fb363261", "passport_number", field_name="passport_number"``
- L406: `- L342: `"fb363261", "passport_number", field_name="passport_number"``
- … и ещё 6 совпадений

### Ключевое слово: `place_of_birth` (14 совпадений)

- L8: `registration, date_of_birth, place_of_birth, паспорт, инн, снилс,`
- L204: `- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"``
- L205: `- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",``
- L210: `- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"``
- L215: `- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"``
- L220: `- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"``
- L223: `### Ключевое слово: `place_of_birth` (2 совпадений)`
- L225: `- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"``
- L226: `- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",``
- L231: `- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",``
- L235: `- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"``
- L250: `- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",``
- L255: `- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",``
- L268: `- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",``

### Ключевое слово: `registration` (12 совпадений)

- L8: `registration, date_of_birth, place_of_birth, паспорт, инн, снилс,`
- L191: `### Ключевое слово: `registration` (1 совпадений)`
- L193: `- L73: `│   ├── middleware.py         # Logging / user registration middleware``
- L199: `- L24: `r"address|registration)\b",``
- L205: `- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",``
- L226: `- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",``
- L228: `### Ключевое слово: `registration` (2 совпадений)`
- L230: `- L24: `r"address|registration)\b",``
- L231: `- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",``
- L250: `- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",``
- L255: `- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",``
- L268: `- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",``

### Ключевое слово: `snils` (13 совпадений)

- L7: `Ключевые слова: passport, passport_number, inn, snils, address,`
- L200: `- L102: `"Ключевые слова: passport, passport_number, inn, snils, address,",``
- L204: `- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"``
- L210: `- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"``
- L211: `- L102: `"Ключевые слова: passport, passport_number, inn, snils, address,",``
- L215: `- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"``
- L216: `- L102: `"Ключевые слова: passport, passport_number, inn, snils, address,",``
- L220: `- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"``
- L221: `- L102: `"Ключевые слова: passport, passport_number, inn, snils, address,",``
- L225: `- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"``
- L233: `### Ключевое слово: `snils` (2 совпадений)`
- L235: `- L23: `r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"``
- L236: `- L102: `"Ключевые слова: passport, passport_number, inn, snils, address,",``

### Ключевое слово: `адрес` (25 совпадений)

- L9: `адрес, регистрация, дата рождения.`
- L33: `### Ключевое слово: `адрес` (1 совпадений)`
- L35: `- L52: `prompt: "🏠 Адрес проживания"``
- L59: `### Ключевое слово: `адрес` (1 совпадений)`
- L61: `- L34: `usdt: "₿ USDT (TRC20): TXYZ... (адрес кошелька)"``
- L79: `### Ключевое слово: `адрес` (1 совпадений)`
- L81: `- L68: `prompt: "🏠 Адрес проживания"``
- L105: `### Ключевое слово: `адрес` (1 совпадений)`
- L107: `- L181: `"usdt": "₿ USDT (TRC20): TXYZ... (адрес кошелька)",``
- L115: `### Ключевое слово: `адрес` (1 совпадений)`
- L117: `- L41: `"🏠 Полный адрес проживания (индекс, город, улица, квартира)",``
- L157: `### Ключевое слово: `адрес` (1 совпадений)`
- L159: `- L21: `5. filling_delivery — ввод данных для доставки (ФИО, телефон, адрес)``
- L238: `### Ключевое слово: `адрес` (2 совпадений)`
- L240: `- L28: `r"\b(паспорт\w*|инн\b|снилс\w*|адрес\w*|регистраци\w*|дата\s+рождения)\b",``
- L241: `- L104: `"адрес, регистрация, дата рождения.",``
- L245: `- L104: `"адрес, регистрация, дата рождения.",``
- L249: `- L28: `r"\b(паспорт\w*|инн\b|снилс\w*|адрес\w*|регистраци\w*|дата\s+рождения)\b",``
- L254: `- L28: `r"\b(паспорт\w*|инн\b|снилс\w*|адрес\w*|регистраци\w*|дата\s+рождения)\b",``
- L259: `- L28: `r"\b(паспорт\w*|инн\b|снилс\w*|адрес\w*|регистраци\w*|дата\s+рождения)\b",``
- L263: `- L104: `"адрес, регистрация, дата рождения.",``
- L267: `- L28: `r"\b(паспорт\w*|инн\b|снилс\w*|адрес\w*|регистраци\w*|дата\s+рождения)\b",``
- L450: `- Единственные совпадения — «адрес доставки» / "Delivery address" в ключах`
- L451: ``delivery_prompt` и `delivery_format_error`. Это адрес **доставки посылки**`
- L452: `(логистика: ФИО получателя, телефон, постамат), а не адрес регистрации/проживания`

### Ключевое слово: `дата рождения` (16 совпадений)

- L9: `адрес, регистрация, дата рождения.`
- L37: `### Ключевое слово: `дата рождения` (3 совпадений)`
- L39: `- L17: `prompt: "🎂 Дата рождения (ДД.ММ.ГГГГ)"``
- L40: `- L45: `prompt: "🎂 Дата рождения (ДД.ММ.ГГГГ)"``
- L41: `- L68: `prompt: "🎂 Дата рождения (ДД.ММ.ГГГГ)"``
- L83: `### Ключевое слово: `дата рождения` (3 совпадений)`
- L85: `- L29: `prompt: "🎂 Дата рождения (ДД.ММ.ГГГГ)"``
- L86: `- L61: `prompt: "🎂 Дата рождения (ДД.ММ.ГГГГ)"``
- L87: `- L89: `prompt: "🎂 Дата рождения (ДД.ММ.ГГГГ)"``
- L119: `### Ключевое слово: `дата рождения` (2 совпадений)`
- L121: `- L37: `Field("birth_date", "🎂 Дата рождения (ДД.ММ.ГГГГ)", "date"),``
- L122: `- L93: `Field("birth_date", "🎂 Дата рождения", "date"),``
- L241: `- L104: `"адрес, регистрация, дата рождения.",``
- L243: `### Ключевое слово: `дата рождения` (1 совпадений)`
- L245: `- L104: `"адрес, регистрация, дата рождения.",``
- L263: `- L104: `"адрес, регистрация, дата рождения.",``

### Ключевое слово: `инн` (14 совпадений)

- L8: `registration, date_of_birth, place_of_birth, паспорт, инн, снилс,`
- L205: `- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",``
- L226: `- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",``
- L231: `- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",``
- L240: `- L28: `r"\b(паспорт\w*|инн\b|снилс\w*|адрес\w*|регистраци\w*|дата\s+рождения)\b",``
- L247: `### Ключевое слово: `инн` (2 совпадений)`
- L249: `- L28: `r"\b(паспорт\w*|инн\b|снилс\w*|адрес\w*|регистраци\w*|дата\s+рождения)\b",``
- L250: `- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",``
- L254: `- L28: `r"\b(паспорт\w*|инн\b|снилс\w*|адрес\w*|регистраци\w*|дата\s+рождения)\b",``
- L255: `- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",``
- L259: `- L28: `r"\b(паспорт\w*|инн\b|снилс\w*|адрес\w*|регистраци\w*|дата\s+рождения)\b",``
- L267: `- L28: `r"\b(паспорт\w*|инн\b|снилс\w*|адрес\w*|регистраци\w*|дата\s+рождения)\b",``
- L268: `- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",``
- L449: `- Ключей с «паспорт», «ИНН», «СНИЛС», «регистрация» — **не найдено**.`

### Ключевое слово: `паспорт` (14 совпадений)

- L8: `registration, date_of_birth, place_of_birth, паспорт, инн, снилс,`
- L205: `- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",``
- L226: `- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",``
- L231: `- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",``
- L240: `- L28: `r"\b(паспорт\w*|инн\b|снилс\w*|адрес\w*|регистраци\w*|дата\s+рождения)\b",``
- L249: `- L28: `r"\b(паспорт\w*|инн\b|снилс\w*|адрес\w*|регистраци\w*|дата\s+рождения)\b",``
- L250: `- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",``
- L252: `### Ключевое слово: `паспорт` (2 совпадений)`
- L254: `- L28: `r"\b(паспорт\w*|инн\b|снилс\w*|адрес\w*|регистраци\w*|дата\s+рождения)\b",``
- L255: `- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",``
- L259: `- L28: `r"\b(паспорт\w*|инн\b|снилс\w*|адрес\w*|регистраци\w*|дата\s+рождения)\b",``
- L267: `- L28: `r"\b(паспорт\w*|инн\b|снилс\w*|адрес\w*|регистраци\w*|дата\s+рождения)\b",``
- L268: `- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",``
- L449: `- Ключей с «паспорт», «ИНН», «СНИЛС», «регистрация» — **не найдено**.`

### Ключевое слово: `паспорта` (8 совпадений)

- L43: `### Ключевое слово: `паспорта` (1 совпадений)`
- L45: `- L20: `prompt: "🛂 Номер паспорта (серия и номер)"``
- L89: `### Ключевое слово: `паспорта` (1 совпадений)`
- L91: `- L32: `prompt: "🛂 Номер паспорта (серия и номер)"``
- L124: `### Ключевое слово: `паспорта` (1 совпадений)`
- L126: `- L38: `Field("pesel", "🆔 PESEL или серия/номер паспорта", "text"),``
- L436: `### Ключевое слово: `паспорта` (1 совпадений)`
- L438: `- L306: `"❌ Неверный формат номера паспорта. "``

### Ключевое слово: `паспорте` (4 совпадений)

- L47: `### Ключевое слово: `паспорте` (1 совпадений)`
- L49: `- L13: `prompt: "👤 ФИО (как в паспорте)"``
- L93: `### Ключевое слово: `паспорте` (1 совпадений)`
- L95: `- L25: `prompt: "👤 ФИО (как в паспорте)"``

### Ключевое слово: `регистраци` (6 совпадений)

- L240: `- L28: `r"\b(паспорт\w*|инн\b|снилс\w*|адрес\w*|регистраци\w*|дата\s+рождения)\b",``
- L249: `- L28: `r"\b(паспорт\w*|инн\b|снилс\w*|адрес\w*|регистраци\w*|дата\s+рождения)\b",``
- L254: `- L28: `r"\b(паспорт\w*|инн\b|снилс\w*|адрес\w*|регистраци\w*|дата\s+рождения)\b",``
- L257: `### Ключевое слово: `регистраци` (1 совпадений)`
- L259: `- L28: `r"\b(паспорт\w*|инн\b|снилс\w*|адрес\w*|регистраци\w*|дата\s+рождения)\b",``
- L267: `- L28: `r"\b(паспорт\w*|инн\b|снилс\w*|адрес\w*|регистраци\w*|дата\s+рождения)\b",``

### Ключевое слово: `регистрации` (4 совпадений)

- L414: `### Ключевое слово: `регистрации` (2 совпадений)`
- L416: `- L24: `Middleware для автоматической регистрации пользователей.``
- L417: `- L30: `Позволяет избежать дублирования кода регистрации в каждом хендлере``
- L452: `(логистика: ФИО получателя, телефон, постамат), а не адрес регистрации/проживания`

### Ключевое слово: `регистрация` (8 совпадений)

- L9: `адрес, регистрация, дата рождения.`
- L241: `- L104: `"адрес, регистрация, дата рождения.",``
- L245: `- L104: `"адрес, регистрация, дата рождения.",``
- L261: `### Ключевое слово: `регистрация` (1 совпадений)`
- L263: `- L104: `"адрес, регистрация, дата рождения.",``
- L419: `### Ключевое слово: `регистрация` (1 совпадений)`
- L421: `- L5: `- RegistrationMiddleware: автоматическая регистрация пользователей``
- L449: `- Ключей с «паспорт», «ИНН», «СНИЛС», «регистрация» — **не найдено**.`

### Ключевое слово: `снилс` (14 совпадений)

- L8: `registration, date_of_birth, place_of_birth, паспорт, инн, снилс,`
- L205: `- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",``
- L226: `- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",``
- L231: `- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",``
- L240: `- L28: `r"\b(паспорт\w*|инн\b|снилс\w*|адрес\w*|регистраци\w*|дата\s+рождения)\b",``
- L249: `- L28: `r"\b(паспорт\w*|инн\b|снилс\w*|адрес\w*|регистраци\w*|дата\s+рождения)\b",``
- L250: `- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",``
- L254: `- L28: `r"\b(паспорт\w*|инн\b|снилс\w*|адрес\w*|регистраци\w*|дата\s+рождения)\b",``
- L255: `- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",``
- L259: `- L28: `r"\b(паспорт\w*|инн\b|снилс\w*|адрес\w*|регистраци\w*|дата\s+рождения)\b",``
- L265: `### Ключевое слово: `снилс` (2 совпадений)`
- L267: `- L28: `r"\b(паспорт\w*|инн\b|снилс\w*|адрес\w*|регистраци\w*|дата\s+рождения)\b",``
- L268: `- L103: `"registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",``
- L449: `- Ключей с «паспорт», «ИНН», «СНИЛС», «регистрация» — **не найдено**.`

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

## `migrations/versions/a1b2c3d4e5f6_remove_personal_data_fields.py`

### Ключевое слово: `date_of_birth` (3 совпадений)

- L34: `"date_of_birth",`
- L41: `"date_of_birth",`
- L48: `"date_of_birth",`

### Ключевое слово: `inn` (3 совпадений)

- L31: `"inn",`
- L38: `"inn",`
- L45: `"inn",`

### Ключевое слово: `passport_number` (3 совпадений)

- L30: `"passport_number",`
- L37: `"passport_number",`
- L44: `"passport_number",`

### Ключевое слово: `snils` (3 совпадений)

- L32: `"snils",`
- L39: `"snils",`
- L46: `"snils",`

## `README.md`

### Ключевое слово: `address` (1 совпадений)

- L27: `- 🚚 **Delivery / pickup** — enter courier address or choose self-pickup`

### Ключевое слово: `registration` (1 совпадений)

- L78: `│   ├── middleware.py         # Logging / user registration middleware`

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

## `tests/conftest.py`

### Ключевое слово: `address` (1 совпадений)

- L79: `# Try connecting to the first resolved address`

## `tests/test_crud.py`

### Ключевое слово: `address` (1 совпадений)

- L129: `"address": "Test St 1",`

## `tests/test_order_coverage.py`

### Ключевое слово: `address` (5 совпадений)

- L6: `- save_delivery (delivery address input)`
- L450: `"""Tests for delivery address input handler."""`
- L502: `assert session["delivery"]["address"] == "Main Street 1, Warsaw"`
- L531: `"""Verify missing address line defaults to '-'."""`
- L543: `assert session["delivery"]["address"] == "-"`

## `tests/test_security.py`

### Ключевое слово: `address` (3 совпадений)

- L155: `"address": "St (1)",`
- L234: `"address": truncate_for_storage(raw_lines[3]),`
- L241: `assert delivery["address"] == "St (1), Apt#2"`

## `tests/test_services.py`

### Ключевое слово: `address` (2 совпадений)

- L110: `"address": "Street 1",`
- L138: `"address": "Main 1",`

## `tests/test_telegram_connectivity.py`

### Ключевое слово: `address` (1 совпадений)

- L51: `"""Verify that ``api.telegram.org`` resolves to at least one IP address.`

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

## 📊 Итоговая статистика

- Файлов с совпадениями: **21**
- Всего совпадений: **460**
