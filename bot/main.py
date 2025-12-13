from __future__ import annotations

import asyncio
import logging
import os
from contextlib import suppress
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiohttp import web

from bot.config import Settings
from bot.logging_conf import setup_logging
from bot.routers import setup_routers

from services.db import connect, apply_migrations
from services.crypto_pay import CryptoPayClient
from services.llm.openai_compat import OpenAICompatClient
from services.llm.orchestrator import Orchestrator
from services.jobs import sync_active_invoices, downgrade_expired_subscriptions, send_daily_checkins
from web.app import create_app


async def start_web_server(app: web.Application, host: str, port: int) -> web.AppRunner:
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    return runner


async def main() -> None:
    settings = Settings()
    setup_logging(settings.log_level)
    log = logging.getLogger("main")

    Path(settings.data_dir).mkdir(parents=True, exist_ok=True)

    db = await connect(settings.db_path)
    await apply_migrations(db, str(Path(__file__).resolve().parent.parent / "migrations"))

    deepseek = OpenAICompatClient(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        default_model=settings.deepseek_model,
    )
    perplexity = OpenAICompatClient(
        api_key=settings.perplexity_api_key,
        base_url=settings.perplexity_base_url,
        default_model=settings.perplexity_model,
    )

    orchestrator = Orchestrator(deepseek=deepseek, perplexity=perplexity, settings=settings)

    cryptopay = CryptoPayClient(api_token=settings.cryptopay_api_token, base_url=settings.cryptopay_base_url)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML, link_preview_is_disabled=True),
    )

    # Dependency injection via bot context
    bot["db"] = db
    bot["settings"] = settings
    bot["orchestrator"] = orchestrator
    bot["cryptopay"] = cryptopay

    dp = Dispatcher()
    dp.include_router(setup_routers())

    # Web server for CryptoPay webhook + health
    app = create_app(bot=bot, db=db, cryptopay=cryptopay, webhook_secret=settings.cryptopay_webhook_secret)
    web_runner = await start_web_server(app, settings.web_server_host, settings.web_server_port)
    log.info("Web server started on %s:%s", settings.web_server_host, settings.web_server_port)

    # Scheduler
    scheduler = AsyncIOScheduler(timezone=settings.timezone)

    scheduler.add_job(
        sync_active_invoices,
        "interval",
        minutes=5,
        args=[bot, db, cryptopay],
        id="sync_invoices",
        replace_existing=True,
    )

    scheduler.add_job(
        downgrade_expired_subscriptions,
        "cron",
        hour=0,
        minute=5,
        args=[db],
        id="downgrade_expired",
        replace_existing=True,
    )

    scheduler.add_job(
        send_daily_checkins,
        "cron",
        hour=settings.checkin_hour,
        minute=settings.checkin_minute,
        args=[bot, db],
        id="daily_checkins",
        replace_existing=True,
    )

    scheduler.start()

    # Start polling
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        with suppress(Exception):
            await web_runner.cleanup()
        with suppress(Exception):
            await cryptopay.aclose()
        with suppress(Exception):
            await deepseek.aclose()
        with suppress(Exception):
            await perplexity.aclose()
        with suppress(Exception):
            await db.close()


if __name__ == "__main__":
    with suppress(ImportError):
        import uvloop

        uvloop.install()
    asyncio.run(main())
