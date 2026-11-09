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
    assert python_obj == datetime.datetime(2023, 4, 1, 15, 30)


def test_template_tag_jdate():
    template = Template(
        '{% load djalaali_tags %}{{ my_date|jdate:"%Y/%m/%d" }}'
    )
    context = Context({"my_date": datetime.date(2023, 4, 1)})
    rendered = template.render(context)
    assert rendered == "1402/01/12"


def test_template_tag_jdatetime():
    template = Template(
        '{% load djalaali_tags %}{{ my_dt|jdate:"%Y-%m-%d %H:%M" }}'
    )
    context = Context({"my_dt": datetime.datetime(2023, 4, 1, 14, 0)})
    rendered = template.render(context)
    assert rendered == "1402-01-12 14:00"
