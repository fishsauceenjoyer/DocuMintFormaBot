"""Tests for configuration module.

Verifies:
    - BOT_TOKEN presence/absence
    - ADMIN_USERNAME presence/absence
    - ROUTING configuration
    - PAYMENT_DETAILS
    - validate_config() behavior
"""

import os
from unittest.mock import patch

import pytest


class TestConfigValues:
    """Tests for config constants."""

    def test_database_url_default(self):
        """Verify DATABASE_URL has a default value."""
        from config import DATABASE_URL

        assert DATABASE_URL is not None
        assert "sqlite" in DATABASE_URL or "postgres" in DATABASE_URL

    def test_routing_has_default(self):
        """Verify ROUTING dict has 'default' key."""
        from config import ROUTING

        assert "default" in ROUTING

    def test_payment_details_keys(self):
        """Verify PAYMENT_DETAILS has all expected payment methods."""
        from config import PAYMENT_DETAILS

        assert "blik" in PAYMENT_DETAILS
        assert "uah" in PAYMENT_DETAILS
        assert "usdt" in PAYMENT_DETAILS

    def test_delivery_prices_positive(self):
        """Verify delivery prices are positive integers."""
        from config import DELIVERY_PRICE_EUR, DELIVERY_PRICE_PLN

        assert DELIVERY_PRICE_EUR > 0
        assert DELIVERY_PRICE_PLN > 0


class TestValidateConfig:
    """Tests for validate_config function."""

    def test_validates_missing_bot_token(self):
        """Verify validate_config fails when BOT_TOKEN is missing."""
        from config import validate_config

        with patch("config_runtime.BOT_TOKEN", None):
            with patch("config_runtime.ADMIN_USERNAME", "admin"):
                with patch("config_runtime.ROUTING", {"default": 123}):
                    with pytest.raises(SystemExit):
                        validate_config()

    def test_validates_placeholder_bot_token(self):
        """Verify validate_config fails when BOT_TOKEN is a placeholder."""
        from config import validate_config

        with patch("config_runtime.BOT_TOKEN", "your_bot_token_here"):
            with patch("config_runtime.ADMIN_USERNAME", "admin"):
                with patch("config_runtime.ROUTING", {"default": 123}):
                    with pytest.raises(SystemExit):
                        validate_config()

    def test_validates_missing_admin_username(self):
        """Verify validate_config fails when ADMIN_USERNAME is missing."""
        from config import validate_config

        with patch("config_runtime.BOT_TOKEN", "123456789:token"):
            with patch("config_runtime.ADMIN_USERNAME", None):
                with patch("config_runtime.ROUTING", {"default": 123}):
                    with pytest.raises(SystemExit):
                        validate_config()

    def test_validates_missing_routing(self):
        """Verify validate_config fails when routing chat IDs are missing."""
        from config import validate_config

        with patch("config_runtime.BOT_TOKEN", "123456789:token"):
            with patch("config_runtime.ADMIN_USERNAME", "admin"):
                with patch("config_runtime.ROUTING", {}):
                    with patch(
                        "config_runtime.ROUTING_KEYS", {"visa": "ROUTING_VISA"}
                    ):
                        # Mock to simulate missing ROUTING['visa']
                        with pytest.raises(SystemExit):
                            validate_config()

    def test_valid_config_passes(self):
        """Verify validate_config passes with all required values."""
        from config import validate_config

        with patch("config_runtime.BOT_TOKEN", "123456789:token"):
            with patch("config_runtime.ADMIN_USERNAME", "admin"):
                with patch("config_runtime.ROUTING", {"default": 123}):
                    with patch("config_runtime.ROUTING_KEYS", {}):
                        with patch(
                            "config_runtime.DATABASE_URL", "sqlite:///test.db"
                        ):
                            # Should not raise
                            validate_config()
