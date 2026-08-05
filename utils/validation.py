"""Field value validation and sanitization.

Provides validation logic for user input fields: type checking, length limits,
and sanitization against SQL injection, XSS and other malicious payloads.
"""

import logging
import re
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# ── Dangerous patterns ────────────────────────────────────────────────
# SQL injection patterns
SQL_INJECTION_PATTERNS = [
    r"(?i)\bSELECT\b.*\bFROM\b",
    r"(?i)\bINSERT\b.*\bINTO\b",
    r"(?i)\bUPDATE\b.*\bSET\b",
    r"(?i)\bDELETE\b.*\bFROM\b",
    r"(?i)\bDROP\b.*\bTABLE\b",
    r"(?i)\bALTER\b.*\bTABLE\b",
    r"(?i)\bCREATE\b.*\bTABLE\b",
    r"(?i)\bTRUNCATE\b",
    r"(?i)\bEXEC\b",
    r"(?i)\bEXECUTE\b",
    r"(?i)\bUNION\b.*\bSELECT\b",
    r"(?i)\bOR\s+1\s*=\s*1\b",
    r"--",
    r"\/\*",
    r"\*\/",
    r"(?i)\bLOAD_FILE\b",
    r"(?i)\bINTO\s+OUTFILE\b",
    r"(?i)\bCHAR\s*\(",
    r"(?i)\bCONCAT\b",
    r"(?i)\bINFORMATION_SCHEMA\b",
]

# XSS patterns
XSS_PATTERNS = [
    r"<script[^>]*>",
    r"<\/script>",
    r"<iframe[^>]*>",
    r"<\/iframe>",
    r"on\w+\s*=",
    r"javascript\s*:",
    r"<svg[^>]*>",
    r"<img[^>]*>",
    r"<body[^>]*>",
    r"<input[^>]*>",
    r"<form[^>]*>",
    r"<embed[^>]*>",
    r"<object[^>]*>",
    r"<link[^>]*>",
    r"<style[^>]*>",
    r"<applet[^>]*>",
    r"<meta[^>]*>",
    r"<base[^>]*>",
    r"<marquee[^>]*>",
    r"vbscript\s*:",
    r"data\s*:",
]

# NoSQL injection patterns (MongoDB operators in JSON-like input)
NOSQL_INJECTION_PATTERNS = [
    r"\$gt\b",
    r"\$lt\b",
    r"\$ne\b",
    r"\$eq\b",
    r"\$regex\b",
    r"\$where\b",
    r"\$exists\b",
    r"\$in\b",
    r"\$nin\b",
    r"\$or\b",
    r"\$and\b",
    r"\$not\b",
]

# Command injection patterns
CMD_INJECTION_PATTERNS = [
    r"[|;&`$]",
    r"\(\)\s*\{",
    r"(?i)\bcurl\b",
    r"(?i)\bwget\b",
    r"(?i)\bping\b",
    r"(?i)\bnc\b",
    r"(?i)\bbash\b",
    r"(?i)\bsh\b",
    r"(?i)\bcmd\b",
    r"(?i)\bpowershell\b",
    r"(?i)\bpython\b",
    r"(?i)\bperl\b",
    r"(?i)\bruby\b",
    r"(?i)\beval\b",
    r"(?i)\bexec\b",
    r"(?i)\bsystem\b",
    r"(?i)\bpassthru\b",
    r"(?i)\bshell_exec\b",
    r"(?i)\bpopen\b",
    r"(?i)\bproc_open\b",
    r"(?i)\bassert\b",
    r"\$\{",
    r"`[^`]*`",
]

