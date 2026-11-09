# djalaali/apps.py
import datetime

from django.apps import AppConfig
from django.db import models


class DjalaaliConfig(AppConfig):
    name = "djalaali"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        self.patch_formfields()
        self.patch_admin_display()

    def patch_formfields(self):
        """Patches ModelForm generation to use Jalali fields by default."""
        from .forms import (
            JalaliDateField,
            JalaliDateInput,
            JalaliDateTimeField,
            JalaliDateTimeInput,
        )

        # We only patch DateField.formfield because DateTimeField inherits from DateField
        # and its formfield method calls super().formfield() which hits our patch.
        original_date_formfield = models.DateField.formfield

        def jalali_formfield(self, **kwargs):
            # If the model field explicitly opts out
            if getattr(self, "gregorian", False):
                return original_date_formfield(self, **kwargs)

            # Check if the instance is a DateTimeField to apply the correct widget/form_class
            if isinstance(self, models.DateTimeField):
                kwargs["form_class"] = JalaliDateTimeField
                kwargs["widget"] = JalaliDateTimeInput()
            else:
                kwargs["form_class"] = JalaliDateField
                kwargs["widget"] = JalaliDateInput()

            return original_date_formfield(self, **kwargs)

        models.DateField.formfield = jalali_formfield

    def patch_admin_display(self):
        """Patches Admin list_display and readonly_fields to show Jalali dates."""
        import django.contrib.admin.helpers as admin_helpers
        import django.contrib.admin.templatetags.admin_list as admin_list
        import django.contrib.admin.utils
        from django.contrib.admin.utils import (
            display_for_field as original_display_for_field,
        )
        from django.contrib.admin.utils import (
            display_for_value as original_display_for_value,
        )

        from django.utils import timezone

        from .jdate import jdate
        from .jdatetime import jdatetime

        def _to_local(value):
            # DB stores UTC (USE_TZ); admin must show the active timezone.
            if isinstance(value, datetime.datetime) and timezone.is_aware(value):
                return timezone.localtime(value)
            return value

        def jalali_display_for_field(value, field, *args, **kwargs):
            value = _to_local(value)
            is_date_field = isinstance(
                field, (models.DateField, models.DateTimeField)
            ) or isinstance(value, (datetime.datetime, datetime.date))
            is_gregorian = isinstance(field, models.Field) and getattr(
                field, "gregorian", False
            )

            if is_date_field and value is not None and not is_gregorian:
                if isinstance(value, datetime.datetime):
                    return jdatetime.fromgregorian(value).strftime(
                        "%Y/%m/%d %H:%M"
                    )
                elif isinstance(value, datetime.date):
                    return jdate.fromgregorian(value).strftime("%Y/%m/%d")
            return original_display_for_field(value, field, *args, **kwargs)

        def jalali_display_for_value(value, *args, **kwargs):
            value = _to_local(value)
            if isinstance(value, (datetime.datetime, datetime.date)):
                if isinstance(value, datetime.datetime):
                    return jdatetime.fromgregorian(value).strftime(
                        "%Y/%m/%d %H:%M"
                    )
                elif isinstance(value, datetime.date):
                    return jdate.fromgregorian(value).strftime("%Y/%m/%d")
            return original_display_for_value(value, *args, **kwargs)

        django.contrib.admin.utils.display_for_field = jalali_display_for_field
        django.contrib.admin.utils.display_for_value = jalali_display_for_value

        admin_list.display_for_field = jalali_display_for_field
        admin_list.display_for_value = jalali_display_for_value

        admin_helpers.display_for_field = jalali_display_for_field
        admin_helpers.display_for_value = jalali_display_for_value
