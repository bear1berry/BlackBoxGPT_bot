from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from bot.keyboards import kb_main
from bot import texts
from services import users as users_repo


router = Router()


@router.message(CommandStart(deep_link=True))
async def cmd_start(message: Message) -> None:
    bot = message.bot
    db = bot["db"]
    settings = bot["settings"]

    ref_code = (message.text or "").split(maxsplit=1)[1].strip() if len((message.text or "").split()) > 1 else ""
    referrer_id = None
    if ref_code:
        referrer_id = await users_repo.find_user_by_ref_code(db, ref_code)
        if referrer_id == message.from_user.id:
            referrer_id = None

    await users_repo.ensure_user(
        db,
        message.from_user.id,
        referrer_id=referrer_id,
        ref_salt=settings.bot_token[:16],
    )

    await message.answer(texts.WELCOME_1, reply_markup=kb_main())
    await message.answer(texts.WELCOME_2, reply_markup=kb_main())
    await message.answer(texts.WELCOME_3, reply_markup=kb_main())


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "🧠 <b>Помощь</b>\n\n"
        "• Выбери режим в «🧠 Режимы»\n"
        "• Подписка — «💎 Подписка»\n"
        "• Профиль и лимиты — «👤 Профиль»\n"
        "• Рефералы — «👥 Рефералы»\n\n"
        "Пиши вопрос обычным сообщением — я отвечу.",
        reply_markup=kb_main(),
    )
