# djalaali/dateformat.py
"""
Jalali date formatting using the format characters of Django's ``date``
template filter (the syntax of Django's ``DATE_FORMAT`` setting).
"""
import datetime

from .algo import month_length
from .jdate import JalaliConfig, jdate
from .jdatetime import jdatetime

def _split(fmt):
    """Yields ``(char, is_literal)`` honouring backslash escapes."""
    chars = iter(fmt)
    for char in chars:
        if char == "\\":
            yield next(chars, "\\"), True
        else:
            yield char, False


def _django_char(value, char):
    config = JalaliConfig()
    hour = getattr(value, "hour", 0)
    gregorian = getattr(value, "_gdatetime", None)
    if char == "d":
        return f"{value.day:02d}"
    if char == "j":
        return str(value.day)
    if char == "D":
        return config.get_weekday_name(value.weekday(), short=True)
    if char == "l":
        return config.get_weekday_name(value.weekday())
    if char == "w":
        return str(value.isoweekday() % 7)
    if char == "z":
        month = value.month
        before = (month - 1) * 31 if month <= 7 else 6 * 31 + (month - 7) * 30
        return str(before + value.day)
    if char == "m":
        return f"{value.month:02d}"
    if char == "n":
        return str(value.month)
    if char == "M":
        return config.get_month_name(value.month, short=True)
    if char == "F":
        return config.get_month_name(value.month)
    if char == "t":
        return str(month_length(value.year, value.month))
    if char == "L":
        return "1" if value.isleap() else "0"
    if char == "y":
        return f"{value.year % 100:02d}"
    if char == "Y":
        return str(value.year)
    if char == "a":
        return config.am_pm["am" if hour < 12 else "pm"]
    if char == "A":
        return config.am_pm["am" if hour < 12 else "pm"]
    if char == "g":
        return str(hour % 12 or 12)
    if char == "G":
        return str(hour)
    if char == "h":
        return f"{hour % 12 or 12:02d}"
    if char == "H":
        return f"{hour:02d}"
    if char == "i":
        return f"{getattr(value, 'minute', 0):02d}"
    if char == "s":
        return f"{getattr(value, 'second', 0):02d}"
    if char == "u":
        return f"{getattr(value, 'microsecond', 0):06d}"
    if char == "O" and gregorian is not None:
        return gregorian.strftime("%z")
    if char in "eT" and gregorian is not None:
        return gregorian.strftime("%Z")
    if char == "c":
        return value.isoformat()
    return char


def format_jalali(value, fmt):
    """Formats a ``jdate``/``jdatetime`` with Django ``date`` syntax."""
    return "".join(
        char if literal else _django_char(value, char)
        for char, literal in _split(fmt)
    )


def format_gregorian(value, fmt):
    """Converts a Gregorian date/datetime to Jalali and formats it."""
    if isinstance(value, datetime.datetime):
        return format_jalali(jdatetime.fromgregorian(value), fmt)
    return format_jalali(jdate.fromgregorian(value), fmt)
