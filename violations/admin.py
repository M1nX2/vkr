from django.contrib import admin
from .models import Violation


@admin.register(Violation)
class ViolationAdmin(admin.ModelAdmin):
    list_display = ['date', 'time', 'type', 'breed', 'muzzle']
    list_filter = ['date', 'type', 'muzzle']
    search_fields = ['type', 'description', 'breed']
    date_hierarchy = 'date'

