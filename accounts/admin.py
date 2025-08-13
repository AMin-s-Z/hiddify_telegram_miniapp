from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'telegram_username', 'telegram_id', 'is_active']
    list_filter = ['is_active', 'is_staff']
    search_fields = ['username', 'telegram_username', 'telegram_id']

    fieldsets = UserAdmin.fieldsets + (
        ('اطلاعات تلگرام', {'fields': ('telegram_id', 'telegram_username',
                                       'telegram_first_name', 'telegram_last_name', 'phone_number')}),
    )