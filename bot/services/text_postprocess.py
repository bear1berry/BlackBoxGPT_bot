import re


def _clean_weird_symbols(text: str) -> str:
    """Убираем странные символы из ответа модели."""
    return text.replace("�", " ")


def _normalise_newlines(text: str) -> str:
    """
    Нормализуем переносы строк:
    - \r\n и \r → \n
    - более двух подряд → максимум два
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _apply_headings(text: str) -> str:
    """
    Преобразуем строки вида "Что-то:" в жирный заголовок:
    "Причины:" → "**Причины**"
    """
    lines = text.split("\n")
    result_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and stripped.endswith(":") and not stripped.startswith("•"):
            result_lines.append(f"**{stripped[:-1]}**")
        else:
            result_lines.append(line)
    return "\n".join(result_lines)


def prepare_answer(raw: str) -> str:
    """
    Базовая предобработка текста перед отправкой пользователю.

    - чистим артефакты
    - приводим переносы строк к аккуратному виду
    - нормализуем маркеры списков
    - делаем заголовки жирными
    """
    text = _clean_weird_symbols(raw)
    text = _normalise_newlines(text)
    # заменяем "-", "•" в начале строк на единый маркер "• "
    text = re.sub(r"(?m)^\s*[-•]\s*", "• ", text)
    text = _apply_headings(text)
    return text
