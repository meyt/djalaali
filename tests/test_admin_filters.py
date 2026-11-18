import datetime
from types import SimpleNamespace
from unittest import mock

import pytest
from django.contrib.admin import DateFieldListFilter, FieldListFilter
from django.contrib.admin.templatetags import admin_list
from django.db import connection, models
from django.test import RequestFactory
from django.utils import timezone

from djalaali.filters import JalaliDateFieldListFilter
from djalaali.lookups import parse_period, period_bounds
from djalaali.models import GregorianDateField


class Entry(models.Model):
    day = models.DateField(null=True)
    moment = models.DateTimeField(null=True)
    plain = GregorianDateField(null=True)

    class Meta:
        app_label = "djalaali"


@pytest.fixture
def entries():
    with connection.schema_editor() as editor:
        editor.create_model(Entry)
    utc = datetime.timezone.utc
    # 2024-03-19 is 1402/12/29, 03-20 is 1403/01/01, 04-19 is 1403/01/31 and
    # 04-20 is 1403/02/01.
    for g in [(2024, 3, 19), (2024, 3, 20), (2024, 4, 19), (2024, 4, 20)]:
        Entry.objects.create(
            day=datetime.date(*g),
            moment=datetime.datetime(*g, 12, 0, tzinfo=utc),
        )
    yield
    with connection.schema_editor() as editor:
        editor.delete_model(Entry)


def test_parse_period():
    assert parse_period("1403") == (1403, None, None)
    assert parse_period("1403-2") == (1403, 2, None)
    assert parse_period("1403-02-05") == (1403, 2, 5)
    for bad in ("", "abc", "1-2-3-4", "1403-x"):
        with pytest.raises(ValueError):
            parse_period(bad)


def test_period_bounds():
    assert period_bounds(1403) == (
        datetime.date(2024, 3, 20),
        datetime.date(2025, 3, 21),
    )
    assert period_bounds(1403, 12) == (
        datetime.date(2025, 2, 19),
        datetime.date(2025, 3, 21),
    )
    assert period_bounds(1403, 1, 1) == (
        datetime.date(2024, 3, 20),
        datetime.date(2024, 3, 21),
    )
    assert period_bounds(1403, 12, 30)[1] == datetime.date(2025, 3, 21)
    with pytest.raises(ValueError):
        period_bounds(1403, 13)
    with pytest.raises(ValueError):
        period_bounds(99999)


def test_jperiod_lookup_date_field(entries):
    days = lambda period: [  # noqa: E731
        e.day.isoformat()
        for e in Entry.objects.filter(day__jperiod=period).order_by("day")
    ]
    assert days("1402") == ["2024-03-19"]
    assert days("1403") == ["2024-03-20", "2024-04-19", "2024-04-20"]
    assert days("1403-1") == ["2024-03-20", "2024-04-19"]
    assert days("1403-02") == ["2024-04-20"]
    assert days("1403-02-01") == ["2024-04-20"]


def test_jperiod_lookup_datetime_field_uses_current_timezone(entries):
    tehran = timezone.zoneinfo.ZoneInfo("Asia/Tehran")
    # 2024-03-19 21:00 UTC is 2024-03-20 00:30 in Tehran: already 1403/01/01.
    Entry.objects.create(
        moment=datetime.datetime(
            2024, 3, 19, 21, 0, tzinfo=datetime.timezone.utc
        )
    )
    with timezone.override(tehran):
        assert Entry.objects.filter(moment__jperiod="1402").count() == 1
        assert Entry.objects.filter(moment__jperiod="1403-1-1").count() == 2
    assert Entry.objects.filter(moment__jperiod="1402").count() == 2


def test_jperiod_lookup_invalid_value():
    with pytest.raises(ValueError):
        Entry.objects.filter(day__jperiod="nope")


def _filter(field_name, now, params=None):
    request = RequestFactory().get("/")
    field = Entry._meta.get_field(field_name)
    with mock.patch("django.utils.timezone.now", return_value=now):
        return FieldListFilter.create(
            field, request, params or {}, Entry, None, field_name
        )


def _links(field_name, now):
    """Filter links as ``{title: {param: str(value)}}`` (Django's version
    differs in whether it stores strings or dates)."""
    return {
        str(title): {k: str(v) for k, v in params.items()}
        for title, params in _filter(field_name, now).links
    }


def test_list_filter_is_registered_for_date_fields_only_when_jalali():
    assert isinstance(_filter("day", timezone.now()), JalaliDateFieldListFilter)
    assert isinstance(_filter("moment", timezone.now()), JalaliDateFieldListFilter)
    plain = _filter("plain", timezone.now())
    assert type(plain) is DateFieldListFilter


