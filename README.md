# DocuMintFormaBot 🗺

**Telegram bot for document ordering services** — a complete order-processing FSM
(Finite State Machine) with multi-language support, inline keyboards, cart
management, delivery/payment options, and a manager/admin panel.

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
- 💳 **Payment methods** — configurable (demo: Blik, UAH card, USDT)
- 📤 **Order routing** — each document type can be forwarded to a different
  manager chat
- ⚡ **Fast order** — regular customers can send a free-form message bypassing
  the step-by-step wizard
- 🆘 **Contact manager** — help button forwards user info to support
- 📦 **Manager panel** — send ready documents and tracking numbers back to clients
- 📊 **Stats** — `/orders`, `/stats` for the admin
- 🐳 **Docker-ready** — multi-stage build + `docker-compose.yml`

---

## Screenshots

See [docs/README.md](docs/README.md) for the full screenshot gallery.

| Main menu | Document selection | Field filling | Payment |
|---|---|---|---|
| ![Main menu](docs/screenshots/main_menu.png) | ![Document choice](docs/screenshots/document_choice.png) | ![Field filling](docs/screenshots/field_filling.png) | ![Payment](docs/screenshots/payment.png) |

> 📸 **Note:** Screenshots are placeholder images. Run the bot locally and
> replace them with real captures from your Telegram client.

---

## Project structure
>>>>>>>
</replace_in_file>
<task_progress>- [x] Stage 4 completed and pushed
- [x] Create branch feat/deploy-and-documentation
- [x] Add Redis service to docker-compose.yml
- [x] REDIS_URL already in .env.example
- [x] Create docs/README.md with screenshot placeholders
- [x] Add Screenshots section to README.md
- [ ] Add Переменные окружения section to README.md
- [ ] Commit and push Stage 5</task_progress>

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
├── tests/                   # Pytest unit tests (failover-ready)
├── Dockerfile               # Multi-stage build
├── docker-compose.yml       # Bot + optional Redis
└── .env.example             # Environment variable template
```

---

## Quick start

### 1. Clone & setup environment

```bash
# Clone the repository
git clone https://github.com/fishsauceenjoyer/DocuMintFormaBot.git
cd DocuMintFormaBot

# Create virtual environment (Windows)
python -m venv .venv
.venv\Scripts\activate

# Create virtual environment (Linux / Mac)
# python -m venv .venv
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure `.env`

```bash
cp .env.example .env
```

Edit `.env` in any text editor. Minimum required changes:

