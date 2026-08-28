from app.utils.phone import normalize_phone


def test_normalizes_leading_eight_to_plus_seven():
    assert normalize_phone("89991234567") == "+79991234567"


def test_normalizes_plain_ten_digits_as_russian_number():
    assert normalize_phone("9991234567") == "+79991234567"


def test_keeps_already_normalized_number():
    assert normalize_phone("+79991234567") == "+79991234567"


def test_strips_formatting_characters():
    assert normalize_phone("+7 (999) 123-45-67") == "+79991234567"


def test_rejects_too_short_input():
    assert normalize_phone("12345") is None


def test_rejects_empty_input():
    assert normalize_phone("") is None
    assert normalize_phone(None) is None


def test_accepts_international_number():
    assert normalize_phone("+31612345678") == "+31612345678"
