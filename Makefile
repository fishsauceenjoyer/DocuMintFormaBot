.PHONY: setup sync lock test lint format run docker-build docker-up clean

# ── Установка ──────────────────────────────────────────────
setup:            ## Первичная настройка: установка uv + окружения
	powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
	uv sync

sync:             ## Синхронизация зависимостей с uv.lock
	uv sync

lock:             ## Пересчитать uv.lock
	uv lock

# ── Тесты и качество ───────────────────────────────────────
test:             ## Запуск всех тестов
	uv run pytest -q

lint:             ## Линтеры и форматтеры
	uv run black --check .
	uv run isort --check-only .
	uv run flake8 .
	uv run mypy .

format:           ## Автоформатирование
	uv run black .
	uv run isort .

# ── Запуск ─────────────────────────────────────────────────
run:              ## Запуск бота
	uv run python main.py

# ── Docker ─────────────────────────────────────────────────
docker-build:     ## Сборка Docker-образа
	docker build -t documintformabot .

docker-up:        ## Запуск через docker compose
	docker compose up -d --build

# ── Очистка ────────────────────────────────────────────────
clean:            ## Удалить venv и кеши
	rm -rf .venv .pytest_cache .mypy_cache htmlcov