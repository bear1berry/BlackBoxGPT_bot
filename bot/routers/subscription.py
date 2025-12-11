from aiogram import Router, F
from aiogram.types import Message

from ..keyboards import subscription_keyboard, main_menu_keyboard
from ..services.storage import get_user_by_telegram_id
from ..services.payments_crypto import create_subscription_invoice

router = Router(name="subscription")

PRICE_PER_MONTH = 5.0
PRICE_FOR_3_MONTHS = 12.0
PRICE_FOR_12_MONTHS = 39.0


@router.message(F.text == "💎 1 месяц")
async def subscribe_1_month(message: Message) -> None:
    await _handle_subscription(message, months=1, price=PRICE_PER_MONTH)


@router.message(F.text == "💎 3 месяца")
async def subscribe_3_months(message: Message) -> None:
    await _handle_subscription(message, months=3, price=PRICE_FOR_3_MONTHS)


@router.message(F.text == "💎 12 месяцев")
async def subscribe_12_months(message: Message) -> None:
    await _handle_subscription(message, months=12, price=PRICE_FOR_12_MONTHS)


async def _handle_subscription(message: Message, months: int, price: float) -> None:
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer(
            "Не удалось найти профиль. Отправь /start и попробуй снова.",
            reply_markup=main_menu_keyboard(),
        )
        return

    pay_url = await create_subscription_invoice(user["id"], months=months, total_price=price)
    if pay_url is None:
        await message.answer(
            "Платёж через Crypto Bot пока не настроен.\n\n"
            "Технически всё готово — достаточно добавить токен Crypto Pay в .env.\n"
            "После этого кнопки оплаты начнут выдавать ссылку на инвойс.",
            reply_markup=subscription_keyboard(),
        )
        return

    await message.answer(
        "💎 **Оформление подписки**\n\n"
        f"Срок: **{months} мес.**\n"
        f"Сумма: **{price} USDT**\n\n"
        "Перейди по ссылке для оплаты, после оплаты статус будет обновлён автоматически (после настройки вебхука):\n"
        f"{pay_url}",
        reply_markup=main_menu_keyboard(),
    )