def test_list_filter_this_month_and_year_follow_jalali_calendar():
    now = datetime.datetime(2024, 4, 25, 10, tzinfo=datetime.timezone.utc)
    links = _links("day", now)
    assert links["This month"] == {
        "day__gte": "2024-04-20",  # 1403/02/01
        "day__lt": "2024-05-21",  # 1403/03/01
    }
    assert links["This year"] == {
        "day__gte": "2024-03-20",
        "day__lt": "2025-03-21",
    }
    # Today / Past 7 days are calendar independent and left as Django has them.
    assert links["Today"]["day__gte"] == "2024-04-25"


def test_list_filter_last_month_wraps_year():
    now = datetime.datetime(2025, 3, 1, 10, tzinfo=datetime.timezone.utc)  # 1403/12/11
    links = _links("day", now)
    assert links["This month"]["day__gte"] == "2025-02-19"
    assert links["This month"]["day__lt"] == "2025-03-21"


def test_list_filter_datetime_field_bounds_are_aware_local_midnight():
    tehran = timezone.zoneinfo.ZoneInfo("Asia/Tehran")
    now = datetime.datetime(2024, 4, 25, 10, tzinfo=datetime.timezone.utc)
    with timezone.override(tehran):
        links = _links("moment", now)
    # Local (Tehran) midnight of 1403/02/01, with its UTC offset.
    assert links["This month"]["moment__gte"].startswith("2024-04-20 00:00:00+0")


def _changelist(entries_qs, field, params=None):
    params = params or {}

    def get_query_string(new_params=None, remove=None):
        kept = {
            k: v
            for k, v in params.items()
            if not any(k.startswith(r) for r in (remove or []))
        }
        kept.update(new_params or {})
        return "?" + "&".join(f"{k}={v}" for k, v in kept.items())

    return SimpleNamespace(
        date_hierarchy=field,
        model=Entry,
        queryset=entries_qs,
        params=params,
        get_query_string=get_query_string,
    )


def titles(result):
    return [c["title"] for c in result["choices"]]


def test_hierarchy_years(entries):
    Entry.objects.create(day=datetime.date(2022, 1, 1))
    result = admin_list.date_hierarchy(_changelist(Entry.objects.all(), "day"))
    assert result["back"] is None
    assert titles(result) == ["1400", "1402", "1403"]
    assert result["choices"][1]["link"] == "?day__jperiod=1402"


def test_hierarchy_single_year_starts_at_months(entries):
    qs = Entry.objects.filter(day__jperiod="1403")
    result = admin_list.date_hierarchy(_changelist(qs, "day"))
    assert result["back"]["title"] == "All dates"
    assert titles(result) == ["فروردین 1403", "اردیبهشت 1403"]


def test_hierarchy_single_month_starts_at_days(entries):
    qs = Entry.objects.filter(day__jperiod="1403-1")
    result = admin_list.date_hierarchy(_changelist(qs, "day"))
    assert result["back"]["title"] == "1403"
    assert titles(result) == ["1 فروردین", "31 فروردین"]


def test_hierarchy_months_of_year(entries):
    Entry.objects.create(day=datetime.date(2022, 1, 1))
    params = {"day__jperiod": "1403"}
    qs = Entry.objects.filter(day__jperiod="1403")
    result = admin_list.date_hierarchy(_changelist(qs, "day", params))
    assert result["back"]["title"] == "All dates"
    assert result["back"]["link"] == "?"
    assert titles(result) == ["فروردین 1403", "اردیبهشت 1403"]
    assert result["choices"][1]["link"] == "?day__jperiod=1403-2"


def test_hierarchy_days_of_month_and_single_day(entries):
    params = {"day__jperiod": "1403-2"}
    qs = Entry.objects.filter(day__jperiod="1403-2")
    result = admin_list.date_hierarchy(_changelist(qs, "day", params))
    assert result["back"]["title"] == "1403"
    assert titles(result) == ["1 اردیبهشت"]
    assert result["choices"][0]["link"] == "?day__jperiod=1403-2-1"

    params = {"day__jperiod": "1403-2-1"}
    qs = Entry.objects.filter(day__jperiod="1403-2-1")
    result = admin_list.date_hierarchy(_changelist(qs, "day", params))
    assert result["back"]["title"] == "اردیبهشت 1403"
    assert result["back"]["link"] == "?day__jperiod=1403-2"
    assert titles(result) == ["1 اردیبهشت"]


def test_hierarchy_datetime_field(entries):
    params = {"moment__jperiod": "1403"}
    qs = Entry.objects.filter(moment__jperiod="1403")
    result = admin_list.date_hierarchy(_changelist(qs, "moment", params))
    assert titles(result) == ["فروردین 1403", "اردیبهشت 1403"]


def test_hierarchy_gregorian_field_and_disabled_use_django(entries):
    original = mock.Mock(return_value="original")
    from djalaali.hierarchy import jalali_date_hierarchy

    cl = _changelist(Entry.objects.all(), "plain")
    assert jalali_date_hierarchy(cl, original) == "original"
    cl = _changelist(Entry.objects.all(), None)
    assert jalali_date_hierarchy(cl, original) == "original"
