# djalaali/templatetags/djalaali_tags.py
import datetime

from django import template

from ..jdate import jdate as JDate
from ..jdatetime import jdatetime as JDateTime

register = template.Library()


@register.filter(name="jdate")
def jdate_filter(value, format_string="%Y/%m/%d"):
    """
    Formats a Gregorian date/datetime as a Jalali date string using native strftime.
    Usage: {{ my_date|jdate:"%Y/%m/%d" }}
    """
    if value in (None, ""):
        return ""
    if isinstance(value, datetime.datetime):
        return JDateTime.fromgregorian(value).strftime(format_string)
    if isinstance(value, datetime.date):
        return JDate.fromgregorian(value).strftime(format_string)
    return value
