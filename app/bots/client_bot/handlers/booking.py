import logging
from datetime import date as date_

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bots.client_bot.keyboards.client_kb import (
    MY_BOOKINGS_BUTTON,
    cancel_booking_confirm_kb,
    confirm_booking_kb,
    dates_kb,
    my_bookings_kb,
    persistent_menu_kb,
    phone_request_kb,
    times_kb,
)
from app.bots.client_bot.states.booking_states import BookingStates
from app.callbacks.factories import BookingActionCallback, BookingStartCallback, DateCallback, MyBookingCallback, SlotCallback
from app.database.models.bot import Bot as BotModel
from app.database.models.bot_settings import BotSettings
from app.database.models.time_slot import SlotStatus
from app.database.repositories.booking_repository import BookingRepository
from app.database.repositories.time_slot_repository import TimeSlotRepository
from app.services.booking_service import BookingService, SlotUnavailableError
from app.services.notification_service import NotificationService
from app.services.slot_service import SlotService
from app.utils.datetime_utils import format_date_ru, format_time, today_in_timezone
from app.utils.phone import normalize_phone

logger = logging.getLogger(__name__)


async def start_booking(
    callback: CallbackQuery, callback_data: BookingStartCallback, state: FSMContext, bot_settings: BotSettings
) -> None:
    await state.clear()
    await state.set_state(BookingStates.waiting_name)
    await callback.message.answer(bot_settings.name_question)
    await callback.answer()


async def process_name(message: Message, state: FSMContext, bot_settings: BotSettings) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Пожалуйста, отправьте имя текстом.")
        return

    await state.update_data(client_name=name)
    await state.set_state(BookingStates.waiting_phone)
    await message.answer(bot_settings.phone_question, reply_markup=phone_request_kb())


async def process_phone(
    message: Message, state: FSMContext, child_bot: BotModel, bot_settings: BotSettings, session: AsyncSession
) -> None:
    raw_phone = message.contact.phone_number if message.contact else (message.text or "")
    phone = normalize_phone(raw_phone)
    if phone is None:
        await message.answer("❌ Не удалось распознать номер телефона. Попробуйте ещё раз, например: +79991234567")
        return

    await state.update_data(phone=phone)

    today = today_in_timezone(bot_settings.timezone)
    available_dates = await SlotService(session).list_available_dates(child_bot.id, today)
    if not available_dates:
        await state.clear()
        await message.answer(
            "😔 К сожалению, сейчас нет свободных дат для записи. Попробуйте позже.",
            reply_markup=persistent_menu_kb(message.from_user.id == child_bot.owner_id),
        )
        return

    await state.set_state(BookingStates.waiting_date)
    await message.answer("📅 Выберите дату:", reply_markup=dates_kb(available_dates))


async def process_date(callback: CallbackQuery, callback_data: DateCallback, state: FSMContext, child_bot: BotModel, session: AsyncSession) -> None:
    picked_date = date_.fromisoformat(callback_data.date)
    slots = await SlotService(session).list_available_for_date(child_bot.id, picked_date)
    if not slots:
        await callback.answer("На эту дату уже нет свободных окон", show_alert=True)
        return

    await state.update_data(date=picked_date.isoformat())
    await state.set_state(BookingStates.waiting_time)
    await callback.message.edit_text(f"📅 {format_date_ru(picked_date)}\n\nВыберите время:", reply_markup=times_kb(slots))
    await callback.answer()


async def process_time(callback: CallbackQuery, callback_data: SlotCallback, state: FSMContext, bot_settings: BotSettings, session: AsyncSession) -> None:
    slot = await TimeSlotRepository(session).get_by_id(callback_data.slot_id)
    if slot is None or slot.status != SlotStatus.AVAILABLE:
        await callback.answer("Это время уже занято, выберите другое", show_alert=True)
        return

    data = await state.update_data(slot_id=slot.id)
    await state.set_state(BookingStates.confirm)

    text = (
        f"{bot_settings.confirmation_text}\n\n"
        f"👤 Имя: {data['client_name']}\n"
        f"📱 Телефон: {data['phone']}\n"
        f"📅 {format_date_ru(slot.date)}\n"
        f"🕐 {format_time(slot.start_time)}\n\n"
        "Всё верно?"
    )
    await callback.message.edit_text(text, reply_markup=confirm_booking_kb())
    await callback.answer()


