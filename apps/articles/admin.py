from django.contrib import admin
from .forms import ArticleAdminForm
from .models import Article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    form = ArticleAdminForm
    list_display = ('title', 'status', 'is_featured', 'author', 'published_at', 'updated_at')
    list_filter = ('status', 'is_featured', 'published_at')
    list_editable = ('status', 'is_featured')
    search_fields = ('title', 'excerpt', 'content')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Article content', {'fields': ('title', 'slug', 'excerpt', 'content', 'featured_image')}),
        ('Publishing', {'fields': ('status', 'is_featured', 'published_at', 'author')}),
        ('Record', {'fields': ('created_at', 'updated_at')}),
    )

    def save_model(self, request, obj, form, change):
        if obj.author_id is None:
            obj.author = request.user
        super().save_model(request, obj, form, change)
