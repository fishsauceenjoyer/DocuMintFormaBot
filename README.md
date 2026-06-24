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

## Manual testing (smoke test)

After starting the bot, walk through this quick check list from a Telegram
client to confirm everything works.

### Happy path (new order)

1. **Start** – send `/start` → you should see the main menu with 3 buttons
2. **New order** – tap *"📋 New order"* → document list appears
3. **Select document** – tap *"🗺 Visa application"* → quantity prompt with the
   price in EUR (e.g. `35 €`)
4. **Pick quantity** – tap `2` → field questionnaire starts
5. **Fill fields** – answer each field (e.g. type "John Doe" for "Full name")
   → after the last field the cart is updated and delivery choice appears
6. **Delivery** – tap *"✅ Yes, delivery"* → enter delivery details
7. **Payment** – tap *"💰 Proceed to payment"* → cart summary + payment options
8. **Choose payment** – tap *"💳 Card"* → payment details + receipt request
9. **Send fake receipt** – send any photo → you should see *"Order #… accepted!
   Estimated processing time: 5–7 business days."*

### Fast order

1. From main menu tap *"👤 I'm a regular customer"* → intro text
2. Type any message and send → you should see *"Your request has been sent to
   the manager!"*

### Language auto-detection

Change your Telegram client language to **English**, **Russian**, or **Ukrainian**
and repeat the happy path. The bot should use the matching locale.

### Admin panel (optional)

If you set `ADMIN_USERNAME` to your own Telegram handle in `.env`:
- `/orders` – should list the order created above
- `/stats` – should show order counts
- `/help_admin` – admin command reference
- `/send_doc ORDER_…` – send a document back (requires the order ID from
  the manager notification chat)

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