async def process_confirm_action(
    callback: CallbackQuery,
    callback_data: BookingActionCallback,
    state: FSMContext,
    bot_settings: BotSettings,
    child_bot: BotModel,
    session: AsyncSession,
    bot: Bot,
) -> None:
    if callback_data.action == "cancel":
        await state.clear()
        await callback.message.edit_text("❌ Запись отменена.")
        await callback.answer()
        return

    if callback_data.action == "edit":
        await state.set_state(BookingStates.waiting_name)
        await callback.message.edit_text(bot_settings.name_question)
        await callback.answer()
        return

    # action == "confirm"
    data = await state.get_data()
    try:
        booking = await BookingService(session).create_booking(
            bot_id=child_bot.id,
            slot_id=data["slot_id"],
            client_telegram_id=callback.from_user.id,
            client_name=data["client_name"],
            phone=data["phone"],
        )
    except SlotUnavailableError:
        today = today_in_timezone(bot_settings.timezone)
        available_dates = await SlotService(session).list_available_dates(child_bot.id, today)
        await state.set_state(BookingStates.waiting_date)
        if not available_dates:
            await state.clear()
            await callback.message.edit_text("😔 К сожалению, это время только что заняли, а других свободных дат сейчас нет.")
            await callback.answer()
            return
        await callback.message.edit_text(
            "😔 К сожалению, это время только что занял другой клиент.\n\nВыберите другое время:",
            reply_markup=dates_kb(available_dates),
        )
        await callback.answer()
        return

    await state.clear()
    slot = booking.slot
    text = f"{bot_settings.success_text}\n\n📅 {format_date_ru(slot.date)}\n🕐 {format_time(slot.start_time)}"
    await callback.message.edit_text(text)
    await callback.answer()

    await NotificationService.notify_owner_new_booking(bot, child_bot.owner_id, booking, slot)


async def show_my_bookings(message: Message, child_bot: BotModel, bot_settings: BotSettings, session: AsyncSession) -> None:
    today = today_in_timezone(bot_settings.timezone)
    bookings = await BookingRepository(session).list_upcoming_by_client(child_bot.id, message.from_user.id, today)
    if not bookings:
        await message.answer("У вас пока нет активных записей.")
        return
    await message.answer("📋 Ваши записи:", reply_markup=my_bookings_kb(bookings))


async def request_cancel_own_booking(callback: CallbackQuery, callback_data: MyBookingCallback) -> None:
    await callback.message.edit_text("Отменить эту запись?", reply_markup=cancel_booking_confirm_kb(callback_data.booking_id))
    await callback.answer()


async def cancel_own_booking_back(callback: CallbackQuery, callback_data: MyBookingCallback) -> None:
    await callback.message.edit_text("Действие отменено.")
    await callback.answer()


async def confirm_cancel_own_booking(
    callback: CallbackQuery, callback_data: MyBookingCallback, child_bot: BotModel, session: AsyncSession, bot: Bot
) -> None:
    booking = await BookingService(session).cancel_booking(callback_data.booking_id, child_bot.id)
    if booking is None:
        await callback.answer("Не удалось отменить запись", show_alert=True)
        return

    await callback.message.edit_text("✅ Запись отменена.")
    await callback.answer()
    await NotificationService.notify_owner_booking_cancelled(bot, child_bot.owner_id, booking, booking.slot)


def register(router: Router) -> None:
    router.callback_query.register(start_booking, BookingStartCallback.filter())
    router.message.register(process_name, BookingStates.waiting_name, F.text)
    router.message.register(process_phone, BookingStates.waiting_phone, F.contact | F.text)
    router.callback_query.register(process_date, DateCallback.filter(), BookingStates.waiting_date)
    router.callback_query.register(process_time, SlotCallback.filter(F.action == "book"), BookingStates.waiting_time)
    router.callback_query.register(process_confirm_action, BookingActionCallback.filter(), BookingStates.confirm)

    router.message.register(show_my_bookings, F.text == MY_BOOKINGS_BUTTON)
    router.callback_query.register(request_cancel_own_booking, MyBookingCallback.filter(F.action == "cancel"))
    router.callback_query.register(cancel_own_booking_back, MyBookingCallback.filter(F.action == "cancel_back"))
    router.callback_query.register(confirm_cancel_own_booking, MyBookingCallback.filter(F.action == "cancel_confirm"))
