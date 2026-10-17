from django.contrib import admin
from .models import CaseStudy, Inquiry, SiteInformation
from .forms import SiteInformationAdminForm
from .staff_forms import CaseStudyStaffForm


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'email', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('name', 'email', 'subject')
    readonly_fields = ('name', 'email', 'phone', 'subject', 'message', 'created_at')

    def has_add_permission(self, request):
        return False


@admin.register(CaseStudy)
class CaseStudyAdmin(admin.ModelAdmin):
    form = CaseStudyStaffForm
    list_display = ('title', 'status', 'is_featured', 'published_at', 'updated_at')
    list_editable = ('status', 'is_featured')
    list_filter = ('status', 'is_featured', 'published_at')
    search_fields = ('title', 'client_label', 'summary')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Case study', {
            'fields': ('title', 'slug', 'client_label', 'summary', 'featured_image'),
        }),
        ('Matter narrative', {
            'fields': ('challenge', 'approach', 'outcome'),
            'description': 'Protect privilege and confidentiality. Remove names, identifying facts and sensitive information unless publication has been expressly approved.',
        }),
        ('Publishing', {
            'fields': ('status', 'is_featured', 'published_at', 'created_at', 'updated_at'),
        }),
    )


@admin.register(SiteInformation)
class SiteInformationAdmin(admin.ModelAdmin):
    form = SiteInformationAdminForm
    fieldsets = (
        ('Branding', {
            'fields': ('firm_name', 'tagline', 'logo', 'favicon'),
        }),
        ('Search & social sharing', {
            'fields': ('site_url', 'seo_title', 'seo_description', 'social_image'),
            'description': 'Default metadata used by search engines and social platforms.',
        }),
        ('Contact details', {
            'fields': (
                'primary_phone', 'secondary_phone', 'primary_email',
                'physical_address', 'postal_address', 'business_hours', 'google_maps_url', 'google_maps_embed_url',
            ),
        }),
        ('Homepage hero', {
            'fields': ('hero_title', 'hero_text', 'hero_image', 'hero_cta_label'),
        }),
        ('Homepage sections', {
            'fields': (
                'practice_section_title', 'practice_section_text',
                'people_section_title', 'people_section_text',
                'home_cta_title', 'home_cta_text',
            ),
        }),
        ('About page', {
            'fields': ('about_title', 'about_text', 'mission_statement'),
        }),
        ('People & contact pages', {
            'fields': (
                'people_page_title', 'people_page_text',
                'lawyers_section_intro', 'staff_section_intro',
                'contact_title', 'contact_intro',
            ),
        }),
        ('Privacy & website notices', {
            'fields': ('legal_disclaimer', 'privacy_policy', 'terms_of_use'),
            'description': 'Optional. Leave blank to use the carefully written fallback website notices.',
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
