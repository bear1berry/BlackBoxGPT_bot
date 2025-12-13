from __future__ import annotations

import re
import html
from typing import List


_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")
_WEIRD = ["​", "﻿"]


def clean_text(text: str) -> str:
    t = text.replace("\r", "")
    for w in _WEIRD:
        t = t.replace(w, "")
    t = _CONTROL_CHARS.sub("", t)
    # normalize spaces
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t).strip()
    return t


def escape_html(text: str) -> str:
    return html.escape(text, quote=False)


def split_parts(html_text: str, limit: int = 3500) -> List[str]:
    if len(html_text) <= limit:
        return [html_text]

    parts: List[str] = []
    buf = ""
    for block in html_text.split("\n\n"):
        add = block if not buf else "\n\n" + block
        if len(buf) + len(add) <= limit:
            buf += add
        else:
            if buf:
                parts.append(buf)
            # if block itself too big, hard split
            while len(block) > limit:
                parts.append(block[:limit])
                block = block[limit:]
            buf = block
    if buf:
        parts.append(buf)
    return parts
