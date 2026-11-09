# djalaali

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
