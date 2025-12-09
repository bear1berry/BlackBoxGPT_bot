import asyncio
import logging
from typing import Literal, Dict, Optional

import httpx
from aiogram import Router, F
from aiogram.enums import ChatAction, ChatType
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message

from bot.config import settings

logger = logging.getLogger(__name__)

router = Router(name="chat-router")

# ------------------------- Типы и режимы -------------------------

Mode = Literal["universal", "medicine", "mentor", "business", "creative"]

DEFAULT_MODE: Mode = "universal"

# Если в settings есть кастомные модели – берём их, иначе дефолты.
MODE_TO_PERPLEXITY_MODEL: Dict[Mode, str] = {
    "universal": getattr(settings, "PERPLEXITY_MODEL_UNIVERSAL", "sonar-reasoning"),
    "medicine": getattr(settings, "PERPLEXITY_MODEL_MEDICINE", "sonar-research"),
    "mentor": getattr(settings, "PERPLEXITY_MODEL_MENTOR", "sonar-reasoning"),
    "business": getattr(settings, "PERPLEXITY_MODEL_BUSINESS", "sonar-reasoning"),
    "creative": getattr(settings, "PERPLEXITY_MODEL_CREATIVE", "sonar-reasoning"),
}

# На каком провайдере что гоняем (можешь перекинуть по вкусу)
MODE_TO_PROVIDER: Dict[Mode, Literal["perplexity", "deepseek"]] = {
    "universal": "perplexity",
    "medicine": "perplexity",
    "mentor": "perplexity",   # тут логично sonar-reasoning
    "business": "deepseek",
    "creative": "deepseek",
}

# ------------------------- Вспомогательные функции -------------------------


def detect_mode_for_user(message: Message) -> Mode:
    """
    Пока что — простой вариант: берём дефолтный режим.
    Здесь можно потом прикрутить:
    - чтение режима из БД (users.current_mode)
    - или из FSM/state
    - или из какого-то middleware.
    """
    return DEFAULT_MODE


def build_system_prompt(mode: Mode) -> str:
    base = (
        "Ты BlackBox GPT — универсальный умный ассистент. "
        "Отвечай всегда по-русски. Не используй Markdown или HTML-разметку — "
        "только обычный текст. Структурируй ответ как мини-статью: "
        "короткое вступление, список ключевых моментов, вывод. "
        "Пиши живо, но без воды, концентрированно и по делу.\n\n"
    )

    if mode == "medicine":
        return (
            base
            + "Режим: Медицина. Помогай как опытный врач, но обязательно добавляй, "
              "что твой ответ не заменяет консультацию лечащего врача. "
              "Всегда уточняй недостающие данные, думай дифференциально."
        )
    if mode == "mentor":
        return (
            base
            + "Режим: Наставник. Ты ментор по жизни, продуктивности и мышлению. "
              "Говори прямо, поддерживающе, давай конкретные шаги и рамки."
        )
    if mode == "business":
        return (
            base
            + "Режим: Бизнес. Ты стратег, который помогает находить идеи, решения, "
              "структурировать проекты и считать выгоду."
        )
    if mode == "creative":
        return (
            base
            + "Режим: Креатив. Помогай с идеями, концептами, текстами, подачей. "
              "Не скатывайся в шутовство, держи премиальный стиль."
        )
    # universal
    return base + "Режим: Универсальный. Можешь помогать в любых темах."


async def call_perplexity(prompt: str, mode: Mode) -> str:
    if not getattr(settings, "PERPLEXITY_API_KEY", None):
        raise RuntimeError("PERPLEXITY_API_KEY не задан в .env")

    url = getattr(
        settings,
        "PERPLEXITY_API_URL",
        "https://api.perplexity.ai/chat/completions",
    )

    model = MODE_TO_PERPLEXITY_MODEL.get(mode, MODE_TO_PERPLEXITY_MODEL[DEFAULT_MODE])
    system_prompt = build_system_prompt(mode)

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.4,
        "top_p": 0.9,
        "max_tokens": 1024,
        "stream": False,
    }

    headers = {
        "Authorization": f"Bearer {settings.PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
    }

    logger.info("Calling Perplexity: model=%s, mode=%s", model, mode)

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        logger.error("Unexpected Perplexity response: %s", data)
        raise RuntimeError("Perplexity вернул неожиданный ответ")


