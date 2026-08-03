"""Field definition used by document templates."""


class Field:
    """Single input field definition inside a document template.

    Attributes:
        id:         Unique field identifier (e.g. "full_name").
        prompt:     Question shown to the customer.
        type:       Field type — "text", "date", "email", "phone",
                    or "optional_text".
        optional:   Whether the field can be left empty.
        max_length: Maximum allowed length. If *None*, uses default per type.
    """

    def __init__(
        self,
        id: str,
        prompt: str,
        field_type: str = "text",
        optional: bool = False,
        max_length: int | None = None,
    ):
        self.id = id
        self.prompt = prompt
        self.type = field_type
        self.optional = optional
        self.max_length = max_length

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
        return hints.get(self.type, f"текст, макс. 255 символов")
