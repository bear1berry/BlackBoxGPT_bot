from __future__ import annotations

from aiogram import Router, F
from aiogram.types import Message

from ..db.db import db
from ..services.storage import ensure_user
from ..services.llm import llm_client, Mode
from ..services.analytics import add_usage_stat
from ..services.usage_limits import check_message_limit
from ..keyboards.main_menu import subscription_keyboard

router = Router()


async def _get_user_mode(user_id: int) -> Mode:
    row = await db.fetchrow(
        "SELECT current_mode FROM users WHERE id = $1",
        user_id,
    )
    if not row:
        return Mode.UNIVERSAL

    raw = row["current_mode"] or "universal"
    try:
        return Mode(raw)
    except ValueError:
        return Mode.UNIVERSAL


@router.message(F.text, ~F.text.startswith("/"))
async def handle_chat(message: Message) -> None:
    # 1. Гарантируем, что пользователь есть в БД
    user_row = await ensure_user(message.from_user)

    # 2. Проверяем лимиты (бесплатный / Premium)
    ok, limit_text = await check_message_limit(user_row["id"])
    if not ok:
        # Лимит превышен — показываем текст + предлагаем оформить подписку
        await message.answer(limit_text, reply_markup=subscription_keyboard)
        return

    # 3. Определяем текущий режим (универсальный / профессиональный)
    mode = await _get_user_mode(user_row["id"])

    # 4. Запрашиваем ответ у LLM (стримингом внутри клиента)
    chunks: list[str] = []
    async for part in llm_client.ask_stream(message.text, mode):
        chunks.append(part)

    answer = "".join(chunks).strip()
    if not answer:
        await message.answer(
            "⚠️ Произошла ошибка при обращении к модели.\n"
            "Попробуй ещё раз немного позже."
        )
        return

    await message.answer(answer)

    # 5. Фиксируем факт использования (для статистики и лимитов)
    await add_usage_stat(user_row["id"], tokens_used=0)
