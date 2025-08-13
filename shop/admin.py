from django.contrib import admin
from django.utils.html import format_html
from .models import VPNPlan, Purchase, PaymentCard
from .telegram_bot import send_approval_notification, send_rejection_notification

@admin.register(VPNPlan)
class VPNPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'duration_days', 'price', 'is_active']
    list_filter = ['is_active', 'duration_days']
    search_fields = ['name']

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'created_at', 'transaction_id']
    list_filter = ['status', 'created_at', 'plan']
    search_fields = ['user__telegram_username', 'transaction_id']
    readonly_fields = ['transaction_id', 'created_at', 'approved_at', 'expires_at']

    fieldsets = (
        ('اطلاعات خرید', {
            'fields': ('user', 'plan', 'status', 'transaction_id')
        }),
        ('پرداخت', {
            'fields': ('payment_receipt',)
        }),
        ('تایید/رد', {
            'fields': ('vpn_config', 'admin_note')
        }),
        ('زمان‌ها', {
            'fields': ('created_at', 'approved_at', 'expires_at')
        }),
    )

    def save_model(self, request, obj, form, change):
        if change:
            old_obj = Purchase.objects.get(pk=obj.pk)

            # اگر وضعیت به تایید شده تغییر کرد
            if old_obj.status != 'approved' and obj.status == 'approved':
                obj.approve()
                # اینجا کد ساخت VPN اضافه می‌شود
                obj.vpn_config = f"VPN Config for {obj.user.telegram_username}\nServer: example.com\nPort: 443\nPassword: {obj.transaction_id[:8]}"
                send_approval_notification(obj)

            # اگر وضعیت به رد شده تغییر کرد
            elif old_obj.status != 'rejected' and obj.status == 'rejected':
                send_rejection_notification(obj)

        super().save_model(request, obj, form, change)

@admin.register(PaymentCard)
class PaymentCardAdmin(admin.ModelAdmin):
    list_display = ['card_number', 'card_holder', 'is_active']
    list_filter = ['is_active']