from django.contrib import admin
from .models import Inquiry, SiteInformation


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'email', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('name', 'email', 'subject')
    readonly_fields = ('created_at',)


@admin.register(SiteInformation)
class SiteInformationAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Branding', {
            'fields': ('firm_name', 'tagline', 'logo', 'favicon'),
        }),
        ('Contact details', {
            'fields': (
                'primary_phone', 'secondary_phone', 'primary_email',
                'physical_address', 'postal_address', 'business_hours', 'google_maps_url',
            ),
        }),
        ('Homepage hero', {
            'fields': ('hero_title', 'hero_text', 'hero_image', 'hero_cta_label'),
        }),
        ('About page', {
            'fields': ('about_title', 'about_text', 'mission_statement'),
        }),
        ('Social media', {
            'fields': ('facebook_url', 'linkedin_url', 'instagram_url'),
        }),
        ('Record', {
            'fields': ('updated_at',),
        }),
    )
    readonly_fields = ('updated_at',)

    def has_add_permission(self, request):
        return not SiteInformation.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
