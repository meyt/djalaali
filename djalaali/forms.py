# djalaali/forms.py
import datetime
import json

from django import forms
from django.core.exceptions import ValidationError
from django.forms.utils import from_current_timezone
from django.utils.translation import gettext_lazy as _

from . import conf
from .algo import ErrorInvalidYear
from .jdate import jdate
from .jdatetime import jdatetime


def _widget_date_format():
    return conf.date_input_formats()[0]


def _names_json(names):
    return json.dumps([str(n) for n in names], ensure_ascii=False)


class JalaliDateInput(forms.TextInput):
    class Media:
        css = {"all": ("djalaali/css/djalaali.css",)}
        js = ("djalaali/js/djalaali-core.js", "djalaali/js/djalaali.js")

    def __init__(
        self,
        attrs=None,
        month_names=None,
        weekday_names=None,
        today_label=None,
    ):
        date_format = _widget_date_format()
        default_attrs = {
            "class": "djalaali-datepicker",
            "placeholder": conf.date_placeholder(date_format),
            "data-date-format": date_format,
            "autocomplete": "off",
            "dir": "auto",
        }

        # These are optional overrides for the JS calendar widget. If omitted,
        # the JS falls back to its own built-in Persian defaults.
        today_label = today_label if today_label is not None else _("Today")
        default_attrs["data-today-label"] = str(today_label)

        if month_names is not None:
            default_attrs["data-month-names"] = _names_json(month_names)
        if weekday_names is not None:
            default_attrs["data-weekday-names"] = _names_json(weekday_names)

        if attrs:
            attrs = dict(attrs)
            if "class" in attrs:
                default_attrs["class"] = (
                    attrs.pop("class") + " djalaali-datepicker"
                )
            default_attrs.update(attrs)
        super().__init__(default_attrs)


class JalaliDateField(forms.DateField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", JalaliDateInput())
        super().__init__(*args, **kwargs)

    def _formats(self):
        # `input_formats` is only an instance attribute when passed explicitly.
        return self.__dict__.get("input_formats") or conf.date_input_formats()

    @classmethod
    def _parse(cls, value, formats):
        """Returns the Gregorian date for `value`, or None if nothing fits."""
        value = str(value).strip()
        for fmt in formats:
            try:
                return jdate.strptime(value, fmt).togregorian()
            except (ValueError, ErrorInvalidYear):
                continue
        return None

    def prepare_value(self, value):
        if value in (None, ""):
            return ""
        if isinstance(value, datetime.datetime):
            value = value.date()
        if isinstance(value, datetime.date):
            return jdate.fromgregorian(value).strftime(_widget_date_format())
        return value

    def to_python(self, value):
        if value in self.empty_values:
            return None
        if isinstance(value, datetime.datetime):
            return value.date()
        if isinstance(value, datetime.date):
            return value

        parsed = self._parse(value, self._formats())
        if parsed is None:
            raise ValidationError(self.error_messages["invalid"], code="invalid")
        return parsed


class JalaliDateTimeInput(forms.MultiWidget):
    class Media:
        css = {"all": ("djalaali/css/djalaali.css",)}
        js = ("djalaali/js/djalaali-core.js", "djalaali/js/djalaali.js")

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
            "autocomplete": "off",
            "data-djalaali-has-time": "true",
            "dir": "auto",
            "data-hour-label": str(_("Hour")),
            "data-minute-label": str(_("Minute")),
            "data-second-label": str(_("Second")),
            "data-today-label": str(today_label),
        }
        if month_names is not None:
            date_attrs["data-month-names"] = _names_json(month_names)
        if weekday_names is not None:
            date_attrs["data-weekday-names"] = _names_json(weekday_names)

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
                return [
                    jdt.strftime(_widget_date_format()),
                    jdt.strftime("%H:%M:%S"),
                ]
            elif isinstance(value, datetime.date):
                jd = jdate.fromgregorian(value)
                return [jd.strftime(_widget_date_format()), ""]
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

            time_str = (time_str or "").strip() or "00:00:00"
            text = f"{str(date_str).strip()} {time_str}"
            formats = self.__dict__.get("input_formats") or (
                conf.datetime_input_formats()
            )
            for fmt in formats:
                try:
                    jdt = jdatetime.strptime(text, fmt)
                except (ValueError, ErrorInvalidYear):
                    continue
                return from_current_timezone(jdt.togregorian())
            raise ValidationError(self.error_messages["invalid"], code="invalid")

        return super().to_python(value)
