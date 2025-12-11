# Деплой BlackBoxGPT в Yandex Cloud

## 1. Виртуальная машина

1. Создай ВМ на Ubuntu 22.04 в Yandex Cloud.
2. Открой порты 22 (SSH) и выход в интернет.

## 2. Базовая подготовка сервера

```bash
sudo apt update && sudo apt install -y git python3 python3-venv python3-pip postgresql-client
```

## 3. Репозиторий и виртуальное окружение

```bash
cd ~
git clone <твоя-ssш-ссылка-на-репозиторий> BlackBoxGPTBot
cd BlackBoxGPTBot

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Настройка БД и миграций

1. Создай базу PostgreSQL (Managed PostgreSQL или локально).
2. Выпиши DSN в формате:

```text
postgresql://user:password@host:5432/blackboxgpt
```

3. Заполни `.env` на основе `.env.example`.

4. Прогон миграций (из корня проекта):

```bash
export DB_DSN="postgresql://user:password@host:5432/blackboxgpt"
psql "$DB_DSN" -f migrations/001_init.sql
```

## 5. Локальный тест

```bash
source venv/bin/activate
python -m bot.main
```

Убедись, что бот отвечает в Telegram.

## 6. Systemd-сервис

```bash
sudo nano /etc/systemd/system/aimedbot.service
```

Вставь содержимое из `deploy/aimedbot.service`, подправь:

- `User=` — на имя своего пользователя;
- `WorkingDirectory=` и `EnvironmentFile=` — на путь к папке проекта;
- `ExecStart=` — на путь к Python в venv.

Затем:

```bash
sudo systemctl daemon-reload
sudo systemctl enable aimedbot.service
sudo systemctl start aimedbot.service

sudo systemctl status aimedbot.service
journalctl -u aimedbot.service -f
```

## 7. Следующие шаги

- Подключить вебхуки Crypto Pay (отдельный endpoint или отдельный сервис).
- Вынести LLM и веб-поиск в микросервисы при росте нагрузки.
- Добавить мониторинг (Prometheus, Grafana, Sentry и т.п.).
