"""
Шаблоны документов с динамическими полями для заполнения (только русский).

Содержит описание типов документов (санэпид, BHP, психотесты, PESEL),
их полей для заполнения и вспомогательные функции для работы с шаблонами.
"""

from typing import Any, Dict, List, Optional


class Field:
    """
    Описание одного поля в шаблоне документа.

    Каждое поле содержит:
        - id: уникальный идентификатор поля (например, "full_name", "birth_date")
        - prompt: текст подсказки на русском языке
        - type: тип поля (text, date, optional_text)
        - optional: является ли поле необязательным
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


DOCUMENT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "sanepid": {
        "name": "📑 Санэпид / СК",
        "price": 150,
        "fields": [
            Field("date", "📅 Дата изготовления (не выходной/праздник)", "date"),
            Field("full_name", "👤 Фамилия и имя как в загранпаспорте", "text"),
            Field("birth_date", "🎂 Дата рождения (ДД.ММ.ГГГГ)", "date"),
            Field("pesel", "🆔 PESEL или серия/номер паспорта", "text"),
            Field(
                "address",
                "🏠 Полный адрес проживания (индекс, город, улица, квартира)",
                "text",
            ),
            Field(
                "workplace",
                "🏢 Место работы (если нет - поставьте '-')",
                "optional_text",
                optional=True,
            ),
            Field(
                "position",
                "💼 Должность (если нет - поставьте '-')",
                "optional_text",
                optional=True,
            ),
        ],
        "example": (
            "02.01.2025\nOlena Romenko\n18.11.1996\nFB363261\n"
            "Kraków, 89-510, ul. Senkiewicza 1/12\nROXI SP.Z O.O.\nSprzedawca"
        ),
    },
    "bhp": {
        "name": "⛑ BHP",
        "price": 100,
        "fields": [
            Field("full_name", "👤 ФИО", "text"),
            Field("pesel", "🆔 PESEL", "text"),
            Field("position", "💼 Должность", "text"),
        ],
    },
    "psychotests": {
        "name": "🚕 Психотесты для водителей",
        "price": 120,
        "fields": [
            Field("full_name", "👤 ФИО водителя", "text"),
            Field("license_number", "📘 Номер удостоверения", "text"),
        ],
    },
    "pesel": {
        "name": "🧧 PESEL без присутствия",
        "price": 200,
        "fields": [
            Field("full_name", "👤 ФИО", "text"),
            Field("birth_date", "🎂 Дата рождения", "date"),
            Field("parents_names", "👪 Имена родителей", "text"),
        ],
    },
}


def get_template(doc_type: str) -> Optional[Dict[str, Any]]:
    """
    Возвращает шаблон документа по его коду.

    Args:
        doc_type: Код типа документа (sanepid, bhp, psychotests, pesel).

    Returns:
        Словарь с данными шаблона (название, цена, поля)
        или None, если тип документа не найден.
    """
    return DOCUMENT_TEMPLATES.get(doc_type)


def get_all_templates() -> List[tuple]:
    """
    Возвращает список всех доступных типов документов.

    Используется для создания кнопок выбора документа.
    Формат: [(код_типа, название), ...]

    Returns:
        Список кортежей (код_типа, название_документа).
    """
    return [(k, v["name"]) for k, v in DOCUMENT_TEMPLATES.items()]


def get_template_price(doc_type: str) -> int:
    """
    Возвращает цену документа по его коду.

    Args:
        doc_type: Код типа документа.

    Returns:
        Цена в злотых (int) или 0, если тип не найден.
    """
    template = get_template(doc_type)
    return template["price"] if template else 0