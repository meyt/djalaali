import datetime
import re

from .algo import is_leap_year, to_gregorian, to_jalaali


class JalaliConfig:
    """
    Configuration for Jalali month and weekday names.
    You can modify these dictionaries globally to change localization.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.months = {
                1: ("فروردین", "فرو"),
                2: ("اردیبهشت", "ارد"),
                3: ("خرداد", "خرد"),
                4: ("تیر", "تیر"),
                5: ("مرداد", "مرد"),
                6: ("شهریور", "شهر"),
                7: ("مهر", "مهر"),
                8: ("آبان", "آبا"),
                9: ("آذر", "آذر"),
                10: ("دی", "دی"),
                11: ("بهمن", "بهم"),
                12: ("اسفند", "اسف"),
            }
            # Python's weekday(): 0=Monday, 6=Sunday
            cls._instance.weekdays = {
                0: ("دوشنبه", "د"),
                1: ("سه‌شنبه", "س"),
                2: ("چهارشنبه", "چ"),
                3: ("پنجشنبه", "پ"),
                4: ("جمعه", "ج"),
                5: ("شنبه", "ش"),
                6: ("یکشنبه", "ی"),
            }
            cls._instance.am_pm = {"am": "ق.ظ", "pm": "ب.ظ"}
        return cls._instance

    def get_month_name(self, month, short=False):
        return self.months[month][1 if short else 0]

    def get_month_by_name(self, name):
        for k, v in self.months.items():
            if name in v:
                return k
        raise ValueError(f"Invalid month name: {name}")

    def get_weekday_name(self, weekday, short=False):
        return self.weekdays[weekday][1 if short else 0]

    def get_weekday_by_name(self, name):
        for k, v in self.weekdays.items():
            if name in v:
                return k
        raise ValueError(f"Invalid weekday name: {name}")


def _parse_date_string(date_string, format):
    directives = {
        "%Y": r"(?P<year>\d{4})",
        "%y": r"(?P<year2>\d{2})",
        "%m": r"(?P<month>\d{1,2})",
        "%d": r"(?P<day>\d{1,2})",
        "%H": r"(?P<hour>\d{1,2})",
        "%I": r"(?P<hour12>\d{1,2})",
        "%M": r"(?P<minute>\d{1,2})",
        "%S": r"(?P<second>\d{1,2})",
        "%f": r"(?P<microsecond>\d{1,6})",
        "%p": r"(?P<ampm>[^ ]+)",
        "%B": r"(?P<month_name>[^ ]+)",
        "%b": r"(?P<month_abbr>[^ ]+)",
        "%A": r"(?P<weekday_name>[^ ]+)",
        "%a": r"(?P<weekday_abbr>[^ ]+)",
        "%w": r"(?P<weekday_num>\d)",
        "%j": r"(?P<doy>\d{3})",
        "%%": r"%",
    }
    regex = ""
    i = 0
    while i < len(format):
        if format[i] == "%" and i + 1 < len(format):
            token = format[i : i + 2]
            if token in directives:
                regex += directives[token]
                i += 2
                continue
        regex += re.escape(format[i])
        i += 1

    m = re.fullmatch(regex, date_string)
    if not m:
        raise ValueError(
            f"time data '{date_string}' does not match format '{format}'"
        )
    return m.groupdict()


class jdate:
    __slots__ = ("_year", "_month", "_day", "_gdate", "_config")

    def __init__(self, year, month, day):
        self._config = JalaliConfig()
        self._year = year
        self._month = month
        self._day = day
        gy, gm, gd = to_gregorian(year, month, day)
        self._gdate = datetime.date(gy, gm, gd)

    @property
    def year(self):
        return self._year

    @property
    def month(self):
        return self._month

    @property
    def day(self):
        return self._day

    @classmethod
    def fromgregorian(cls, date):
        jy, jm, jd = to_jalaali(date.year, date.month, date.day)
        return cls(jy, jm, jd)

    def togregorian(self):
        return self._gdate

    @classmethod
    def today(cls):
        return cls.fromgregorian(datetime.date.today())

    @classmethod
    def fromisoformat(cls, isostr):
        parts = isostr.split("-")
        if len(parts) == 3:
            return cls(int(parts[0]), int(parts[1]), int(parts[2]))
        raise ValueError(f"Invalid ISO format: {isostr}")

    def isoformat(self):
        return f"{self._year:04d}-{self._month:02d}-{self._day:02d}"

    def weekday(self):
        return self._gdate.weekday()  # 0=Monday, 6=Sunday

    def isoweekday(self):
        return self._gdate.isoweekday()  # 1=Monday, 7=Sunday

    def isleap(self):
        return is_leap_year(self._year)

    def __add__(self, other):
        if isinstance(other, datetime.timedelta):
            return jdate.fromgregorian(self._gdate + other)
        return NotImplemented

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if isinstance(other, datetime.timedelta):
            return jdate.fromgregorian(self._gdate - other)
        if isinstance(other, jdate):
            return self._gdate - other._gdate
        if isinstance(other, datetime.date):
            return self._gdate - other
        return NotImplemented

    def __eq__(self, other):
        if isinstance(other, jdate):
            return self._gdate == other._gdate
        if isinstance(other, datetime.date):
            return self._gdate == other
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, jdate):
            return self._gdate < other._gdate
        if isinstance(other, datetime.date):
            return self._gdate < other
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, jdate):
            return self._gdate <= other._gdate
        if isinstance(other, datetime.date):
            return self._gdate <= other
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, jdate):
            return self._gdate > other._gdate
        if isinstance(other, datetime.date):
            return self._gdate > other
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, jdate):
            return self._gdate >= other._gdate
        if isinstance(other, datetime.date):
            return self._gdate >= other
        return NotImplemented

    def __hash__(self):
        return hash(self._gdate)

    def __str__(self):
        return self.isoformat()

    def __repr__(self):
        return f"jdate({self._year}, {self._month}, {self._day})"

    def timetuple(self):
        return self._gdate.timetuple()

    def strftime(self, fmt):
        pattern = re.compile(r"%([a-zA-Z]|%)")

        def replace_token(match):
            char = match.group(1)
            if char == "%":
                return "%"
            if char == "a":
                return self._config.get_weekday_name(
                    self.weekday(), short=True
                )
            if char == "A":
                return self._config.get_weekday_name(
                    self.weekday(), short=False
                )
            if char == "w":
                return str((self._gdate.isoweekday()) % 7)
            if char == "d":
                return f"{self.day:02d}"
            if char == "b":
                return self._config.get_month_name(self.month, short=True)
            if char == "B":
                return self._config.get_month_name(self.month, short=False)
            if char == "m":
                return f"{self.month:02d}"
            if char == "y":
                return f"{self.year % 100:02d}"
            if char == "Y":
                return f"{self.year:04d}"
            if char == "j":
                if self.month <= 6:
                    doy = (self.month - 1) * 31 + self.day
                else:
                    doy = 6 * 31 + (self.month - 7) * 30 + self.day
                return f"{doy:03d}"
            if char == "H":
                return f"{getattr(self, 'hour', 0):02d}"
            if char == "I":
                h = getattr(self, "hour", 0)
                h12 = h % 12 or 12
                return f"{h12:02d}"
            if char == "p":
                h = getattr(self, "hour", 0)
                return (
                    self._config.am_pm["am"]
                    if h < 12
                    else self._config.am_pm["pm"]
                )
            if char == "M":
                return f"{getattr(self, 'minute', 0):02d}"
            if char == "S":
                return f"{getattr(self, 'second', 0):02d}"
            if char == "f":
                return f"{getattr(self, 'microsecond', 0):06d}"
            if char == "z":
                gdt = getattr(self, "_gdatetime", self._gdate)
                return gdt.strftime("%z")
            if char == "Z":
                gdt = getattr(self, "_gdatetime", self._gdate)
                return gdt.strftime("%Z")
            if char == "c":
                wd = self._config.get_weekday_name(self.weekday(), short=True)
                mn = self._config.get_month_name(self.month, short=True)
                h = getattr(self, "hour", 0)
                m = getattr(self, "minute", 0)
                s = getattr(self, "second", 0)
                return f"{wd} {mn} {self.day:2d} {h:02d}:{m:02d}:{s:02d} {self.year:04d}"
            if char == "x":
                wd = self._config.get_weekday_name(self.weekday(), short=True)
                mn = self._config.get_month_name(self.month, short=True)
                return f"{wd} {mn} {self.day:2d} {self.year:04d}"
            if char == "X":
                h = getattr(self, "hour", 0)
                m = getattr(self, "minute", 0)
                s = getattr(self, "second", 0)
                return f"{h:02d}:{m:02d}:{s:02d}"
            return match.group(0)

        return pattern.sub(replace_token, fmt)

    @classmethod
    def strptime(cls, date_string, format):
        config = JalaliConfig()
        d = _parse_date_string(date_string, format)

        if "year" in d:
            year = int(d["year"])
        elif "year2" in d:
            y2 = int(d["year2"])
            year = 1300 + y2 if y2 >= 70 else 1400 + y2
        else:
            year = 1300

        if "month" in d:
            month = int(d["month"])
        elif "month_name" in d:
            month = config.get_month_by_name(d["month_name"])
        elif "month_abbr" in d:
            month = config.get_month_by_name(d["month_abbr"])
        elif "doy" in d:
            doy = int(d["doy"])
            if doy <= 186:
                month = (doy - 1) // 31 + 1
            else:
                month = (doy - 187) // 30 + 7
        else:
            month = 1

        if "day" in d:
            day = int(d["day"])
        elif "doy" in d:
            doy = int(d["doy"])
            if doy <= 186:
                day = (doy - 1) % 31 + 1
            else:
                day = (doy - 187) % 30 + 1
        else:
            day = 1

        return cls(year, month, day)
