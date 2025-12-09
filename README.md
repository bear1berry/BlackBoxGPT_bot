# BlackBox GPT — Universal AI Assistant

Telegram-бот на базе `aiogram 3`, DeepSeek / Perplexity и Yandex SpeechKit.

## Быстрый старт

1. Склонируй репозиторий и перейди в папку проекта.
2. Создай и активируй виртуальное окружение Python 3.10+.
3. Установи зависимости:

   ```bash
   pip install -r requirements.txt
   ```

4. Создай файл `.env` на основе `.env.example` и заполни переменные:
   * `BOT_TOKEN` — токен Telegram-бота.
   * `DEEPSEEK_*` / `PERPLEXITY_*` — ключи и настройки моделей.
   * `YANDEX_*` — токен и настройки Yandex SpeechKit.

5. Запусти бота локально:

   ```bash
   python -m bot.main
   ```

6. Для продакшена создай `systemd`-юнит и укажи команду запуска:

   ```bash
   /home/<user>/BlackBoxGPT_bot/venv/bin/python -m bot.main
   ```

Структура кода разделена на:

* `bot/config.py` — конфигурация и загрузка `.env`.
* `bot/routers/` — обработчики команд, навигации и чата.
* `bot/services/` — обращение к LLM и Yandex SpeechKit, простое хранилище пользователей.
* `bot/keyboards/` — клавиатуры.
* `data/users.json` — простое JSON-хранилище профилей и режима пользователя.
