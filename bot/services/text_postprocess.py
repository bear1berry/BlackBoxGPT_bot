import re

def prepare_answer(text: str) -> str:
    """
    Очищает и форматирует текст ответа.
    Убирает лишние символы, форматирует заголовки, списки.
    """
    # Убираем лишние пробелы и переносы
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = text.strip()
    
    # Форматируем заголовки: если строка заканчивается на : и не содержит точек, делаем жирным
    lines = text.split('\n')
    processed_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.endswith(':') and '.' not in stripped:
            processed_lines.append(f'*{stripped}*')
        else:
            processed_lines.append(stripped)
    
    text = '\n'.join(processed_lines)
    
    # Добавляем эмодзи в начале, если их нет
    if not any(char in text for char in ['🤖', '💡', '⚠️', '📌', '🔍']):
        # Можно добавить случайный эмодзи в зависимости от содержания
        if '?' in text:
            text = '💡 ' + text
        else:
            text = '🤖 ' + text
    
    return text
