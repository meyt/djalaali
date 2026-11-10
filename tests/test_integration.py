# djalaali/tests/test_integration.py
import datetime

from django.template import Context, Template

from djalaali.forms import JalaliDateField, JalaliDateTimeField


def test_jalali_date_field_prepare_value():
    field = JalaliDateField()
    gregorian_date = datetime.date(2023, 4, 1)
    prepared = field.prepare_value(gregorian_date)
    assert prepared == "1402/01/12"


def test_jalali_date_field_to_python():
    field = JalaliDateField()
    python_obj = field.to_python("1402/01/12")
    assert isinstance(python_obj, datetime.date)
    assert python_obj == datetime.date(2023, 4, 1)


def test_jalali_datetime_field_decompress():
    field = JalaliDateTimeField()
    gregorian_dt = datetime.datetime(2023, 4, 1, 15, 30)
    # For MultiWidget fields, widget.decompress handles splitting the datetime object
    prepared = field.widget.decompress(gregorian_dt)
    assert "1402/01/12" in prepared[0]
    assert "15:30" in prepared[1]


def test_jalali_datetime_field_to_python():
    field = JalaliDateTimeField()
    python_obj = field.to_python(["1402/01/12", "15:30:00"])
    assert isinstance(python_obj, datetime.datetime)
    # USE_TZ=True: result is aware in the current timezone, like Django's own field.
    assert python_obj.replace(tzinfo=None) == datetime.datetime(2023, 4, 1, 15, 30)
    assert python_obj.tzinfo is not None


def test_template_tag_jdate():
    template = Template(
        '{% load djalaali_tags %}{{ my_date|jdate:"Y/m/d" }}'
    )
    context = Context({"my_date": datetime.date(2023, 4, 1)})
    rendered = template.render(context)
    assert rendered == "1402/01/12"


def test_template_tag_jdatetime():
    template = Template(
        '{% load djalaali_tags %}{{ my_dt|jdate:"Y-m-d H:i" }}'
    )
    context = Context({"my_dt": datetime.datetime(2023, 4, 1, 14, 0)})
    rendered = template.render(context)
    assert rendered == "1402-01-12 14:00"


def test_jalali_date_field_rejects_invalid_jalali_date():
    import pytest
    from django.core.exceptions import ValidationError

    field = JalaliDateField()
    for bad in ("1402/12/30", "1403/07/31", "1403/01/01zzz"):
        with pytest.raises(ValidationError):
            field.clean(bad)
    assert field.clean("1403/12/30") == datetime.date(2025, 3, 20)


def test_jalali_datetime_field_partial_time():
    import pytest
    from django.core.exceptions import ValidationError

    field = JalaliDateTimeField()
    assert field.clean(["1403/01/01", ""]).hour == 0
    assert field.clean(["1403/01/01", "10:30"]).minute == 30
    with pytest.raises(ValidationError):
        field.clean(["1402/12/30", "10:30"])


def test_jalali_date_input_keeps_picker_class():
    from djalaali.forms import JalaliDateInput

    widget = JalaliDateInput(attrs={"class": "form-control"})
    assert widget.attrs["class"] == "form-control djalaali-datepicker"


def test_model_formfield_respects_explicit_widget():
    from django import forms
    from django.db import models

    from djalaali.forms import JalaliDateInput

    custom = forms.DateInput()
    # Field.__init__ deep-copies widget instances, so compare by type.
    assert type(models.DateField().formfield(widget=custom).widget) is (
        forms.DateInput
    )
    assert isinstance(models.DateField().formfield().widget, JalaliDateInput)
