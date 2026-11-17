import django
from django.conf import settings


def pytest_configure():
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["djalaali"],
            USE_TZ=True,
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
            TEMPLATES=[
                {"BACKEND": "django.template.backends.django.DjangoTemplates"}
            ],
        )
        django.setup()
