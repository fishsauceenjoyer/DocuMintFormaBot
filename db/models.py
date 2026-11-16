"""SQLAlchemy database models for the Telegram bot.

Contains table and relationship definitions:
    - User — bot users
    - DocumentType — document types with prices and routing configuration
    - Order — orders with delivery and payment info
    - OrderItem — individual line items within an order
"""

import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    """Return the current UTC time as an aware datetime (Python 3.12 safe)."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.

    All models inherit from this class for unified metadata and table configuration.
    """

    pass


class UserRole(enum.Enum):
    """User roles within the system.

    Possible values:
        - USER: regular customer
        - MANAGER: staff member working with orders
        - ADMIN: full-access administrator
    """

    USER = "user"
    MANAGER = "manager"
    ADMIN = "admin"


class OrderStatus(enum.Enum):
    """Order statuses throughout processing.

    Sequence: pending → paid → processing → ready → shipped → completed.
    Orders can also be cancelled at any stage.
    """

    PENDING = "pending"
    PAID = "paid"
    PROCESSING = "processing"
    READY = "ready"
    SHIPPED = "shipped"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class User(Base):
    """Bot user model.

    Stores Telegram user information: username, chat_id,
    phone number, role, and interface language.

    Relationships:
        - Orders are linked through Order.user_id.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=True)
    chat_id: Mapped[int] = mapped_column(Integer, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    role: Mapped[str] = mapped_column(String(20), default="user")
    language: Mapped[str] = mapped_column(String(10), default="en")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"


class DocumentType(Base):
    """Document type / template model.

    Defines the name, price and routing configuration for each
    document category. The *code* field matches the routing keys
    used in :mod:`data.business_config`.

    Attributes:
        code: Unique type code (e.g. ``"poster_terminator1"``).
        name_uk / name_ru / name_en: Display names.
        price: Unit price in PLN.
        target_chat_id: Manager chat ID for this document type.
        is_active: Whether the type is available for ordering.
    """

    __tablename__ = "document_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name_uk: Mapped[str] = mapped_column(String(255), nullable=False)
    name_ru: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    price: Mapped[int] = mapped_column(Integer, default=0)
    description_uk: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_ru: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_chat_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

    def __repr__(self):
        return f"<DocumentType(code={self.code}, name={self.name_uk})>"


class Order(Base):
    """Order model.

    Stores full order information: ID, status, total price,
    payment method, delivery data, tracking number, and the
    order contents as JSON.

    Attributes:
        order_id: Unique order number (``ORDER_YYYYMMDD_XXXX``).
        status: Current status (see :class:`OrderStatus`).
        documents_json: JSON with order details (types, fields, quantities).
    """

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    total_price: Mapped[int] = mapped_column(Integer, default=0)
    payment_method: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    payment_proof_file_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    delivery_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    delivery_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    delivery_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    delivery_paczkomat: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    documents_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    def __repr__(self):
        return f"<Order(order_id={self.order_id}, status={self.status})>"


class OrderItem(Base):
    """Line item inside an order — a single document with parameters.

    Stores the document type, quantity, unit price and
    JSON data with filled-in fields for each instance.

    Relationships:
        - Linked to an order via *order_id*.
        - Document type references :class:`DocumentType.code`.
    """

    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(Integer, nullable=False)
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[int] = mapped_column(Integer, default=0)
    data_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self):
        return (
            f"<OrderItem(order_id={self.order_id}, "
            f"type={self.document_type}, qty={self.quantity})>"
        )
