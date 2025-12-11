from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from ..config import settings
from ..keyboards.main_menu import (
    BACK_BUTTON_TEXT,
    main_menu_keyboard,
    modes_keyboard,
    subscription_keyboard,
    referrals_keyboard,
)
from ..services.llm import Mode
from ..services.payments_crypto import (
    PLANS,
    create_invoice_for_user,
    refresh_user_payments_and_subscriptions,
)
from ..services.storage import (
    ensure_user,
    get_user_mode,
    set_user_mode,
    sync_user_premium_flag,
)

router = Router()


def _parse_ref_code_from_start(message: Message) -> str | None:
    if not message.text:
        return None
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return None
    arg = parts[1].strip()
    if not arg:
        return None
    return arg


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    ref_code = _parse_ref_code_from_start(message)

    user_row = await ensure_user(message.from_user, ref_code)
    await sync_user_premium_flag(user_row["id"])

    text = (
        "👋 Привет! Я BlackBoxGPT — твой универсальный AI-ассистент.\n\n"
        "Я помогу с задачами из работы, жизни, учёбы и медицины (с безопасными ограничениями).\n\n"
        "📌 Как пользоваться:\n"
        "• Выбери режим в меню ниже.\n"
        "• Или просто напиши свой первый запрос — я пойму."
    )
    await message.answer(text, reply_markup=main_menu_keyboard())


# ==== Главное меню ====

@router.message(F.text == "🧠 Режимы")
async def menu_modes(message: Message) -> None:
    await message.answer(
        "🧠 Режимы работы\n\nВыбери режим, в котором я буду отвечать на твои запросы.",
        reply_markup=modes_keyboard(),
    )


@router.message(F.text == "💎 Подписка")
async def menu_subscription(message: Message) -> None:
    user_row = await ensure_user(message.from_user)
    user_row = await sync_user_premium_flag(user_row["id"])

    if user_row["is_premium"]:
        text = (
            "💎 Подписка\n\n"
            "У тебя активен тариф **Premium**.\n"
            f"Доступно до: <b>{user_row['premium_until']:%d.%m.%Y}</b>.\n\n"
            "Лимит: до 100 запросов в день."
        )
    else:
        text = (
            "💎 Подписка\n\n"
            "Сейчас у тебя базовый бесплатный тариф:\n"
            "• 10 запросов в день.\n\n"
            "Оформи Premium, чтобы получить до 100 запросов в день и приоритетные ответы."
        )

    await message.answer(text, reply_markup=subscription_keyboard())


@router.message(F.text == "👤 Профиль")
async def menu_profile(message: Message) -> None:
    user_row = await ensure_user(message.from_user)
    user_row = await sync_user_premium_flag(user_row["id"])
    mode = await get_user_mode(user_row["id"])

    text = (
        "👤 Профиль\n\n"
        f"ID: <code>{user_row['telegram_id']}</code>\n"
        f"Ник: @{message.from_user.username or '—'}\n"
        f"Текущий режим: {'Универсальный' if mode is Mode.UNIVERSAL else 'Профессиональный'}\n"
        f"Тариф: {'Premium' if user_row['is_premium'] else 'Базовый'}"
    )
    await message.answer(text, reply_markup=main_menu_keyboard())


@router.message(F.text == "👥 Рефералы")
async def menu_referrals(message: Message) -> None:
    user_row = await ensure_user(message.from_user)
    ref_code = user_row["referral_code"]
    link = f"https://t.me/{settings.bot_username}?start={ref_code}"

    text = (
        "👥 Реферальная программа\n\n"
        "Отправь эту ссылку друзьям — они сразу попадут в BlackBoxGPT:\n"
        f"<code>{link}</code>\n\n"
        "В будущем сюда можно добавить бонусы за приглашённых пользователей."
    )
    await message.answer(text, reply_markup=referrals_keyboard())


# ==== Переключение режимов ====

@router.message(F.text == "🧠 Универсальный")
async def set_mode_universal(message: Message) -> None:
    user_row = await ensure_user(message.from_user)
    await set_user_mode(user_row["id"], Mode.UNIVERSAL)

    text = (
        "🧠 Универсальный режим активирован.\n\n"
        "Теперь просто напиши запрос — я буду отвечать в универсальном стиле: "
        "по делу, без лишнего шума."
    )
    await message.answer(text, reply_markup=main_menu_keyboard())


@router.message(F.text == "💼 Профессиональный")
async def set_mode_professional(message: Message) -> None:
    user_row = await ensure_user(message.from_user)
    await set_user_mode(user_row["id"], Mode.PROFESSIONAL)

    text = (
        "💼 Профессиональный режим активирован.\n\n"
        "Теперь я буду подстраиваться под сложные задачи: "
        "анализ, стратегия, медицина, наставничество, бизнес. "
        "Когда нужно — буду подключать веб-поиск через Perplexity."
    )
    await message.answer(text, reply_markup=main_menu_keyboard())


@router.message(F.text == BACK_BUTTON_TEXT)
async def go_back(message: Message) -> None:
    await message.answer("Возвращаю тебя в главное меню.", reply_markup=main_menu_keyboard())


# ==== Кнопки подписки (создание инвойсов) ====

@router.message(F.text.in_(("💎 1 месяц", "💎 3 месяца", "💎 12 месяцев")))
async def handle_subscription_buttons(message: Message) -> None:
    user_row = await ensure_user(message.from_user)

    mapping = {
        "💎 1 месяц": "premium_1m",
        "💎 3 месяца": "premium_3m",
        "💎 12 месяцев": "premium_12m",
    }
    plan_code = mapping[message.text]

    plan = PLANS[plan_code]

    if not settings.cryptopay_api_token:
        await message.answer(
            "Платёж через Crypto Bot пока не настроен.\n\n"
            "Технически всё готово — достаточно добавить токен Crypto Pay в .env.",
        )
        return

    payment_id, pay_url = await create_invoice_for_user(user_row["id"], plan_code)

    text = (
        f"💎 {plan.title}\n\n"
        f"Стоимость: <b>{plan.amount_usdt} USDT</b>.\n\n"
        "Нажми на ссылку ниже, чтобы оплатить через Crypto Bot:\n"
        f"{pay_url}\n\n"
        "После оплаты просто вернись в чат или нажми /start — подписка активируется автоматически."
    )
    await message.answer(text)


# Дополнительная кнопка/команда на случай, если пользователь хочет явно «обновить статус»
@router.message(F.text == "🔄 Проверить оплату")
async def manual_refresh_payments(message: Message) -> None:
    user_row = await ensure_user(message.from_user)
    await refresh_user_payments_and_subscriptions(user_row["id"])
    user_row = await sync_user_premium_flag(user_row["id"])

    if user_row["is_premium"]:
        text = (
            "✅ Платёж найден, подписка активирована.\n\n"
            f"Premium действует до <b>{user_row['premium_until']:%d.%m.%Y}</b>."
        )
    else:
        text = "Платёж пока не найден. Если ты уверен, что оплатил — попробуй чуть позже."

    await message.answer(text, reply_markup=main_menu_keyboard())
