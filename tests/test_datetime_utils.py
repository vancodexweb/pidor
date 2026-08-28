from datetime import date, time

from app.utils.datetime_utils import format_date_ru, parse_date_time_line, parse_time_line


def test_parse_time_line_valid():
    assert parse_time_line("10:00") == time(10, 0)
    assert parse_time_line("23:59") == time(23, 59)


def test_parse_time_line_invalid():
    assert parse_time_line("25:00") is None
    assert parse_time_line("not a time") is None


def test_parse_date_time_line_valid():
    assert parse_date_time_line("29.08.2026 15:30") == (date(2026, 8, 29), time(15, 30))


def test_parse_date_time_line_invalid():
    assert parse_date_time_line("31.02.2026 10:00") is None
    assert parse_date_time_line("29-08-2026 15:30") is None


def test_format_date_ru():
    assert format_date_ru(date(2026, 8, 29)) == "29 августа"
