from aiogram.filters.callback_data import CallbackData


class CalendarNavCallback(CallbackData, prefix="calnav"):
    purpose: str  # "add_slot" | "view_slots" | "delete_slot" | "bookings"
    year: int
    month: int


class CalendarDayCallback(CallbackData, prefix="calday"):
    purpose: str  # "add_slot" | "view_slots" | "delete_slot" | "bookings"
    date: str  # ISO format YYYY-MM-DD


class DateCallback(CallbackData, prefix="date"):
    date: str  # ISO format YYYY-MM-DD, used in the client date-picker


class SlotCallback(CallbackData, prefix="slot"):
    action: str  # "book" | "delete" | "delete_confirm" | "delete_cancel"
    slot_id: int


class BookingActionCallback(CallbackData, prefix="bkact"):
    action: str  # "confirm" | "edit" | "cancel"
    booking_id: int = 0  # 0 while booking not yet created (confirm/edit/cancel of draft)


class MyBookingCallback(CallbackData, prefix="mybk"):
    action: str  # "cancel" | "cancel_confirm" | "cancel_back"
    booking_id: int


class AdminBookingCallback(CallbackData, prefix="adbk"):
    action: str  # "cancel" | "cancel_confirm" | "cancel_back"
    booking_id: int


class MyBotCallback(CallbackData, prefix="mybot"):
    action: str  # "open" | "start" | "stop" | "delete" | "delete_confirm" | "back"
    bot_id: int


class BookingStartCallback(CallbackData, prefix="bkstart"):
    action: str = "start"


class SettingsFieldCallback(CallbackData, prefix="setf"):
    field: str


class NoopCallback(CallbackData, prefix="noop"):
    pass