| Variable | Description | How to get |
|----------|-------------|------------|
| `BOT_TOKEN` | Telegram bot token | Create a bot via [@BotFather](https://t.me/BotFather) → `/newbot` |
| `ADMIN_USERNAME` | Your Telegram username | Open Telegram → Settings → Username (e.g. `@yourname`) |
| `ROUTING_DEFAULT` | Chat ID for manager | See instructions below |

**How to get a chat ID:**
1. Add [@userinfobot](https://t.me/userinfobot) to your contacts
2. Forward any message to it → it replies with your chat ID
3. Create a **private group** → add the bot → send `/id` → get group chat ID
4. Use this ID in `ROUTING_DEFAULT` and other `ROUTING_*` variables

### 3. Run

```bash
# Locally
python main.py

# Or with Docker
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

# Payment details — shown to customer after order
PAYMENT_BLIK="Blik przelew na numer telefonu: ..."
PAYMENT_UAH="Перевод на гривневую карту: ..."
PAYMENT_USDT="USDT (TRC20): ..."

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

### Switching business configuration

The repository ships with **two** business config files:

| File | Purpose |
|------|---------|
| `data/business_config.py` | **Active** — demo "consular services" (visa, passport, etc.) |
| `data/business_config_original.py` | **Reference** — original data (sanepid, BHP, PESEL, psychotests) — **not imported** |

To switch back to the original configuration:

1. Rename files:
   ```bash
   mv data/business_config.py data/business_config_demo.py      # keep demo as backup
   mv data/business_config_original.py data/business_config.py  # activate original
   ```
2. Update `.env` — replace routing variable names and chat IDs:

   | Demo variable | Original variable |
   |---|---|
   | `ROUTING_VISA` | `ROUTING_SANEPID` |
   | `ROUTING_PASSPORT` | `ROUTING_BHP` |
   | `ROUTING_CRIMINAL_RECORD` | `ROUTING_PSYCHOTESTS` |
   | `ROUTING_APOSTILLE` | `ROUTING_PESEL` |

3. (Optional) Reset `locales/` strings if the original payment methods are used.


---

## Переменные окружения

Полный шаблон со всеми переменными находится в [`.env.example`](.env.example).
Скопируйте его перед запуском:

```bash
cp .env.example .env
```

| Переменная | Обязательна | Описание |
|---|---|---|
| `BOT_TOKEN` | ✅ | Токен бота от [@BotFather](https://t.me/BotFather) |
| `ADMIN_USERNAME` | ✅ | Имя пользователя админа в Telegram (без `@`) |
| `ROUTING_VISA` | ✅ | Chat ID для заказов на визу |
| `ROUTING_PASSPORT` | ✅ | Chat ID для заказов на загранпаспорт |
| `ROUTING_CRIMINAL_RECORD` | ✅ | Chat ID для справок о несудимости |
| `ROUTING_APOSTILLE` | ✅ | Chat ID для апостиля |
| `ROUTING_DEFAULT` | ✅ | Chat ID по умолчанию (fallback) |
| `MANAGER_ID` | ❌ | Chat ID для fallback-уведомлений об ошибках |
| `PAYMENT_BLIK` | ❌ | Реквизиты Blik |
| `PAYMENT_UAH` | ❌ | Реквизиты UAH-перевода |
| `PAYMENT_USDT` | ❌ | USDT-кошелёк |
| `DATABASE_URL` | ❌ | URL базы данных (SQLite / PostgreSQL / MySQL) |
| `REDIS_URL` | ❌ | URL Redis для FSM (опционально, для продакшена) |

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

## Running tests

```bash
# Default — all tests use mocks (no Telegram API needed)
pytest -v

# If you have a real bot token and network — test real API
pytest -v --with-real-api

# All tests with coverage
pytest --cov=. -v
```

## Database migrations

This project uses **Alembic** for schema versioning. The initial migration
`migrations/versions/138da28f5512_initial_schema.py` captures the current SQLAlchemy
models (`users`, `document_types`, `orders`, `order_items`).

### First-time setup

```bash
# Install Alembic if not already present
pip install alembic

# Apply all migrations to the local SQLite database
alembic upgrade head
```

### Common commands

```bash
# Create a new empty migration
alembic revision -m "describe your change"

# Autogenerate a migration from model changes (best-effort; review before applying)
alembic revision --autogenerate -m "describe your change"

# Apply migrations
alembic upgrade head

# Downgrade one step
alembic downgrade -1

# Show current revision
alembic current
```

### Switching environments

`migrations/env.py` reads `DATABASE_URL` from the environment, so the same
migrations work for SQLite, PostgreSQL, and MySQL without code changes:

```env
# Local development
DATABASE_URL=sqlite:///bot.db

# Production
DATABASE_URL=postgresql://user:pass@host/db
```

The test suite has a **failover mechanism**: by default all tests use mocked
Telegram objects and run completely offline. Pass `--with-real-api` to test
against the live Telegram API (requires `BOT_TOKEN` + internet connectivity).
The connectivity probe (`test_telegram_api_dns_resolves`) runs every session
and switches all downstream tests to mocks when the API is unreachable.

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
8. **Choose payment** – tap *"💳 Blik"* → payment details + receipt request
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

## Uploading changes to GitHub from VS Code

### First time setup

1. **Create a Personal Access Token** on GitHub:
   - Go to https://github.com/settings/tokens
   - Click **Generate new token (classic)**
   - Select scopes: `repo` (full control)
   - Click **Generate token**
   - **Copy the token** — it looks like `ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXX`
   - Save it somewhere safe (you won't see it again)

2. **Configure the remote** (one time):
   ```bash
   git remote add origin https://github.com/fishsauceenjoyer/DocuMintFormaBot.git
   ```

3. **Push the branch** (enter your GitHub username and the token as password):
   ```bash
   git push -u origin feat/payment-methods-rename
   ```
   - Username: `fishsauceenjoyer`
   - Password: paste your **token** (`ghp_...`)

### Each subsequent change

**Option A — VS Code GUI (recommended):**
1. Open **Source Control** tab (Ctrl+Shift+G)
2. Stage files (click `+` next to each file)
3. Write a commit message
4. Click **Commit**
5. Click **Sync Changes** or **Push**

**Option B — Terminal:**
```bash
git add .
git commit -m "feat: description of your change"
git push
```

### If VS Code asks for credentials

On Windows, VS Code may store your token in **Windows Credential Manager**:
1. Open **Control Panel** → **Credential Manager** → **Windows Credentials**
2. Under "Generic Credentials", find `git:https://github.com`
3. Edit and replace the password with your new token

---

## License

MIT