from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bots.main_bot.keyboards.keyboards import STATS_BUTTON
from app.database.models.booking import BookingStatus
from app.database.repositories.booking_repository import BookingRepository
from app.database.repositories.bot_repository import BotRepository


async def show_stats(message: Message, session: AsyncSession) -> None:
    bots = await BotRepository(session).list_by_owner(message.from_user.id)
    booking_repo = BookingRepository(session)

    active_bots = sum(1 for b in bots if b.active)
    total_all = 0
    total_confirmed = 0
    for bot in bots:
        total_all += await booking_repo.count_by_bot_and_status(bot.id)
        total_confirmed += await booking_repo.count_by_bot_and_status(bot.id, BookingStatus.CONFIRMED)

    text = (
        "📊 Статистика\n\n"
        f"Всего ботов: {len(bots)}\n"
        f"Активных ботов: {active_bots}\n"
        f"Всего заявок: {total_all}\n"
        f"Активных записей: {total_confirmed}"
    )
    await message.answer(text)


def register(router: Router) -> None:
    router.message.register(show_stats, F.text == STATS_BUTTON)