# ── Date format validation ────────────────────────────────────────────
DATE_PATTERN = re.compile(r"^\d{1,2}\.\d{1,2}\.\d{4}$")
PHONE_PATTERN = re.compile(r"^[\+\d\s\-\(\)]{6,20}$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Import config-based constants at runtime to avoid circular imports
_imported_config = None


def _get_config():
    """Lazy-import business config constants."""
    global _imported_config
    if _imported_config is None:
        from data.business_config import (
            ALLOWED_COUNTRIES_HINT,
            DESTINATION_COUNTRIES,
            PASSPORT_NUMBER_PATTERN,
        )

        _imported_config = {
            "DESTINATION_COUNTRIES": DESTINATION_COUNTRIES,
            "ALLOWED_COUNTRIES_HINT": ALLOWED_COUNTRIES_HINT,
            "PASSPORT_NUMBER_PATTERN": PASSPORT_NUMBER_PATTERN,
        }
    return _imported_config


@dataclass
class ValidationResult:
    """Result of a field validation.

    Attributes:
        is_valid: Whether the value passed all checks.
        error_message: Human-readable error description (empty if valid).
        sanitized_value: Cleaned value safe for storage.
    """

    is_valid: bool
    error_message: str = ""
    sanitized_value: str = ""


def sanitize_text(value: str) -> str:
    """Remove leading/trailing whitespace and normalize internal whitespace.

    Args:
        value: Raw user input.

    Returns:
        Cleaned string.
    """
    return " ".join(value.split())


def has_malicious_patterns(value: str) -> Optional[str]:
    """Check if the value contains malicious patterns.

    Args:
        value: The string to check.

    Returns:
        A description of the first malicious pattern found, or *None* if safe.
    """
    # Check SQL injection
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, value):
            return f"Обнаружен потенциально опасный SQL-синтаксис"

    # Check XSS
    for pattern in XSS_PATTERNS:
        if re.search(pattern, value):
            return f"Обнаружен потенциально опасный HTML/JavaScript-синтаксис"

    # Check NoSQL injection
    for pattern in NOSQL_INJECTION_PATTERNS:
        if re.search(pattern, value):
            return f"Обнаружен потенциально опасный синтаксис"

    # Check command injection
    for pattern in CMD_INJECTION_PATTERNS:
        if re.search(pattern, value):
            return f"Обнаружен потенциально опасный командный синтаксис"

    return None


