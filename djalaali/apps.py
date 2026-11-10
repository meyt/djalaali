# djalaali/apps.py
import datetime

from django.apps import AppConfig
from django import forms
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

            # Respect explicit caller choices (Meta.widgets, custom form_class);
            # only replace unset values and the stock Django admin defaults.
            widget = kwargs.get("widget")
            widget_cls = widget if isinstance(widget, type) else type(widget)
            if widget is None or widget_cls.__module__ == (
                "django.contrib.admin.widgets"
            ):
                kwargs.pop("widget", None)
                replace_widget = True
            else:
                replace_widget = False
            # DateTimeField.formfield passes forms.DateTimeField as its stock
            # default through super(), so treat the stock classes as unset.
            if kwargs.get("form_class") in (
                None,
                forms.DateField,
                forms.DateTimeField,
                forms.SplitDateTimeField,
            ):
                kwargs.pop("form_class", None)
                replace_form_class = True
            else:
                replace_form_class = False

            if isinstance(self, models.DateTimeField):
                if replace_form_class:
                    kwargs["form_class"] = JalaliDateTimeField
                if replace_widget:
                    kwargs["widget"] = JalaliDateTimeInput()
            else:
                if replace_form_class:
                    kwargs["form_class"] = JalaliDateField
                if replace_widget:
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

        from . import conf, dateformat

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
                    return dateformat.format_gregorian(
                        value, conf.datetime_format()
                    )
                elif isinstance(value, datetime.date):
                    return dateformat.format_gregorian(
                        value, conf.date_format()
                    )
            return original_display_for_field(value, field, *args, **kwargs)

        def jalali_display_for_value(value, *args, **kwargs):
            value = _to_local(value)
            if isinstance(value, (datetime.datetime, datetime.date)):
                if isinstance(value, datetime.datetime):
                    return dateformat.format_gregorian(
                        value, conf.datetime_format()
                    )
                return dateformat.format_gregorian(value, conf.date_format())
            return original_display_for_value(value, *args, **kwargs)

        django.contrib.admin.utils.display_for_field = jalali_display_for_field
        django.contrib.admin.utils.display_for_value = jalali_display_for_value

        admin_list.display_for_field = jalali_display_for_field
        admin_list.display_for_value = jalali_display_for_value

        admin_helpers.display_for_field = jalali_display_for_field
        admin_helpers.display_for_value = jalali_display_for_value