async def call_deepseek(prompt: str, mode: Mode) -> str:
    if not getattr(settings, "DEEPSEEK_API_KEY", None):
        raise RuntimeError("DEEPSEEK_API_KEY не задан в .env")

    url = getattr(
        settings,
        "DEEPSEEK_API_URL",
        "https://api.deepseek.com/chat/completions",
    )

    system_prompt = build_system_prompt(mode)

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.4,
        "top_p": 0.9,
        "max_tokens": 2048,
        "stream": False,
    }

    headers = {
        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    logger.info("Calling DeepSeek: model=deepseek-chat, mode=%s", mode)

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        logger.error("Unexpected DeepSeek response: %s", data)
        raise RuntimeError("DeepSeek вернул неожиданный ответ")


async def generate_answer(prompt: str, mode: Mode) -> str:
    """
    Центральная точка: решаем, какой провайдер дёргать, и возвращаем текст.
    """
    provider = MODE_TO_PROVIDER.get(mode, "perplexity")

    if provider == "deepseek":
        return await call_deepseek(prompt, mode)
    else:
        return await call_perplexity(prompt, mode)


async def stream_edit_text(message: Message, full_text: str) -> None:
    """
    "Живой" стриминг: постепенно дописываем текст в одном сообщении.

    Важно:
    - Ответ без HTML/Markdown, чтобы не ломать разметку при обрезке.
    - Редактируем не чаще, чем раз в ~0.25 сек, чтобы не упираться в лимиты.
    """
    full_text = full_text.strip()
    if not full_text:
        try:
            await message.edit_text("Ответ пустой. Попробуй задать вопрос иначе.")
        except TelegramBadRequest:
            pass
        return

    words = full_text.split()
    buffer = ""
    last_edit = asyncio.get_event_loop().time()

    for idx, word in enumerate(words, start=1):
        if not buffer:
            buffer = word
        else:
            buffer += " " + word

        now = asyncio.get_event_loop().time()
        # Обновляем сообщение примерно 3–4 раза в секунду
        if now - last_edit >= 0.25 or idx == len(words):
            try:
                await message.edit_text(buffer)
            except TelegramBadRequest as e:
                # Например, "message is not modified" — просто игнорируем
                logger.debug("edit_text error during streaming: %s", e)
            last_edit = now

    # На всякий случай финальное обновление
    if buffer != full_text:
        try:
            await message.edit_text(full_text)
        except TelegramBadRequest:
            pass


# ------------------------- Обработчик сообщений -------------------------


@router.message(
    F.chat.type == ChatType.PRIVATE,
    F.text,
    ~F.via_bot,
)
async def handle_user_message(message: Message) -> None:
    """
    Основной обработчик диалога:
    - определяем режим (пока дефолт)
    - показываем "печатает"
    - создаём заготовку сообщения
    - дёргаем LLM (Perplexity / DeepSeek)
    - стримим ответ в одном сообщении.
    """
    user_input = (message.text or "").strip()
    if not user_input:
        return

    mode: Mode = detect_mode_for_user(message)
    logger.info(
        "New user message: user_id=%s, mode=%s, text=%r",
        message.from_user.id if message.from_user else None,
        mode,
        user_input[:200],
    )

    # Показываем "печатает"
    try:
        await message.bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING,
        )
    except Exception as e:
        logger.debug("Failed to send chat action: %s", e)

    # Черновик ответа
    try:
        draft = await message.answer(
            "🧠 Думаю над ответом...\n\n"
            "Если вдруг будет задержка — я просто тщательно обрабатываю запрос.",
        )
    except TelegramBadRequest as e:
        logger.error("Failed to send draft message: %s", e)
        # В крайнем случае — просто сваливаемся
        return

    try:
        raw_answer = await generate_answer(user_input, mode)
    except Exception as e:
        logger.exception("LLM error:")
        try:
            await draft.edit_text(
                "⚠️ Произошла ошибка при обращении к модели.\n"
                "Попробуй ещё раз чуть позже или переформулируй запрос."
            )
        except TelegramBadRequest:
            pass
        return

    await stream_edit_text(draft, raw_answer)
