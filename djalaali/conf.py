# djalaali/conf.py
from django.conf import settings

_DATE_INPUT_FORMATS = ["%Y/%m/%d", "%Y-%m-%d", "%Y.%m.%d"]

DEFAULTS = {
    # Display (admin change list, read-only fields, `jdate` filter). Django
    # `date` filter syntax, like Django's DATE_FORMAT.
    "DJALAALI_DATE_FORMAT": "Y/m/d",
    "DJALAALI_DATETIME_FORMAT": "Y/m/d H:i",
    # Form input parsing, like Django's DATE_INPUT_FORMATS. strptime syntax;
    # the first one is also how widgets render a value.
    "DJALAALI_DATE_INPUT_FORMATS": _DATE_INPUT_FORMATS,
    "DJALAALI_DATETIME_INPUT_FORMATS": [
        f"{date} {time}"
        for date in _DATE_INPUT_FORMATS
        for time in ("%H:%M:%S", "%H:%M")
    ],
}


def get_setting(name):
    return getattr(settings, name, DEFAULTS[name])


def date_format():
    return get_setting("DJALAALI_DATE_FORMAT")


def datetime_format():
    return get_setting("DJALAALI_DATETIME_FORMAT")


def date_input_formats():
    return list(get_setting("DJALAALI_DATE_INPUT_FORMATS"))


def datetime_input_formats():
    """
    ``DJALAALI_DATETIME_INPUT_FORMATS`` plus every date input format combined
    with a time, so whatever the split widget renders can always be parsed.
    """
    formats = list(get_setting("DJALAALI_DATETIME_INPUT_FORMATS"))
    for date in date_input_formats():
        for time in ("%H:%M:%S", "%H:%M"):
            if f"{date} {time}" not in formats:
                formats.append(f"{date} {time}")
    return formats


def date_placeholder(fmt):
    """Human readable placeholder, e.g. ``%Y/%m/%d`` -> ``YYYY/MM/DD``."""
    for token, text in (("%Y", "YYYY"), ("%m", "MM"), ("%d", "DD")):
        fmt = fmt.replace(token, text)
    return fmt
