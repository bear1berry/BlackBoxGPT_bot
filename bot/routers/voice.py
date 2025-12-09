from __future__ import annotations

import logging
from pathlib import Path

from aiogram import Router, F
from aiogram.types import Message, FSInputFile

from bot.services import storage, llm, yandex_voice


router = Router(name="voice-router")
logger = logging.getLogger(__name__)

TEMP_DIR = Path("temp_voice")


@router.message(F.voice)
async def handle_voice(message: Message) -> None:
    user = message.from_user
    if user is None:
        return

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    ogg_in = TEMP_DIR / f"in_{message.voice.file_id}.ogg"

    # Скачиваем голосовое
    await message.bot.download(message.voice, destination=ogg_in)

    try:
        text = await yandex_voice.stt_from_file(ogg_in)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Yandex STT error: %s", exc)
        await message.answer(
            "⚠️ Не удалось распознать голос. Попробуй ещё раз или напиши текстом."
        )
        return

    mode = await storage.get_user_mode(user.id)
    profile = await storage.get_profile(user.id)

    await message.answer(f"📝 Распознанный текст:\n\n<code>{text}</code>")

    reply_text = await llm.ask_llm(
        user_id=user.id,
        mode=mode,
        user_text=text,
        profile=profile,
    )

    try:
        ogg_out = await yandex_voice.tts_to_file(reply_text, TEMP_DIR)
        voice_file = FSInputFile(ogg_out)
        await message.answer_voice(
            voice=voice_file,
            caption="🗣 Ответ голосом (Yandex TTS)",
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Yandex TTS error: %s", exc)
        await message.answer(reply_text)
