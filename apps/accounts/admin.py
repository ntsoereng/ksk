from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    ordering = ('email',)
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Contact details', {'fields': ('phone_number',)}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('email', 'first_name', 'last_name', 'phone_number', 'password1', 'password2')}),
    )
    search_fields = ('email', 'first_name', 'last_name')
