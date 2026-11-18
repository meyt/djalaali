# djalaali/lookups.py
import datetime

from django.conf import settings
from django.db import models
from django.db.models.lookups import GreaterThanOrEqual, LessThan, Lookup
from django.utils import timezone

from .jdate import jdate


def parse_period(value):
    """``"1403"``, ``"1403-2"`` or ``"1403-02-05"`` -> ``(year, month, day)``."""
    try:
        parts = [int(part) for part in str(value).split("-")]
    except ValueError:
        raise ValueError(f"Invalid Jalali period: {value!r}") from None
    if not 1 <= len(parts) <= 3:
        raise ValueError(f"Invalid Jalali period: {value!r}")
    year, month, day = parts + [None] * (3 - len(parts))
    return year, month, day


def period_bounds(year, month=None, day=None):
    """Gregorian ``(start, end)`` dates of a Jalali year, month or day (end exclusive)."""
    start = jdate(year, month or 1, day or 1)
    if day:
        end = start + datetime.timedelta(days=1)
    elif month:
        end = jdate(year + (month == 12), month % 12 + 1, 1)
    else:
        end = jdate(year + 1, 1, 1)
    return start.togregorian(), end.togregorian()


class JalaliPeriod(Lookup):
    """
    ``date__jperiod="1403"`` / ``"1403-02"`` / ``"1403-02-05"``: matches a
    Jalali year, month or day. Used by the admin ``date_hierarchy``.
    """

    lookup_name = "jperiod"
    prepare_rhs = False

    def get_prep_lookup(self):
        self.bounds = period_bounds(*parse_period(self.rhs))
        return self.rhs

    def as_sql(self, compiler, connection):
        start, end = self.bounds
        if isinstance(self.lhs.output_field, models.DateTimeField):
            start, end = (
                datetime.datetime.combine(value, datetime.time())
                for value in (start, end)
            )
            if settings.USE_TZ:
                start = timezone.make_aware(start)
                end = timezone.make_aware(end)
        lower_sql, lower_params = compiler.compile(
            GreaterThanOrEqual(self.lhs, start)
        )
        upper_sql, upper_params = compiler.compile(LessThan(self.lhs, end))
        return (
            f"({lower_sql} AND {upper_sql})",
            (*lower_params, *upper_params),
        )
