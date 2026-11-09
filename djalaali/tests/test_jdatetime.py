# djalaali/tests/test_jdatetime.py
import datetime
import zoneinfo

from djalaali.jdate import JalaliConfig, jdate
from djalaali.jdatetime import jdatetime


def test_jdate_creation():
    jd = jdate(1402, 1, 11)
    assert jd.year == 1402
    assert jd.month == 1
    assert jd.day == 11


def test_jdate_from_gregorian():
    gd = datetime.date(2023, 4, 1)
    jd = jdate.fromgregorian(gd)
    assert (jd.year, jd.month, jd.day) == (1402, 1, 12)


def test_jdate_to_gregorian():
    jd = jdate(1402, 1, 12)
    gd = jd.togregorian()
    assert (gd.year, gd.month, gd.day) == (2023, 4, 1)


def test_jdatetime_now():
    jdt = jdatetime.now()
    assert isinstance(jdt, jdatetime)
    assert jdt.year > 1400


def test_jdatetime_from_gregorian():
    gdt = datetime.datetime(2023, 4, 1, 15, 30)
    jdt = jdatetime.fromgregorian(gdt)
    assert (jdt.year, jdt.month, jdt.day) == (1402, 1, 12)
    assert (jdt.hour, jdt.minute) == (15, 30)


def test_jdatetime_to_gregorian():
    jdt = jdatetime(1402, 1, 12, 15, 30)
    gdt = jdt.togregorian()
    assert gdt == datetime.datetime(2023, 4, 1, 15, 30)


def test_jdate_strftime():
    jd = jdate(1402, 1, 11)
    assert jd.strftime("%Y/%m/%d") == "1402/01/11"
    assert jd.strftime("%y-%m-%d") == "02-01-11"
    assert jd.strftime("%B") == "فروردین"
    assert jd.strftime("%b") == "فرو"


def test_jdatetime_strftime():
    jdt = jdatetime(1402, 1, 11, 14, 30, 45)
    assert jdt.strftime("%Y/%m/%d %H:%M:%S") == "1402/01/11 14:30:45"
    assert jdt.strftime("%H:%M") == "14:30"


def test_jdate_strptime():
    jd = jdate.strptime("1402/01/11", "%Y/%m/%d")
    assert (jd.year, jd.month, jd.day) == (1402, 1, 11)


def test_jdatetime_strptime():
    jdt = jdatetime.strptime("1402-01-11 10:30:00", "%Y-%m-%d %H:%M:%S")
    assert (jdt.year, jdt.month, jdt.day) == (1402, 1, 11)
    assert (jdt.hour, jdt.minute, jdt.second) == (10, 30, 0)


def test_jdate_arithmetic():
    jd1 = jdate(1402, 1, 11)
    jd2 = jd1 + datetime.timedelta(days=10)
    assert (jd2.year, jd2.month, jd2.day) == (1402, 1, 21)

    diff = jd2 - jd1
    assert diff.days == 10


def test_jdatetime_arithmetic():
    jdt1 = jdatetime(1402, 1, 11, 10, 0)
    jdt2 = jdt1 + datetime.timedelta(hours=5)
    assert jdt2.hour == 15


def test_jdate_comparisons():
    jd1 = jdate(1402, 1, 11)
    jd2 = jdate(1402, 1, 12)
    assert jd1 < jd2
    assert jd1 != jd2
    assert jd1 == jdate(1402, 1, 11)


def test_jdatetime_with_timezone():
    tz = zoneinfo.ZoneInfo("Asia/Tehran")
    jdt = jdatetime.now(tz)
    assert jdt.tzinfo is not None
    assert jdt.strftime("%z") != ""


def test_jalali_config_customization():
    config = JalaliConfig()
    original_name = config.months[1][0]

    # Customize
    config.months[1] = ("Farvardin", "Far")

    jd = jdate(1402, 1, 11)
    assert jd.strftime("%B") == "Farvardin"
    assert jd.strftime("%b") == "Far"

    # Restore to avoid side effects
    config.months[1] = (original_name, "فرو")
