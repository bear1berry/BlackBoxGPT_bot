# BlackBoxGPT — Universal AI Assistant (Telegram)

Минималистичный Telegram-бот с двумя режимами (DeepSeek / Pro с Perplexity+WEB), подписками через CryptoPay (CryptoBot), рефералкой, лимитами, памятью и стримингом ответа.

## 1) Что умеет (Level 1–3)

- 🧠 **Единый мозг**: контекст диалога (SQLite), простая “память” + стиль пользователя.
- 💬 **Один интерфейс**: вся навигация через нижнее меню (ReplyKeyboard).
- 💰 **Подписки + рефералка**:
  - CryptoPay (CryptoBot) — USDT, авто-активация по webhook и авто-проверка статусов.
  - Реф-ссылка, статистика по приведённым и Premium.
- 🎯 **Адаптация под стиль**: длина сообщений/эмодзи/мат → параметры стиля в prompt.
- 🧠 **Режимы**:
  - Универсальный — DeepSeek (без WEB)
  - Профессиональный — DeepSeek + Perplexity (WEB-исследование), структурная выдача

**Важное:** инлайн-кнопок нет, кроме одной — `➡️ Продолжить` для длинных ответов.

---

## 2) Быстрый запуск (локально)

### Требования
- Python 3.10+
- Telegram Bot Token
- DeepSeek API key (обязательно)
- Perplexity API key (опционально, для WEB-режима)
- CryptoPay API token (обязательно для оплаты)

### Установка
```bash
git clone <your_repo_url>
cd BlackBoxGPT_bot

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env
```

Открой `.env` и заполни:
- `BOT_TOKEN`, `BOT_USERNAME`
- `LOG_LEVEL` (опционально, INFO/WARNING/ERROR)
- `DEEPSEEK_API_KEY`
- `PERPLEXITY_API_KEY` (если нужен WEB)
- `CRYPTOPAY_API_TOKEN`
- `CRYPTOPAY_WEBHOOK_SECRET` (случайная строка)

### Запуск
```bash
python -m bot.main
```

Проверка:
- `GET http://<host>:8080/health` → `{"ok": true}`

---

## 3) Webhook для CryptoPay

CryptoPay шлёт POST на HTTPS URL.  
Маршрут в проекте:

```
POST /cryptopay/webhook/<CRYPTOPAY_WEBHOOK_SECRET>
```

**Как включить:**
1) Открой @CryptoBot → Crypto Pay → My Apps → выбери app → Webhooks → Enable  
2) Укажи URL: `https://YOUR_DOMAIN/cryptopay/webhook/<secret>`

> Если у тебя пока нет домена/HTTPS — используй nginx + TLS (Let’s Encrypt), либо проксируй через Cloudflare.

---

## 4) Деплой на Ubuntu + systemd (пример)

### systemd unit
Файл: `systemd/blackboxgpt.service`

1) Скопируй в `/etc/systemd/system/blackboxgpt.service`
2) Заполни пути (WORKDIR) и пользователя
3) Включи:
```bash
sudo systemctl daemon-reload
sudo systemctl enable blackboxgpt
sudo systemctl restart blackboxgpt
sudo journalctl -u blackboxgpt -n 200 --no-pager
```

---

## 5) Где менять логику

- Режимы / промты: `services/llm/prompts.py`
- Оркестратор (DeepSeek + Perplexity): `services/llm/orchestrator.py`
- Лимиты: `services/limits.py`
- Оплаты: `services/crypto_pay.py`, `services/payments.py`, `services/jobs.py`
- Меню/UX тексты: `bot/texts.py`, `bot/keyboards.py`

---

## 6) Безопасность

- Webhook проверяется по `crypto-pay-api-signature`.
- Режим «медицина»: обязательный дисклеймер + жёсткий запрет на дозировки.

---

## License
MIT (если нужно — замени под свой проект)
