import re
from datetime import date as date_
from datetime import time as time_
from datetime import datetime
from zoneinfo import ZoneInfo

MONTHS_RU_GENITIVE = {
    1: "января",
    2: "февраля",
    3: "марта",
    4: "апреля",
    5: "мая",
    6: "июня",
    7: "июля",
    8: "августа",
    9: "сентября",
    10: "октября",
    11: "ноября",
    12: "декабря",
}

MONTHS_RU_NOMINATIVE = {
    1: "Январь",
    2: "Февраль",
    3: "Март",
    4: "Апрель",
    5: "Май",
    6: "Июнь",
    7: "Июль",
    8: "Август",
    9: "Сентябрь",
    10: "Октябрь",
    11: "Ноябрь",
    12: "Декабрь",
}

WEEKDAYS_RU_SHORT = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

_TIME_RE = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")
_DATE_TIME_RE = re.compile(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})\s+([01]?\d|2[0-3]):([0-5]\d)$")


def format_date_ru(value: date_) -> str:
    return f"{value.day} {MONTHS_RU_GENITIVE[value.month]}"


def format_date_ru_full(value: date_) -> str:
    return f"{value.day} {MONTHS_RU_GENITIVE[value.month]} {value.year}"


def format_time(value: time_) -> str:
    return value.strftime("%H:%M")


def parse_time_line(line: str) -> time_ | None:
    """Parse a bare 'HH:MM' line."""
    match = _TIME_RE.match(line.strip())
    if not match:
        return None
    hour, minute = int(match.group(1)), int(match.group(2))
    return time_(hour=hour, minute=minute)


def parse_date_time_line(line: str) -> tuple[date_, time_] | None:
    """Parse a full 'DD.MM.YYYY HH:MM' line."""
    match = _DATE_TIME_RE.match(line.strip())
    if not match:
        return None
    day, month, year, hour, minute = (int(g) for g in match.groups())
    try:
        return date_(year=year, month=month, day=day), time_(hour=hour, minute=minute)
    except ValueError:
        return None


def now_in_timezone(timezone: str) -> datetime:
    return datetime.now(ZoneInfo(timezone))


def today_in_timezone(timezone: str) -> date_:
    return now_in_timezone(timezone).date()
