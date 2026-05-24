# 🤖 DocuMintFormaBot

Telegram-бот для автоматизации приёма заказов на оформление документов (Санэпид/СК, BHP, PESEL, психотесты и др.).

## Возможности

- 📋 Выбор типа документа из списка шаблонов с ценами
- 📝 Динамический опросник полей для каждого документа
- 🛒 Корзина с добавлением нескольких документов в один заказ
- 🚚 Доставка InPost (данные для пачкомата)
- 💳 Выбор способа оплаты (Blik, Гривна, USDT)
- 📤 Автоматическая отправка заказов менеджерам (маршрутизация по типу документа)
- ⚡ Режим "Постоянный клиент" для быстрых заказов
- 🆘 Кнопка "Связь с менеджером"
- 📦 Отправка трек-номера и готовых документов клиентам
- 📊 Статистика заказов для администратора
- 🐳 Полная Docker-поддержка

## Структура проекта

```
documintformabot/
├── main.py                 # Точка входа
├── config.py               # Конфигурация (токен, ID чатов, реквизиты)
├── db/
│   ├── models.py           # SQLAlchemy модели (User, Order, DocumentType, OrderItem)
│   └── crud.py             # CRUD-операции для работы с БД
├── fsm/
│   └── states.py           # Состояния FSM (конечный автомат)
├── handlers/
│   ├── start.py            # Команда /start, главное меню
│   ├── order.py            # Основной поток заказа
│   ├── fast_order.py       # Быстрый заказ для постоянных клиентов
│   └── admin.py            # Админ-панель (/orders, /stats, /send_doc, /track)
├── templates/
│   └── documents.py        # Шаблоны документов (поля, цены)
├── utils/
│   ├── auth.py             # Декораторы для проверки прав администратора
│   ├── i18n.py             # Интернационализация (ru/uk)
│   ├── middleware.py       # Middleware (логирование, регистрация пользователей)
│   └── router.py           # Маршрутизация заказов менеджерам
├── keyboards/
│   └── buttons.py          # Inline-клавиатуры
├── locales/
│   ├── ru.json             # Русская локализация
│   └── uk.json             # Украинская локализация
├── tests/
│   ├── conftest.py         # Фикстуры для тестов
│   ├── test_order.py       # Тесты заказов
│   └── test_fast_order.py  # Тесты быстрых заказов
├── Dockerfile              # Multi-stage Docker-сборка
├── docker-compose.yml      # Docker Compose (бот + опционально Redis)
└── .env.example            # Пример конфигурации
```

## Быстрый старт

### Локально (без Docker)

```bash
# 1. Клонировать репозиторий
git clone <repo-url> documintformabot
cd documintformabot

# 2. Создать виртуальное окружение и установить зависимости
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
pip install -r requirements.txt

# 3. Настроить .env
cp .env.example .env
# Отредактировать .env: вставить BOT_TOKEN и ADMIN_USERNAME

# 4. Запустить
python main.py
```

### В Docker (рекомендуется)

```bash
# 1. Настроить .env (скопировать из .env.example и отредактировать)
cp .env.example .env

# 2. Собрать и запустить
docker compose up --build -d

# 3. Посмотреть логи
docker compose logs -f

# 4. Остановить
docker compose down
```

## Настройка .env

```env
# Обязательные параметры
BOT_TOKEN=your_bot_token_here       # Токен от @BotFather
ADMIN_USERNAME=your_admin_username  # Telegram username администратора

# Маршрутизация заказов по чатам менеджеров
ROUTING_SANEPID=-100123456789       # Чат для Санэпид/СК
ROUTING_BHP=-100987654321           # Чат для BHP
ROUTING_PSYCHOTESTS=123456789       # Чат для психотестов
ROUTING_PESEL=-100123456788         # Чат для PESEL
ROUTING_DEFAULT=555555555           # Чат по умолчанию

# Платёжные реквизиты
PAYMENT_BLIK="Номер телефона: +48 XXX XXX XXX"
PAYMENT_UAH="ПриватБанк: 5168 XXXX XXXX XXXX"
PAYMENT_USDT="TRC20: адрес кошелька"

# База данных (SQLite для разработки, PostgreSQL для продакшена)
DATABASE_URL=sqlite:///bot.db

# Redis (опционально — для production)
# REDIS_URL=redis://localhost:6379/0
```

## Цены на документы

| Документ | Цена |
|----------|------|
| 📑 Санэпид / СК | 150 zł |
| ⛑ BHP | 100 zł |
| 🚕 Психотесты для водителей | 120 zł |
| 🧧 PESEL без присутствия | 200 zł |
| 🚚 Доставка InPost | +20 zł |

## Команды для администратора

- `/send_doc ORDER_123ABC` — отправить готовый документ клиенту
- `/track ORDER_123ABC TRACK123` — отправить трек-номер
- `/orders` — список всех заказов
- `/stats` — статистика заказов
- `/help_admin` — справка по командам

## Для разработчиков

```bash
# Форматирование
black .

# Линтинг
flake8 .

# Проверка типов
mypy .

# Запуск тестов
pytest -v

# Запуск тестов с coverage
pytest --cov=. -v
```

## Лицензия

MIT