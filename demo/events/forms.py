from django import forms

from djalaali.forms import JalaliDateField, JalaliDateInput

from .models import Event


class EventForm(forms.ModelForm):
    """Model fields are Jalali automatically; no widget setup needed."""

    class Meta:
        model = Event
        fields = ["title", "date", "starts_at", "registered_on"]


class ConvertForm(forms.Form):
    """Plain form using the field directly, with custom widget labels."""

    date = JalaliDateField(
        widget=JalaliDateInput(today_label="Go to today"),
        label="Jalali date",
    )
