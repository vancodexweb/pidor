from datetime import date as date_

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from app.callbacks.factories import BookingActionCallback, BookingStartCallback, DateCallback, MyBookingCallback, SlotCallback
from app.database.models.booking import Booking
from app.database.models.time_slot import TimeSlot
from app.utils.datetime_utils import format_date_ru, format_time

# Deliberately distinct from admin_kb.MY_BOOKINGS_BUTTON ("📋 Мои записи") so the
# two reply-keyboard handlers never collide on the same button text.
MY_BOOKINGS_BUTTON = "📖 Мои записи"
ADMIN_PANEL_BUTTON = "👩‍💼 Админ-панель"


def start_booking_kb(button_text: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=button_text, callback_data=BookingStartCallback().pack())]]
    )


def persistent_menu_kb(is_owner: bool) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=MY_BOOKINGS_BUTTON)]]
    if is_owner:
        rows.append([KeyboardButton(text=ADMIN_PANEL_BUTTON)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def phone_request_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def dates_kb(dates: list[date_]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=format_date_ru(d), callback_data=DateCallback(date=d.isoformat()).pack())]
        for d in dates
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def times_kb(slots: list[TimeSlot]) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text=format_time(s.start_time), callback_data=SlotCallback(action="book", slot_id=s.id).pack())
        for s in slots
    ]
    rows = [buttons[i : i + 3] for i in range(0, len(buttons), 3)]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_booking_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data=BookingActionCallback(action="confirm").pack())],
            [InlineKeyboardButton(text="✏️ Изменить", callback_data=BookingActionCallback(action="edit").pack())],
            [InlineKeyboardButton(text="❌ Отмена", callback_data=BookingActionCallback(action="cancel").pack())],
        ]
    )


def my_bookings_kb(bookings: list[Booking]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"❌ Отменить {format_date_ru(b.slot.date)} {format_time(b.slot.start_time)}",
                callback_data=MyBookingCallback(action="cancel", booking_id=b.id).pack(),
            )
        ]
        for b in bookings
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def cancel_booking_confirm_kb(booking_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да", callback_data=MyBookingCallback(action="cancel_confirm", booking_id=booking_id).pack()),
                InlineKeyboardButton(text="❌ Нет", callback_data=MyBookingCallback(action="cancel_back", booking_id=booking_id).pack()),
            ]
        ]
    )
