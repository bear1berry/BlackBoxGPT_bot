import asyncio
import logging
import os
from typing import Dict

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

import httpx
from dotenv import load_dotenv

# =========================
#   ЗАГРУЗКА НАСТРОЕК
# =========================

# .env ожидается в корне проекта: ~/BlackBoxGPT_bot/.env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in .env")
if not DEEPSEEK_API_KEY:
    raise RuntimeError("DEEPSEEK_API_KEY is not set in .env")

# =========================
#   КЛАВИАТУРЫ
# =========================

MAIN_MENU_KB = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🧠 Режимы")],
        [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="💎 Подписка")],
        [KeyboardButton(text="👥 Рефералы")],
    ],
    resize_keyboard=True,
)

MODES_MENU_KB = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🧠 Универсальный")],
        [KeyboardButton(text="🩺 Медицина"), KeyboardButton(text="🔥 Наставник")],
        [KeyboardButton(text="💼 Бизнес"), KeyboardButton(text="🎨 Креатив")],
        [KeyboardButton(text="⬅️ Назад")],
    ],
    resize_keyboard=True,
)

# user_id -> текущий режим
USER_MODES: Dict[int, str] = {}

MODE_SYSTEM_PROMPTS: Dict[str, str] = {
    "Универсальный": (
        "Ты — универсальный ИИ-ассистент BlackBox GPT. "
        "Отвечай структурировано, по делу, без воды. Пиши на русском языке."
    ),
    "Медицина": (
        "Ты — ИИ-помощник врача. Ты НЕ ставишь диагнозов и НЕ назначаешь лечение. "
        "Ты помогаешь разбираться в исследованиях, симптомах и тактике обращения к врачу. "
        "При любом серьёзном или остром состоянии обязательно рекомендовавешь очный приём."
    ),
    "Наставник": (
        "Ты — личный наставник по развитию личности, дисциплине и продуктивности. "
        "Отвечай прямолинейно, жёстко, но поддерживающе."
    ),
    "Бизнес": (
        "Ты — стратег и консультант по бизнесу и деньгам. Помогаешь искать идеи, "
        "анализировать ниши и выстраивать простые пошаговые планы."
    ),
    "Креатив": (
        "Ты — креативный генератор идей: тексты, сценарии, визуальные концепты. "
        "Не бойся предлагать нестандартные и смелые решения."
    ),
}


# =========================
#   ВЗАИМОДЕЙСТВИЕ С DEEPSEEK
# =========================

async def ask_deepseek(user_id: int, text: str) -> str:
    """Отправка запроса в DeepSeek с учётом выбранного режима пользователя."""
    mode = USER_MODES.get(user_id, "Универсальный")
    system_prompt = MODE_SYSTEM_PROMPTS.get(mode, MODE_SYSTEM_PROMPTS["Универсальный"])

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        "temperature": 0.7,
        "max_tokens": 1200,
    }

    url = f"{DEEPSEEK_BASE_URL}/chat/completions"
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()


# =========================
#   ОСНОВНАЯ ЛОГИКА БОТА
# =========================

async def on_startup(bot: Bot) -> None:
    me = await bot.get_me()
    logging.info("Bot started as @%s (id=%s)", me.username, me.id)


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # ---------- /start ----------
    @dp.message(CommandStart())
    async def cmd_start(message: Message) -> None:
        USER_MODES[message.from_user.id] = "Универсальный"
        text = (
            "<b>BlackBox GPT — Universal AI Assistant</b>\n\n"
            "Я готов работать. Выбери режим через кнопку <b>🧠 Режимы</b> "
            "или сразу задай вопрос — по умолчанию включён универсальный режим."
        )
        await message.answer(text, reply_markup=MAIN_MENU_KB)

    # ---------- Меню режимов ----------
    @dp.message(F.text == "🧠 Режимы")
    async def open_modes(message: Message) -> None:
        await message.answer(
            "Выбери режим работы мозга 🧠:",
            reply_markup=MODES_MENU_KB,
        )

    # ---------- Выбор конкретного режима ----------
    @dp.message(
        F.text.in_(
            ["🧠 Универсальный", "🩺 Медицина", "🔥 Наставник", "💼 Бизнес", "🎨 Креатив"]
        )
    )
    async def set_mode(message: Message) -> None:
        # отрезаем эмодзи и пробел
        label = message.text.split(" ", 1)[1] if " " in message.text else message.text
        USER_MODES[message.from_user.id] = label
        await message.answer(
            f"✅ Режим обновлён: <b>{label}</b>.\n\n"
            "Теперь просто напиши запрос — я буду отвечать в этом режиме.",
            reply_markup=MAIN_MENU_KB,
        )

    # ---------- Назад ----------
    @dp.message(F.text == "⬅️ Назад")
    async def back_to_main(message: Message) -> None:
        await message.answer("Возвращаю на главный экран.", reply_markup=MAIN_MENU_KB)

    # ---------- Профиль ----------
    @dp.message(F.text == "👤 Профиль")
    async def profile(message: Message) -> None:
        mode = USER_MODES.get(message.from_user.id, "Универсальный")
        await message.answer(
            "👤 <b>Профиль</b>\n\n"
            f"Текущий режим: <b>{mode}</b>\n"
            "Память и персонализация будут доступны в следующих версиях.",
            reply_markup=MAIN_MENU_KB,
        )

    # ---------- Подписка ----------
    @dp.message(F.text == "💎 Подписка")
    async def subscription(message: Message) -> None:
        await message.answer(
            "💎 <b>Подписка</b>\n\n"
            "Скоро здесь появится Premium с более мощными моделями и приоритетом в очереди.",
            reply_markup=MAIN_MENU_KB,
        )

    # ---------- Рефералы ----------
    @dp.message(F.text == "👥 Рефералы")
    async def referrals(message: Message) -> None:
        await message.answer(
            "👥 <b>Рефералы</b>\n\n"
            "Реферальная программа в разработке. "
            "В будущих версиях ты сможешь получать бонусы за приглашённых друзей.",
            reply_markup=MAIN_MENU_KB,
        )

    # ---------- Основной чат ----------
    @dp.message(F.text)
    async def chat(message: Message) -> None:
        try:
            await message.answer("⌛ Обрабатываю запрос, дай мне пару секунд...")
            answer = await ask_deepseek(message.from_user.id, message.text)
            await message.answer(answer)
        except httpx.HTTPStatusError as e:
            logging.exception("DeepSeek HTTP error")
            await message.answer(
                "⚠️ <b>Ошибка при обращении к модели</b>.\n"
                "Попробуй повторить запрос чуть позже.\n\n"
                f"Тех. деталь: {e.response.status_code}"
            )
        except Exception:
            logging.exception("Unexpected error in chat handler")
            await message.answer(
                "⚠️ <b>Непредвиденная ошибка</b>.\n"
                "Я уже записал это в лог. Попробуй ещё раз сформулировать запрос."
            )

    # ---------- Запуск ----------
    await on_startup(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
