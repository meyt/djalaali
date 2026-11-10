import csv
import gzip
import os

import pytest

from djalaali.algo import (
    Month,
    is_leap_year,
    month_length,
    to_gregorian,
    to_jalaali,
)


def parse_date(s):
    parts = s.split(":")
    return int(parts[0]), int(parts[1]), int(parts[2])


def _load_test_data():
    path = os.path.join(
        os.path.dirname(__file__), "icu-dates-1876-2124.csv.gz"
    )
    if not os.path.exists(path):
        return None
    with gzip.open(path, "rt", newline="") as f:
        reader = csv.reader(f)
        return list(reader)


_DATA = _load_test_data()


# Static, hand-checked conversions used as sanity tests in addition
# to the table-driven tests from the CSV file.
STATIC_CASES = [
    # (gregorian, expected_jalaali)
    ((2024, 1, 1), (1402, 10, 11)),
    ((2024, 3, 20), (1403, 1, 1)),
    ((2023, 3, 21), (1402, 1, 1)),
    ((2000, 1, 1), (1378, 10, 11)),
    ((1979, 3, 21), (1358, 1, 1)),
    ((1876, 1, 1), (1254, 10, 11)),
]


@pytest.mark.parametrize(
    "gregorian, expected_jalaali",
    STATIC_CASES,
    ids=[f"{g[0]}-{g[1]:02d}-{g[2]:02d}" for g, _ in STATIC_CASES],
)
def test_static_conversions(gregorian, expected_jalaali):
    gy, gm, gd = gregorian
    ejy, ejm, ejd = expected_jalaali

    jy, jm, jd = to_jalaali(gy, gm, gd)
    assert (jy, jm, jd) == (ejy, ejm, ejd), (
        f"G2J Failed for {gregorian}: got {(jy, jm, jd)}, want {expected_jalaali}"
    )

    rgy, rgm, rgd = to_gregorian(ejy, ejm, ejd)
    assert (rgy, rgm, rgd) == (gy, gm, gd), (
        f"J2G Failed for {expected_jalaali}: got {(rgy, rgm, rgd)}, want {gregorian}"
    )


def test_month_enum_values():
    assert int(Month.Farvardin) == 1
    assert int(Month.Esfand) == 12
    assert Month(7) == Month.Mehr


def test_month_length():
    # First six months always 31 days
    for m in range(1, 7):
        assert month_length(1402, m) == 31
    # Next five months always 30 days
    for m in range(7, 12):
        assert month_length(1402, m) == 30
    # Esfand: 30 in leap year, 29 otherwise
    # 1403 is a Jalaali leap year
    assert month_length(1403, 12) == 30
    # 1402 is not a leap year
    assert month_length(1402, 12) == 29


def test_is_leap_year():
    # 1403 is leap, 1402 is not
    assert is_leap_year(1403) is True
    assert is_leap_year(1402) is False


def test_invalid_jalaali_date_raises():
    # Out of range year
    with pytest.raises(Exception):
        to_gregorian(-100, 1, 1)

    # Invalid month
    with pytest.raises(ValueError):
        to_gregorian(1402, 13, 1)

    # Invalid day (1402 Esfand has only 29 days)
    with pytest.raises(ValueError):
        to_gregorian(1402, 12, 30)

    # Valid leap day for 1403 should NOT raise
    gy, gm, gd = to_gregorian(1403, 12, 30)
    assert (gy, gm, gd) == (2025, 3, 20)


def test_round_trip_near_year_boundaries():
    # Round-trip conversion should be idempotent across year boundaries.
    for gy, gm, gd in [
        (2023, 3, 20),
        (2023, 3, 21),
        (2024, 3, 19),
        (2024, 3, 20),
    ]:
        jy, jm, jd = to_jalaali(gy, gm, gd)
        rgy, rgm, rgd = to_gregorian(jy, jm, jd)
        assert (rgy, rgm, rgd) == (gy, gm, gd)


# ---------------------------------------------------------------------------
# Table-driven tests from the gzipped CSV file produced from ICU data.
# Mirrors the Go test `TestIcuDates`.
# ---------------------------------------------------------------------------
if _DATA is None:

    def test_icu_dates_skipped():
        pytest.skip("icu-dates-1876-2124.csv.gz not found next to test file")

else:
    # One test per Gregorian year: ~90k single-row tests cost more in pytest
    # (and xdist) overhead than in actual work.
    _BY_YEAR = {}
    for _row in _DATA:
        _BY_YEAR.setdefault(parse_date(_row[0])[0], []).append(_row)

    @pytest.mark.parametrize(
        "rows",
        _BY_YEAR.values(),
        ids=[str(y) for y in _BY_YEAR],
    )
    def test_icu_dates(rows):
        for row in rows:
            gy, gm, gd = parse_date(row[0])
            ejy, ejm, ejd = parse_date(row[1])

            jy, jm, jd = to_jalaali(gy, gm, gd)
            assert (jy, jm, jd) == (ejy, ejm, ejd), (
                f"G2J Failed for {row[0]}: Got {jy}:{jm}:{jd}, "
                f"Want {ejy}:{ejm}:{ejd}"
            )

            rgy, rgm, rgd = to_gregorian(ejy, ejm, ejd)
            assert (rgy, rgm, rgd) == (gy, gm, gd), (
                f"J2G Failed for {row[1]}: Got {rgy}:{rgm}:{rgd}, "
                f"Want {gy}:{gm}:{gd}"
            )


def test_invalid_year_error_carries_year():
    from djalaali.algo import ErrorInvalidYear, _jal_cal

    with pytest.raises(ErrorInvalidYear) as exc:
        _jal_cal(-100)
    assert exc.value.year == -100
    assert "-100" in str(exc.value)


def test_roundtrip_every_supported_year():
    for jy in range(-61, 3178):
        gy, gm, gd = to_gregorian(jy, 1, 1)
        assert to_jalaali(gy, gm, gd) == (jy, 1, 1)
