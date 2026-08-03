"""Tests for the templates/documents module.

Verifies:
    - get_all_templates returns a list of (code, name) tuples
    - get_template returns the full template dict
    - get_template returns None for missing codes
    - Template structure (fields, prices, names)
"""

import pytest


class TestGetAllTemplates:
    """Tests for get_all_templates function."""

    def test_returns_list(self):
        """Verify get_all_templates returns a list."""
        from templates.documents import get_all_templates
        templates = get_all_templates()
        assert isinstance(templates, list)

    def test_returns_tuple_pairs(self):
        """Verify each item is a (code, name) tuple."""
        from templates.documents import get_all_templates
        templates = get_all_templates()
        for item in templates:
            assert isinstance(item, tuple)
            assert len(item) == 2
            code, name = item
            assert isinstance(code, str)
            assert isinstance(name, str)

    def test_includes_visa(self):
        """Verify 'visa' is in the list."""
        from templates.documents import get_all_templates
        codes = [code for code, _ in get_all_templates()]
        assert "visa" in codes

    def test_includes_passport(self):
        """Verify 'passport' is in the list."""
        from templates.documents import get_all_templates
        codes = [code for code, _ in get_all_templates()]
        assert "passport" in codes

    def test_names_are_translated(self):
        """Verify names contain English text or emoji."""
        from templates.documents import get_all_templates
        for code, name in get_all_templates():
            assert len(name) > 0, f"Empty name for {code}"
            # Names should be non-empty strings with content
            assert not name.startswith("[")  # Not a missing template indicator


class TestGetTemplate:
    """Tests for get_template function."""

    def test_returns_dict_for_visa(self):
        """Verify get_template('visa') returns a dict with expected keys."""
        from templates.documents import get_template
        template = get_template("visa")
        assert template is not None
        assert isinstance(template, dict)
        # Templates use name_* keys, not 'code'
        assert "name_en" in template
        assert "name_ru" in template
        assert "fields" in template
        assert "price_eur" in template
        assert "price_pln" in template

    def test_returns_dict_for_passport(self):
        """Verify get_template('passport') returns a dict."""
        from templates.documents import get_template
        template = get_template("passport")
        assert template is not None
        assert "name_en" in template
        assert "fields" in template

    def test_returns_none_for_missing_code(self):
        """Verify get_template returns None for nonexistent code."""
        from templates.documents import get_template
        assert get_template("nonexistent_code_xyz") is None

    def test_returns_none_for_empty_string(self):
        """Verify get_template returns None for empty string."""
        from templates.documents import get_template
        assert get_template("") is None

    def test_template_has_required_keys(self):
        """Verify each template has required structural keys."""
        from templates.documents import get_all_templates, get_template
        codes = [code for code, _ in get_all_templates()]
        for code in codes:
            template = get_template(code)
            assert template is not None, f"Template {code} not found"
            for key in ("name_en", "fields", "price_eur", "price_pln"):
                assert key in template, f"Template {code} missing key '{key}'"

    def test_fields_have_required_attributes(self):
        """Verify each field has id, prompt, type."""
        from templates.documents import get_all_templates, get_template
        from templates.fields import Field

        codes = [code for code, _ in get_all_templates()]
        for code in codes:
            template = get_template(code)
            assert template is not None, f"Template {code} not found"
            for field in template["fields"]:
                assert isinstance(field, Field), f"Field in {code} is not a Field object"
                assert field.id, f"Field in {code} has no id"
                assert field.prompt, f"Field {field.id} in {code} has no prompt"
                assert field.type, f"Field {field.id} in {code} has no type"

    def test_template_price_exists(self):
        """Verify pricing information exists for templates."""
        from templates.documents import get_all_templates, get_template
        codes = [code for code, _ in get_all_templates()]
        for code in codes:
            template = get_template(code)
            assert template is not None, f"Template {code} not found"
            # Templates use price_eur and price_pln keys
            has_price = "price_eur" in template and "price_pln" in template
            assert has_price, f"Template {code} has no pricing info"
            assert isinstance(template["price_eur"], int), f"price_eur for {code} is not int"
            assert isinstance(template["price_pln"], int), f"price_pln for {code} is not int"
            assert template["price_eur"] > 0, f"price_eur for {code} is not positive"
            assert template["price_pln"] > 0, f"price_pln for {code} is not positive"


class TestTemplatePricing:
    """Tests for business_config pricing integration."""

    def test_get_price_eur_returns_positive_int(self):
        """Verify get_price_eur returns a positive integer for known codes."""
        from data.business_config import get_price_eur
        from templates.documents import get_all_templates

        codes = [code for code, _ in get_all_templates()]
        for code in codes:
            price = get_price_eur(code)
            assert isinstance(price, int), f"Price for {code} is not int"
            assert price > 0, f"Price for {code} is not positive"

    def test_get_price_pln_returns_positive_int(self):
        """Verify get_price_pln returns a positive integer for known codes."""
        from data.business_config import get_price_pln
        from templates.documents import get_all_templates

        codes = [code for code, _ in get_all_templates()]
        for code in codes:
            price = get_price_pln(code)
            assert isinstance(price, int), f"PLN price for {code} is not int"
            assert price > 0, f"PLN price for {code} is not positive"

    def test_get_price_eur_returns_zero_for_unknown(self):
        """Verify get_price_eur returns 0 for unknown code."""
        from data.business_config import get_price_eur
        assert get_price_eur("nonexistent") == 0

    def test_get_price_pln_returns_zero_for_unknown(self):
        """Verify get_price_pln returns 0 for unknown code."""
        from data.business_config import get_price_pln
        assert get_price_pln("nonexistent") == 0