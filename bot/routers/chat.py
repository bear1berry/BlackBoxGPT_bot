# bot/routers/chat.py
from __future__ import annotations

import io
import re
import time
from html import escape as html_escape

from aiogram import Router, F
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
from services.speechkit import recognize_oggopus, SpeechKitError


router = Router()

_MEDICAL_RE = re.compile(
    r"\b(болит|боль|температур|кашел|насморк|давлен|пульс|тошнит|рвот|понос|диаре|сыпь|аллерг|анализ|симптом|врач|лекарств|таблет|антибиот|дозировк|мг|ml|мл)\b",
    re.IGNORECASE,
)


def _strip_tags(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html)


async def _download_telegram_file_as_bytes(message: Message, file_id: str) -> bytes:
    bot = message.bot
    tg_file = await bot.get_file(file_id)
    buf = io.BytesIO()
    await bot.download_file(tg_file.file_path, destination=buf)
    return buf.getvalue()


async def _process_user_text(message: Message, db, settings, orchestrator, user_text: str) -> None:
    # ensure user exists
    u = await users_repo.get_user(db, message.from_user.id)
    if not u:
        u = await users_repo.ensure_user(
            db,
            message.from_user.id,
            referrer_id=None,
            ref_salt=settings.bot_token[:16],
        )

    user_text = clean_text(user_text or "")
    if not user_text.strip():
        await message.answer("Не вижу текста. Попробуй ещё раз 🙂", reply_markup=kb_main())
        return

    is_admin = bool(getattr(settings, "is_admin", lambda _x: False)(u.user_id))

    # update style signals
    new_style = update_style(u.style, user_text)
    await users_repo.set_style(db, u.user_id, new_style)
    u.style = new_style

    # limits (админов не режем)
    if not is_admin:
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
    await memory_repo.add(db, u.user_id, "user", user_text[:4000])

    # loader message
    loading = await message.answer("⌛ <i>Думаю над ответом…</i>", reply_markup=kb_main())

    last_edit = 0.0
    can_edit = True

    async def safe_edit(text: str, reply_markup=None) -> bool:
        nonlocal can_edit
        if not can_edit:
            return False
        try:
            await loading.edit_text(text, reply_markup=reply_markup)
            return True
        except TelegramBadRequest as e:
            msg = str(e)
            if ("message can't be edited" in msg) or ("message to edit not found" in msg):
                can_edit = False
            return False
        except Exception:
            return False

    async def on_delta(preview_html_escaped: str) -> None:
        nonlocal last_edit
        now = time.monotonic()
        if now - last_edit < 0.9:
            return
        last_edit = now
        await safe_edit("⌛ <i>Думаю над ответом…</i>\n\n" + preview_html_escaped)

    try:
        html_out = await orchestrator.answer_stream(
            db,
            u.user_id,
            u.mode,
            u.style,
            user_text,
            on_delta=on_delta,
        )
    except Exception:
        if not await safe_edit(texts.GENERIC_ERROR, reply_markup=None):
            await message.answer(texts.GENERIC_ERROR, reply_markup=kb_main())
        return

    if u.mode == "pro" and _MEDICAL_RE.search(user_text):
        html_out = texts.MEDICAL_DISCLAIMER + "\n\n" + html_out

    parts = orchestrator.split_for_telegram(html_out)

    if len(parts) == 1:
        ok = await safe_edit(parts[0], reply_markup=None)
        if not ok:
            await message.answer(parts[0])
    else:
        state = await cont_repo.create(db, u.user_id, parts)
        ok = await safe_edit(parts[0], reply_markup=ikb_continue(state.token))
        if not ok:
            await message.answer(parts[0], reply_markup=ikb_continue(state.token))

    await memory_repo.add(db, u.user_id, "assistant", _strip_tags(parts[0])[:4000])


@router.message(F.voice)
async def voice_chat(message: Message, db, settings, orchestrator, cryptopay=None):
    loading = await message.answer("🎙️ <i>Распознаю голос…</i>", reply_markup=kb_main())

    try:
        audio_bytes = await _download_telegram_file_as_bytes(message, message.voice.file_id)
        stt = await recognize_oggopus(audio_bytes, settings=settings)
        text = stt.text.strip()
    except SpeechKitError as e:
        await loading.edit_text(f"❌ <b>Голос не распознан</b>\n\n{html_escape(str(e))}", reply_markup=kb_main())
        return
    except Exception:
        await loading.edit_text("❌ Не получилось обработать голос. Попробуй ещё раз.", reply_markup=kb_main())
        return

    preview = html_escape(text[:220])
    await loading.edit_text(
        f"🎙️ <i>Распознано:</i> <code>{preview}</code>\n\n⌛ <i>Думаю над ответом…</i>",
        reply_markup=kb_main(),
    )

    await _process_user_text(message, db, settings, orchestrator, text)


@router.message(F.text & ~F.text.startswith("/"))
async def chat(message: Message, db, settings, orchestrator, cryptopay=None):
    await _process_user_text(message, db, settings, orchestrator, message.text or "")
