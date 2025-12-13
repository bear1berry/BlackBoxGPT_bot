from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict

_EMOJI_RE = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]")
_PROFANITY_RE = re.compile(r"\b(бля|сука|нах|хуй|пизд|ёб|еба|заеб|пох|мудак)\b", re.IGNORECASE)


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def update_style(style: Dict[str, Any], user_text: str) -> Dict[str, Any]:
    s = dict(style or {})

    msg_len = len(user_text.strip())
    emoji = len(_EMOJI_RE.findall(user_text))
    prof = len(_PROFANITY_RE.findall(user_text))

    n = int(s.get("n", 0)) + 1
    s["n"] = n

    avg_len = float(s.get("avg_len", 0.0))
    s["avg_len"] = avg_len + (msg_len - avg_len) / n

    emoji_rate = float(s.get("emoji_rate", 0.0))
    s["emoji_rate"] = emoji_rate + ((emoji / max(1, msg_len)) - emoji_rate) / n

    prof_rate = float(s.get("prof_rate", 0.0))
    s["prof_rate"] = prof_rate + ((1.0 if prof > 0 else 0.0) - prof_rate) / n

    # user preference: concise vs detailed
    concise = float(s.get("concise", 0.5))
    if msg_len < 120:
        concise = _clamp(concise + 0.02)
    elif msg_len > 400:
        concise = _clamp(concise - 0.02)
    s["concise"] = concise

    return s


def style_prompt(style: Dict[str, Any]) -> str:
    concise = float(style.get("concise", 0.5))
    emoji_rate = float(style.get("emoji_rate", 0.0))
    prof_rate = float(style.get("prof_rate", 0.0))

    verbosity = "коротко и по делу" if concise >= 0.55 else "развёрнуто, но без воды"
    emoji_policy = "эмодзи — лаконично, по смыслу" if emoji_rate < 0.01 else "эмодзи — по делу, но не перебор"
    tone = "живой, уверенный, без токсичности"
    if prof_rate > 0.15:
        tone += "; допускай мягкий разговорный мат в цитатах пользователя, но сам не эскалируй"

    return (
        f"Стиль ответа: {verbosity}. Тон: {tone}. {emoji_policy}.\n"
        "Формат: заголовки, смысловые блоки, ключевые слова выделяй <b>жирным</b>, избегай странных символов."
    )
