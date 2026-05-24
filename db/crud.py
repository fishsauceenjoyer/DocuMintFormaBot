"""
CRUD операции для работы с базой данных SQLite.

Содержит функции для создания, чтения, обновления данных
пользователей, документов, заказов и позиций заказов.
Использует SQLAlchemy ORM для взаимодействия с БД.
"""

import json
from datetime import datetime
from typing import List, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from db.models import Base, DocumentType, Order, OrderItem, User

# Create engine - in production, use proper database URL
engine = create_engine(
    "sqlite:///bot.db", connect_args={"check_same_thread": False}, poolclass=StaticPool
)

# Create tables
Base.metadata.create_all(engine)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Генератор для получения сессии базы данных.

    Используется в качестве зависимости для получения объекта Session.
    Автоматически закрывает сессию после использования.

    Yields:
        Session: Сессия SQLAlchemy для работы с БД.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# User operations
def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """
    Находит пользователя по его username в Telegram.

    Args:
        db: Сессия базы данных.
        username: Username пользователя Telegram.

    Returns:
        Объект User или None, если пользователь не найден.
    """
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """
    Находит пользователя по его ID в локальной БД.

    Args:
        db: Сессия базы данных.
        user_id: ID пользователя в локальной БД (не Telegram).

    Returns:
        Объект User или None, если пользователь не найден.
    """
    return db.query(User).filter(User.id == user_id).first()


