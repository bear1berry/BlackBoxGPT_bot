from __future__ import annotations

import re
import time
from typing import Optional

from aiogram import Router
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest

from bot.keyboards import ikb_continue, kb_main
from bot import texts
from services import users as users_repo
from services import limits as limits_service
from services import memory as memory_repo
from services import continues as cont_repo
from services.llm.style import update_style
from services.llm.postprocess import clean_text


router = Router()

_MEDICAL_RE = re.compile(
    r"\b(болит|боль|температур|кашел|насморк|давлен|пульс|тошнит|рвот|понос|диаре|сыпь|аллерг|анализ|симптом|врач|лекарств|таблет|антибиот|дозировк|мг|ml|мл)\b",
    re.IGNORECASE,
)


def _strip_tags(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html)


@router.message(lambda m: m.text and not m.text.startswith("/"))
async def chat(message: Message) -> None:
    bot = message.bot
    db = bot["db"]
    settings = bot["settings"]
    orchestrator = bot["orchestrator"]

    # ensure user exists
    u = await users_repo.get_user(db, message.from_user.id)
    if not u:
        u = await users_repo.ensure_user(db, message.from_user.id, referrer_id=None, ref_salt=settings.bot_token[:16])

    # update style signals
    new_style = update_style(u.style, message.text or "")
    await users_repo.set_style(db, u.user_id, new_style)
    u.style = new_style

    # limits
    res = await limits_service.consume(
        db,
        u.user_id,
        timezone=settings.timezone,
        basic_trial_limit=settings.basic_trial_limit,
        premium_daily_limit=settings.premium_daily_limit,
    )
    if not res.ok:
        if res.reason == "trial":
            await message.answer(texts.TRIAL_LIMIT_REACHED, reply_markup=kb_main())
            await message.answer("💎 Оформить подписку можно в «💎 Подписка».", reply_markup=kb_main())
            return
        if res.reason == "daily":
            await message.answer(texts.DAILY_LIMIT_REACHED, reply_markup=kb_main())
            return

    # refresh user after usage update
    u = await users_repo.get_user(db, u.user_id)
    assert u is not None

    # remember user msg
    await memory_repo.add(db, u.user_id, "user", clean_text(message.text or "")[:4000])

    # loader message
    loading = await message.answer("⌛ <i>Думаю над ответом…</i>", reply_markup=kb_main())

    last_edit = 0.0

    async def on_delta(preview_html_escaped: str) -> None:
        nonlocal last_edit
        now = time.monotonic()
        if now - last_edit < 0.9:
            return
        last_edit = now
        try:
            await loading.edit_text("⌛ <i>Думаю над ответом…</i>\n\n" + preview_html_escaped)
        except TelegramBadRequest:
            pass
        except Exception:
            pass

    try:
        html_out = await orchestrator.answer_stream(
            db,
            u.user_id,
            u.mode,
            u.style,
            message.text or "",
            on_delta=on_delta,
        )
    except Exception:
        await loading.edit_text(texts.GENERIC_ERROR)
        return

    # medical disclaimer (pro)
    if u.mode == "pro" and _MEDICAL_RE.search(message.text or ""):
        html_out = texts.MEDICAL_DISCLAIMER + "\n\n" + html_out

    parts = orchestrator.split_for_telegram(html_out)

    if len(parts) == 1:
        await loading.edit_text(parts[0], reply_markup=None)
    else:
        state = await cont_repo.create(db, u.user_id, parts)
        await loading.edit_text(parts[0], reply_markup=ikb_continue(state.token))

    # store assistant memory (plain)
    await memory_repo.add(db, u.user_id, "assistant", _strip_tags(parts[0])[:4000])
