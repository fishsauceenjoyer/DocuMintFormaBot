"""
Модели базы данных (SQLAlchemy) для Telegram-бота.

Содержит описание таблиц и связей между ними:
    - User — пользователи бота
    - DocumentType — типы документов с ценами и настройками маршрутизации
    - Order — заказы с информацией о доставке и оплате
    - OrderItem — отдельные позиции внутри заказа
"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Базовый класс для всех моделей SQLAlchemy.

    Все модели наследуются от этого класса для единой настройки
    метаданных и конфигурации таблиц.
    """

    pass


class UserRole(enum.Enum):
    """
    Роли пользователей в системе.

    Возможные значения:
        - USER: обычный пользователь (клиент)
        - MANAGER: менеджер, работающий с заказами
        - ADMIN: администратор с полным доступом
    """

    USER = "user"
    MANAGER = "manager"
    ADMIN = "admin"


class OrderStatus(enum.Enum):
    """
    Статусы заказа в процессе обработки.

    Последовательность: pending → paid → processing → ready → shipped → completed
    Также возможна отмена (cancelled) на любом этапе.
    """

    PENDING = "pending"  # Ожидает оплаты
    PAID = "paid"  # Оплачен, ожидает обработки
    PROCESSING = "processing"  # В обработке
    READY = "ready"  # Готов к отправке
    SHIPPED = "shipped"  # Отправлен (есть трек-номер)
    COMPLETED = "completed"  # Выполнен
    CANCELLED = "cancelled"  # Отменён


class User(Base):
    """
    Модель пользователя бота.

    Хранит информацию о пользователе Telegram: username, chat_id,
    номер телефона, роль и выбранный язык интерфейса.

    Связи:
        - Заказы пользователя доступны через Order.user_id
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=True)
    chat_id: Mapped[int] = mapped_column(Integer, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    role: Mapped[str] = mapped_column(String(20), default="user")
    language: Mapped[str] = mapped_column(String(10), default="uk")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"


class DocumentType(Base):
    """
    Модель типа документа (шаблон).

    Определяет название, цену и настройки маршрутизации для каждого
    типа документа (санэпид, BHP, психотесты, PESEL).

    Свойства:
        - code: уникальный код типа (sanepid, bhp, psychotests, pesel)
        - name_uk / name_ru: название на украинском и русском
        - price: стоимость единицы в злотых
        - target_chat_id: ID чата менеджера для данного типа
        - is_active: активен ли тип (можно ли заказать)
    """

    __tablename__ = "document_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name_uk: Mapped[str] = mapped_column(String(255), nullable=False)
    name_ru: Mapped[str] = mapped_column(String(255), nullable=False)
    price: Mapped[int] = mapped_column(Integer, default=0)
    description_uk: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_ru: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_chat_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<DocumentType(code={self.code}, name={self.name_uk})>"


class Order(Base):
    """
    Модель заказа.

    Хранит полную информацию о заказе: номер, статус, сумму,
    способ оплаты, данные доставки, трек-номер и содержимое
    заказа в JSON-формате.

    Свойства:
        - order_id: уникальный номер заказа (ORDER_XXXXXXXX)
        - status: текущий статус (см. OrderStatus)
        - documents_json: JSON с деталями заказа (типы, поля, количество)
        - delivery_*: данные для доставки InPost
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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<Order(order_id={self.order_id}, status={self.status})>"


class OrderItem(Base):
    """
    Модель позиции в заказе — отдельный документ с его параметрами.

    Хранит тип документа, количество, цену за единицу и
    JSON-данные с заполненными полями для каждого экземпляра.

    Связи:
        - Привязана к заказу через order_id
        - Тип документа ссылается на DocumentType.code
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
