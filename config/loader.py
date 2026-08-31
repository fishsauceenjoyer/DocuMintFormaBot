"""Business configuration loader.

Loads business configuration from YAML files into validated pydantic
dataclasses. This decouples business data (services, prices, fields,
limits) from Python code so it can be edited without restarting the bot.

Usage::

    from config.loader import BusinessConfigLoader

    loader = BusinessConfigLoader()
    loader.load_from_yaml("configs/base.yaml")
    loader.load_from_yaml("configs/services.yaml")

    service = loader.get_service("visa")
    errors = loader.validate_order([{"type": "visa", "quantity": 6}])
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, field_validator

# ──────────────────────────────────────────────────────────────────────
# Pydantic models
# ──────────────────────────────────────────────────────────────────────


class FieldConfig(BaseModel):
    """A single input field definition inside a service."""

    id: str
    prompt: str
    type: str = "text"
    optional: bool = False
    max_length: Optional[int] = None
    choices: Optional[List[str]] = None
    min: Optional[int] = None
    max: Optional[int] = None

    @field_validator("type")
    @classmethod
    def _validate_type(cls, value: str) -> str:
        allowed = {
            "text",
            "date",
            "email",
            "phone",
            "optional_text",
            "choice",
            "integer",
        }
        if value not in allowed:
            raise ValueError(f"Unsupported field type: {value}")
        return value

    @field_validator("choices")
    @classmethod
    def _validate_choices(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value is not None and len(value) == 0:
            raise ValueError("choices must not be empty")
        return value


class ServiceLimits(BaseModel):
    """Order constraints for a service."""

    max_per_order: int = Field(default=5, ge=1)


class ServicePrice(BaseModel):
    """Price definition for a service."""

    base: int = Field(ge=0)
    pln: Optional[int] = Field(default=None, ge=0)
    currency: str = "EUR"


class ServiceConfig(BaseModel):
    """A single service (document type / product) definition."""

    id: str
    name: Dict[str, str]
    price: ServicePrice
    fields: List[FieldConfig] = Field(default_factory=list)
    limits: ServiceLimits = Field(default_factory=ServiceLimits)

    def name_for(self, language: str) -> str:
        """Return the localized name, falling back to en → ru → first."""
        for key in (language, "en", "ru"):
            if key in self.name:
                return self.name[key]
        return next(iter(self.name.values()), self.id)


class BaseConfig(BaseModel):
    """Top-level base configuration (version, currencies, delivery, etc.)."""

    version: str = "1.0"
    currencies: Dict[str, Any] = Field(default_factory=dict)
    delivery: Dict[str, Any] = Field(default_factory=dict)
    payment_methods: Dict[str, str] = Field(default_factory=dict)
    countries: Dict[str, Dict[str, str]] = Field(default_factory=dict)
    passport_number_pattern: str = r"^[A-Z0-9\s\-\.\/]{3,30}$"
    routing_keys: Dict[str, str] = Field(default_factory=dict)


class ServicesConfig(BaseModel):
    """Top-level services configuration."""

    services: List[ServiceConfig] = Field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────
# Loader
# ──────────────────────────────────────────────────────────────────────

_DEFAULT_CONFIGS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "configs"
)


class BusinessConfigLoader:
    """Loads and validates business configuration from YAML files.

    Attributes:
        base: Loaded :class:`BaseConfig` (or ``None`` before loading).
        services: Loaded :class:`ServicesConfig` (or ``None`` before loading).
    """

    def __init__(self, configs_dir: str = _DEFAULT_CONFIGS_DIR) -> None:
        self.configs_dir = configs_dir
        self.base: Optional[BaseConfig] = None
        self.services: Optional[ServicesConfig] = None

    # ── Loading ──────────────────────────────────────────────────────

    def load_from_yaml(self, path: str) -> None:
        """Load a YAML file and merge it into the loader state.

        The file is parsed with ``yaml.safe_load`` and validated with
        pydantic. ``base.yaml`` populates :attr:`base`; ``services.yaml``
        populates :attr:`services`.

        Args:
            path: Path to the YAML file (absolute or relative to CWD).

        Raises:
            FileNotFoundError: If the file does not exist.
            yaml.YAMLError: If the file is not valid YAML.
            pydantic.ValidationError: If the structure is invalid.
        """
        file_path = Path(path)
        if not file_path.is_absolute():
            file_path = Path(self.configs_dir) / file_path

        with open(file_path, encoding="utf-8") as fh:
            raw: dict = yaml.safe_load(fh) or {}

        if "services" in raw:
            self.services = ServicesConfig.model_validate(raw)
        else:
            self.base = BaseConfig.model_validate(raw)

    def load_defaults(self) -> None:
        """Load ``base.yaml`` and ``services.yaml`` from the configs dir."""
        self.load_from_yaml(os.path.join(self.configs_dir, "base.yaml"))
        self.load_from_yaml(os.path.join(self.configs_dir, "services.yaml"))

    # ── Accessors ────────────────────────────────────────────────────

    def get_service(self, service_id: str) -> Optional[ServiceConfig]:
        """Return the service dataclass by its id, or ``None`` if missing.

        Args:
            service_id: Unique service identifier (e.g. ``"visa"``).

        Returns:
            :class:`ServiceConfig` or ``None``.
        """
        if self.services is None:
            return None
        for service in self.services.services:
            if service.id == service_id:
                return service
        return None

    def get_all_services(self) -> List[ServiceConfig]:
        """Return all loaded services (empty list if none loaded)."""
        if self.services is None:
            return []
        return list(self.services.services)

    def get_price(self, service_id: str, currency: str = "EUR") -> int:
        """Return the base price for a service in the requested currency.

        The YAML stores a single base price with a currency. For backward
        compatibility with the old PLN/EUR dual pricing, the PLN price is
        derived by multiplying the EUR base price by 4 (the historical
        ratio used in the demo configs).

        Args:
            service_id: Service identifier.
            currency: ``"EUR"`` or ``"PLN"``.

        Returns:
            Price in the requested currency, or ``0`` if unknown.
        """
        service = self.get_service(service_id)
        if service is None:
            return 0
        if currency == "PLN":
            if service.price.pln is not None:
                return service.price.pln
            return service.price.base * 4
        return service.price.base

    # ── Validation ───────────────────────────────────────────────────

    def validate_order(self, items: List[Dict[str, Any]]) -> List[str]:
        """Validate order items against service limits.

        Each item must be a dict with at least ``type`` and ``quantity``
        keys. Returns a list of human-readable error messages; an empty
        list means the order is valid.

        Args:
            items: List of cart items, e.g.
                ``[{"type": "visa", "quantity": 2}]``.

        Returns:
            List of error strings (empty when valid).
        """
        errors: List[str] = []
        if self.services is None:
            errors.append("Services configuration is not loaded")
            return errors

        for item in items:
            service_id = item.get("type")
            quantity = item.get("quantity", 1)
            if not isinstance(service_id, str):
                errors.append(f"Invalid service id: {service_id!r}")
                continue
            service = self.get_service(service_id)
            if service is None:
                errors.append(f"Unknown service: {service_id}")
                continue
            if quantity > service.limits.max_per_order:
                errors.append(
                    f"Service '{service_id}': quantity {quantity} exceeds "
                    f"max per order {service.limits.max_per_order}"
                )
        return errors


# Module-level singleton for easy import
_loader: Optional[BusinessConfigLoader] = None


def get_loader() -> BusinessConfigLoader:
    """Return the global :class:`BusinessConfigLoader` singleton.

    The first call loads the default YAML files from ``configs/``.

    Returns:
        Configured loader instance.
    """
    global _loader
    if _loader is None:
        _loader = BusinessConfigLoader()
        _loader.load_defaults()
    return _loader
