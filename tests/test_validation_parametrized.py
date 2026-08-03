"""Parametrized wrapper for validation tests.

Replaces many repetitive tests from test_validation.py using
pytest.mark.parametrize to reduce duplication.

Keep this alongside test_validation.py until we merge parametrization
into the original file.
"""

import pytest

from utils.validation import has_malicious_patterns, validate_field_value


@pytest.mark.parametrize(
    "input_text,should_be_malicious",
    [
        ("SELECT * FROM users", True),
        ("DROP TABLE orders", True),
        ("1 UNION SELECT * FROM passwords", True),
        ("' OR 1=1 --", True),
        ("admin'--", True),
        ("INSERT INTO users VALUES (...)", True),
        ("<script>alert('xss')</script>", True),
        ("<iframe src='evil.com'></iframe>", True),
        ("onclick=evil()", True),
        ("javascript:alert(1)", True),
        ("<svg onload=alert(1)>", True),
        ('{"$gt": ""}', True),
        ("{$where: 'this.password'}", True),
        ("{$regex: '.*'}", True),
        ("| cat /etc/passwd", True),
        ("; rm -rf /", True),
        ("`id`", True),
        ("eval(malicious_code)", True),
        # Safe inputs
        ("John Doe", False),
        ("Fifth Avenue 123", False),
        ("Иван Петров", False),
        ("13.01.2022", False),
        ("ул. Пушкина, д. 10, кв. 5", False),
    ],
)
def test_has_malicious_patterns_parametrized(input_text, should_be_malicious):
    result = has_malicious_patterns(input_text)
    assert (result is not None) == should_be_malicious


@pytest.mark.parametrize(
    "value,expected_valid,expected_error_contains",
    [
        ("", False, "пустым"),
        ("A" * 300, False, "Максимум"),
        ("A" * 255, True, ""),
        ("2024-12-31", True, ""),
        ("31.12.2024", True, ""),
        ("<script>alert(1)</script>", False, "недопустимые символы"),
    ],
)
def test_valid_text_cases_parametrized(value, expected_valid, expected_error_contains):
    result = validate_field_value(value, "text", field_name="test")
    assert result.is_valid == expected_valid
    if expected_error_contains:
        assert expected_error_contains in result.error_message


@pytest.mark.parametrize(
    "country,expected_valid",
    [
        ("PL", True),
        ("RU", True),
        ("RS", True),
        ("AM", True),
        ("pl", True),
        ("XX", False),
        ("POL", False),
    ],
)
def test_country_code_parametrized(country, expected_valid):
    result = validate_field_value(country, "country_code", field_name="country")
    assert result.is_valid == expected_valid
