from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from ..keyboards import main_menu_keyboard
from ..services.storage import ensure_user

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    payload = ""
    if message.text:
        parts = message.text.split(maxsplit=1)
        if len(parts) == 2:
            payload = parts[1].strip()

    ref_code = None
    if payload.startswith("ref_"):
        ref_code = payload.removeprefix("ref_")

    await ensure_user(message.from_user, ref_code)

    text = (
        "👋 Привет! Я **BlackBoxGPT — твой универсальный AI-ассистент.**\n\n"
        "Я помогу с задачами из работы, жизни, учёбы и медицины (с безопасными ограничениями).\n\n"
        "💡 _Как пользоваться:_\n"
        "• Выбери режим в меню ниже.\n"
        "• Или просто напиши свой первый запрос — я пойму."
    )
    await message.answer(text, reply_markup=main_menu_keyboard())
