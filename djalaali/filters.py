# djalaali/filters.py
from django.contrib.admin.filters import DateFieldListFilter
from django.db import models
from django.utils import timezone

from .jdate import jdate


class JalaliDateFieldListFilter(DateFieldListFilter):
    """
    ``DateFieldListFilter`` whose "This month" and "This year" follow the
    Jalali calendar.
    """

    def __init__(self, field, request, params, model, model_admin, field_path):
        super().__init__(
            field, request, params, model, model_admin, field_path
        )
        now = timezone.now()
        if timezone.is_aware(now):
            now = timezone.localtime(now)
        if isinstance(field, models.DateTimeField):
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            today = now.date()

        jtoday = jdate.fromgregorian(now.date())
        month_start = jdate(jtoday.year, jtoday.month, 1)
        if jtoday.month == 12:
            next_month = jdate(jtoday.year + 1, 1, 1)
        else:
            next_month = jdate(jtoday.year, jtoday.month + 1, 1)
        year_start = jdate(jtoday.year, 1, 1)
        next_year = jdate(jtoday.year + 1, 1, 1)

        def at(value):
            gregorian = value.togregorian()
            return today.replace(
                year=gregorian.year, month=gregorian.month, day=gregorian.day
            )

        links = list(self.links)
        # Same order as DateFieldListFilter: any, today, 7 days, month, year.
        for index, (start, end) in (
            (3, (month_start, next_month)),
            (4, (year_start, next_year)),
        ):
            links[index] = (
                links[index][0],
                {
                    self.lookup_kwarg_since: at(start),
                    self.lookup_kwarg_until: at(end),
                },
            )
        self.links = tuple(links)
