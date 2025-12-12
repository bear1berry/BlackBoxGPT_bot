from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Text
from aiogram.fsm.context import FSMContext

from bot.keyboards.main_menu import get_main_menu, get_modes_menu
from bot.keyboards.common import get_back_keyboard

router = Router()

@router.message(Text("🧠 Режимы"))
async def modes_menu(message: Message, state: FSMContext):
    await message.answer(
        "Выбери режим общения:\n\n"
        "• *Универсальный* — для повседневных вопросов\n"
        "• *Профессиональный* — для сложных задач\n"
        "• *Наставник* — для дисциплины и целей\n"
        "• *Медицина* — общие рекомендации по здоровью\n\n"
        "Выбор режима повлияет на стиль и глубину ответов.",
        reply_markup=get_modes_menu(),
        parse_mode="Markdown"
    )

@router.message(Text("⬅️ Назад"))
async def back_to_main(message: Message, state: FSMContext):
    await message.answer("Главное меню:", reply_markup=get_main_menu())

# Обработчики выбора режима
@router.message(Text("Универсальный"))
async def set_universal_mode(message: Message, state: FSMContext):
    # Здесь должна быть логика сохранения режима в БД
    await message.answer("Режим *Универсальный* активирован. Теперь я буду отвечать в повседневном стиле.", parse_mode="Markdown")

@router.message(Text("Профессиональный"))
async def set_professional_mode(message: Message, state: FSMContext):
    await message.answer("Режим *Профессиональный* активирован. Готов к сложным задачам и глубокому анализу.", parse_mode="Markdown")

@router.message(Text("Наставник"))
async def set_mentor_mode(message: Message, state: FSMContext):
    await message.answer("Режим *Наставник* активирован. Буду помогать с дисциплиной и достижением целей.", parse_mode="Markdown")

@router.message(Text("Медицина"))
async def set_medical_mode(message: Message, state: FSMContext):
    await message.answer(
        "Режим *Медицина* активирован.\n\n"
        "⚠️ *Внимание*: Я не ставлю диагнозы и не назначаю лечение. Мои ответы носят информационный характер. При серьезных симптомах обратитесь к врачу.",
        parse_mode="Markdown"
    )
