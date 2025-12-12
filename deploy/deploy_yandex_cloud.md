# Deploy на Yandex Cloud (Ubuntu)

1. Обновить систему и установить зависимости:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip git postgresql
```

2. Клонировать репозиторий:

```bash
cd /home/bear1berry
git clone https://github.com/bear1berry/BlackBoxGPT_bot.git
cd BlackBoxGPT_bot
```

3. Создать виртуальное окружение и установить зависимости:

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

4. Настроить PostgreSQL и базу `blackboxgpt`, выполнить миграции из `migrations/001_init.sql`.

5. Создать файл `.env` на основе `.env.example`.

6. Скопировать unit-файл сервиса:

```bash
sudo cp deploy/aimedbot.service /etc/systemd/system/aimedbot.service
sudo systemctl daemon-reload
sudo systemctl enable aimedbot.service
sudo systemctl start aimedbot.service
sudo systemctl status aimedbot.service
```

7. Для обновлений кода:

```bash
cd /home/bear1berry/BlackBoxGPT_bot
git pull origin main
source venv/bin/activate
pip install -r requirements.txt  # при изменении зависимостей
sudo systemctl restart aimedbot.service
```
