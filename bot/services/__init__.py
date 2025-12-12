# bot/services/__init__.py

"""
Общий фасад для сервисов работы с LLM.

Здесь:
- переэкспортируем Mode и StyleParams;
- даём прямые функции ask_llm / ask_llm_stream;
- создаём совместимый объект llm_client для старого кода
  (у которого ожидаются методы .ask() и .ask_stream()).
"""

from .llm import Mode, StyleParams, ask_llm, ask_llm_stream


class LLMClientCompat:
    """
    Обёртка для обратной совместимости.

    Старый код мог делать:
        from bot.services import llm_client
        await llm_client.ask(...)
        async for chunk in llm_client.ask_stream(...)

    Теперь под капотом это просто прокси к функциям ask_llm / ask_llm_stream.
    """

    async def ask(self, *args, **kwargs):
        return await ask_llm(*args, **kwargs)

    async def ask_stream(self, *args, **kwargs):
        async for chunk in ask_llm_stream(*args, **kwargs):
            yield chunk


# Глобальный экземпляр для старого кода
llm_client = LLMClientCompat()

__all__ = [
    "Mode",
    "StyleParams",
    "ask_llm",
    "ask_llm_stream",
    "llm_client",
]
