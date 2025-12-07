# BlackBox GPT — Universal AI Assistant

Минималистичный Telegram-бот с режимами, лимитами, профилем и ядром под монетизацию.

## Технологии

- Python 3.10
- aiogram 3.x
- PostgreSQL
- SQLAlchemy async
- DeepSeek API
- Yandex Cloud (VM + systemd)

## Быстрый старт (локально)

```bash
git clone <repo-url> BlackBoxGPT
cd BlackBoxGPT

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# заполни токены и PLANNER_DATABASE_URL

# прогон миграций
make migrate

# запуск бота
make run
```

## Деплой на Yandex Cloud

1. Скопировать код на VM.
2. Создать и активировать venv, установить зависимости.
3. Настроить `.env` в `/home/<user>/BlackBoxGPT/.env`.
4. Скопировать `deploy/blackboxgpt.service.example` в `/etc/systemd/system/blackboxgpt.service` и поправить пути.
5. `sudo systemctl daemon-reload`
6. `sudo systemctl enable blackboxgpt.service`
7. `sudo systemctl start blackboxgpt.service`
8. Смотреть логи: `journalctl -u blackboxgpt.service -f`

## MVP, который покрывает Фазы 0–2

- Чистая структура проекта `bot/`, разделение по слоям.
- Настройки через Pydantic Settings (`config.py`).
- PostgreSQL + миграции (`migrations/*.sql`).
- Модели пользователей, профилей, подписок, рефералок, usage-статистики, платежей.
- LLM-сервис поверх DeepSeek (`services/llm.py`).
- Режимы: Универсальный, Медицина, Наставник, Бизнес, Креатив.
- Профиль пользователя: bio, цели.
- Лимиты по запросам через middleware.
- Таскбар-меню: режимы, профиль, подписка, рефералы.
- Systemd unit для продакшн-запуска на Yandex Cloud.

Следующие фичи (Фазы 3–9) подключаются поверх этого ядра:
оплата, полноценная рефералка, аналитика, очереди, A/B, веб-доступ и т.д.
