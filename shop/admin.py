from django.contrib import admin
from .models import TelegramUser, VPNPlan, Order

@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ('telegram_id', 'first_name', 'username', 'created_at')
    search_fields = ('first_name', 'username')

@admin.register(VPNPlan)
class VPNPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_days')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'plan', 'status', 'created_at')
    list_filter = ('status', 'plan')
    search_fields = ('user__first_name', 'user__telegram_id')
    list_editable = ('status',) # اجازه ویرایش وضعیت از همین لیست
    autocomplete_fields = ('user', 'plan')