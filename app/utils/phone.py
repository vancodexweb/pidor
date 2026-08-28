import re

_DIGITS_RE = re.compile(r"\d+")


def normalize_phone(raw: str) -> str | None:
    """Normalize a user-supplied phone number to E.164-like format (+<digits>).

    Returns None if the input doesn't look like a plausible phone number.
    Handles the common Russian/CIS case of a leading 8 meaning +7.
    """
    if not raw:
        return None

    digits = "".join(_DIGITS_RE.findall(raw))
    if not digits:
        return None

    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    elif len(digits) == 10 and not raw.strip().startswith("+"):
        digits = "7" + digits

    if not (10 <= len(digits) <= 15):
        return None

    return "+" + digits
