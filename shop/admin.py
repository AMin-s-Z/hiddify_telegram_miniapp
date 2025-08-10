import string
from random import random

from django.contrib import admin
from .models import Plan, Order, VPNAccount
from django.utils import timezone
from .telegram_bot import TelegramBot, send_to_telegram

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_irr', 'duration_days', 'data_gb', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')

class VPNAccountInline(admin.StackedInline):
    model = VPNAccount
    readonly_fields = ('username', 'password', 'server_address', 'expires_at', 'created_at')
    extra = 0
    can_delete = False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'plan', 'amount_irr', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('user__username', 'user__telegram_username')
    readonly_fields = ('user', 'plan', 'amount_irr', 'receipt_image', 'created_at')
    inlines = [VPNAccountInline]

    def save_model(self, request, obj, form, change):
        old_status = None
        if obj.pk:
            old_obj = Order.objects.get(pk=obj.pk)
            old_status = old_obj.status

        super().save_model(request, obj, form, change)

        # اگر وضعیت به "تایید شده" تغییر کرده است
        if old_status != 'approved' and obj.status == 'approved':
            # بررسی وجود اکانت VPN
            vpn_account, created = VPNAccount.objects.get_or_create(
                order=obj,
                user=obj.user,
                defaults={
                    'username': f"vpn_{obj.user.id}_{obj.id}_{random.randint(1000, 9999)}",
                    'password': ''.join(random.choices(string.ascii_letters + string.digits, k=12)),
                    'server_address': "vpn.example.com:443",
                    'expires_at': timezone.now() + timezone.timedelta(days=obj.plan.duration_days),
                    'is_active': True
                }
            )

            if created:
                # ارسال اطلاعات اکانت به کاربر از طریق تلگرام
                bot = TelegramBot()
                send_to_telegram(bot.send_vpn_account_to_user)(vpn_account)

@admin.register(VPNAccount)
class VPNAccountAdmin(admin.ModelAdmin):
    list_display = ('username', 'user', 'server_address', 'expires_at', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('username', 'user__username', 'user__telegram_username')
    readonly_fields = ('created_at',)