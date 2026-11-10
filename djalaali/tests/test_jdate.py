import datetime

import pytest

from djalaali.jdate import JalaliConfig, _parse_date_string, jdate
from djalaali.jdatetime import jdatetime


def test_config_lookup_by_name():
    cfg = JalaliConfig()
    assert cfg.get_month_by_name("مهر") == 7
    assert cfg.get_month_by_name("فرو") == 1
    assert cfg.get_weekday_by_name("شنبه") == 5
    assert cfg.get_weekday_by_name("ج") == 4
    with pytest.raises(ValueError):
        cfg.get_month_by_name("nope")
    with pytest.raises(ValueError):
        cfg.get_weekday_by_name("nope")


def test_parse_date_string_mismatch():
    with pytest.raises(ValueError):
        _parse_date_string("abc", "%Y")


def test_parse_date_string_trailing_percent_is_literal():
    assert _parse_date_string("5%", "%d%") == {"day": "5"}


def test_parse_date_string_unknown_directive_is_literal():
    assert _parse_date_string("%Q", "%Q") == {}


def test_parse_date_string_literal_percent():
    assert _parse_date_string("%", "%%") == {}


def test_basic_accessors_and_conversion():
    jd = jdate(1402, 1, 12)
    assert jd.togregorian() == datetime.date(2023, 4, 1)
    assert jd.weekday() == 5
    assert jd.isoweekday() == 6
    assert jd.isleap() is False
    assert jd.timetuple().tm_year == 2023
    assert str(jd) == "1402-01-12"
    assert repr(jd) == "jdate(1402, 1, 12)"
    assert jd.isoformat() == "1402-01-12"
    assert jdate.fromisoformat("1402-01-12") == jd
    with pytest.raises(ValueError):
        jdate.fromisoformat("1402/01/12")
    assert isinstance(jdate.today(), jdate)


def test_arithmetic():
    jd = jdate(1402, 1, 12)
    one = datetime.timedelta(days=1)
    assert jd + one == jdate(1402, 1, 13)
    assert one + jd == jdate(1402, 1, 13)
    assert jd - one == jdate(1402, 1, 11)
    assert jd - jdate(1402, 1, 10) == datetime.timedelta(days=2)
    assert jd - datetime.date(2023, 3, 30) == datetime.timedelta(days=2)
    assert jd.__add__(1) is NotImplemented
    assert jd.__sub__("x") is NotImplemented
    with pytest.raises(TypeError):
        jd + 1
    with pytest.raises(TypeError):
        jd - "x"


def test_comparisons():
    a, b = jdate(1402, 1, 12), jdate(1402, 1, 13)
    g = datetime.date(2023, 4, 1)
    assert a == jdate(1402, 1, 12) and a == g
    assert a < b and a <= b and b > a and b >= a
    assert a < datetime.date(2023, 4, 2)
    assert a <= g and a >= g and not a > g and not a < g
    assert hash(a) == hash(g)
    for op in ("__eq__", "__lt__", "__le__", "__gt__", "__ge__"):
        assert getattr(a, op)("x") is NotImplemented
    assert a != "x"
    with pytest.raises(TypeError):
        a < "x"


@pytest.mark.parametrize(
    "fmt,expected",
    [
        ("%a", "ش"),
        ("%A", "شنبه"),
        ("%w", "6"),
        ("%d", "12"),
        ("%b", "فرو"),
        ("%B", "فروردین"),
        ("%m", "01"),
        ("%y", "02"),
        ("%Y", "1402"),
        ("%j", "012"),
        ("%H", "00"),
        ("%I", "12"),
        ("%p", "ق.ظ"),
        ("%M", "00"),
        ("%S", "00"),
        ("%f", "000000"),
        ("%z", ""),
        ("%Z", ""),
        ("%c", "ش فرو 12 00:00:00 1402"),
        ("%x", "ش فرو 12 1402"),
        ("%X", "00:00:00"),
        ("%%", "%"),
        ("%q", "%q"),
    ],
)
def test_strftime_date(fmt, expected):
    assert jdate(1402, 1, 12).strftime(fmt) == expected


def test_strftime_day_of_year_second_half():
    assert jdate(1402, 7, 3).strftime("%j") == "189"


def test_strftime_datetime_time_parts():
    jdt = jdatetime(1402, 1, 12, 15, 4, 5, 6)
    assert jdt.strftime("%H %I %p %M %S %f") == "15 03 ب.ظ 04 05 000006"


