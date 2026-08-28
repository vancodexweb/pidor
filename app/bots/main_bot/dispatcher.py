from aiogram import Dispatcher, Router
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bots.main_bot.handlers import create_bot, help as help_handler, my_bots, settings, start, stats
from app.bots.main_bot.middlewares.db_middleware import DbSessionMiddleware
from app.services.bot_manager import BotManager


def build_main_dispatcher(
    session_pool: async_sessionmaker[AsyncSession], bot_manager: BotManager, encryption_key: str
) -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    dp["bot_manager"] = bot_manager
    dp["encryption_key"] = encryption_key
    dp.update.outer_middleware(DbSessionMiddleware(session_pool))

    router = Router(name="main_bot")
    start.register(router)
    my_bots.register(router)
    create_bot.register(router)
    stats.register(router)
    settings.register(router)
    help_handler.register(router)

    dp.include_router(router)
    return dp
