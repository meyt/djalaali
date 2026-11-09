from django.db import models


class GregorianDateField(models.DateField):
    """
    Use this field if you want to opt-out of global Jalali conversion
    and use standard Gregorian dates in forms and admin for a specific field.
    """

    gregorian = True