def test_strptime():
    assert jdate.strptime("1402/01/12", "%Y/%m/%d") == jdate(1402, 1, 12)
    assert jdate.strptime("02/01/12", "%y/%m/%d") == jdate(1402, 1, 12)
    assert jdate.strptime("72/01/12", "%y/%m/%d") == jdate(1372, 1, 12)
    assert jdate.strptime("12 مهر 1402", "%d %B %Y") == jdate(1402, 7, 12)
    assert jdate.strptime("12 مهر 1402", "%d %b %Y") == jdate(1402, 7, 12)
    assert jdate.strptime("1402 012", "%Y %j") == jdate(1402, 1, 12)
    assert jdate.strptime("1402 189", "%Y %j") == jdate(1402, 7, 3)
    assert jdate.strptime("1402", "%Y") == jdate(1402, 1, 1)
    assert jdate.strptime("12", "%d") == jdate(1300, 1, 12)


def test_jdatetime_strptime_variants():
    f = jdatetime.strptime
    assert f("02/01/12", "%y/%m/%d") == jdatetime(1402, 1, 12)
    assert f("72/01/12", "%y/%m/%d") == jdatetime(1372, 1, 12)
    assert f("12 مهر 1402", "%d %B %Y") == jdatetime(1402, 7, 12)
    assert f("12 مهر 1402", "%d %b %Y") == jdatetime(1402, 7, 12)
    assert f("1402 012", "%Y %j") == jdatetime(1402, 1, 12)
    assert f("1402 189", "%Y %j") == jdatetime(1402, 7, 3)
    assert f("1402", "%Y") == jdatetime(1402, 1, 1)
    assert f("12", "%d") == jdatetime(1300, 1, 12)
    assert f("1402/01/12 13:14:15.5", "%Y/%m/%d %H:%M:%S.%f") == jdatetime(
        1402, 1, 12, 13, 14, 15, 5
    )
    assert f("03 ب.ظ", "%I %p").hour == 15
    assert f("12 ب.ظ", "%I %p").hour == 12
    assert f("03 ق.ظ", "%I %p").hour == 3
    assert f("12 ق.ظ", "%I %p").hour == 0
    assert f("03", "%I").hour == 3


def test_jdatetime_misc():
    jdt = jdatetime(1402, 1, 12, 15, 30, 1, 2, tzinfo=datetime.timezone.utc)
    assert (jdt.hour, jdt.minute, jdt.second, jdt.microsecond) == (15, 30, 1, 2)
    assert jdt.tzinfo is datetime.timezone.utc
    assert jdt.timetuple().tm_hour == 15
    assert "jdatetime(1402, 1, 12, 15, 30, 1, 2" in repr(jdt)
    assert jdt.isoformat() == "1402-01-12T15:30:01.000002+00:00"
    assert isinstance(jdatetime.now(), jdatetime)
    assert jdatetime.now(datetime.timezone.utc).tzinfo is not None
    assert jdatetime.fromgregorian(datetime.date(2023, 4, 1)) == jdatetime(
        1402, 1, 12
    )
    assert hash(jdt) == hash(jdt.togregorian())


def test_jdatetime_fromisoformat():
    assert jdatetime.fromisoformat("1402-01-12T15:30:00") == jdatetime(
        1402, 1, 12, 15, 30
    )
    assert jdatetime.fromisoformat("1402-01-12 15:30") == jdatetime(
        1402, 1, 12, 15, 30
    )
    assert jdatetime.fromisoformat("1402-01-12") == jdatetime(1402, 1, 12)
    with pytest.raises(ValueError):
        jdatetime.fromisoformat("1402/01/12")


def test_jdatetime_arithmetic_and_comparison():
    a = jdatetime(1402, 1, 12, 10)
    b = jdatetime(1402, 1, 12, 11)
    g = datetime.datetime(2023, 4, 1, 10)
    hour = datetime.timedelta(hours=1)
    assert a + hour == b
    assert b - hour == a
    assert b - a == hour
    assert b - g == hour
    assert a.__add__(1) is NotImplemented
    assert a.__sub__("x") is NotImplemented
    assert a == g and a == jdatetime(1402, 1, 12, 10)
    assert a != jdate(1402, 1, 12)
    assert a != datetime.date(2023, 4, 1)
    assert a != "x"
    assert a < b and a <= b and b > a and b >= a
    assert a < datetime.datetime(2023, 4, 1, 11)
    assert a <= g and a >= g and not a > g
    # non-datetime operands fall back to the jdate implementations
    assert a.__lt__("x") is NotImplemented
    assert a.__le__("x") is NotImplemented
    assert a.__gt__("x") is NotImplemented
    assert a.__ge__("x") is NotImplemented
