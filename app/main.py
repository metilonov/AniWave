from __future__ import annotations

import asyncio
import contextlib
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.bot.access import ChatRegistrationMiddleware
from app.bot.routers import all_routers
from app.config import get_settings
from app.health import start_health_server
from app.logging_config import setup_logging
from app.services import build_services, close_services

log = logging.getLogger(__name__)


async def main() -> None:
    settings = get_settings()
    settings.validate_runtime()
    setup_logging(settings.log_level)

    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    for router in all_routers():
        dp.include_router(router)

    services = await build_services(settings, bot)
    dp["services"] = services

    registration = ChatRegistrationMiddleware(services.repo, settings.channel_id)
    dp.message.outer_middleware(registration)
    dp.callback_query.outer_middleware(registration)

    health_server = None
    if settings.health_enabled:
        health_server = await start_health_server(settings.health_host, settings.health_port)
    monitor_task = asyncio.create_task(services.monitor.run_forever(), name="release-monitor")

    try:
        me = await bot.get_me()
        log.info(
            "AniWave started as @%s; owner=%s; channel=%s",
            me.username,
            settings.admin_id,
            settings.channel_id,
        )
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        services.monitor.stop()
        monitor_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await monitor_task
        if health_server is not None:
            health_server.close()
            await health_server.wait_closed()
        await close_services(services)
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
