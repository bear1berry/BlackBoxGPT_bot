# bot/routers/chat.py
from __future__ import annotations

import io
import re
import time
from typing import Optional

from aiogram import F, Router
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

# SpeechKit (STT)
try:
    from services.speechkit import SpeechKitError, SpeechKitSTT
except Exception:  # чтобы не падать, если файл ещё не создан
    SpeechKitSTT = None  # type: ignore
    SpeechKitError = Exception  # type: ignore


router = Router()

_MEDICAL_RE = re.compile(
    r"\b(болит|боль|температур|кашел|насморк|давлен|пульс|тошнит|рвот|понос|диаре|сыпь|аллерг|анализ|симптом|врач|лекарств|таблет|антибиот|дозировк|мг|ml|мл)\b",
    re.IGNORECASE,
)


def _strip_tags(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html)


async def _process_user_text(message: Message, db, settings, orchestrator, user_text: str) -> None:
    text = (user_text or "").strip()
    if not text:
        await message.answer("Напиши текстом или запиши голосом 🙂", reply_markup=kb_main())
        return

    # ensure user exists
    u = await users_repo.get_user(db, message.from_user.id)
    if not u:
        u = await users_repo.ensure_user(
            db,
            message.from_user.id,
            referrer_id=None,
            ref_salt=settings.bot_token[:16],
        )

    # update style signals
    new_style = update_style(u.style, text)
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
    await memory_repo.add(db, u.user_id, "user", clean_text(text)[:4000])

    # loader message
    loading = await message.answer("⌛ <i>Думаю над ответом…</i>", reply_markup=kb_main())

    last_edit = 0.0
    can_edit = True

    async def safe_edit(html: str, reply_markup=None) -> bool:
        """
        Единая точка редактирования loader-сообщения.
        Если Telegram запретил редактировать — больше не пытаемся, уходим в fallback.
        """
        nonlocal can_edit
        if not can_edit:
            return False
        try:
            await loading.edit_text(html, reply_markup=reply_markup)
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
            text,
            on_delta=on_delta,
        )
    except Exception:
        if not await safe_edit(texts.GENERIC_ERROR, reply_markup=None):
            await message.answer(texts.GENERIC_ERROR, reply_markup=kb_main())
        return

    # medical disclaimer (pro)
    if u.mode == "pro" and _MEDICAL_RE.search(text):
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


@router.message(F.voice)
async def chat_voice(message: Message, db, settings, orchestrator, cryptopay=None):
    # защита от падений если конфиг/сервис ещё не добавлены
    enable_voice = bool(getattr(settings, "enable_voice", False))
    if not enable_voice or SpeechKitSTT is None:
        await message.answer("🎙️ Голосовые сейчас отключены.", reply_markup=kb_main())
        return

    api_key = getattr(settings, "speechkit_api_key", "") or ""
    iam_token = getattr(settings, "speechkit_iam_token", "") or ""
    folder_id = getattr(settings, "speechkit_folder_id", "") or ""
    lang = getattr(settings, "speechkit_lang", "ru-RU") or "ru-RU"
    topic = getattr(settings, "speechkit_topic", "general") or "general"

    stt = SpeechKitSTT(
        api_key=api_key,
        iam_token=iam_token,
        folder_id=folder_id,
        lang=lang,
        topic=topic,
    )

    if not stt.is_enabled():
        await message.answer("🎙️ SpeechKit не настроен (нет ключа/токена).", reply_markup=kb_main())
        return

    # скачать voice из Telegram (ogg/opus)
    buf = io.BytesIO()
    await message.bot.download(message.voice, destination=buf)
    audio_bytes = buf.getvalue()

    try:
        recognized = await stt.recognize_oggopus(audio_bytes)
    except SpeechKitError as e:
        await message.answer(f"🎙️ Не смог распознать голос: {e}", reply_markup=kb_main())
        return
    except Exception:
        await message.answer("🎙️ Ошибка распознавания. Попробуй ещё раз короче/чётче.", reply_markup=kb_main())
        return

    recognized = (recognized or "").strip()
    if not recognized:
        await message.answer("🎙️ Ничего не расслышал. Скажи чуть громче/короче 🙂", reply_markup=kb_main())
        return

    await _process_user_text(message, db, settings, orchestrator, recognized)


@router.message(lambda m: m.text and not m.text.startswith("/"))
async def chat(message: Message, db, settings, orchestrator, cryptopay=None):
    await _process_user_text(message, db, settings, orchestrator, message.text or "")
