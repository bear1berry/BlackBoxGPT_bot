import asyncio
import logging
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.client.default import DefaultBotProperties

from .config import BOT_TOKEN, PLAN_FREE_DAILY_LIMIT
from .storage import Storage
from .reminders import ReminderStorage, ReminderService, ReminderScheduler
from .planner import PlannerStorage, PlannerService, PlannerAIParser, setup_planner_router
from .llm import ask_llm_stream, analyze_intent
from .payments import create_cryptobot_invoice, is_invoice_paid
from .audio import speech_to_text, text_to_speech

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Globals ---
storage = Storage()
reminder_storage = ReminderStorage()
reminder_service = ReminderService(reminder_storage)
planner_storage = PlannerStorage()
planner_service = PlannerService(planner_storage, PlannerAIParser())

router = Router()
router.include_router(setup_planner_router(planner_service))

# --- Keyboards ---
def get_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧠 Режимы", callback_data="nav:modes"),
         InlineKeyboardButton(text="🗓 Планировщик", callback_data="planner:open")],
        [InlineKeyboardButton(text="💎 Подписка", callback_data="nav:sub"),
         InlineKeyboardButton(text="👤 Профиль", callback_data="nav:profile")]
    ])

def get_modes_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Универсальный", callback_data="mode:universal")],
        [InlineKeyboardButton(text="Медицина", callback_data="mode:medicine"),
         InlineKeyboardButton(text="Бизнес", callback_data="mode:business")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="nav:root")]
    ])

def get_sub_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 Мес ($7.99)", callback_data="subs:1m")],
        [InlineKeyboardButton(text="🔄 Проверить оплату", callback_data="subs:check")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="nav:root")]
    ])

# --- Handlers ---

@router.message(CommandStart())
async def start(msg: Message):
    user, created = storage.get_or_create_user(msg.from_user.id, msg.from_user)
    txt = "👋 **Привет! Я BlackBox GPT.**\n\nЯ твой универсальный ассистент, планировщик и наставник."
    await msg.answer(txt, reply_markup=get_main_kb(), parse_mode="Markdown")

@router.callback_query(F.data == "nav:root")
async def nav_root(call: CallbackQuery):
    await call.message.edit_text("Главное меню:", reply_markup=get_main_kb())

@router.callback_query(F.data == "nav:modes")
async def nav_modes(call: CallbackQuery):
    await call.message.edit_text("Выбери режим работы мозга:", reply_markup=get_modes_kb())

@router.callback_query(F.data.startswith("mode:"))
async def set_mode(call: CallbackQuery):
    mode = call.data.split(":")[1]
    storage.set_mode(call.from_user.id, mode)
    await call.answer(f"Режим: {mode}")
    await call.message.edit_text(f"✅ Установлен режим: **{mode}**", reply_markup=get_main_kb(), parse_mode="Markdown")

@router.callback_query(F.data == "nav:profile")
async def profile(call: CallbackQuery):
    user, _ = storage.get_or_create_user(call.from_user.id, call.from_user)
    txt = (f"👤 **Профиль**\n\nID: `{user.id}`\nПлан: {user.plan_code}\n"
           f"Запросов сегодня: {user.daily_used}")
    await call.message.edit_text(txt, reply_markup=get_main_kb(), parse_mode="Markdown")

@router.callback_query(F.data == "nav:sub")
async def sub_menu(call: CallbackQuery):
    await call.message.edit_text("💎 **Premium Access**\n\nСнимает лимиты и дает доступ к Deep Audit.", reply_markup=get_sub_kb(), parse_mode="Markdown")

@router.callback_query(F.data.startswith("subs:"))
async def sub_action(call: CallbackQuery):
    action = call.data.split(":")[1]
    user, _ = storage.get_or_create_user(call.from_user.id, call.from_user)
    
    if action == "check":
        invoice_id, _ = storage.get_last_invoice(user)
        if invoice_id and await is_invoice_paid(invoice_id):
            storage.activate_premium(user, 1)
            await call.answer("Оплата успешна! Премиум активирован.", show_alert=True)
        else:
            await call.answer("Оплата не найдена.", show_alert=True)
    elif action in ["1m", "3m"]:
        try:
            res = await create_cryptobot_invoice(action)
            storage.store_invoice(user, res['invoice_id'], "month_1") # Simplified
            await call.message.edit_text(f"Оплатите по ссылке:\n{res['pay_url']}", reply_markup=get_sub_kb())
        except Exception as e:
            await call.answer(f"Ошибка создания счета: {e}", show_alert=True)

# --- Message Processor ---

@router.message(F.voice)
async def handle_voice(msg: Message):
    # 1. Download
    f = await msg.bot.get_file(msg.voice.file_id)
    path = f"data/voice_{msg.message_id}.ogg"
    await msg.bot.download_file(f.file_path, path)
    
    # 2. Transcribe
    from pathlib import Path
    text = await speech_to_text(Path(path))
    if not text:
        await msg.answer("Не удалось распознать голос.")
        return
    
    await msg.answer(f"🎤: {text}")
    # Continue as text
    await handle_text(msg, text_override=text)

@router.message(F.text)
async def handle_text(msg: Message, text_override: str = None):
    text = text_override or msg.text
    user, _ = storage.get_or_create_user(msg.from_user.id, msg.from_user)

    # 1. Check Planner Intent
    planner_resp = await planner_service.handle_text(user.id, text)
    if planner_resp:
        await msg.answer(planner_resp)
        return

    # 2. Check Reminder Intent
    reminder_resp = await reminder_service.try_handle_message(user.id, text)
    if reminder_resp:
        await msg.answer(reminder_resp)
        return

    # 3. LLM
    if user.daily_used >= PLAN_FREE_DAILY_LIMIT and user.plan_code == "free":
        await msg.answer("Лимит исчерпан. Купите подписку.")
        return

    storage.log_message(user.id, "user", text)
    sent = await msg.answer("⏳ Думаю...")
    
    full_resp = ""
    async for chunk in ask_llm_stream(text, mode_key=user.mode_key):
        full_resp += chunk.get("delta", "")
        if len(full_resp) % 50 == 0: # Throttle edits
             try: await sent.edit_text(full_resp + "...")
             except: pass
    
    await sent.edit_text(full_resp, parse_mode="Markdown")
    storage.apply_usage(user)
    storage.log_message(user.id, "assistant", full_resp)

# --- Startup ---

async def main():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    dp.include_router(router)
    
    # Start Scheduler
    scheduler = ReminderScheduler(bot, reminder_storage)
    scheduler.start()
    
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot started!")
    try:
        await dp.start_polling(bot)
    finally:
        await scheduler.stop()
