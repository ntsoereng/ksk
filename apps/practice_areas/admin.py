from django.contrib import admin
from .models import PracticeArea


@admin.register(PracticeArea)
class PracticeAreaAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_featured', 'display_order', 'is_active')
    list_editable = ('is_featured', 'display_order', 'is_active')
    list_filter = ('is_active', 'is_featured')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'short_description', 'description')
