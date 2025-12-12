from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.keyboards.main_menu import get_main_menu

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    # Простой онбординг
    await message.answer(
        "👋 Привет! Я BlackBoxGPT — твой универсальный AI-ассистент.\n\n"
        "Я умею:\n"
        "• Отвечать на вопросы в разных режимах (🧠 Режимы)\n"
        "• Помогать с профессиональными темами\n"
        "• Давать советы по здоровью (без диагнозов)\n"
        "• Работать с подпиской и реферальной программой\n\n"
        "Выбери пункт в меню ниже, чтобы начать!",
        reply_markup=get_main_menu()
    )
