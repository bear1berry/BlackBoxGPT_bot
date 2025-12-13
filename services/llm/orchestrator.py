from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

import aiosqlite

from services.llm.openai_compat import OpenAICompatClient
from services.llm import prompts
from services.llm.postprocess import clean_text, escape_html, split_parts
from services.llm.style import style_prompt
from services import memory as memory_repo


_MEDICAL_RE = re.compile(
    r"\b(болит|боль|температур|кашел|насморк|давлен|пульс|тошнит|рвот|понос|диаре|сыпь|аллерг|анализ|симптом|врач|лекарств|таблет|антибиот|дозировк|мг|ml|мл)\b",
    re.IGNORECASE,
)

_DOSAGE_RE = re.compile(r"\b(\d+\s?(мг|mg|мл|ml|таб|капс))\b", re.IGNORECASE)

_DISCIPLINE_RE = re.compile(
    r"\b(дисциплин|режим|привычк|цели|план|мотивац|продуктив|сон|тренировк|чек\s?-?ин|отч[её]т)\b",
    re.IGNORECASE,
)

_NEEDS_WEB_RE = re.compile(
    r"\b(сегодня|сейчас|последн|новост|актуал|цена|стоимост|курс|ставк|расписан|закон|регламент|обновлен|202[4-9]|президент|ceo)\b",
    re.IGNORECASE,
)


def _is_medical(text: str) -> bool:
    return bool(_MEDICAL_RE.search(text))


def _wants_dosage(text: str) -> bool:
    return "доз" in text.lower() or bool(_DOSAGE_RE.search(text))


def _is_discipline(text: str) -> bool:
    return bool(_DISCIPLINE_RE.search(text))


def _needs_web(text: str) -> bool:
    return bool(_NEEDS_WEB_RE.search(text))


def _sanitize_telegram_html(html_text: str) -> str:
    """Make Telegram HTML safe.

    Telegram parses HTML strictly:
    - only a small whitelist of tags is supported
    - any stray '<' or '&' outside tags/entities breaks the whole message

    We:
    1) strip unsupported tags
    2) normalize supported tags to the plain form (no attributes)
    3) escape text segments outside tags while preserving existing entities
    """

    allowed = ("b", "i", "u", "code", "pre", "blockquote")
    allowed_re = "|".join(allowed)

    # 1) remove unsupported tags entirely
    s = re.sub(rf"</?(?!({allowed_re})\b)[^>]*>", "", html_text)

    # 2) normalize allowed opening tags (Telegram is picky about attributes)
    s = re.sub(rf"<({allowed_re})\b[^>]*>", r"<\1>", s)

    # 3) escape text outside tags, but keep entities like &amp; intact
    tag_split = re.compile(rf"(</?(?:{allowed_re})>)", re.IGNORECASE)
    entity_re = re.compile(r"&(#\d+|#x[0-9a-fA-F]+|[a-zA-Z]+);")

    def escape_text_preserving_entities(text: str) -> str:
        # Escape < and > always
        text = text.replace("<", "&lt;").replace(">", "&gt;")

        # Escape & only when it is NOT part of an entity
        out = []
        i = 0
        while i < len(text):
            if text[i] == "&":
                m = entity_re.match(text, i)
                if m:
                    out.append(m.group(0))
                    i = m.end()
                    continue
                out.append("&amp;")
                i += 1
                continue
            out.append(text[i])
            i += 1
        return "".join(out)

    chunks = tag_split.split(s)
    safe: list[str] = []
    for ch in chunks:
        if not ch:
            continue
        if tag_split.fullmatch(ch):
            safe.append(ch.lower())
        else:
            safe.append(escape_text_preserving_entities(ch))

    return "".join(safe)


