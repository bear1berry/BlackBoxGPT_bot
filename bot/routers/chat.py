# bot/routers/chat.py
from __future__ import annotations
import io
import logging

from aiogram import Router, F
from aiogram.types import Message

from ..db import get_session
from ..models import User
from ..keyboards import main_menu_keyboard
from ..texts import format_llm_answer
from ..services.perplexity import ask_perplexity, ModeType
from ..services.referrals import get_or_create_user
from ..services.yandex_speech import recognize_speech, synthesize_speech

router = Router(name="chat")
logger = logging.getLogger(__name__)


async def _ensure_user(message: Message) -> User:
    async with (await get_session()) as session:
        user = await get_or_create_user(session, message.from_user)
        return user


@router.message(F.voice)
async def handle_voice(message: Message) -> None:
    """
    Обработка голосовых сообщений:
    — скачиваем ogg/opus,
    — отправляем в Yandex STT,
    — обрабатываем запрос через Perplexity.
    """
    bot = message.bot
    user = await _ensure_user(message)

    # скачиваем файл
    file = await bot.get_file(message.voice.file_id)
    buf = io.BytesIO()
    await bot.download_file(file.file_path, destination=buf)
    audio_bytes = buf.getvalue()

    await message.answer("🎧 Распознаю голосовое сообщение…")

    text = await recognize_speech(audio_bytes)
    if not text:
        await message.answer(
            "😔 Не удалось распознать голос. Попробуй ещё раз — желательно говорить ближе к микрофону."
        )
        return

    await message.answer(
        f"🗣 Распознанный текст:\n<i>{text}</i>\n\nОбрабатываю запрос…"
    )

    mode: ModeType = user.current_mode if user.current_mode in (
        "universal", "medicine", "mentor", "business", "creative"
    ) else "universal"

    system_prompt = (
        "Ты — умный ассистент BlackBox GPT. Отвечай структурировано, как крутая статья: "
        "заголовки, списки, чёткие шаги, минимум воды."
    )
    answer = await ask_perplexity(mode=mode, user_prompt=text, system_prompt=system_prompt)

    answer = format_llm_answer(answer)

    await bot.send_chat_action(message.chat.id, "typing")
    await message.answer(answer, reply_markup=main_menu_keyboard())

    # Если захочешь озвучивать ответ:
    # audio = await synthesize_speech(answer)
    # if audio:
    #     await message.answer_voice(audio)


@router.message(F.text & ~F.text.startswith("/"))
async def handle_text(message: Message) -> None:
    """
    Любой текст, который не команда — это запрос к модели.
    """
    bot = message.bot
    async with (await get_session()) as session:
        user = await get_or_create_user(session, message.from_user)
        mode: ModeType = (
            user.current_mode
            if user.current_mode in ("universal", "medicine", "mentor", "business", "creative")
            else "universal"
        )

    user_prompt = message.text

    system_prompt = (
        "Ты — умный ассистент BlackBox GPT. Отвечай структурировано, как крутая статья: "
        "используй подзаголовки, списки, выделяй ключевые мысли, не лей воду и не уходи в лишнюю философию."
    )

    await bot.send_chat_action(message.chat.id, "typing")
    answer = await ask_perplexity(mode=mode, user_prompt=user_prompt, system_prompt=system_prompt)
    answer = format_llm_answer(answer)

    await message.answer(answer, reply_markup=main_menu_keyboard())
