from django.db import models

from djalaali.models import GregorianDateField


class Event(models.Model):
    title = models.CharField(max_length=100)
    # Plain Django fields: djalaali swaps in Jalali form fields and admin display.
    date = models.DateField()
    starts_at = models.DateTimeField(null=True, blank=True)
    # Opt-out: stays Gregorian in forms and admin.
    registered_on = GregorianDateField(null=True, blank=True)

    class Meta:
        ordering = ["date"]

    def __str__(self):
        return self.title
