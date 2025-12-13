from __future__ import annotations

import re
import html
from typing import List, Tuple


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
    """Split Telegram HTML into message-sized chunks.

    Telegram is strict about HTML entity parsing. The splitter:
    - tries to keep paragraph boundaries ("\n\n")
    - never cuts inside an HTML tag
    - balances supported tags across chunks (closes at the end, re-opens in the next)
    """

    if len(html_text) <= limit:
        return [html_text]

    allowed = {"b", "i", "u", "code", "pre", "blockquote"}
    tag_re = re.compile(r"</?([a-zA-Z0-9]+)(?:\s[^>]*)?>")

    StackItem = Tuple[str, str]  # (tag_name, opening_tag)

    def parse_tags(text: str, stack: list[StackItem]) -> list[StackItem]:
        for m in tag_re.finditer(text):
            full = m.group(0)
            name = (m.group(1) or "").lower()
            if name not in allowed:
                continue
            if full.startswith("</"):
                # keep nesting sane: close the nearest matching tag
                if stack and stack[-1][0] == name:
                    stack.pop()
                else:
                    # if badly nested, drop everything up to the match
                    for i in range(len(stack) - 1, -1, -1):
                        if stack[i][0] == name:
                            del stack[i:]
                            break
                continue

            # opening tag (ignore self-closing)
            if full.endswith("/>"):
                continue
            # normalize attributes away: Telegram HTML is picky
            stack.append((name, f"<{name}>"))
        return stack

    def open_tags(stack: list[StackItem]) -> str:
        return "".join(t[1] for t in stack)

    def close_tags(stack: list[StackItem]) -> str:
        return "".join(f"</{t[0]}>" for t in reversed(stack))

    def safe_cut(s: str, max_len: int) -> int:
        if len(s) <= max_len:
            return len(s)
        cut = max_len
        # Avoid cutting inside a tag.
        prefix = s[:cut]
        lt = prefix.rfind("<")
        gt = prefix.rfind(">")
        if lt > gt:
            cut = lt
        return max(1, cut)

    parts: List[str] = []
    stack: list[StackItem] = []
    buf = ""  # current chunk WITHOUT forced closing tags

    blocks = html_text.split("\n\n")
    for bi, block in enumerate(blocks):
        sep = "\n\n" if buf and buf != open_tags(stack) else ""

        # optimistic append with tag accounting
        tmp_stack = stack.copy()
        parse_tags(sep + block, tmp_stack)
        candidate = buf + sep + block
        if len(candidate) + len(close_tags(tmp_stack)) <= limit:
            buf = candidate
            stack = tmp_stack
            continue

        # flush current buffer if it has content
        if buf:
            parts.append(buf + close_tags(stack))
            buf = open_tags(stack)

        # now split the block itself across multiple chunks
        remaining = block
        first_piece = True
        while remaining:
            sep2 = "" if (first_piece or buf == open_tags(stack)) else "\n\n"

            # compute a conservative max take
            base_len = len(buf) + len(sep2)
            max_take = max(1, limit - base_len - len(close_tags(stack)))
            max_take = min(max_take, len(remaining))

            take = safe_cut(remaining, max_take)

            # adjust take to account for tag changes inside the chunk
            while take > 1:
                tmp_stack2 = stack.copy()
                parse_tags(sep2 + remaining[:take], tmp_stack2)
                if len(buf) + len(sep2) + take + len(close_tags(tmp_stack2)) <= limit:
                    break
                take = safe_cut(remaining, take - 1)

            chunk = remaining[:take]
            remaining = remaining[take:]

            buf += sep2 + chunk
            parse_tags(sep2 + chunk, stack)

            if remaining:
                parts.append(buf + close_tags(stack))
                buf = open_tags(stack)
                first_piece = True
            else:
                first_piece = False

    if buf:
        parts.append(buf + close_tags(stack))

    # hard fallback: guarantee non-empty parts
    return [p for p in parts if p.strip()] or [html_text[:limit]]
