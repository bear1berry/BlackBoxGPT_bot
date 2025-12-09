from __future__ import annotations

import logging

from aiogram import Router, F
from aiogram.types import Message

from bot.services import storage, llm


router = Router(name="chat-router")
logger = logging.getLogger(__name__)


@router.message(F.text)
async def handle_text(message: Message) -> None:
    """
    Основной диалоговый обработчик.
    Все сообщения, которые не поймали другие роутеры, попадают сюда.
    """
    user = message.from_user
    if user is None:
        return

    text = message.text or ""
    if text.startswith("/"):
        # Не перехватываем сервисные команды
        return

    mode = await storage.get_user_mode(user.id)
    profile = await storage.get_profile(user.id)

    await message.answer_chat_action("typing")

    reply = await llm.ask_llm(
        user_id=user.id,
        mode=mode,
        user_text=text,
        profile=profile,
    )

    await message.answer(reply)