def validate_field_value(
    value: str,
    field_type: str = "text",
    max_length: Optional[int] = None,
    field_name: str = "",
    choices: Optional[list] = None,
    min_value: Optional[int] = None,
    max_value: Optional[int] = None,
) -> ValidationResult:
    """Validate a single field value for type, length and malicious content.

    Args:
        value: Raw user input string.
        field_type: Expected type ("text", "date", "email", "phone", "optional_text",
            "choice", "integer").
        max_length: Maximum allowed string length. If *None*, uses defaults per type.
        field_name: Human-readable field name for error messages.
        choices: For ``field_type="choice"`` — list of allowed values.
        min_value: For ``field_type="integer"`` — minimum allowed value.
        max_value: For ``field_type="integer"`` — maximum allowed value.

    Returns:
        A :class:`ValidationResult` with the outcome.
    """
    if not value:
        return ValidationResult(
            is_valid=False,
            error_message="❌ Поле не может быть пустым.",
            sanitized_value="",
        )

    # Sanitize
    cleaned = sanitize_text(value)

    # Re-check after sanitization: whitespace-only input becomes empty
    if not cleaned:
        return ValidationResult(
            is_valid=False,
            error_message="❌ Поле не может быть пустым.",
            sanitized_value="",
        )

    # Check length
    if max_length is None:
        max_length = _get_default_max_length(field_type)

    if len(cleaned) > max_length:
        return ValidationResult(
            is_valid=False,
            error_message=(
                f"❌ Слишком длинное значение. "
                f"Максимум {max_length} символов, "
                f"вы ввели {len(cleaned)}."
            ),
            sanitized_value=cleaned[:max_length],
        )

    # Type-specific validation
    if field_type == "date":
        if not DATE_PATTERN.match(cleaned):
            return ValidationResult(
                is_valid=False,
                error_message="❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ (например, 31.12.2024).",
                sanitized_value=cleaned,
            )
        # Validate date is real
        parts = cleaned.split(".")
        _ = int(parts[0])
        _ = int(parts[1])
        year = int(parts[2])
        from datetime import datetime, timezone

        current_year = datetime.now(timezone.utc).year
        if year < 1900 or year > current_year:
            return ValidationResult(
                is_valid=False,
                error_message=f"❌ Год должен быть между 1900 и {current_year}.",
                sanitized_value=cleaned,
            )
        # Calendar correctness first: catches 31.02, 30.02, 29.02 non-leap,
        # 00.xx, 32.xx, etc. in one check via datetime.strptime.
        try:
            datetime.strptime(cleaned, "%d.%m.%Y")
        except ValueError:
            return ValidationResult(
                is_valid=False,
                error_message="❌ Такой даты не существует. Проверьте день и месяц.",
                sanitized_value=cleaned,
            )

    elif field_type == "email":
        if not EMAIL_PATTERN.match(cleaned):
            return ValidationResult(
                is_valid=False,
                error_message="❌ Неверный формат email. Используйте example@domain.com.",
                sanitized_value=cleaned,
            )

    elif field_type == "phone":
        if not PHONE_PATTERN.match(cleaned):
            return ValidationResult(
                is_valid=False,
                error_message="❌ Неверный формат телефона. Используйте +XXXXXXXXXXX.",
                sanitized_value=cleaned,
            )

    elif field_type == "passport_number":
        cfg = _get_config()
        pattern = re.compile(cfg["PASSPORT_NUMBER_PATTERN"])
        if not pattern.match(cleaned.upper()):
            return ValidationResult(
                is_valid=False,
                error_message=(
                    "❌ Неверный формат номера паспорта. "
                    "Допустимы: буквы A-Z, цифры 0-9, пробел, дефис, точка, слеш. "
                    "Длина от 3 до 30 символов."
                ),
                sanitized_value=cleaned.upper(),
            )
        cleaned = cleaned.upper()

    elif field_type == "country_code":
        cfg = _get_config()
        allowed = cfg["DESTINATION_COUNTRIES"]
        code = cleaned.upper()
        if len(code) != 2 or code not in allowed:
            hint = cfg["ALLOWED_COUNTRIES_HINT"]
            return ValidationResult(
                is_valid=False,
                error_message=(
                    f"❌ Неверный код страны. " f"Допустимые страны: {hint}"
                ),
                sanitized_value=code,
            )
        cleaned = code

    elif field_type == "choice":
        if not choices:
            return ValidationResult(
                is_valid=False,
                error_message="❌ Для этого поля не заданы допустимые варианты.",
                sanitized_value=cleaned,
            )
        # Case-insensitive match; store the canonical value from choices.
        lowered = {str(c).lower(): str(c) for c in choices}
        match = lowered.get(cleaned.lower())
        if match is None:
            allowed = ", ".join(str(c) for c in choices)
            return ValidationResult(
                is_valid=False,
                error_message=f"❌ Недопустимое значение. Выберите одно из: {allowed}",
                sanitized_value=cleaned,
            )
        cleaned = match

    elif field_type == "integer":
        try:
            int_value = int(cleaned)
        except ValueError:
            return ValidationResult(
                is_valid=False,
                error_message="❌ Введите целое число.",
                sanitized_value=cleaned,
            )
        if min_value is not None and int_value < min_value:
            return ValidationResult(
                is_valid=False,
                error_message=f"❌ Минимальное значение: {min_value}.",
                sanitized_value=cleaned,
            )
        if max_value is not None and int_value > max_value:
            return ValidationResult(
                is_valid=False,
                error_message=f"❌ Максимальное значение: {max_value}.",
                sanitized_value=cleaned,
            )
        cleaned = str(int_value)

    # Check for malicious patterns (only for text fields where injection is possible)
    if field_type in ("text", "optional_text"):
        malicious = has_malicious_patterns(cleaned)
        if malicious:
            logger.warning(
                f"Malicious content detected in field '{field_name}': {malicious}"
            )
            return ValidationResult(
                is_valid=False,
                error_message=(
                    f"❌ В введённых данных обнаружены недопустимые символы. "
                    f"Пожалуйста, уберите спецсимволы и попробуйте снова."
                ),
                sanitized_value=cleaned,
            )

    return ValidationResult(is_valid=True, sanitized_value=cleaned)


def _get_default_max_length(field_type: str) -> int:
    """Return the default max length for a field type based on DB column sizes."""
    if field_type == "date":
        return 10  # DD.MM.YYYY
    elif field_type == "email":
        return 255  # delivery_email in Order model
    elif field_type == "phone":
        return 20  # delivery_phone in Order model
    elif field_type == "optional_text":
        return 255
    else:
        return 255  # default String(255) in models
