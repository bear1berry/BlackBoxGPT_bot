# bot/routers/chat.py
from __future__ import annotations

import io
import re
import time

from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message

from bot import texts
from bot.keyboards import ikb_continue, kb_main
from services import continues as cont_repo
from services import limits as limits_service
from services import memory as memory_repo
from services import users as users_repo
from services.llm.postprocess import clean_text
from services.llm.style import update_style
from services.voice import SpeechkitError, speech_to_text_oggopus

router = Router()

_MEDICAL_RE = re.compile(
    r"\b(болит|боль|температур|кашел|насморк|давлен|пульс|тошнит|рвот|понос|диаре|сыпь|аллерг|анализ|симптом|врач|лекарств|таблет|антибиот|дозировк|мг|ml|мл)\b",
    re.IGNORECASE,
)


def _strip_tags(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html)


async def _ensure_user(db, settings, user_id: int):
    u = await users_repo.get_user(db, user_id)
    if not u:
        u = await users_repo.ensure_user(
            db,
            user_id,
            referrer_id=None,
            ref_salt=settings.bot_token[:16],
        )
    return u


async def _run_llm_flow(message: Message, db, settings, orchestrator, user_text: str, *, preface: str = "") -> None:
    # ensure user exists
    u = await _ensure_user(db, settings, message.from_user.id)

    # update style signals
    new_style = update_style(u.style, user_text)
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
    await memory_repo.add(db, u.user_id, "user", clean_text(user_text)[:4000])

    # loader message
    loading_text = "⌛ <i>Думаю над ответом…</i>"
    if preface:
        loading_text = preface + "\n" + loading_text
    loading = await message.answer(loading_text, reply_markup=kb_main())

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
        await safe_edit(loading_text + "\n\n" + preview_html_escaped)

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

    # medical disclaimer (pro)
    if u.mode == "pro" and _MEDICAL_RE.search(user_text or ""):
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

    # store assistant memory (plain)
    await memory_repo.add(db, u.user_id, "assistant", _strip_tags(parts[0])[:4000])


@router.message(lambda m: m.voice is not None)
async def chat_voice(message: Message, db, settings, orchestrator, cryptopay=None):
    if not getattr(settings, "enable_voice", False):
        await message.answer("🎙️ Голосовые сейчас выключены.", reply_markup=kb_main())
        return

    # экономим SpeechKit, если лимиты уже выбиты
    u = await _ensure_user(db, settings, message.from_user.id)
    res = await limits_service.peek(  # если peek нет — см. ниже примечание
        db,
        u.user_id,
        timezone=settings.timezone,
        basic_trial_limit=settings.basic_trial_limit,
        premium_daily_limit=settings.premium_daily_limit,
    )
    if res is not None and not res.ok:
        # если у тебя нет peek — просто убери этот блок, и лимиты проверятся внутри _run_llm_flow
        if res.reason == "trial":
            await message.answer(texts.TRIAL_LIMIT_REACHED, reply_markup=kb_main())
            await message.answer("💎 Оформить подписку можно в «💎 Подписка».", reply_markup=kb_main())
            return
        if res.reason == "daily":
            await message.answer(texts.DAILY_LIMIT_REACHED, reply_markup=kb_main())
            return

    # скачиваем voice (ogg/opus)
    loading = await message.answer("🎙️ <i>Расшифровываю голос…</i>", reply_markup=kb_main())
    try:
        file = await message.bot.get_file(message.voice.file_id)
        buf = io.BytesIO()
        await message.bot.download_file(file.file_path, buf)
        audio_bytes = buf.getvalue()

        text = await speech_to_text_oggopus(
            audio_bytes,
            api_key=settings.speechkit_api_key,
            folder_id=settings.speechkit_folder_id,
            lang=settings.speechkit_lang,
            topic=settings.speechkit_topic,
            timeout_sec=settings.speechkit_timeout_sec,
        )
    except SpeechkitError:
        await loading.edit_text("🎙️ Не смог распознать голос. Попробуй чуть медленнее/громче.", reply_markup=kb_main())
        return
    except Exception:
        await loading.edit_text("🎙️ Ошибка обработки голосового.", reply_markup=kb_main())
        return

    # убираем “временное” сообщение и запускаем обычный текстовый пайплайн
    try:
        await loading.delete()
    except Exception:
        pass

    await _run_llm_flow(
        message,
        db,
        settings,
        orchestrator,
        text,
        preface=f"📝 <b>Расшифровка:</b> {_strip_tags(text)[:300]}",
    )


@router.message(lambda m: m.text and not m.text.startswith("/"))
async def chat(message: Message, db, settings, orchestrator, cryptopay=None):
    await _run_llm_flow(message, db, settings, orchestrator, message.text or "")
