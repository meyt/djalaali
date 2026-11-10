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

```python
from djalaali.jdate import jdate

d = jdate(1403, 1, 1)
```

## Development

```sh
make install
make test
```

## License

MIT
