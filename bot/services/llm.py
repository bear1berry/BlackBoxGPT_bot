import httpx
import logging
from bot.config import settings

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.deepseek_key = settings.DEEPSEEK_API_KEY.get_secret_value() if settings.DEEPSEEK_API_KEY else None
        self.perplexity_key = settings.PERPLEXITY_API_KEY.get_secret_value() if settings.PERPLEXITY_API_KEY else None

    async def ask(self, prompt: str, mode: str = "universal", style_params: dict = None) -> str:
        if mode == "universal" and self.deepseek_key:
            return await self._ask_deepseek(prompt)
        elif mode == "professional" and self.perplexity_key:
            return await self._ask_perplexity(prompt)
        else:
            # Fallback на DeepSeek, если нет ключа Perplexity
            if self.deepseek_key:
                return await self._ask_deepseek(prompt)
            else:
                return "⚠️ Не настроены API-ключи для моделей."

    async def _ask_deepseek(self, prompt: str) -> str:
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.deepseek_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=data, headers=headers, timeout=30.0)
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
            except Exception as e:
                logger.error(f"DeepSeek request error: {e}")
                return "⚠️ Ошибка при запросе к DeepSeek."

    async def _ask_perplexity(self, prompt: str) -> str:
        url = "https://api.perplexity.ai/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.perplexity_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "sonar-medium-online",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=data, headers=headers, timeout=30.0)
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
            except Exception as e:
                logger.error(f"Perplexity request error: {e}")
                return "⚠️ Ошибка при запросе к Perplexity."

    async def ask_stream(self, prompt: str, mode: str = "universal", style_params: dict = None):
        # Заглушка для потокового ответа. В реальности нужно реализовать асинхронный генератор.
        # Здесь для простоты возвращаем не потоковый ответ.
        answer = await self.ask(prompt, mode, style_params)
        yield answer
