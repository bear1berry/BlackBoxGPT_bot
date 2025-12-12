def plural_ru(n: int, form1: str, form2: str, form5: str) -> str:
    """
    Простая функция для русских окончаний: 1 месяц, 2 месяца, 5 месяцев.
    """
    n_abs = abs(n) % 100
    n1 = n_abs % 10
    if 11 <= n_abs <= 19:
        return f"{n} {form5}"
    if 2 <= n1 <= 4:
        return f"{n} {form2}"
    if n1 == 1:
        return f"{n} {form1}"
    return f"{n} {form5}"
