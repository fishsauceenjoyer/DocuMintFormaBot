"""Field definition used by document templates."""

from typing import List, Optional


class Field:
    """Single input field definition inside a document template.

    Attributes:
        id:         Unique field identifier (e.g. "full_name").
        prompt:     Question shown to the customer.
        type:       Field type — "text", "date", "email", "phone",
                    "optional_text", "choice", or "integer".
        optional:   Whether the field can be left empty.
        max_length: Maximum allowed length. If *None*, uses default per type.
        choices:    For ``type="choice"`` — list of allowed values.
        min_value:  For ``type="integer"`` — minimum allowed value.
        max_value:  For ``type="integer"`` — maximum allowed value.
    """

    def __init__(
        self,
        id: str,
        prompt: str,
        field_type: str = "text",
        optional: bool = False,
        max_length: Optional[int] = None,
        choices: Optional[List[str]] = None,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
    ):
        self.id = id
        self.prompt = prompt
        self.type = field_type
        self.optional = optional
        self.max_length = max_length
        self.choices = choices
        self.min_value = min_value
        self.max_value = max_value

    def type_hint(self) -> str:
        """Return a short type/length hint shown to the user under the prompt."""
        from data.business_config import ALLOWED_COUNTRIES_HINT

        hints = {
            "text": f"текст, макс. {self.max_length or 255} символов",
            "date": "дата в формате ДД.ММ.ГГГГ (год 1900-текущий)",
            "email": "email, макс. 255 символов",
            "phone": "телефон, макс. 20 символов",
            "optional_text": f"текст, макс. {self.max_length or 255} символов, необязательно",
            "passport_number": "буквы A-Z, цифры 0-9, дефис, точка, слеш. Длина 3-30",
            "country_code": f"код страны (2 буквы). Допустимые: {ALLOWED_COUNTRIES_HINT}",
        }
        if self.type == "choice":
            options = ", ".join(self.choices) if self.choices else "—"
            return f"выберите один из вариантов: {options}"
        if self.type == "integer":
            if self.min_value is not None and self.max_value is not None:
                return f"целое число от {self.min_value} до {self.max_value}"
            if self.min_value is not None:
                return f"целое число, минимум {self.min_value}"
            if self.max_value is not None:
                return f"целое число, максимум {self.max_value}"
            return "целое число"
        return hints.get(self.type, f"текст, макс. 255 символов")
