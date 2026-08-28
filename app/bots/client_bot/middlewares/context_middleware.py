import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.database.repositories.bot_repository import BotRepository
from app.database.repositories.bot_settings_repository import BotSettingsRepository

logger = logging.getLogger(__name__)


class BotContextMiddleware(BaseMiddleware):
    """Resolves which child bot an update belongs to and injects its context.

    Runs as an outer middleware so every handler and filter downstream can
    depend on `session`, `child_bot`, and `bot_settings` without re-querying.
    """

    def __init__(self, session_pool: async_sessionmaker[AsyncSession]) -> None:
        self.session_pool = session_pool

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        bot: Bot = data["bot"]

        async with self.session_pool() as session:
            bot_repo = BotRepository(session)
            child_bot = await bot_repo.get_by_telegram_bot_id(bot.id)

            if child_bot is None or not child_bot.active:
                logger.warning("Dropping update for unknown/inactive child bot telegram_bot_id=%s", bot.id)
                return None

            settings_repo = BotSettingsRepository(session)
            bot_settings = await settings_repo.get_by_bot_id(child_bot.id)

            data["session"] = session
            data["child_bot"] = child_bot
            data["bot_settings"] = bot_settings

            return await handler(event, data)