def create_user(
    db: Session, username: str, chat_id: Optional[int] = None, role: str = "user"
) -> User:
    """
    Создаёт нового пользователя.

    Если пользователь с таким username уже существует — будет ошибка
    целостности данных (нужна проверка перед вызовом).

    Args:
        db: Сессия базы данных.
        username: Username пользователя Telegram.
        chat_id: ID чата Telegram (опционально).
        role: Роль пользователя (user/manager/admin).

    Returns:
        Созданный объект User.
    """
    user = User(username=username, chat_id=chat_id, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user_chat_id(db: Session, user: User, chat_id: int):
    """
    Обновляет chat_id пользователя.

    Используется для сохранения актуального ID чата,
    чтобы бот мог отправлять пользователю уведомления.

    Args:
        db: Сессия базы данных.
        user: Объект пользователя для обновления.
        chat_id: Новый ID чата Telegram.
    """
    user.chat_id = chat_id
    user.updated_at = datetime.utcnow()
    db.commit()


def update_user_language(db: Session, user: User, language: str):
    """
    Обновляет выбранный язык интерфейса пользователя.

    Args:
        db: Сессия базы данных.
        user: Объект пользователя для обновления.
        language: Код языка ('uk' или 'ru').
    """
    user.language = language
    user.updated_at = datetime.utcnow()
    db.commit()


# Document type operations
def get_document_type(db: Session, code: str) -> Optional[DocumentType]:
    """
    Находит тип документа по его коду.

    Args:
        db: Сессия базы данных.
        code: Код типа документа (sanepid, bhp, psychotests, pesel).

    Returns:
        Объект DocumentType или None, если не найден.
    """
    return db.query(DocumentType).filter(DocumentType.code == code).first()


def get_all_document_types(db: Session) -> List[DocumentType]:
    """
    Возвращает все активные типы документов.

    Фильтрует только те типы, у которых is_active = True.

    Args:
        db: Сессия базы данных.

    Returns:
        Список активных объектов DocumentType.
    """
    return db.query(DocumentType).filter(DocumentType.is_active.is_(True)).all()


# Order operations
def create_order(
    db: Session,
    order_id: str,
    user_id: int,
    total_price: int,
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
        db: Сессия базы данных.
        order_id: Уникальный номер заказа (ORDER_XXXXXXXX).
        user_id: ID пользователя в локальной БД.
        total_price: Итоговая сумма заказа в злотых.
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
        total_price=total_price,
        payment_method=payment_method,
        payment_proof_file_id=payment_proof_file_id,
        delivery_name=delivery.get("name") if delivery else None,
        delivery_phone=delivery.get("phone") if delivery else None,
        delivery_email=delivery.get("email") if delivery else None,
        delivery_paczkomat=delivery.get("paczkomat") if delivery else None,
        documents_json=json.dumps(documents, ensure_ascii=False) if documents else None,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def get_order_by_id(db: Session, order_id: str) -> Optional[Order]:
    """
    Находит заказ по его номеру.

    Args:
        db: Сессия базы данных.
        order_id: Номер заказа (ORDER_XXXXXXXX).

    Returns:
        Объект Order или None, если не найден.
    """
    return db.query(Order).filter(Order.order_id == order_id).first()


def get_orders_by_user(db: Session, user_id: int) -> List[Order]:
    """
    Возвращает все заказы пользователя, отсортированные по дате (сначала новые).

    Args:
        db: Сессия базы данных.
        user_id: ID пользователя в локальной БД.

    Returns:
        Список заказов пользователя.
    """
    return (
        db.query(Order)
        .filter(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .all()
    )


def update_order_status(db: Session, order: Order, status: str):
    """
    Обновляет статус заказа.

    Args:
        db: Сессия базы данных.
        order: Объект заказа для обновления.
        status: Новый статус (см. OrderStatus enum).
    """
    order.status = status
    order.updated_at = datetime.utcnow()
    db.commit()


def update_order_tracking(db: Session, order: Order, tracking_number: str):
    """
    Добавляет трек-номер к заказу и меняет статус на "shipped".

    Args:
        db: Сессия базы данных.
        order: Объект заказа для обновления.
        tracking_number: Трек-номер почтовой службы.
    """
    order.tracking_number = tracking_number
    order.status = "shipped"
    order.updated_at = datetime.utcnow()
    db.commit()


def update_order_payment_proof(db: Session, order: Order, file_id: str):
    """
    Сохраняет file_id подтверждения оплаты и меняет статус на "paid".

    Args:
        db: Сессия базы данных.
        order: Объект заказа для обновления.
        file_id: File_id фото/документа с чеком оплаты.
    """
    order.payment_proof_file_id = file_id
    order.status = "paid"
    order.updated_at = datetime.utcnow()
    db.commit()


def get_all_orders(db: Session) -> List[Order]:
    """
    Возвращает все заказы из базы данных, отсортированные по дате (сначала новые).

    Args:
        db: Сессия базы данных.

    Returns:
        Список всех заказов.
    """
    return db.query(Order).order_by(Order.created_at.desc()).all()


def get_orders_by_status(db: Session, status: str) -> List[Order]:
    """
    Возвращает заказы с указанным статусом.

    Args:
        db: Сессия базы данных.
        status: Статус для фильтрации (см. OrderStatus enum).

    Returns:
        Список заказов с указанным статусом.
    """
    return (
        db.query(Order)
        .filter(Order.status == status)
        .order_by(Order.created_at.desc())
        .all()
    )


def get_order_stats(db: Session) -> dict:
    """
    Возвращает статистику по заказам.

    Args:
        db: Сессия базы данных.

    Returns:
        Словарь с ключами total, pending, paid, processing,
        ready, shipped, completed, cancelled.
    """
    total = db.query(Order).count()
    pending = db.query(Order).filter(Order.status == "pending").count()
    paid = db.query(Order).filter(Order.status == "paid").count()
    processing = db.query(Order).filter(Order.status == "processing").count()
    ready = db.query(Order).filter(Order.status == "ready").count()
    shipped = db.query(Order).filter(Order.status == "shipped").count()
    completed = db.query(Order).filter(Order.status == "completed").count()
    cancelled = db.query(Order).filter(Order.status == "cancelled").count()

    return {
        "total": total,
        "pending": pending,
        "paid": paid,
        "processing": processing,
        "ready": ready,
        "shipped": shipped,
        "completed": completed,
        "cancelled": cancelled,
    }


# Order item operations
def create_order_item(
    db: Session,
    order_id: int,
    document_type: str,
    quantity: int,
    unit_price: int,
    data: Optional[dict] = None,
) -> OrderItem:
    """
    Создаёт позицию заказа (отдельный тип документа с количеством).

    Args:
        db: Сессия базы данных.
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
    db.commit()
    db.refresh(item)
    return item


# Helper to initialize default document types
def init_default_document_types(db: Session):
    """
    Инициализирует типы документов по умолчанию, если они ещё не созданы.

    Добавляет стандартные типы (санэпид, BHP, психотесты, PESEL)
    с базовыми ценами и настройками маршрутизации.

    Args:
        db: Сессия базы данных для добавления записей.
    """
    default_types = [
        {
            "code": "sanepid",
            "name_uk": "📑 Санэпід / СК",
            "name_ru": "📑 Санэпид / СК",
            "price": 150,
            "target_chat_id": -100123456789,
        },
        {
            "code": "bhp",
            "name_uk": "⛑ BHP",
            "name_ru": "⛑ BHP",
            "price": 100,
            "target_chat_id": -100987654321,
        },
        {
            "code": "psychotests",
            "name_uk": "🚕 Психотести для водіїв",
            "name_ru": "🚕 Психотесты для водителей",
            "price": 120,
            "target_chat_id": 123456789,
        },
        {
            "code": "pesel",
            "name_uk": "🧧 PESEL без присутності",
            "name_ru": "🧧 PESEL без присутствия",
            "price": 200,
            "target_chat_id": -100123456788,
        },
    ]

    for doc_type in default_types:
        existing = get_document_type(db, doc_type["code"])
        if not existing:
            new_type = DocumentType(**doc_type)
            db.add(new_type)

    db.commit()


def init_db():
    """
    Полная инициализация базы данных: создание таблиц и наполнение данными.

    Выполняется при первом запуске для создания структуры БД
    и добавления стандартных типов документов.
    """
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        init_default_document_types(db)


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")