@dataclass
class Orchestrator:
    deepseek: OpenAICompatClient
    perplexity: OpenAICompatClient
    settings: Any  # Settings

    async def build_messages(
        self,
        db: aiosqlite.Connection,
        user_id: int,
        mode: str,
        user_style: dict[str, Any],
        user_text: str,
        *,
        extra_system: str = "",
    ) -> list[dict[str, str]]:
        sys = prompts.UNIVERSAL_SYSTEM if mode == "universal" else prompts.PRO_SYSTEM
        sys += "\n" + style_prompt(user_style)

        if mode == "pro" and _is_discipline(user_text):
            sys += "\n" + prompts.DISCIPLINE_SYSTEM

        if _is_medical(user_text):
            sys += "\n" + prompts.MEDICAL_GUARD

        if extra_system:
            sys += "\n" + extra_system

        msgs: list[dict[str, str]] = [{"role": "system", "content": sys}]

        recent = await memory_repo.get_recent(db, user_id, self.settings.max_context_messages)
        for m in recent:
            if m.role not in ("user", "assistant"):
                continue
            msgs.append({"role": m.role, "content": clean_text(m.content)[:1200]})

        msgs.append({"role": "user", "content": clean_text(user_text)[:4000]})
        return msgs

    async def research(self, user_text: str) -> str:
        if not self.settings.enable_pro_research or not self.settings.perplexity_api_key:
            return ""

        q = (
            "Собери факты из WEB по запросу. Ответ строго в формате:\n"
            "Факты (5–10 пунктов): ...\n"
            "Источники: 3–8 ссылок домен+заголовок, нумерация [1]...[N].\n"
            "Коротко, без воды.\n\n"
            f"Запрос: {user_text}"
        )

        resp = await self.perplexity.chat(
            messages=[
                {"role": "system", "content": "Ты исследователь. Не выдумывай источники."},
                {"role": "user", "content": q},
            ],
            temperature=0.1,
            max_tokens=900,
            extra={
                "search_recency_filter": "week",
                "web_search_options": {"search_context_size": "high"},
            },
        )
        return clean_text(resp.content)

    async def answer_stream(
        self,
        db: aiosqlite.Connection,
        user_id: int,
        mode: str,
        user_style: dict[str, Any],
        user_text: str,
        on_delta: Callable[[str], Awaitable[None]] | None = None,
    ) -> str:
        if _is_medical(user_text) and _wants_dosage(user_text):
            return clean_text(
                "Я не могу безопасно давать точные дозировки и схемы лечения по переписке. "
                "Могу помочь разобраться, какие вопросы задать врачу, какие красные флаги важны, "
                "и как безопасно действовать до очной консультации."
            )

        use_perplexity_primary = mode == "pro" and bool(self.settings.perplexity_api_key) and _needs_web(user_text)

        if use_perplexity_primary:
            messages = await self.build_messages(
                db,
                user_id,
                mode,
                user_style,
                user_text,
                extra_system="Если используешь WEB — в конце добавь блок «Источники» с 3–8 ссылками.",
            )
        else:
            messages = await self.build_messages(db, user_id, mode, user_style, user_text)

            research_block = ""
            if mode == "pro":
                try:
                    research_block = await self.research(user_text)
                except Exception:
                    research_block = ""

            if research_block:
                messages.insert(1, {"role": "system", "content": "WEB-данные (для проверки фактов):\n" + research_block})

        client = self.perplexity if use_perplexity_primary else self.deepseek

        raw = ""
        async for delta in client.chat_stream(
            messages=messages,
            model=(self.settings.perplexity_model if use_perplexity_primary else self.settings.deepseek_model),
            temperature=0.2,
            max_tokens=1800,
            extra=(
                {
                    "search_recency_filter": "week",
                    "web_search_options": {"search_context_size": "high"},
                }
                if use_perplexity_primary
                else None
            ),
        ):
            raw += delta
            if on_delta:
                preview = escape_html(clean_text(raw)[-1200:])
                await on_delta(preview)

        raw = clean_text(raw)

        # editor pass -> HTML (DeepSeek)
        if self.settings.enable_formatter_pass and self.settings.deepseek_api_key:
            try:
                edited = await self.deepseek.chat(
                    messages=[
                        {"role": "system", "content": prompts.EDITOR_SYSTEM},
                        {"role": "user", "content": raw},
                    ],
                    model=self.settings.deepseek_model,
                    temperature=0.15,
                    max_tokens=1400,
                )
                html_out = clean_text(edited.content)
            except Exception:
                html_out = escape_html(raw)
        else:
            html_out = escape_html(raw)

        html_out = _sanitize_telegram_html(html_out)
        return html_out

    def split_for_telegram(self, html_text: str) -> list[str]:
        return split_parts(html_text, limit=3500)
