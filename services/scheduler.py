from __future__ import annotations

import asyncio
import datetime as dt
import logging

from aiogram import Bot

from bot.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Простенький планировщик без сторонних библиотек.
# Сейчас это каркас, который можно расширить под рассылки мотивации и научных фактов.


async def _send_daily_messages(bot: Bot) -> None:
    while True:
        try:
            now_utc = dt.datetime.now(dt.timezone.utc)
            # Пример: можно вычислить локальное время по Москве и в нужный час
            # отправлять мотивацию/научные факты.
            # Сейчас логика отключена, чтобы не спамить.

            await asyncio.sleep(60)
        except Exception:
            logger.exception("Scheduler loop error")
            await asyncio.sleep(60)


async def start_scheduler(bot: Bot) -> None:
    asyncio.create_task(_send_daily_messages(bot))
    logger.info("Scheduler started")
