import logging
from io import BytesIO

from aiogram import Router, F, Bot
from aiogram.enums import ChatAction
from aiogram.types import Message
from aiogram.types.input_file import BufferedInputFile

from bot.services.storage import get_user_mode, ensure_user
from bot.services.llm import ask_llm
from bot.services import audio

router = Router(name="chat")
logger = logging.getLogger(__name__)


@router.message(F.voice)
async def handle_voice(message: Message, bot: Bot) -> None:
    user = message.from_user
    if user is None:
        return

    await ensure_user(user.id, user.full_name)
    mode = await get_user_mode(user.id)

    # Скачиваем голосовое сообщение
    buf = BytesIO()
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.RECORD_VOICE)
    await bot.download(message.voice.file_id, buf)
    ogg_bytes = buf.getvalue()

    # Распознаём речь
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    text = await audio.speech_to_text(ogg_bytes)
    if not text:
        await message.answer(
            "Не получилось распознать голосовое сообщение. "
            "Попробуй ещё раз или напиши текстом."
        )
        return

    # Отправляем запрос в LLM
    reply_text = await ask_llm(user_message=text, mode=mode, user_id=user.id)

    # Пытаемся озвучить ответ
    tts_bytes = await audio.text_to_speech(reply_text)
    if tts_bytes:
        voice_file = BufferedInputFile(tts_bytes, filename="answer.ogg")
        await message.answer_audio(audio=voice_file, caption=reply_text[:1024])
    else:
        await message.answer(reply_text)


@router.message(F.text)
async def handle_text(message: Message, bot: Bot) -> None:
    # Команды обрабатываются другими роутерами
    if message.text.startswith("/"):
        return

    user = message.from_user
    if user is None:
        return

    await ensure_user(user.id, user.full_name)
    mode = await get_user_mode(user.id)

    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    reply_text = await ask_llm(user_message=message.text, mode=mode, user_id=user.id)
    await message.answer(reply_text)
