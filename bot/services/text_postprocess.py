from __future__ import annotations


def clean_llm_answer(text: str) -> str:
    """
    Простая пост-обработка ответа модели:
    - убираем лидирующие/хвостовые пробелы
    - иногда модели любят начинать с ```markdown — режем это.
    """
    text = text.strip()

    fence = "```"
    if text.startswith(fence):
        # убираем первую строку ```markdown / ```json / ```
        parts = text.splitlines()
        # удаляем первую строку
        parts = parts[1:]
        # если в конце тоже есть ``` — убираем
        if parts and parts[-1].strip() == fence:
            parts = parts[:-1]
        text = "\n".join(parts).strip()

    return text
