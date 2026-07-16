from django.contrib import admin
from .models import Attorney


@admin.register(Attorney)
class AttorneyAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'title', 'is_active', 'display_order')
    list_editable = ('is_active', 'display_order')
    list_filter = ('is_active', 'practice_areas')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'title')
    filter_horizontal = ('practice_areas',)
