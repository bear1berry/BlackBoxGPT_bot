from __future__ import annotations

from io import BytesIO

from aiogram import F, Router
from aiogram.types import Message

from bot.services import audio as audio_service
from bot.services.llm import generate_answer
from bot.texts import AUDIO_STT_ERROR_TEXT

router = Router(name="chat")


@router.message(F.voice)
async def handle_voice(message: Message) -> None:
    voice = message.voice
    file = await message.bot.get_file(voice.file_id)

    buffer = BytesIO()
    await message.bot.download_file(file.file_path, destination=buffer)
    audio_bytes = buffer.getvalue()

    try:
        text = await audio_service.speech_to_text(audio_bytes)
    except Exception:
        await message.answer(AUDIO_STT_ERROR_TEXT)
        return

    await message.answer(f"🎙 Распознанный текст:\n<code>{text}</code>")
    reply = await generate_answer(
        user_id=message.from_user.id,
        username=message.from_user.username,
        message=text,
    )
    await message.answer(reply)


@router.message(F.text)
async def handle_text(message: Message) -> None:
    reply = await generate_answer(
        user_id=message.from_user.id,
        username=message.from_user.username,
        message=message.text,
    )
    await message.answer(reply)
