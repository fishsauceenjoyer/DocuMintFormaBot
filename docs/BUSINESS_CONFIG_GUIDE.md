# Business Configuration Guide

This document is the **mandatory reference** for any AI model writing or modifying
code, tests, or prompts in this repository. Read it *before* writing any code.

## Single Source of Truth

All domain-specific business data lives in **`data/business_config.py`**. This file
is the contract between the bot logic, the database schema, and the validators.

Document templates (fields, prices, names) are loaded from
**`config/templates.yaml`** so business users can edit them without touching Python
code. The YAML loader in `data/business_config.py` parses that file into the same
structure the code expects.

## Key Constants

| Constant | Type | Purpose |
|----------|------|---------|
| `DOCUMENT_TEMPLATES` | `Dict[str, Dict]` | Loaded from YAML; each template has `name_ru`, `name_uk`, `name_en`, `price_pln`, `price_eur`, `fields`, `example` |
| `ROUTING_KEYS` | `Dict[str, str]` | Maps document code → env var name for manager chat routing |
| `DELIVERY_PRICE_PLN` | `int` | Delivery price in PLN |
| `DELIVERY_PRICE_EUR` | `int` | Delivery price in EUR |
| `PAYMENT_DETAILS` | `Dict[str, str]` | Payment instructions per method (`blik`, `uah`, `usdt`) |
| `SUPPORTED_CURRENCIES` | `List[str]` | `["EUR", "PLN"]` |
| `COUNTRY_CODES` / `DESTINATION_COUNTRIES` | `Dict`/`List` | Allowed destination countries for visa fields |
| `PASSPORT_NUMBER_PATTERN` | `str` | Regex for passport number format |

Helper functions: `get_template(doc_code)`, `get_all_templates()`,
`get_price_pln(doc_code)`, `get_price_eur(doc_code)`.

## Database Schema Alignment

`db/models.py` defines the SQLAlchemy tables. When storing user input, **respect the
column sizes** — otherwise PostgreSQL raises `DataError`:

| Order column | DB type | Max length |
|--------------|---------|------------|
| `delivery_name` | `String(255)` | 255 |
| `delivery_phone` | `String(20)` | 20 |
| `delivery_email` | `String(255)` | 255 |
| `delivery_paczkomat` | `String(100)` | 100 |
| `payment_method` | `String(20)` | 20 |
| `payment_proof_file_id` | `String(255)` | 255 |

The validators in `utils/validation.py` already mirror these limits
(`_get_default_max_length`). The `save_delivery` handler in `handlers/order.py`
uses `truncate_for_storage` with the matching per-field limits.

## Rules for AI Models

1. **Never hardcode** document types, prices, routing keys, or payment details in
   handlers/tests — always import from `data/business_config.py`.
2. **Never change** `data/business_config_original.py` — it is a frozen reference
   file used to restore the original business data.
3. **Keep types aligned**: if you add a document template in
   `config/templates.yaml`, ensure `ROUTING_KEYS` (and `.env` vars) cover it, and
   that tests exercise it.
4. **Currencies**: the bot supports `EUR` and `PLN` only. Any new currency requires
   updating `SUPPORTED_CURRENCIES`, `config.py`, and `services/pricing.py`.
5. **Language coverage**: every user-facing string must exist in `locales/ru.json`,
   `locales/en.json`, `locales/uk.json`.

## Common Pitfalls

- Forgetting that `criminal_record_check` and other multi-word codes break naive
  `split("_")[1]` parsing — use `split("_", 1)`.
- Hardcoding a price that differs from `config/templates.yaml`.
- Adding a field type without a corresponding branch in `utils/validation.py`.
- Storing delivery values longer than the DB column permits (see table above).