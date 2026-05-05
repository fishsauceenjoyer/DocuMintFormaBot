"""
Конфигурация бота.

Содержит настройки маршрутизации заказов по чатам менеджеров,
платёжные реквизиты, стоимость доставки и другие константы.
Значения загружаются из переменных окружения (.env файла).
"""

import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ID чатов для разных типов документов (захардкодить или в БД)
ROUTING = {
    "sanepid": -100123456789,  # чат санэпид
    "bhp": -100987654321,  # чат BHP
    "psychotests": 123456789,  # личка менеджера
    "pesel": -100123456788,  # чат PESEL
    "default": 555555555,  # куда всё остальное
}

# Реквизиты для оплаты
PAYMENT_DETAILS = {
    "blik": "Номер телефона: +48 123 456 789",
    "uah": "ПриватБанк: 5168 7456 1234 5678\nПолучатель: Ivanov Ivan",
    "usdt": "TRC20: TXYZ... (кошелек)",
}

# Стоимость доставки
DELIVERY_PRICE = 20  # zł

# Админ username
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")

# База данных
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot.db")