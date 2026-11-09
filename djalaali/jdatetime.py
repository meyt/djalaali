import datetime

from .algo import to_gregorian, to_jalaali
from .jdate import JalaliConfig, _parse_date_string, jdate


class jdatetime(jdate):
    __slots__ = (
        "_hour",
        "_minute",
        "_second",
        "_microsecond",
        "_tzinfo",
        "_gdatetime",
    )

    def __init__(
        self,
        year,
        month,
        day,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
        tzinfo=None,
    ):
        super().__init__(year, month, day)
        self._hour = hour
        self._minute = minute
        self._second = second
        self._microsecond = microsecond
        self._tzinfo = tzinfo

        gy, gm, gd = to_gregorian(year, month, day)
        self._gdatetime = datetime.datetime(
            gy, gm, gd, hour, minute, second, microsecond, tzinfo
        )
        self._gdate = self._gdatetime.date()

    @property
    def hour(self):
        return self._hour

    @property
    def minute(self):
        return self._minute

    @property
    def second(self):
        return self._second

    @property
    def microsecond(self):
        return self._microsecond

    @property
    def tzinfo(self):
        return self._tzinfo

    @classmethod
    def fromgregorian(cls, dt):
        if not isinstance(dt, datetime.datetime):
            dt = datetime.datetime(dt.year, dt.month, dt.day)
        jy, jm, jd = to_jalaali(dt.year, dt.month, dt.day)
        return cls(
            jy,
            jm,
            jd,
            dt.hour,
            dt.minute,
            dt.second,
            dt.microsecond,
            dt.tzinfo,
        )

    def togregorian(self):
        return self._gdatetime

    @classmethod
    def now(cls, tz=None):
        return cls.fromgregorian(datetime.datetime.now(tz))

    def isoformat(self):
        s = super().isoformat()
        return f"{s}T{self._gdatetime.timetz().isoformat()}"

    @classmethod
    def fromisoformat(cls, isostr):
        date_part, sep, time_part = isostr.replace(" ", "T").partition("T")
        parts = date_part.split("-")
        if len(parts) != 3:
            raise ValueError(f"Invalid ISO format: {isostr}")
        t = datetime.time.fromisoformat(time_part) if sep else datetime.time()
        return cls(
            int(parts[0]),
            int(parts[1]),
            int(parts[2]),
            t.hour,
            t.minute,
            t.second,
            t.microsecond,
            t.tzinfo,
        )

    def __add__(self, other):
        if isinstance(other, datetime.timedelta):
            return jdatetime.fromgregorian(self._gdatetime + other)
        return NotImplemented

    def __sub__(self, other):
        if isinstance(other, datetime.timedelta):
            return jdatetime.fromgregorian(self._gdatetime - other)
        if isinstance(other, jdatetime):
            return self._gdatetime - other._gdatetime
        if isinstance(other, datetime.datetime):
            return self._gdatetime - other
        return NotImplemented

    def __eq__(self, other):
        if isinstance(other, jdatetime):
            return self._gdatetime == other._gdatetime
        if isinstance(other, datetime.datetime):
            return self._gdatetime == other
        if isinstance(other, (jdate, datetime.date)):
            return False
        return super().__eq__(other)

    def __lt__(self, other):
        if isinstance(other, jdatetime):
            return self._gdatetime < other._gdatetime
        if isinstance(other, datetime.datetime):
            return self._gdatetime < other
        return super().__lt__(other)

    def __le__(self, other):
        if isinstance(other, jdatetime):
            return self._gdatetime <= other._gdatetime
        if isinstance(other, datetime.datetime):
            return self._gdatetime <= other
        return super().__le__(other)

    def __gt__(self, other):
        if isinstance(other, jdatetime):
            return self._gdatetime > other._gdatetime
        if isinstance(other, datetime.datetime):
            return self._gdatetime > other
        return super().__gt__(other)

    def __ge__(self, other):
        if isinstance(other, jdatetime):
            return self._gdatetime >= other._gdatetime
        if isinstance(other, datetime.datetime):
            return self._gdatetime >= other
        return super().__ge__(other)

    def __hash__(self):
        return hash(self._gdatetime)

    def __repr__(self):
        return f"jdatetime({self._year}, {self._month}, {self._day}, {self._hour}, {self._minute}, {self._second}, {self._microsecond}, tzinfo={self._tzinfo})"

    def timetuple(self):
        return self._gdatetime.timetuple()

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

        hour = 0
        if "hour" in d:
            hour = int(d["hour"])
        elif "hour12" in d:
            hour12 = int(d["hour12"])
            if "ampm" in d:
                if d["ampm"] == config.am_pm["pm"]:
                    hour = hour12 + 12 if hour12 != 12 else 12
                else:
                    hour = hour12 if hour12 != 12 else 0
            else:
                hour = hour12

        minute = int(d.get("minute", 0))
        second = int(d.get("second", 0))
        microsecond = int(d.get("microsecond", 0))

        return cls(year, month, day, hour, minute, second, microsecond)
