# djalaali

[![build](https://img.shields.io/github/actions/workflow/status/meyt/djalaali/test.yml?branch=master&logo=github&label=build)](https://github.com/meyt/djalaali/actions/workflows/test.yml)
[![coverage](https://img.shields.io/coveralls/github/meyt/djalaali/master?label=coverage)](https://coveralls.io/github/meyt/djalaali)
[![python](https://img.shields.io/pypi/pyversions/djalaali?label=python)](https://pypi.org/project/djalaali/)
[![django](https://img.shields.io/pypi/frameworkversions/django/djalaali?label=django)](https://pypi.org/project/djalaali/)

Jalali (Persian) calendar support for Django: `jdate` and `jdatetime` types,
model and form fields, and template tags.

## Install

```sh
pip install djalaali
```

Add `"djalaali"` to `INSTALLED_APPS`.

## Usage

### Dates and datetimes

`jdate` and `jdatetime` mirror the API of `datetime.date` and
`datetime.datetime`.

```python
import datetime
from djalaali.jdate import jdate
from djalaali.jdatetime import jdatetime

d = jdate(1403, 1, 1)
d = jdate.fromgregorian(datetime.date(2024, 3, 20))  # jdate(1403, 1, 1)
d.togregorian()                                      # datetime.date(2024, 3, 20)
d.isleap()                                           # True
d.isoformat()                                        # "1403-01-01"
d.strftime("%A %d %B %Y")                            # "چهارشنبه 01 فروردین 1403"

jdate.today()
jdate.fromisoformat("1403-01-01")
jdate.strptime("1403/01/15", "%Y/%m/%d")

d + datetime.timedelta(days=30)                      # jdate(1403, 1, 31)
d - jdate(1402, 12, 1)                               # datetime.timedelta(days=29)
d < jdate(1403, 2, 1)                                # True

t = jdatetime(1403, 1, 1, 13, 5)
t.togregorian()                                      # datetime.datetime(2024, 3, 20, 13, 5)
t.strftime("%Y/%m/%d %H:%M")                         # "1403/01/01 13:05"
jdatetime.now()
```

Dates outside the supported Jalali years (-61 to 3177) raise
`djalaali.algo.ErrorInvalidYear`; invalid dates such as `jdate(1403, 12, 31)`
raise `ValueError`.

### Low-level conversion

```python
from djalaali.algo import to_jalaali, to_gregorian, is_leap_year, month_length

to_jalaali(2024, 3, 20)    # (1403, 1, 1)
to_gregorian(1403, 1, 1)   # (2024, 3, 20)
is_leap_year(1403)         # True
month_length(1403, 12)     # 30
```

Conversions use a C extension when one is available and fall back to an
identical pure-Python implementation otherwise (about 60x slower, same
results). Check `djalaali.algo.HAS_C_EXTENSION` to see which is active, or set
`DJALAALI_PURE_PYTHON=1` to force the Python one.

### Models, forms and admin

With `"djalaali"` in `INSTALLED_APPS`, every `DateField` and `DateTimeField`
automatically gets a Jalali form field with a calendar picker, in `ModelForm`s
and in the admin. Values are still stored as Gregorian dates in the database.

```python
from django.db import models
from djalaali.models import GregorianDateField


class Event(models.Model):
    title = models.CharField(max_length=100)
    date = models.DateField()                     # Jalali in forms and admin
    starts_at = models.DateTimeField(null=True)   # Jalali in forms and admin
    registered_on = GregorianDateField(null=True)  # opts out, stays Gregorian
```

Widgets or form classes you set explicitly (for example in `Meta.widgets`) are
left alone. You can also use the fields directly in plain forms:

```python
from django import forms
from djalaali.forms import JalaliDateField, JalaliDateTimeField, JalaliDateInput


class EventForm(forms.Form):
    date = JalaliDateField()
    starts_at = JalaliDateTimeField(required=False)
    # Optional overrides for the calendar widget labels:
    birthday = JalaliDateField(widget=JalaliDateInput(today_label="امروز"))
```

Render the form with `{{ form.media }}` in your template so the calendar's CSS
and JavaScript are loaded.

### Date formats

Settings mirror Django's `DATE_FORMAT` / `DATE_INPUT_FORMATS` family. Defaults
are shown:

```python
# Display (Django `date` filter syntax, like DATE_FORMAT): admin change list,
# read-only fields, and the `jdate` filter when used without an argument.
DJALAALI_DATE_FORMAT = "Y/m/d"
DJALAALI_DATETIME_FORMAT = "Y/m/d H:i"

# Form input parsing (strptime syntax, like DATE_INPUT_FORMATS), tried in order.
DJALAALI_DATE_INPUT_FORMATS = ["%Y/%m/%d", "%Y-%m-%d", "%Y.%m.%d"]
DJALAALI_DATETIME_INPUT_FORMATS = [
    "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M",
    "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M",
    "%Y.%m.%d %H:%M:%S", "%Y.%m.%d %H:%M",
]
```

As in Django, the first entry of `DJALAALI_DATE_INPUT_FORMATS` is how widgets
render a value, and it also drives the placeholder and the calendar picker, so
it may only use `%Y`, `%m`, `%d` and literal separators. The datetime widget
has separate date and time inputs; their combined text is matched against
`DJALAALI_DATETIME_INPUT_FORMATS` and against every date input format combined
with `%H:%M:%S` or `%H:%M`. The time input itself is rendered as `HH:MM:SS`.
`input_formats=` on `JalaliDateField` / `JalaliDateTimeField` overrides the
settings.

Supported Django format characters: `d j D l w z m n M F t L y Y a A g G h H i
s u O e T c`, with `\` to escape. Others are output as-is.

The `jdate` filter argument uses the same syntax: `{{ d|jdate:"j F Y" }}`.

### Template filter

```django
{% load djalaali_tags %}

{{ event.date|jdate }}                      {# 1403/01/01 #}
{{ event.date|jdate:"d F Y" }}              {# 01 فروردین 1403 #}
{{ event.starts_at|jdate:"Y/m/d H:i" }}
```

### Month and weekday names

Names come from `JalaliConfig` and can be changed globally, for example to
use Latin transliterations:

```python
from djalaali.jdate import JalaliConfig

JalaliConfig().months[1] = ("Farvardin", "Far")
```

A runnable example lives in [demo/](demo/) (`make demo`).

## Development

```sh
make install
make test
```

## License

MIT
