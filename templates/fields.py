"""Field definition used by document templates."""


class Field:
    """Single input field definition inside a document template.

    Attributes:
        id:       Unique field identifier (e.g. "full_name").
        prompt:   Question shown to the customer.
        type:     Field type — "text", "date", or "optional_text".
        optional: Whether the field can be left empty.
    """

    def __init__(
        self,
        id: str,
        prompt: str,
        field_type: str = "text",
        optional: bool = False,
    ):
        self.id = id
        self.prompt = prompt
        self.type = field_type
        self.optional = optional
