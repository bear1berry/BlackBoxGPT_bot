from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.services.llm import LLMClient
from bot.services.text_postprocess import prepare_answer

router = Router()

# Определяем состояния
class ChatState(StatesGroup):
    waiting_for_message = State()

llm_client = LLMClient()

@router.message()
async def handle_message(message: Message, state: FSMContext):
    # Если пользователь ввел текст, обрабатываем его
    if message.text and message.text not in ["🧠 Режимы", "👤 Профиль", "💎 Подписка", "👥 Рефералы", "⬅️ Назад"]:
        # Устанавливаем состояние, чтобы в будущем можно было обрабатывать диалог
        await state.set_state(ChatState.waiting_for_message)
        
        # Отправляем сообщение о том, что бот думает
        thinking_msg = await message.answer("🤔 Думаю над ответом...")
        
        # Получаем ответ от LLM
        response_text = ""
        try:
            # В данном примере используем не потоковый ответ, но можно переделать на потоковый
            response_text = await llm_client.ask(message.text, mode="universal")
        except Exception as e:
            response_text = f"Произошла ошибка при получении ответа: {e}"
        
        # Обрабатываем ответ (очистка, форматирование)
        processed_text = prepare_answer(response_text)
        
        # Отправляем обработанный ответ
        await thinking_msg.edit_text(processed_text)
        
        # Сбрасываем состояние
        await state.clear()
