from __future__ import annotations

from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from bot.keyboards import ikb_continue
from services import continues as cont_repo

router = Router()


@router.callback_query(lambda c: c.data and c.data.startswith("cont:"))
async def cont(cb: CallbackQuery, db) -> None:
    data = cb.data or ""
    token = data.split(":", 1)[1] if ":" in data else ""
    if not token:
        await cb.answer()
        return

    st = await cont_repo.get(db, token)
    if not st or st.user_id != cb.from_user.id:
        await cb.answer("Сессия устарела.", show_alert=False)
        try:
            await cb.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        return

    next_idx = st.idx + 1
    if next_idx >= len(st.parts):
        await cont_repo.delete(db, token)
        await cb.answer()
        try:
            await cb.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        return

    await cont_repo.bump(db, token)

    text = st.parts[next_idx]
    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass
    except Exception:
        pass

    if next_idx == len(st.parts) - 1:
        await cb.message.answer(text)
        await cont_repo.delete(db, token)
    else:
        await cb.message.answer(text, reply_markup=ikb_continue(token))

    await cb.answer()
