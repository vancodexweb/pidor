import calendar
from datetime import date as date_

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.callbacks.factories import CalendarDayCallback, CalendarNavCallback, NoopCallback
from app.utils.datetime_utils import MONTHS_RU_NOMINATIVE, WEEKDAYS_RU_SHORT


def build_calendar(
    purpose: str,
    year: int,
    month: int,
    today: date_,
    highlighted_dates: set[date_] | None = None,
) -> InlineKeyboardMarkup:
    """Build a month-view inline calendar.

    `purpose` tags which admin flow the picked date is for (add_slot /
    view_slots / delete_slot / bookings) so a single generic handler can
    route the CalendarDayCallback correctly.
    """
    highlighted = highlighted_dates or set()
    month_calendar = calendar.Calendar(firstweekday=0)  # Monday first
    rows: list[list[InlineKeyboardButton]] = []

    rows.append([InlineKeyboardButton(text=f"{MONTHS_RU_NOMINATIVE[month]} {year}", callback_data=NoopCallback().pack())])
    rows.append([InlineKeyboardButton(text=d, callback_data=NoopCallback().pack()) for d in WEEKDAYS_RU_SHORT])

    week_row: list[InlineKeyboardButton] = []
    for day in month_calendar.itermonthdates(year, month):
        if day.month != month:
            week_row.append(InlineKeyboardButton(text=" ", callback_data=NoopCallback().pack()))
        elif day < today:
            week_row.append(InlineKeyboardButton(text="·", callback_data=NoopCallback().pack()))
        else:
            label = f"🟢{day.day}" if day in highlighted else str(day.day)
            week_row.append(
                InlineKeyboardButton(
                    text=label,
                    callback_data=CalendarDayCallback(purpose=purpose, date=day.isoformat()).pack(),
                )
            )
        if len(week_row) == 7:
            rows.append(week_row)
            week_row = []

    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1
    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1

    rows.append(
        [
            InlineKeyboardButton(
                text="◀️",
                callback_data=CalendarNavCallback(purpose=purpose, year=prev_year, month=prev_month).pack(),
            ),
            InlineKeyboardButton(
                text="▶️",
                callback_data=CalendarNavCallback(purpose=purpose, year=next_year, month=next_month).pack(),
            ),
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)
