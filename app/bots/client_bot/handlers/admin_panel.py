from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bots.client_bot.filters.is_owner import IsOwner
from app.bots.client_bot.keyboards.admin_kb import BACK_BUTTON, STATS_BUTTON, admin_menu_kb
from app.bots.client_bot.keyboards.client_kb import ADMIN_PANEL_BUTTON, persistent_menu_kb
from app.database.models.bot import Bot as BotModel
from app.database.models.booking import BookingStatus
from app.database.models.bot_settings import BotSettings
from app.database.repositories.booking_repository import BookingRepository
from app.database.repositories.time_slot_repository import TimeSlotRepository
from app.utils.datetime_utils import today_in_timezone


async def open_admin_panel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("👩‍💼 Админ-панель", reply_markup=admin_menu_kb())


async def close_admin_panel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Главное меню", reply_markup=persistent_menu_kb(True))


async def show_stats(message: Message, child_bot: BotModel, bot_settings: BotSettings, session: AsyncSession) -> None:
    today = today_in_timezone(bot_settings.timezone)
    booking_repo = BookingRepository(session)
    slot_repo = TimeSlotRepository(session)

    total = await booking_repo.count_by_bot_and_status(child_bot.id)
    confirmed = await booking_repo.count_by_bot_and_status(child_bot.id, BookingStatus.CONFIRMED)
    cancelled = await booking_repo.count_by_bot_and_status(child_bot.id, BookingStatus.CANCELLED)

    available_dates = await slot_repo.list_available_dates(child_bot.id, today)
    available_slots_total = 0
    for available_date in available_dates:
        available_slots_total += len(await slot_repo.list_available_by_date(child_bot.id, available_date))

    text = (
        "📊 Статистика\n\n"
        f"Всего записей: {total}\n"
        f"Активных: {confirmed}\n"
        f"Отменённых: {cancelled}\n"
        f"Свободных окон: {available_slots_total}"
    )
    await message.answer(text)


def register(router: Router) -> None:
    router.message.register(open_admin_panel, F.text == ADMIN_PANEL_BUTTON, IsOwner())
    router.message.register(close_admin_panel, F.text == BACK_BUTTON, IsOwner())
    router.message.register(show_stats, F.text == STATS_BUTTON, IsOwner())
