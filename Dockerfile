# ============================================
# Dockerfile for DocuMintFormaBot (uv)
# ============================================

# Stage 1: Build stage
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

WORKDIR /app

# Копируем манифесты зависимостей
COPY pyproject.toml uv.lock ./

# Устанавливаем зависимости в виртуальное окружение
# --frozen — используем uv.lock без пересчёта
# --no-dev — не ставим dev-зависимости в продакшн
RUN uv sync --frozen --no-dev --no-install-project

# Stage 2: Runtime stage
FROM python:3.11-slim AS runtime

WORKDIR /app

# Копируем uv в runtime (нужен для uv run / uv sync при старте)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Копируем установленные пакеты из builder
COPY --from=builder /app/.venv /app/.venv

# Копируем приложение
COPY . .

# Создаём .env из примера, если нет
RUN if [ ! -f .env ]; then cp .env.example .env; fi

# Путь к venv
ENV PATH="/app/.venv/bin:$PATH"

# Expose port (не используется для polling, но для healthcheck)
EXPOSE 8080

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "from config import validate_config; validate_config()" || exit 1

# Запуск бота через uv run
CMD ["uv", "run", "python", "main.py"]