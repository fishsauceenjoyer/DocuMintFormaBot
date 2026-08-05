"""Tests for the demo poster-printing business config.

Verifies:
    - All three poster services are present in DOCUMENT_TEMPLATES
    - Each template has size, color, quantity fields with correct types/choices/range
    - Validation accepts valid choices/integers and rejects invalid ones
    - Price calculation (base + size/color surcharges) works correctly
"""

import pytest

from data.business_config_demo import (
    DOCUMENT_TEMPLATES,
    POSTER_BASE_PRICE_EUR,
    POSTER_BASE_PRICE_PLN,
    get_all_templates,
    get_price_eur,
    get_price_pln,
    get_template,
)
from utils.validation import validate_field_value

POSTER_CODES = ["poster_terminator1", "poster_terminator2", "poster_predator"]


class TestDemoTemplates:
    """Verify the demo config exposes the three poster services."""

    def test_all_three_services_present(self):
        """All three poster codes must be in DOCUMENT_TEMPLATES."""
        for code in POSTER_CODES:
            assert code in DOCUMENT_TEMPLATES, f"{code} missing from templates"

    def test_get_all_templates_contains_posters(self):
        """get_all_templates must return all three poster codes."""
        codes = [code for code, _ in get_all_templates()]
        for code in POSTER_CODES:
            assert code in codes

    def test_get_template_returns_dict(self):
        """get_template returns a dict for each poster code."""
        for code in POSTER_CODES:
            tpl = get_template(code)
            assert tpl is not None
            assert isinstance(tpl, dict)

    def test_template_has_required_keys(self):
        """Each template has name_*, price_*, fields."""
        for code in POSTER_CODES:
            tpl = get_template(code)
            assert tpl is not None
            assert "name_ru" in tpl
            assert "name_uk" in tpl
            assert "name_en" in tpl
            assert "price_pln" in tpl
            assert "price_eur" in tpl
            assert "fields" in tpl

    def test_template_has_size_color_quantity_fields(self):
        """Each template has size, color, quantity fields."""
        for code in POSTER_CODES:
            tpl = get_template(code)
            assert tpl is not None
            field_ids = [f.id for f in tpl["fields"]]
            assert "size" in field_ids
            assert "color" in field_ids
            assert "quantity" in field_ids

    def test_size_field_is_choice_with_correct_options(self):
        """size field is a choice with A4/A3/A2."""
        for code in POSTER_CODES:
            tpl = get_template(code)
            assert tpl is not None
            size_field = next(f for f in tpl["fields"] if f.id == "size")
            assert size_field.type == "choice"
            assert size_field.choices == ["A4", "A3", "A2"]

    def test_color_field_is_choice_with_correct_options(self):
        """color field is a choice with color/bw."""
        for code in POSTER_CODES:
            tpl = get_template(code)
            assert tpl is not None
            color_field = next(f for f in tpl["fields"] if f.id == "color")
            assert color_field.type == "choice"
            assert color_field.choices == ["color", "bw"]

    def test_quantity_field_is_integer_1_to_5(self):
        """quantity field is an integer with min 1, max 5."""
        for code in POSTER_CODES:
            tpl = get_template(code)
            assert tpl is not None
            qty_field = next(f for f in tpl["fields"] if f.id == "quantity")
            assert qty_field.type == "integer"
            assert qty_field.min_value == 1
            assert qty_field.max_value == 5


class TestDemoValidation:
    """Verify choice/integer validation for poster fields."""

    @pytest.mark.parametrize("value", ["A4", "A3", "A2"])
    def test_valid_size_values(self, value):
        """Valid size choices pass validation."""
        result = validate_field_value(
            value=value,
            field_type="choice",
            choices=["A4", "A3", "A2"],
        )
        assert result.is_valid
        assert result.sanitized_value == value

    @pytest.mark.parametrize("value", ["A5", "B4", "A1", "A4x"])
    def test_invalid_size_values(self, value):
        """Invalid size choices are rejected."""
        result = validate_field_value(
            value=value,
            field_type="choice",
            choices=["A4", "A3", "A2"],
        )
        assert not result.is_valid

    @pytest.mark.parametrize("value", ["color", "bw"])
    def test_valid_color_values(self, value):
        """Valid color choices pass validation."""
        result = validate_field_value(
            value=value,
            field_type="choice",
            choices=["color", "bw"],
        )
        assert result.is_valid
        assert result.sanitized_value == value

    @pytest.mark.parametrize("value", ["red", "black", "blue", "sepia"])
    def test_invalid_color_values(self, value):
        """Invalid color choices are rejected."""
        result = validate_field_value(
            value=value,
            field_type="choice",
            choices=["color", "bw"],
        )
        assert not result.is_valid

    @pytest.mark.parametrize("value", ["1", "2", "3", "4", "5"])
    def test_valid_quantity_values(self, value):
        """Valid quantity integers pass validation."""
        result = validate_field_value(
            value=value,
            field_type="integer",
            min_value=1,
            max_value=5,
        )
        assert result.is_valid
        assert result.sanitized_value == value

    @pytest.mark.parametrize("value", ["0", "6", "-1", "abc", "2.5"])
    def test_invalid_quantity_values(self, value):
        """Invalid quantity values are rejected."""
        result = validate_field_value(
            value=value,
            field_type="integer",
            min_value=1,
            max_value=5,
        )
        assert not result.is_valid


class TestDemoPricing:
    """Verify poster price calculation (base + size/color surcharges)."""

    def test_base_prices_positive(self):
        """Base prices are positive for all posters."""
        for code in POSTER_CODES:
            assert POSTER_BASE_PRICE_EUR[code] > 0
            assert POSTER_BASE_PRICE_PLN[code] > 0

    def test_get_price_eur_base(self):
        """get_price_eur without size/color returns the base price."""
        for code in POSTER_CODES:
            assert get_price_eur(code) == POSTER_BASE_PRICE_EUR[code]

    def test_get_price_pln_base(self):
        """get_price_pln without size/color returns the base price."""
        for code in POSTER_CODES:
            assert get_price_pln(code) == POSTER_BASE_PRICE_PLN[code]

    def test_get_price_eur_with_size(self):
        """get_price_eur with size adds the size surcharge."""
        # Terminator 1 base = 10 EUR; A3 surcharge = 5 → 15
        assert get_price_eur("poster_terminator1", size="A3") == 15
        # A2 surcharge = 10 → 20
        assert get_price_eur("poster_terminator1", size="A2") == 20

    def test_get_price_eur_with_color(self):
        """get_price_eur with color adds the color surcharge."""
        # Terminator 2 base = 15 EUR; color surcharge = 3 → 18
        assert get_price_eur("poster_terminator2", color="color") == 18
        # bw surcharge = 0 → 15
        assert get_price_eur("poster_terminator2", color="bw") == 15

    def test_get_price_eur_with_size_and_color(self):
        """get_price_eur with both size and color adds both surcharges."""
        # Predator base = 20 EUR; A2 = +10; color = +3 → 33
        assert get_price_eur("poster_predator", size="A2", color="color") == 33

    def test_get_price_pln_with_size_and_color(self):
        """get_price_pln with both size and color adds both surcharges."""
        # Terminator 1 base = 40 PLN; A3 = +20; color = +12 → 72
        assert get_price_pln("poster_terminator1", size="A3", color="color") == 72

    def test_unknown_code_returns_zero(self):
        """Unknown poster codes return 0."""
        assert get_price_eur("nonexistent") == 0
        assert get_price_pln("nonexistent") == 0