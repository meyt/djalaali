# djalaali/forms.py
import datetime

from django import forms
from django.utils.translation import gettext_lazy as _

from .jdate import jdate
from .jdatetime import jdatetime


class JalaliDateInput(forms.TextInput):
    class Media:
        css = {"all": ("djalaali/css/djalaali.css",)}
        js = ("djalaali/js/djalaali.js",)

    def __init__(
        self,
        attrs=None,
        month_names=None,
        weekday_names=None,
        today_label=None,
    ):
        default_attrs = {
            "class": "djalaali-datepicker",
            "placeholder": "YYYY/MM/DD",
            "autocomplete": "off",
            "dir": "auto",
        }

        # These are optional overrides for the JS calendar widget. If omitted,
        # the JS falls back to its own built-in Persian defaults.
        today_label = today_label if today_label is not None else _("Today")
        default_attrs["data-today-label"] = str(today_label)

        if month_names is not None:
            default_attrs["data-month-names"] = ",".join(
                str(m) for m in month_names
            )
        if weekday_names is not None:
            default_attrs["data-weekday-names"] = ",".join(
                str(w) for w in weekday_names
            )

        if attrs:
            if "class" in attrs:
                default_attrs["class"] = (
                    attrs["class"] + " djalaali-datepicker"
                )
            default_attrs.update(attrs)
        super().__init__(default_attrs)


class JalaliDateField(forms.DateField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", JalaliDateInput())
        kwargs.setdefault(
            "input_formats", ["%Y/%m/%d", "%Y-%m-%d", "%Y.%m.%d"]
        )
        super().__init__(*args, **kwargs)

    def prepare_value(self, value):
        if value in (None, ""):
            return ""
        if isinstance(value, datetime.datetime):
            value = value.date()
        if isinstance(value, datetime.date):
            return jdate.fromgregorian(value).strftime("%Y/%m/%d")
        return value

    def to_python(self, value):
        if value in self.empty_values:
            return None
        if isinstance(value, datetime.datetime):
            return value.date()
        if isinstance(value, datetime.date):
            return value

        try:
            str_value = str(value).replace("-", "/").replace(".", "/").strip()
            jd = jdate.strptime(str_value, "%Y/%m/%d")
            return jd.togregorian()
        except Exception:
            pass

        return super().to_python(value)


class JalaliDateTimeInput(forms.MultiWidget):
    class Media:
        css = {"all": ("djalaali/css/djalaali.css",)}
        js = ("djalaali/js/djalaali.js",)

    def __init__(
        self,
        attrs=None,
        month_names=None,
        weekday_names=None,
        today_label=None,
    ):
        today_label = today_label if today_label is not None else _("Today")

        date_attrs = {
            "class": "vTextField djalaali-datepicker",
            "placeholder": "YYYY/MM/DD",
            "autocomplete": "off",
            "data-djalaali-has-time": "true",
            "dir": "auto",
            "data-hour-label": str(_("Hour")),
            "data-minute-label": str(_("Minute")),
            "data-second-label": str(_("Second")),
            "data-today-label": str(today_label),
        }
        if month_names is not None:
            date_attrs["data-month-names"] = ",".join(
                str(m) for m in month_names
            )
        if weekday_names is not None:
            date_attrs["data-weekday-names"] = ",".join(
                str(w) for w in weekday_names
            )

        time_attrs = {
            "class": "vTimeField",
            "placeholder": "HH:MM:SS",
            "dir": "auto",
        }
        widgets = (
            JalaliDateInput(attrs=date_attrs),
            forms.TimeInput(attrs=time_attrs),
        )
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            if isinstance(value, datetime.datetime):
                jdt = jdatetime.fromgregorian(value)
                return [jdt.strftime("%Y/%m/%d"), jdt.strftime("%H:%M:%S")]
            elif isinstance(value, datetime.date):
                jd = jdate.fromgregorian(value)
                return [jd.strftime("%Y/%m/%d"), ""]
        return [None, None]


class JalaliDateTimeField(forms.DateTimeField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", JalaliDateTimeInput())
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        if isinstance(value, list):
            date_str = value[0]
            time_str = value[1] if len(value) > 1 else ""

            if not date_str:
                return None

            try:
                combined = f"{date_str} {time_str}".strip()
                jdt = jdatetime.strptime(combined, "%Y/%m/%d %H:%M:%S")
                return jdt.togregorian()
            except Exception:
                pass

        return super().to_python(value)
