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

# ID чатов для разных типов документов (из .env)
ROUTING = {
    "sanepid": int(os.getenv("ROUTING_SANEPID", "-100123456789")),
    "bhp": int(os.getenv("ROUTING_BHP", "-100987654321")),
    "psychotests": int(os.getenv("ROUTING_PSYCHOTESTS", "123456789")),
    "pesel": int(os.getenv("ROUTING_PESEL", "-100123456788")),
    "default": int(os.getenv("ROUTING_DEFAULT", "555555555")),
}

# Реквизиты для оплаты (из .env)
PAYMENT_DETAILS = {
    "blik": os.getenv("PAYMENT_BLIK", "Номер телефона: +48 123 456 789"),
    "uah": os.getenv("PAYMENT_UAH", "ПриватБанк: 5168 7456 1234 5678\nПолучатель: Ivanov Ivan"),
    "usdt": os.getenv("PAYMENT_USDT", "TRC20: TXYZ... (кошелек)"),
}

# Стоимость доставки
DELIVERY_PRICE = 20  # zł

# Админ username
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")

# База данных
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot.db")