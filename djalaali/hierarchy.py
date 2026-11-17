# djalaali/hierarchy.py
from django.contrib.admin.utils import get_fields_from_path
from django.db import models
from django.utils.translation import gettext as _

from . import dateformat
from .jdate import jdate
from .lookups import parse_period


def jalali_date_hierarchy(cl, original):
    """
    Jalali version of the admin ``date_hierarchy`` drill-down. Links filter
    with the ``<field>__jperiod`` lookup (see ``lookups.JalaliPeriod``).
    ``original`` is Django's implementation, used for Gregorian fields.
    """
    if not cl.date_hierarchy:
        return original(cl)
    field_name = cl.date_hierarchy
    field = get_fields_from_path(cl.model, field_name)[-1]
    if getattr(field, "gregorian", False):
        return original(cl)

    is_datetime = isinstance(field, models.DateTimeField)
    period_field = f"{field_name}__jperiod"
    field_generic = f"{field_name}__"

    def link(period=None):
        filters = {period_field: period} if period else {}
        return cl.get_query_string(filters, [field_generic])

    queryset = cl.queryset
    days = (
        queryset.datetimes(field_name, "day")
        if is_datetime
        else queryset.dates(field_name, "day")
    )
    days = sorted({jdate.fromgregorian(d.date() if is_datetime else d) for d in days})

    period = cl.params.get(period_field)
    year = month = day = None
    if period:
        year, month, day = parse_period(period)
    elif days and days[0].year == days[-1].year:
        year = days[0].year
        if days[0].month == days[-1].month:
            month = days[0].month

    def fmt(value, format_string):
        return dateformat.format_jalali(value, format_string)

    if year and month and day:
        return {
            "show": True,
            "back": {
                "link": link(f"{year}-{month}"),
                "title": fmt(jdate(year, month, 1), "F Y"),
            },
            "choices": [{"title": fmt(jdate(year, month, day), "j F")}],
        }
    if year and month:
        return {
            "show": True,
            "back": {"link": link(str(year)), "title": str(year)},
            "choices": [
                {
                    "link": link(f"{year}-{month}-{d.day}"),
                    "title": fmt(d, "j F"),
                }
                for d in days
                if (d.year, d.month) == (year, month)
            ],
        }
    if year:
        months = sorted({(d.year, d.month) for d in days if d.year == year})
        return {
            "show": True,
            "back": {"link": link(), "title": _("All dates")},
            "choices": [
                {
                    "link": link(f"{year}-{m}"),
                    "title": fmt(jdate(year, m, 1), "F Y"),
                }
                for _y, m in months
            ],
        }
    return {
        "show": True,
        "back": None,
        "choices": [
            {"link": link(str(y)), "title": str(y)}
            for y in sorted({d.year for d in days})
        ],
    }
