from aiogram import Dispatcher, Router
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bots.client_bot.handlers import (
    admin_bookings,
    admin_panel,
    admin_settings,
    admin_slots,
    booking,
    client_start,
)
from app.bots.client_bot.middlewares.context_middleware import BotContextMiddleware


def build_client_dispatcher(session_pool: async_sessionmaker[AsyncSession]) -> Dispatcher:
    """Build a brand-new Dispatcher for one child bot.

    Every child bot gets its own Dispatcher/Router/FSM storage instance so
    bots are fully isolated at runtime: one bot crashing or being stopped
    can never affect another's polling loop or FSM state.
    """
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.outer_middleware(BotContextMiddleware(session_pool))

    router = Router(name="client_bot")
    client_start.register(router)
    booking.register(router)
    admin_panel.register(router)
    admin_slots.register(router)
    admin_bookings.register(router)
    admin_settings.register(router)

    dp.include_router(router)
    return dp
