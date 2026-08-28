from datetime import date as date_

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bots.client_bot.filters.is_owner import IsOwner
from app.bots.client_bot.keyboards.admin_kb import MY_BOOKINGS_BUTTON, bookings_list_kb, cancel_admin_booking_confirm_kb
from app.bots.client_bot.keyboards.calendar_kb import build_calendar
from app.callbacks.factories import AdminBookingCallback, CalendarDayCallback, CalendarNavCallback
from app.database.models.bot import Bot as BotModel
from app.database.models.bot_settings import BotSettings
from app.database.repositories.booking_repository import BookingRepository
from app.services.booking_service import BookingService
from app.utils.datetime_utils import format_date_ru_full, today_in_timezone

BOOKINGS_PURPOSE = "bookings"


async def open_bookings_calendar(message: Message, state: FSMContext, bot_settings: BotSettings) -> None:
    await state.clear()
    today = today_in_timezone(bot_settings.timezone)
    await message.answer(
        "📋 Мои записи\n\nВыберите дату:",
        reply_markup=build_calendar(BOOKINGS_PURPOSE, today.year, today.month, today),
    )


async def navigate_bookings_calendar(callback: CallbackQuery, callback_data: CalendarNavCallback, bot_settings: BotSettings) -> None:
    today = today_in_timezone(bot_settings.timezone)
    await callback.message.edit_reply_markup(
        reply_markup=build_calendar(BOOKINGS_PURPOSE, callback_data.year, callback_data.month, today)
    )
    await callback.answer()


async def pick_bookings_day(callback: CallbackQuery, callback_data: CalendarDayCallback, child_bot: BotModel, session: AsyncSession) -> None:
    picked_date = date_.fromisoformat(callback_data.date)
    bookings = await BookingRepository(session).list_by_bot_and_date(child_bot.id, picked_date)
    if not bookings:
        await callback.message.answer(f"📅 {format_date_ru_full(picked_date)}\n\nЗаписей нет.")
    else:
        await callback.message.answer(f"📅 {format_date_ru_full(picked_date)}", reply_markup=bookings_list_kb(bookings))
    await callback.answer()


async def request_cancel_booking(callback: CallbackQuery, callback_data: AdminBookingCallback) -> None:
    await callback.message.edit_text("Отменить эту запись?", reply_markup=cancel_admin_booking_confirm_kb(callback_data.booking_id))
    await callback.answer()


async def cancel_booking_back(callback: CallbackQuery) -> None:
    await callback.message.edit_text("Действие отменено.")
    await callback.answer()


async def confirm_cancel_booking(
    callback: CallbackQuery, callback_data: AdminBookingCallback, child_bot: BotModel, session: AsyncSession
) -> None:
    booking = await BookingService(session).cancel_booking(callback_data.booking_id, child_bot.id)
    if booking is None:
        await callback.answer("Не удалось отменить запись", show_alert=True)
        return
    await callback.message.edit_text("✅ Запись отменена.")
    await callback.answer()


def register(router: Router) -> None:
    router.message.register(open_bookings_calendar, F.text == MY_BOOKINGS_BUTTON, IsOwner())
    router.callback_query.register(navigate_bookings_calendar, CalendarNavCallback.filter(F.purpose == BOOKINGS_PURPOSE), IsOwner())
    router.callback_query.register(pick_bookings_day, CalendarDayCallback.filter(F.purpose == BOOKINGS_PURPOSE), IsOwner())

    router.callback_query.register(request_cancel_booking, AdminBookingCallback.filter(F.action == "cancel"), IsOwner())
    router.callback_query.register(cancel_booking_back, AdminBookingCallback.filter(F.action == "cancel_back"), IsOwner())
    router.callback_query.register(confirm_cancel_booking, AdminBookingCallback.filter(F.action == "cancel_confirm"), IsOwner())
