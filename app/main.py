import asyncio
import contextlib
import logging
import signal

from aiogram import Bot

from app.bots.main_bot.dispatcher import build_main_dispatcher
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.database.session import create_engine_and_session_pool
from app.services.bot_manager import BotManager

logger = logging.getLogger(__name__)


async def run() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)
    logger.info("Starting application")

    engine, session_pool = create_engine_and_session_pool(settings)
    bot_manager = BotManager(session_pool, settings.encryption_key)
    # No default parse_mode: owner-editable free text (welcome text, confirmation
    # text, etc.) is sent as-is, and Telegram's strict HTML parser would reject
    # a sendMessage call outright if that text ever contained a bare "<" or "&".
    main_bot = Bot(token=settings.main_bot_token)
    main_dp = build_main_dispatcher(session_pool, bot_manager, settings.encryption_key)

    stop_event = asyncio.Event()

    def _request_stop() -> None:
        logger.info("Shutdown signal received")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _request_stop)
        except NotImplementedError:
            # Not every platform/event loop supports signal handlers (e.g. Windows).
            # Production deployment is Linux/Docker, where this always works.
            pass

    polling_task: asyncio.Task | None = None
    stop_waiter: asyncio.Task | None = None

    try:
        await bot_manager.restore_bots()

        polling_task = asyncio.create_task(main_dp.start_polling(main_bot, handle_signals=False))
        stop_waiter = asyncio.create_task(stop_event.wait())
        await asyncio.wait({polling_task, stop_waiter}, return_when=asyncio.FIRST_COMPLETED)
    finally:
        logger.info("Shutting down")

        for task in (polling_task, stop_waiter):
            if task is not None and not task.done():
                task.cancel()
        if polling_task is not None:
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await polling_task

        await bot_manager.shutdown()
        with contextlib.suppress(Exception):
            await main_bot.session.close()
        await engine.dispose()

        logger.info("Shutdown complete")


def main() -> None:
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(run())


if __name__ == "__main__":
    main()
