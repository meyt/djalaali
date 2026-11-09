"""
jalaali - A Python implementation of the Jalaali calendar conversion.

Ported from https://github.com/jalaali/go-jalaali
"""

from enum import IntEnum

# Jalaali leap year break points
BREAKS = [
    -61,
    9,
    38,
    199,
    426,
    686,
    756,
    818,
    1111,
    1181,
    1210,
    1635,
    2060,
    2097,
    2192,
    2262,
    2324,
    2394,
    2456,
    3178,
]


class Month(IntEnum):
    """Represents a Jalaali month (1-12)."""

    Farvardin = 1
    Ordibehesht = 2
    Khordad = 3
    Tir = 4
    Mordad = 5
    Shahrivar = 6
    Mehr = 7
    Aban = 8
    Azar = 9
    Dey = 10
    Bahman = 11
    Esfand = 12


class ErrorInvalidYear(Exception):
    """Raised when year is out of valid range."""

    def __init__(self, year):
        self.year = year
        super().__init__(f"jalaali: {year} is invalid year")


def _div(a, b):
    """Integer division truncated toward zero (matches Go's `/` for ints)."""
    q = abs(a) // abs(b)
    if (a < 0) != (b < 0):
        q = -q
    return q


def _mod(a, b):
    """Remainder with sign of dividend (matches Go's `%` for ints)."""
    r = abs(a) % abs(b)
    if a < 0:
        r = -r
    return r


def to_jalaali(gy, gm, gd):
    """
    Convert a Gregorian date to a Jalaali date.

    Returns a tuple (jy, jm, jd).
    Raises ErrorInvalidYear if the resulting Jalaali year is out of range.
    """
    return _d2j(_g2d(gy, gm, gd))


def to_gregorian(jy, jm, jd):
    """
    Convert a Jalaali date to a Gregorian date.

    Returns a tuple (gy, gm, gd).
    Raises ValueError for an invalid Jalaali date.
    Raises ErrorInvalidYear if the year is out of range.
    """
    if not _is_valid_date(jy, jm, jd):
        raise ValueError(
            f"invalid jalaali date: year={jy}, month={jm}, day={jd}"
        )
    jdn = _j2d(jy, jm, jd)
    return _d2g(jdn)


def is_leap_year(jy):
    """Return True if the given Jalaali year is a leap year."""
    leap, _, _, _ = _jal_cal(jy)
    return leap == 0


def month_length(jy, jm):
    """Return the number of days in the given Jalaali month."""
    if jm <= 6:
        return 31
    elif jm <= 11:
        return 30
    if is_leap_year(jy):
        return 30
    return 29


def _is_valid_date(jy, jm, jd):
    if jy < -61 or jy > 3177 or jm < 1 or jm > 12 or jd < 1:
        return False
    return jd <= month_length(jy, jm)


def _j2d(jy, jm, jd):
    _, gy, march, _ = _jal_cal(jy)
    return _g2d(gy, 3, march) + (jm - 1) * 31 - _div(jm, 7) * (jm - 7) + jd - 1


def _d2j(jdn):
    gy, _, _ = _d2g(jdn)
    jy = gy - 621
    leap, _, march, _ = _jal_cal(jy)
    jdn1f = _g2d(gy, 3, march)
    k = jdn - jdn1f
    if k >= 0:
        if k <= 185:
            jm = 1 + _div(k, 31)
            jd = _mod(k, 31) + 1
            return jy, jm, jd
        k -= 186
    else:
        jy -= 1
        k += 179
        if leap == 1:
            k += 1
    jm = 7 + _div(k, 30)
    jd = _mod(k, 30) + 1
    return jy, jm, jd


def _jal_cal(jy):
    bl = len(BREAKS)
    gy = jy + 621
    leap_j = -14
    jp = BREAKS[0]
    jump = 0

    if jy < jp or jy >= BREAKS[bl - 1]:
        raise ErrorInvalidYear(jy)

    for i in range(1, bl):
        jm = BREAKS[i]
        jump = jm - jp
        if jy < jm:
            break
        leap_j += _div(jump, 33) * 8 + _div(_mod(jump, 33), 4)
        jp = jm

    n = jy - jp
    leap_j += _div(n, 33) * 8 + _div(_mod(n, 33) + 3, 4)
    if _mod(jump, 33) == 4 and jump - n == 4:
        leap_j += 1

    leap_g = _div(gy, 4) - _div((_div(gy, 100) + 1) * 3, 4) - 150
    march = 20 + leap_j - leap_g

    if jump - n < 6:
        n = n - jump + _div(jump + 4, 33) * 33

    leap = _mod(_mod(n + 1, 33) - 1, 4)
    if leap == -1:
        leap = 4

    return leap, gy, march, None


def _g2d(gy, gm, gd):
    d = (
        _div((gy + _div(gm - 8, 6) + 100100) * 1461, 4)
        + _div(153 * _mod(gm + 9, 12) + 2, 5)
        + gd
        - 34840408
    )
    d = d - _div(_div(gy + 100100 + _div(gm - 8, 6), 100) * 3, 4) + 752
    return d


def _d2g(jdn):
    j = 4 * jdn + 139361631
    j = j + _div(_div(4 * jdn + 183187720, 146097) * 3, 4) * 4 - 3908
    i = _div(_mod(j, 1461), 4) * 5 + 308
    gd = _div(_mod(i, 153), 5) + 1
    gm = _mod(_div(i, 153), 12) + 1
    gy = _div(j, 1461) - 100100 + _div(8 - gm, 6)
    return gy, gm, gd
