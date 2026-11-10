# djalaali/templatetags/djalaali_tags.py
import datetime

from django import template

from .. import conf, dateformat

register = template.Library()


@register.filter(name="jdate")
def jdate_filter(value, format_string=None):
    """
    Formats a Gregorian date/datetime as a Jalali date string, using the
    syntax of Django's ``date`` filter.
    Usage: {{ my_date|jdate:"j F Y" }}
    Without an argument, DJALAALI_DATE_FORMAT is used.
    """
    if value in (None, ""):
        return ""
    if not isinstance(value, datetime.date):
        return value
    return dateformat.format_gregorian(
        value, format_string or conf.date_format()
    )
