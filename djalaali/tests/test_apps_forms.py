import datetime

import pytest
from django import forms
from django.contrib.admin import widgets as admin_widgets
from django.contrib.admin.helpers import display_for_field as helpers_dff
from django.contrib.admin.utils import display_for_field, display_for_value
from django.core.exceptions import ValidationError
from django.db import models
from django.template import Context, Template
from django.utils import timezone

from djalaali.forms import (
    JalaliDateField,
    JalaliDateInput,
    JalaliDateTimeField,
    JalaliDateTimeInput,
)
from djalaali.templatetags.djalaali_tags import jdate_filter


# --- model formfield patch -------------------------------------------------


def test_formfield_date_defaults():
    f = models.DateField().formfield()
    assert isinstance(f, JalaliDateField)
    assert isinstance(f.widget, JalaliDateInput)


def test_formfield_datetime_defaults():
    f = models.DateTimeField().formfield()
    assert isinstance(f, JalaliDateTimeField)
    assert isinstance(f.widget, JalaliDateTimeInput)


def test_formfield_gregorian_opt_out():
    field = models.DateField()
    field.gregorian = True
    assert type(field.formfield()) is forms.DateField


def test_formfield_replaces_admin_widget_and_split_form_class():
    f = models.DateTimeField().formfield(
        widget=admin_widgets.AdminSplitDateTime,
        form_class=forms.SplitDateTimeField,
    )
    assert isinstance(f, JalaliDateTimeField)
    assert isinstance(f.widget, JalaliDateTimeInput)


def test_formfield_respects_explicit_choices():
    class MyWidget(forms.TextInput):
        pass

    class MyField(forms.DateField):
        pass

    f = models.DateField().formfield(widget=MyWidget, form_class=MyField)
    assert type(f) is MyField
    assert isinstance(f.widget, MyWidget)

    class MyDateTimeField(forms.DateTimeField):
        pass

    f = models.DateTimeField().formfield(
        widget=MyWidget(), form_class=MyDateTimeField
    )
    assert type(f) is MyDateTimeField
    assert isinstance(f.widget, MyWidget)


# --- admin display patch ---------------------------------------------------


def test_display_for_field_date():
    out = display_for_field(datetime.date(2023, 4, 1), models.DateField(), "-")
    assert out == "1402/01/12"
    assert helpers_dff is display_for_field


def test_display_for_field_datetime_aware_converted_to_local():
    value = datetime.datetime(2023, 4, 1, 15, 30, tzinfo=datetime.timezone.utc)
    out = display_for_field(value, models.DateTimeField(), "-")
    local = timezone.localtime(value)
    assert out.startswith("1402/01/12")
    assert out.endswith(f"{local.hour:02d}:{local.minute:02d}")


def test_display_for_field_naive_datetime_without_date_field():
    value = datetime.datetime(2023, 4, 1, 15, 30)
    assert display_for_field(value, models.CharField(), "-") == "1402/01/12 15:30"


def test_display_for_field_gregorian_and_none_fall_back():
    field = models.DateField()
    field.gregorian = True
    out = display_for_field(datetime.date(2023, 4, 1), field, "-")
    assert "1402" not in out
    assert display_for_field(None, models.DateField(), "EMPTY") == "EMPTY"


def test_display_for_field_non_date_value_on_date_field_falls_back():
    assert display_for_field("text", models.DateField(), "-") == "text"


def test_display_for_value():
    assert display_for_value(datetime.date(2023, 4, 1), "-") == "1402/01/12"
    assert (
        display_for_value(datetime.datetime(2023, 4, 1, 1, 2), "-")
        == "1402/01/12 01:02"
    )
    assert display_for_value(5, "-") == "5"


# --- forms -----------------------------------------------------------------


