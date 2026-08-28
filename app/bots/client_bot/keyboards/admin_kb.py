from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from app.callbacks.factories import AdminBookingCallback, SettingsFieldCallback, SlotCallback
from app.database.models.booking import Booking
from app.database.models.time_slot import SlotStatus, TimeSlot
from app.utils.datetime_utils import format_time

ADD_SLOT_BUTTON = "➕ Добавить время"
VIEW_SLOTS_BUTTON = "📅 Свободные окна"
DELETE_SLOT_BUTTON = "❌ Удалить время"
MY_BOOKINGS_BUTTON = "📋 Мои записи"
SETTINGS_BUTTON = "⚙️ Настройки"
STATS_BUTTON = "📊 Статистика"
BACK_BUTTON = "⬅️ Назад"

FIELD_LABELS = {
    "welcome_text": "Приветственный текст",
    "welcome_sticker_file_id": "Sticker приветствия",
    "welcome_image_file_id": "Изображение приветствия",
    "start_button_text": "Текст кнопки записи",
    "name_question": "Вопрос имени",
    "phone_question": "Вопрос телефона",
    "confirmation_text": "Текст подтверждения",
    "success_text": "Текст успешной записи",
    "timezone": "Часовой пояс",
}


def admin_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=ADD_SLOT_BUTTON), KeyboardButton(text=VIEW_SLOTS_BUTTON)],
            [KeyboardButton(text=DELETE_SLOT_BUTTON), KeyboardButton(text=MY_BOOKINGS_BUTTON)],
            [KeyboardButton(text=SETTINGS_BUTTON), KeyboardButton(text=STATS_BUTTON)],
            [KeyboardButton(text=BACK_BUTTON)],
        ],
        resize_keyboard=True,
    )


def slots_status_text(date_label: str, slots: list[TimeSlot]) -> str:
    if not slots:
        return f"📅 {date_label}\n\nНа эту дату нет добавленных окон."
    lines = [f"📅 {date_label}", ""]
    for slot in slots:
        icon = "🟢" if slot.status == SlotStatus.AVAILABLE else "🔴"
        state = "свободно" if slot.status == SlotStatus.AVAILABLE else "занято"
        lines.append(f"{icon} {format_time(slot.start_time)} — {state}")
    return "\n".join(lines)


def deletable_slots_kb(slots: list[TimeSlot]) -> InlineKeyboardMarkup:
    available = [s for s in slots if s.status == SlotStatus.AVAILABLE]
    rows = [
        [InlineKeyboardButton(text=format_time(s.start_time), callback_data=SlotCallback(action="delete", slot_id=s.id).pack())]
        for s in available
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_delete_slot_kb(slot_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да", callback_data=SlotCallback(action="delete_confirm", slot_id=slot_id).pack()),
                InlineKeyboardButton(text="❌ Отмена", callback_data=SlotCallback(action="delete_cancel", slot_id=slot_id).pack()),
            ]
        ]
    )


def bookings_list_kb(bookings: list[Booking]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"❌ Отменить {format_time(b.slot.start_time)} — {b.client_name}",
                callback_data=AdminBookingCallback(action="cancel", booking_id=b.id).pack(),
            )
        ]
        for b in bookings
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def cancel_admin_booking_confirm_kb(booking_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да", callback_data=AdminBookingCallback(action="cancel_confirm", booking_id=booking_id).pack()),
                InlineKeyboardButton(text="❌ Нет", callback_data=AdminBookingCallback(action="cancel_back", booking_id=booking_id).pack()),
            ]
        ]
    )


def settings_menu_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=label, callback_data=SettingsFieldCallback(field=field).pack())]
        for field, label in FIELD_LABELS.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
