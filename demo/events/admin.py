from django.contrib import admin

from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["title", "date", "starts_at", "registered_on"]
    list_filter = ["date", "starts_at", "registered_on"]
    date_hierarchy = "date"
