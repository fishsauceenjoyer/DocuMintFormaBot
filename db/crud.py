"""Database access layer.

The module owns the SQLAlchemy async engine/session factory and exposes small
CRUD helpers for users, document types, orders, order items, and admin
statistics. DATABASE_URL comes from config.py, so local SQLite and hosted
Postgres use the same application code.

The engine is asynchronous (``create_async_engine``) with a connection pool
configured for production load (``pool_size=10``, ``max_overflow=20``) so the
bot does not drop connections under heavy traffic.
"""

import json
from datetime import datetime, timezone
from typing import List, Optional, cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config import DATABASE_URL
from db.models import Base, DocumentType, Order, OrderItem, User


def _async_url(url: str) -> str:
    """Convert a sync SQLAlchemy URL to its async driver equivalent.

    - ``postgresql://`` → ``postgresql+asyncpg://``
    - ``sqlite:///`` → ``sqlite+aiosqlite:///``
    - ``postgresql+psycopg2://`` → ``postgresql+asyncpg://``
    """
    if url.startswith("postgresql+psycopg2://"):
        return url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("sqlite://"):
        return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    return url


# SQLAlchemy async engine — works with both SQLite (local dev) and PostgreSQL
# (production). Connection pooling is configured explicitly so the bot does not
# drop connections under load. For SQLite, pool_size/max_overflow are ignored
# (SQLite only allows one writer at a time, which is fine for single-bot usage).
async_engine = create_async_engine(
    _async_url(DATABASE_URL),
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

# Async session factory (tables are created in init_db() / init_default_document_types())
AsyncSessionLocal = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db():
    """
    Асинхронный генератор для получения сессии базы данных.

    Используется в качестве зависимости для получения объекта AsyncSession.
    Автоматически закрывает сессию после использования.

    Yields:
        AsyncSession: Асинхронная сессия SQLAlchemy для работы с БД.
    """
    async with AsyncSessionLocal() as db:
        yield db


# User operations
async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """
    Находит пользователя по его username в Telegram.

    Args:
        db: Асинхронная сессия базы данных.
        username: Username пользователя Telegram.

    Returns:
        Объект User или None, если пользователь не найден.
    """
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """
    Находит пользователя по его ID в локальной БД.

    Args:
        db: Асинхронная сессия базы данных.
        user_id: ID пользователя в локальной БД (не Telegram).

    Returns:
        Объект User или None, если пользователь не найден.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession, username: str, chat_id: Optional[int] = None, role: str = "user"
) -> User:
    """
    Создаёт нового пользователя.

    Если пользователь с таким username уже существует — будет ошибка
    целостности данных (нужна проверка перед вызовом).

    Args:
        db: Асинхронная сессия базы данных.
        username: Username пользователя Telegram.
        chat_id: ID чата Telegram (опционально).
        role: Роль пользователя (user/manager/admin).

    Returns:
        Созданный объект User.
    """
    user = User(username=username, chat_id=chat_id, role=role)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user_chat_id(db: AsyncSession, user: User, chat_id: int):
    """
    Обновляет chat_id пользователя.

    Используется для сохранения актуального ID чата,
    чтобы бот мог отправлять пользователю уведомления.

    Args:
        db: Асинхронная сессия базы данных.
        user: Объект пользователя для обновления.
        chat_id: Новый ID чата Telegram.
    """
    user.chat_id = chat_id
    user.updated_at = datetime.now(timezone.utc)
    await db.commit()


async def update_user_language(db: AsyncSession, user: User, language: str):
    """
    Обновляет выбранный язык интерфейса пользователя.

    Args:
        db: Асинхронная сессия базы данных.
        user: Объект пользователя для обновления.
        language: Код языка ('uk' или 'ru').
    """
    user.language = language
    user.updated_at = datetime.now(timezone.utc)
    await db.commit()


# Document type operations
async def get_document_type(db: AsyncSession, code: str) -> Optional[DocumentType]:
    """
    Находит тип документа по его коду.

    Args:
        db: Асинхронная сессия базы данных.
        code: Код типа документа (sanepid, bhp, psychotests, pesel).

    Returns:
        Объект DocumentType или None, если не найден.
    """
    result = await db.execute(select(DocumentType).where(DocumentType.code == code))
    return result.scalar_one_or_none()


async def get_all_document_types(db: AsyncSession) -> List[DocumentType]:
    """
    Возвращает все активные типы документов.

    Фильтрует только те типы, у которых is_active = True.

    Args:
        db: Асинхронная сессия базы данных.

    Returns:
        Список активных объектов DocumentType.
    """
    result = await db.execute(
        select(DocumentType).where(DocumentType.is_active.is_(True))
    )
    return list(result.scalars().all())


# Order operations
async def create_order(
    db: AsyncSession,
    order_id: str,
    user_id: int,
    total_price: int,
    status: str = "pending",
    payment_method: Optional[str] = None,
    payment_proof_file_id: Optional[str] = None,
    delivery: Optional[dict] = None,
    documents: Optional[list] = None,
) -> Order:
    """
    Создаёт новый заказ в базе данных.

    Сохраняет все данные заказа: номер, сумму, способ оплаты,
    доказательство оплаты, данные доставки и JSON с содержимым.

    Args:
        db: Асинхронная сессия базы данных.
        order_id: Уникальный номер заказа (ORDER_XXXXXXXX).
        user_id: ID пользователя в локальной БД.
        total_price: Итоговая сумма заказа в злотых.
        status: Начальный статус заказа.
        payment_method: Способ оплаты (blik/uah/usdt).
        payment_proof_file_id: File_id фото/документа чека.
        delivery: Словарь с данными доставки (name, phone, email, paczkomat).
        documents: Список словарей с данными заказанных документов.

    Returns:
        Созданный объект Order.
    """
    order = Order(
        order_id=order_id,
        user_id=user_id,
        status=status,
        total_price=total_price,
        payment_method=payment_method,
        payment_proof_file_id=payment_proof_file_id,
        delivery_name=delivery.get("name") if delivery else None,
        delivery_phone=delivery.get("phone") if delivery else None,
        delivery_email=delivery.get("email") if delivery else None,
        delivery_paczkomat=delivery.get("address") if delivery else None,
        documents_json=json.dumps(documents, ensure_ascii=False) if documents else None,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


async def get_order_by_id(db: AsyncSession, order_id: str) -> Optional[Order]:
    """
    Находит заказ по его номеру.

    Args:
        db: Асинхронная сессия базы данных.
        order_id: Номер заказа (ORDER_XXXXXXXX).

    Returns:
        Объект Order или None, если не найден.
    """
    result = await db.execute(select(Order).where(Order.order_id == order_id))
    return result.scalar_one_or_none()


async def get_orders_by_user(db: AsyncSession, user_id: int) -> List[Order]:
    """
    Возвращает все заказы пользователя, отсортированные по дате (сначала новые).

    Args:
        db: Асинхронная сессия базы данных.
        user_id: ID пользователя в локальной БД.

    Returns:
        Список заказов пользователя.
    """
    result = await db.execute(
        select(Order).where(Order.user_id == user_id).order_by(Order.created_at.desc())
    )
    return list(result.scalars().all())


async def update_order_status(db: AsyncSession, order: Order, status: str):
    """
    Обновляет статус заказа.

    Args:
        db: Асинхронная сессия базы данных.
        order: Объект заказа для обновления.
        status: Новый статус (см. OrderStatus enum).
    """
    order.status = status
    order.updated_at = datetime.now(timezone.utc)
    await db.commit()


async def update_order_tracking(db: AsyncSession, order: Order, tracking_number: str):
    """
    Добавляет трек-номер к заказу и меняет статус на "shipped".

    Args:
        db: Асинхронная сессия базы данных.
        order: Объект заказа для обновления.
        tracking_number: Трек-номер почтовой службы.
    """
    order.tracking_number = tracking_number
    order.status = "shipped"
    order.updated_at = datetime.now(timezone.utc)
    await db.commit()


async def update_order_payment_proof(db: AsyncSession, order: Order, file_id: str):
    """
    Сохраняет file_id подтверждения оплаты и меняет статус на "paid".

    Args:
        db: Асинхронная сессия базы данных.
        order: Объект заказа для обновления.
        file_id: File_id фото/документа с чеком оплаты.
    """
    order.payment_proof_file_id = file_id
    order.status = "paid"
    order.updated_at = datetime.now(timezone.utc)
    await db.commit()


async def get_all_orders(db: AsyncSession) -> List[Order]:
    """
    Возвращает все заказы из базы данных, отсортированные по дате (сначала новые).

    Args:
        db: Асинхронная сессия базы данных.

    Returns:
        Список всех заказов.
    """
    result = await db.execute(select(Order).order_by(Order.created_at.desc()))
    return list(result.scalars().all())


async def get_orders_by_status(db: AsyncSession, status: str) -> List[Order]:
    """
    Возвращает заказы с указанным статусом.

    Args:
        db: Асинхронная сессия базы данных.
        status: Статус для фильтрации (см. OrderStatus enum).

    Returns:
        Список заказов с указанным статусом.
    """
    result = await db.execute(
        select(Order).where(Order.status == status).order_by(Order.created_at.desc())
    )
    return list(result.scalars().all())


async def get_order_stats(db: AsyncSession) -> dict:
    """
    Возвращает статистику по заказам.

    Args:
        db: Асинхронная сессия базы данных.

    Returns:
        Словарь с ключами total, pending, paid, processing,
        ready, shipped, completed, cancelled.
    """
    total = (await db.execute(select(Order))).scalars().all()
    total_count = len(total)
    pending = len(
        (await db.execute(select(Order).where(Order.status == "pending")))
        .scalars()
        .all()
    )
    paid = len(
        (await db.execute(select(Order).where(Order.status == "paid"))).scalars().all()
    )
    processing = len(
        (await db.execute(select(Order).where(Order.status == "processing")))
        .scalars()
        .all()
    )
    ready = len(
        (await db.execute(select(Order).where(Order.status == "ready"))).scalars().all()
    )
    shipped = len(
        (await db.execute(select(Order).where(Order.status == "shipped")))
        .scalars()
        .all()
    )
    completed = len(
        (await db.execute(select(Order).where(Order.status == "completed")))
        .scalars()
        .all()
    )
    cancelled = len(
        (await db.execute(select(Order).where(Order.status == "cancelled")))
        .scalars()
        .all()
    )

    return {
        "total": total_count,
        "pending": pending,
        "paid": paid,
        "processing": processing,
        "ready": ready,
        "shipped": shipped,
        "completed": completed,
        "cancelled": cancelled,
    }


# Order item operations
async def create_order_item(
    db: AsyncSession,
    order_id: int,
    document_type: str,
    quantity: int,
    unit_price: int,
    data: Optional[dict] = None,
) -> OrderItem:
    """
    Создаёт позицию заказа (отдельный тип документа с количеством).

    Args:
        db: Асинхронная сессия базы данных.
        order_id: ID заказа в локальной БД.
        document_type: Код типа документа.
        quantity: Количество экземпляров.
        unit_price: Цена за единицу в злотых.
        data: JSON-данные с заполненными полями документа.

    Returns:
        Созданный объект OrderItem.
    """
    item = OrderItem(
        order_id=order_id,
        document_type=document_type,
        quantity=quantity,
        unit_price=unit_price,
        data_json=json.dumps(data, ensure_ascii=False) if data else None,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


# Helper to initialize default document types
async def init_default_document_types(db: AsyncSession):
    """
    Инициализирует типы документов по умолчанию, если они ещё не созданы.

    Добавляет стандартные типы из демо-конфига (консульские услуги)
    с базовыми ценами и настройками маршрутизации.

    Args:
        db: Асинхронная сессия базы данных для добавления записей.
    """
    from data.business_config import DOCUMENT_TEMPLATES, ROUTING_KEYS

    default_types = [
        {
            "code": code,
            "name_uk": tmpl.get("name_uk", tmpl["name_en"]),
            "name_ru": tmpl.get("name_ru", tmpl["name_en"]),
            "name_en": tmpl.get("name_en", tmpl["name_ru"]),
            "price": tmpl["price_pln"],
        }
        for code, tmpl in DOCUMENT_TEMPLATES.items()
    ]

    for doc_type in default_types:
        existing = await get_document_type(db, cast(str, doc_type["code"]))
        if not existing:
            new_type = DocumentType(**doc_type)
            db.add(new_type)

    await db.commit()


async def init_db():
    """
    Полная инициализация базы данных: создание таблиц и наполнение данными.

    Выполняется при первом запуске для создания структуры БД
    и добавления стандартных типов документов.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as db:
        await init_default_document_types(db)


if __name__ == "__main__":
    import asyncio

    asyncio.run(init_db())
    print("Database initialized successfully!")
