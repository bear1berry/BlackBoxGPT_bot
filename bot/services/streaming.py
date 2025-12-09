from __future__ import annotations

import asyncio
from typing import Optional

from aiogram.types import Message, ReplyKeyboardMarkup


async def send_streaming_reply(
    message: Message,
    text: str,
    reply_markup: Optional[ReplyKeyboardMarkup] = None,
    chunk_chars: int = 600,
    delay: float = 0.25,
) -> None:
    """Fake streaming: gradually extends a single message with chunks of text.

    Это не стрим напрямую из модели, но визуально создаёт эффект
    «набирающегося» ответа.
    """
    text = (text or "").strip()
    if not text:
        return

    # Разбиваем текст на логические блоки
    parts = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current: str = ""

    for part in parts:
        if not current:
            current = part
            continue

        if len(current) + 2 + len(part) <= chunk_chars:
            current = current + "\n\n" + part
        else:
            chunks.append(current)
            current = part

    if current:
        chunks.append(current)

    if not chunks:
        chunks = [text]

    # Отправляем первый блок
    sent = await message.answer(chunks[0], reply_markup=reply_markup)

    # Если блок всего один — стримить нечего
    if len(chunks) == 1:
        return

    # Добавляем остальные куски с задержкой, редактируя то же сообщение
    for block in chunks[1:]:
        await asyncio.sleep(delay)
        new_text = (sent.text or "") + "\n\n" + block
        await sent.edit_text(new_text)
