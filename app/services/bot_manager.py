import asyncio
import contextlib
import logging

from aiogram import Bot, Dispatcher
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bots.client_bot.dispatcher import build_client_dispatcher
from app.core.security import decrypt_token
from app.database.repositories.bot_repository import BotRepository

logger = logging.getLogger(__name__)


class BotManager:
    """Owns the lifecycle of every child bot's polling task.

    Each child bot runs as an independent asyncio.Task wrapping its own
    (Bot, Dispatcher) pair, so a crash or intentional stop of one bot never
    affects any other bot or the main constructor bot.
    """

    def __init__(self, session_pool: async_sessionmaker[AsyncSession], encryption_key: str) -> None:
        self._session_pool = session_pool
        self._encryption_key = encryption_key
        self._tasks: dict[int, asyncio.Task] = {}

    def is_running(self, bot_id: int) -> bool:
        return bot_id in self._tasks

    async def start_bot(self, bot_id: int, token: str) -> None:
        if bot_id in self._tasks:
            logger.info("Bot id=%s is already running, skipping start", bot_id)
            return

        # No default parse_mode — see the comment in app/main.py for why.
        bot_instance = Bot(token=token)
        dispatcher = build_client_dispatcher(self._session_pool)

        task = asyncio.create_task(self._run(bot_id, bot_instance, dispatcher), name=f"child-bot-{bot_id}")
        self._tasks[bot_id] = task
        logger.info("Started polling for bot id=%s", bot_id)

    async def _run(self, bot_id: int, bot_instance: Bot, dispatcher: Dispatcher) -> None:
        try:
            await dispatcher.start_polling(bot_instance, handle_signals=False)
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("Child bot id=%s crashed", bot_id)
        finally:
            with contextlib.suppress(Exception):
                await bot_instance.session.close()
            self._tasks.pop(bot_id, None)

    async def stop_bot(self, bot_id: int) -> None:
        task = self._tasks.pop(bot_id, None)
        if task is None:
            return
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        logger.info("Stopped polling for bot id=%s", bot_id)

    async def restart_bot(self, bot_id: int, token: str) -> None:
        await self.stop_bot(bot_id)
        await self.start_bot(bot_id, token)

    async def remove_bot(self, bot_id: int) -> None:
        await self.stop_bot(bot_id)

    async def restore_bots(self) -> None:
        async with self._session_pool() as session:
            rows = await BotRepository(session).list_active()

        for row in rows:
            try:
                token = decrypt_token(row.token_encrypted, self._encryption_key)
                await self.start_bot(row.id, token)
                logger.info("Restored bot id=%s username=@%s", row.id, row.username)
            except Exception:
                logger.exception("Failed to restore bot id=%s", row.id)

    async def shutdown(self) -> None:
        for bot_id in list(self._tasks.keys()):
            await self.stop_bot(bot_id)
