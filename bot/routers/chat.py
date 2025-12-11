import asyncio

from aiogram import Router, F
from aiogram.types import Message

from ..services.storage import ensure_user, get_current_mode
from ..services.llm import llm_client, infer_style_from_text
from ..services.analytics import increment_usage, estimate_tokens

router = Router(name="chat")

_MENU_TEXTS = {
    "🧠 Режимы",
    "👤 Профиль",
    "💎 Подписка",
    "👥 Рефералы",
    "⬅️ Назад",
    "🧠 Универсальный",
    "💼 Профессиональный",
    "🔥 Наставник",
    "🩺 Медицина",
    "💎 1 месяц",
    "💎 3 месяца",
    "💎 12 месяцев",
}


@router.message(F.text)
async def handle_chat(message: Message) -> None:
    if not message.text:
        return
    if message.text.startswith("/"):
        return
    if message.text in _MENU_TEXTS:
        return

    tg_user = message.from_user
    user = await ensure_user(tg_user)
    mode = await get_current_mode(user)
    style = infer_style_from_text(message.text)

    thinking_msg = await message.answer("⏳ Думаю над ответом...")

    try:
        parts = []
        async for chunk in llm_client.ask_stream(
            user_prompt=message.text,
            mode=mode,
            style=style,
        ):
            parts.append(chunk)
            await thinking_msg.edit_text("".join(parts))
            await asyncio.sleep(0.05)

        full_text = "".join(parts)
        tokens_used = estimate_tokens(full_text)
        await increment_usage(user["id"], tokens_used)
    except Exception:
        await thinking_msg.edit_text(
            "⚠️ Произошла ошибка при обращении к модели.\n"
            "Попробуй ещё раз чуть позже или измени формулировку запроса."
        )