def test_date_input_options_and_attrs():
    w = JalaliDateInput(
        attrs={"class": "x", "id": "i"},
        month_names=["a", "b"],
        weekday_names=["c", "d"],
        today_label="T",
    )
    assert JalaliDateInput(attrs={"id": "j"}).attrs["class"] == "djalaali-datepicker"
    assert w.attrs["class"] == "x djalaali-datepicker"
    assert w.attrs["id"] == "i"
    assert w.attrs["data-month-names"] == '["a", "b"]'
    assert w.attrs["data-weekday-names"] == '["c", "d"]'
    assert w.attrs["data-today-label"] == "T"
    assert "js" in str(w.media._js) or w.media._js


def test_datetime_input_options():
    w = JalaliDateTimeInput(
        month_names=["a"], weekday_names=["b"], today_label="T"
    )
    attrs = w.widgets[0].attrs
    assert attrs["data-month-names"] == '["a"]'
    assert attrs["data-weekday-names"] == '["b"]'
    assert attrs["data-today-label"] == "T"
    assert w.media._js


def test_datetime_decompress():
    w = JalaliDateTimeInput()
    assert w.decompress(None) == [None, None]
    assert w.decompress(datetime.date(2023, 4, 1)) == ["1402/01/12", ""]
    assert w.decompress(datetime.datetime(2023, 4, 1, 1, 2, 3)) == [
        "1402/01/12",
        "01:02:03",
    ]
    assert w.decompress("garbage") == [None, None]


def test_date_field_prepare_value():
    f = JalaliDateField()
    assert f.prepare_value(None) == ""
    assert f.prepare_value("") == ""
    assert f.prepare_value(datetime.datetime(2023, 4, 1, 5)) == "1402/01/12"
    assert f.prepare_value("1402/01/12") == "1402/01/12"


def test_date_field_to_python():
    f = JalaliDateField()
    assert f.to_python("") is None
    assert f.to_python(datetime.datetime(2023, 4, 1, 5)) == datetime.date(2023, 4, 1)
    assert f.to_python(datetime.date(2023, 4, 1)) == datetime.date(2023, 4, 1)
    assert f.to_python("1402-1-12") == datetime.date(2023, 4, 1)
    assert f.to_python("1402.01.12") == datetime.date(2023, 4, 1)
    # not in Jalali shape: falls through to Django's parsing (and fails)
    with pytest.raises(ValidationError):
        f.to_python("garbage")
    # shaped right but impossible
    with pytest.raises(ValidationError):
        f.to_python("1402/13/45")
    with pytest.raises(ValidationError):
        f.to_python("5000/01/01")


def test_datetime_field_to_python_variants():
    f = JalaliDateTimeField()
    assert f.to_python(["", "10:00"]) is None
    r = f.to_python(["1402/01/12", ""])
    assert (r.hour, r.minute, r.second) == (0, 0, 0)
    r = f.to_python(["1402-01-12", "10:20"])
    assert (r.hour, r.minute, r.second) == (10, 20, 0)
    r = f.to_python(["1402/01/12"])
    assert r.hour == 0
    r = f.to_python(["1402/01/12", None])
    assert r.hour == 0
    with pytest.raises(ValidationError):
        f.to_python(["1402/13/45", "10:00"])
    with pytest.raises(ValidationError):
        f.to_python(["5000/01/01", "10:00"])


def test_datetime_field_to_python_non_list():
    f = JalaliDateTimeField()
    r = f.to_python(datetime.datetime(2023, 4, 1, 5))
    assert r.year == 2023


# --- templatetags ----------------------------------------------------------


def test_filter_values():
    assert jdate_filter(None) == ""
    assert jdate_filter("") == ""
    assert jdate_filter(datetime.date(2023, 4, 1)) == "1402/01/12"
    assert jdate_filter(datetime.datetime(2023, 4, 1, 5, 6), "%H:%M") == "05:06"
    assert jdate_filter("text") == "text"


def test_filter_in_template():
    t = Template("{% load djalaali_tags %}{{ d|jdate:'%Y' }}")
    assert t.render(Context({"d": datetime.date(2023, 4, 1)})) == "1402"
