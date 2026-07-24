from django.contrib import admin
from .models import Attorney


@admin.register(Attorney)
class AttorneyAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'title', 'member_type', 'display_order', 'is_featured', 'is_active')
    list_editable = ('display_order', 'is_featured', 'is_active')
    list_filter = ('member_type', 'is_featured', 'is_active', 'practice_areas')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'title')
    filter_horizontal = ('practice_areas',)
    ordering = ('member_type', 'display_order', 'user__last_name')

    fieldsets = (
        ('Person', {'fields': ('user', 'title', 'member_type', 'slug', 'photo')}),
        ('Profile', {'fields': ('biography', 'admission', 'email', 'phone', 'practice_areas')}),
        ('Publishing & hierarchy', {
            'fields': ('is_active', 'is_featured', 'display_order'),
            'description': 'Legal professionals display before general staff. Use display order to set hierarchy within each group (0 first, then 1, 2, and so on).',
        }),
    )
