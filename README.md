# BlackBox GPT — Telegram Bot

Универсальный Telegram‑ассистент с режимами (универсальный, медицина, наставник, бизнес, креатив), адаптивным LLM‑ядром (DeepSeek / Perplexity) и поддержкой голоса через Yandex SpeechKit.

## 1. Стек

- Python 3.10
- aiogram 3.13.1
- PostgreSQL (asyncpg + SQLAlchemy 2)
- DeepSeek / Perplexity API
- Yandex Cloud SpeechKit (STT)

## 2. Подготовка окружения

```bash
git clone https://github.com/USERNAME/BlackBoxGPT_bot.git
cd BlackBoxGPT_bot

python -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Настройка .env

Создай файл `.env` в корне проекта и заполни:

```env
BOT_TOKEN=ТВОЙ_TELEGRAM_BOT_TOKEN
ADMIN_IDS=123456789

LLM_PROVIDER=deepseek

DEEPSEEK_API_KEY=...
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

PERPLEXITY_API_KEY=
PERPLEXITY_API_BASE=https://api.perplexity.ai
PERPLEXITY_MODEL=sonar-reasoning

YANDEX_IAM_TOKEN=...
YANDEX_FOLDER_ID=...
YANDEX_TTS_VOICE=filipp
YANDEX_TTS_LANG=ru-RU

CRYPTOPAY_API_TOKEN=

PRICE_1M=7.99
PRICE_3M=25.99
PRICE_12M=89.99

POSTGRES_DSN=postgresql+asyncpg://user:password@localhost:5432/blackboxgpt

LOG_LEVEL=INFO
LLM_TIMEOUT_SEC=120
```

> `ADMIN_IDS` — список id через запятую (например `123,456`), или один id.

## 4. Локальный запуск

```bash
source venv/bin/activate
python -m bot.main
```

Если всё хорошо, в логах увидишь `Start polling`.

## 5. Настройка systemd (Yandex Cloud / Ubuntu)

Создай файл сервиса:

```bash
sudo nano /etc/systemd/system/blackboxgpt.service
```

Содержимое:

```ini
[Unit]
Description=BlackBox GPT Telegram Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/bear1berry/BlackBoxGPT_bot
Environment="PYTHONPATH=/home/bear1berry/BlackBoxGPT_bot"
ExecStart=/home/bear1berry/BlackBoxGPT_bot/venv/bin/python -m bot.main
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Применить и запустить:

```bash
sudo systemctl daemon-reload
sudo systemctl enable blackboxgpt
sudo systemctl start blackboxgpt
```

Проверка статуса и логов:

```bash
sudo systemctl status blackboxgpt
sudo journalctl -u blackboxgpt -f
```

## 6. Голос (Yandex STT)

- Включи SpeechKit в Yandex Cloud.
- Получи `IAM-токен` и `folder_id`.
- Заполни `YANDEX_IAM_TOKEN` и `YANDEX_FOLDER_ID` в `.env`.
- Отправляй голосовые сообщения боту — он распознаёт текст и отвечает.

## 7. Переключение провайдера LLM

В `.env`:

```env
LLM_PROVIDER=deepseek  # или perplexity
```

При наличии ключей бот сам выберет доступного провайдера и корректно обработает временные ошибки.

## 8. Структура проекта

- `bot/main.py` — точка входа
- `bot/config.py` — конфигурация и pydantic Settings
- `bot/handlers/` — хэндлеры сообщений и команд
- `bot/services/` — интеграции с LLM и аудио
- `bot/storage/` — модели БД и репозитории
- `bot/keyboards/` — UI‑клавиатуры
- `bot/texts.py` — текстовые шаблоны и константы
- `bot/utils/` — логирование и утилиты

Проект готов к расширению: можно добавить оплату, рефералы, дополнительные режимы, личный кабинет и т.п.
