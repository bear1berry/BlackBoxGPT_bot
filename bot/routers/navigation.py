from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from bot.keyboards.reply import main_menu_kb
from bot.keyboards.inline import modes_kb, profile_kb, subscription_kb, referrals_kb
from bot.services.storage import set_user_mode, get_user_mode, ensure_user
from bot.texts import mode_changed_text, main_menu_text

router = Router(name="navigation")


@router.message(F.text == "🧠 Режимы")
async def open_modes(message: Message) -> None:
    user = message.from_user
    if user is None:
        return

    await ensure_user(user.id, user.full_name)
    await message.answer("Выбери режим работы бота:", reply_markup=modes_kb())


@router.message(F.text == "👤 Профиль")
async def open_profile(message: Message) -> None:
    user = message.from_user
    if user is None:
        return

    await ensure_user(user.id, user.full_name)
    user_mode = await get_user_mode(user.id)
    text = (
        "👤 <b>Профиль</b>\n\n"
        f"Текущий режим: <b>{user_mode}</b>\n\n"
        "Скоро здесь появятся дополнительные настройки и персонализация."
    )
    await message.answer(text, reply_markup=profile_kb())


@router.message(F.text == "💎 Подписка")
async def open_subscription(message: Message) -> None:
    await message.answer(
        "💎 <b>Подписка</b>\n\n"
        "Премиум-функции находятся в разработке. "
        "Здесь появятся тарифы и оплата через Crypto Bot / Crypto Pay.",
        reply_markup=subscription_kb(),
    )


@router.message(F.text == "👥 Рефералы")
async def open_referrals(message: Message) -> None:
    await message.answer(
        "👥 <b>Реферальная программа</b>\n\n"
        "Здесь будет твоя персональная ссылка и статистика приглашённых пользователей.",
        reply_markup=referrals_kb(),
    )


@router.callback_query(F.data == "nav:back_main")
async def cb_back_main(callback: CallbackQuery) -> None:
    await callback.message.edit_text(main_menu_text(), reply_markup=None)
    await callback.message.answer("Главное меню ниже 👇", reply_markup=main_menu_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("mode:"))
async def cb_change_mode(callback: CallbackQuery) -> None:
    user = callback.from_user
    if user is None or callback.data is None:
        await callback.answer()
        return

    mode = callback.data.split(":", 1)[1]
    await set_user_mode(user.id, mode)

    text = mode_changed_text(mode)
    try:
        await callback.message.edit_text(text, reply_markup=None)
    except Exception:
        await callback.message.answer(text)

    await callback.message.answer(main_menu_text(), reply_markup=main_menu_kb())
    await callback.answer("Режим обновлён")
