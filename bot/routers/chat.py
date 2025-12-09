from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import Message

from bot.keyboards import main_menu_kb
from bot.services.llm import ask_llm
from bot.services.streaming import send_streaming_reply
from bot.texts import build_main_menu_text
from db.crud import (
    add_dialog_message,
    get_last_dialog_messages,
    get_or_create_user,
)

logger = logging.getLogger(__name__)

router = Router(name="chat")


@router.message(F.text & ~F.text.startswith("/"))
async def handle_chat_message(message: Message) -> None:
    tg_user = message.from_user
    if not tg_user:
        await message.answer("⚠️ Не удалось определить пользователя.")
        return

    user, _created = await get_or_create_user(tg_user)
    prompt = message.text.strip()

    # Сохраняем запрос
    await add_dialog_message(user.id, "user", prompt)

    # Получаем последние сообщения диалога
    history = await get_last_dialog_messages(user.id, limit=10)

    # Запрашиваем LLM
    answer = await ask_llm(user, prompt, history)

    # Сохраняем ответ
    await add_dialog_message(user.id, "assistant", answer)

    # Стримим ответ красиво, с уже установленной главной клавиатурой
    await send_streaming_reply(
        message=message,
        text=answer,
        reply_markup=main_menu_kb(),
    )
