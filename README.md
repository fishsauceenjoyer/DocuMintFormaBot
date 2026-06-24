# 🗺 DocuMint 🛂

**Demo Telegram bot for document ordering services** — a showcase project that
illustrates a complete order-processing FSM (Finite State Machine) with
multi-language support, inline keyboards, cart management, delivery/payment
options, and a manager/admin panel.

> 🔍 This is a **demo** project. The business logic (document types, prices,
> routing keys) lives in a single config file — drop in your own data to
> repurpose the bot for any document-as-a-service scenario.

---

## Features

- 🌍 **Multi-language** — English, Russian, Ukrainian (auto-detected from
  Telegram settings, falls back to English)
- 📋 **Document catalogue** — choose from visa applications, passports,
  criminal record checks, apostille, etc.
- 📝 **Dynamic field questionnaire** — each document type defines its own set
  of input fields
- 🛒 **Cart** — add multiple documents of different types in a single order
- 🚚 **Delivery / pickup** — enter courier address or choose self-pickup
- 💳 **Payment methods** — configurable (demo: bank transfer, crypto, online)
- 📤 **Order routing** — each document type can be forwarded to a different
  manager chat
- ⚡ **Fast order** — regular customers can send a free-form message bypassing
  the step-by-step wizard
- 🆘 **Contact manager** — help button forwards user info to support
- 📦 **Manager panel** — send ready documents and tracking numbers back to clients
- 📊 **Stats** — `/orders`, `/stats` for the admin
- 🐳 **Docker-ready** — multi-stage build + `docker-compose.yml`

---

## Project structure

```
documintformabot/
├── main.py                  # Entry point
├── config.py                # Runtime config (token, routing, DB)
├── data/
│   └── business_config.py   # 📌 Business data: document types, prices,
│                            #    fields, payment details, routing keys
├── db/
│   ├── models.py            # SQLAlchemy models (User, Order, …)
│   └── crud.py              # CRUD operations
├── fsm/
│   └── states.py            # FSM states
├── handlers/
│   ├── start.py             # /start, main menu
│   ├── order.py             # Main order FSM flow
│   ├── fast_order.py        # Fast order for repeat customers
│   └── admin.py             # Manager panel
├── templates/
│   ├── fields.py            # Field class
│   └── documents.py         # Thin wrapper over data/business_config.py
├── utils/
│   ├── auth.py              # Admin-only decorator
│   ├── i18n.py              # i18n manager + user_language() helper
│   ├── middleware.py         # Logging / user registration middleware
│   └── router.py             # Order routing to manager chats
├── keyboards/
│   └── buttons.py           # Inline keyboards
├── locales/
│   ├── en.json              # English translations
│   ├── ru.json              # Russian translations
│   └── uk.json              # Ukrainian translations
├── tests/                   # Pytest unit tests
├── Dockerfile               # Multi-stage build
├── docker-compose.yml       # Bot + optional Redis
└── .env.example             # Environment variable template
```

---

## Quick start

### Locally

```bash
# 1. Clone
git clone <repo-url> documintformabot
cd documintformabot

# 2. Virtual env + deps
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
pip install -r requirements.txt

# 3. Configure .env
cp .env.example .env
# Edit .env: insert BOT_TOKEN and ADMIN_USERNAME

# 4. Run
python main.py
```

### Docker (recommended)

```bash
cp .env.example .env
# Edit .env

docker compose up --build -d
docker compose logs -f
docker compose down
```

---

## Configuration

### `.env`

```env
# REQUIRED
BOT_TOKEN=your_bot_token_here
ADMIN_USERNAME=your_admin_username

# Routing — chat IDs for each document type
ROUTING_VISA=-100123456789
ROUTING_PASSPORT=-100987654321
ROUTING_CRIMINAL_RECORD=123456789
ROUTING_APOSTILLE=-100123456788
ROUTING_DEFAULT=555555555

# Database (SQLite for dev, PostgreSQL for production)
DATABASE_URL=sqlite:///bot.db
```

### `data/business_config.py`

This is **the only file you need to edit** to customise the bot for your own
business. It defines:

| Item               | Description                                  |
|--------------------|----------------------------------------------|
| `DOCUMENT_TEMPLATES` | Document types, display names (RU/UK/EN), fields, prices (PLN & EUR) |
| `ROUTING_KEYS`       | Maps document codes → environment variable names |
| `DELIVERY_PRICE_*`   | Delivery cost                                 |
| `PAYMENT_DETAILS`    | Payment instructions shown to customers       |

### Prices (demo)

| Document                              | PLN  | EUR  |
|---------------------------------------|------|------|
| 🗺 Visa application                   | 150  | 35   |
| 🛂 Foreign passport                   | 200  | 45   |
| 📜 Criminal record check              | 100  | 25   |
| 📑 Apostille                          | 120  | 30   |
| 🚚 Delivery                           | +20  | +5   |

---

## Admin commands

| Command                         | Description                        |
|---------------------------------|------------------------------------|
| `/send_doc ORDER_123ABC`        | Send a completed document          |
| `/track ORDER_123ABC TRACK123`  | Send a tracking number             |
| `/orders`                       | List all orders                    |
| `/stats`                        | Order statistics                   |
| `/help_admin`                   | Admin help                         |

---

## For developers

```bash
# Format
black .

# Lint
flake8 .

# Type checking
mypy .

# Tests
pytest -v
pytest --cov=. -v
```

---

## Deployment (Timeweb Cloud)

1. Create a **PostgreSQL** database (free tier available).
2. Create a **Cloud Apps** Docker container.
3. Set environment variables (see `.env.example`).
4. Set health-check port to **8080**.
5. Deploy — auto-rebuilds on git push.

---

## License

MIT