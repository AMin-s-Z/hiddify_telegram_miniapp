from django.contrib import admin, messages
from django.utils.html import format_html
from datetime import timedelta
from django.utils import timezone
from .models import Plan, TelegramProfile, Purchase
from .utils.telegram import send_telegram_message

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin): list_display = ('name', 'price', 'duration')

@admin.register(TelegramProfile)
class TelegramProfileAdmin(admin.ModelAdmin): list_display = ('user', 'telegram_id', 'username', 'auth_date')

def generate_vpn_config(purchase: Purchase) -> str:
    user_id = purchase.user.telegram_profile.telegram_id
    plan_name = purchase.plan.name
    expiry_date = timezone.now() + timedelta(days=purchase.plan.duration)
    return f"[VPN Config - For User {user_id}]\nPlan: {plan_name}\nExpires: {expiry_date.strftime('%Y-%m-%d %H:%M')}\nServer: vpn.example.com\nKey: {hash(purchase.id)}-{hash(user_id)}\n--- End of Config ---"

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'status', 'purchase_date', 'display_receipt')
    list_filter, search_fields, readonly_fields, list_per_page = ('status', 'plan'), ('user__username', 'plan__name'), ('purchase_date', 'display_receipt_in_form'), 20
    actions = ['approve_purchases', 'reject_purchases']
    fieldsets = ((None, {'fields': ('user', 'plan', 'status', 'purchase_date')}), ('Receipt & Config', {'fields': ('display_receipt_in_form', 'vpn_config')}),)
    def display_receipt(self, obj): return format_html(f'<a href="{obj.receipt_image.url}" target="_blank"><img src="{obj.receipt_image.url}" width="100" /></a>')
    display_receipt.short_description = "Receipt Image"
    def display_receipt_in_form(self, obj): return self.display_receipt(obj)
    display_receipt_in_form.short_description = "Receipt Image"
    @admin.action(description="Approve selected purchases")
    def approve_purchases(self, request, queryset):
        for purchase in queryset.filter(status=Purchase.Status.PENDING):
            purchase.status, purchase.vpn_config = Purchase.Status.APPROVED, generate_vpn_config(purchase)
            purchase.save()
            send_telegram_message(purchase.user.telegram_profile.telegram_id, f"✅ Your purchase for the *{purchase.plan.name}* plan has been approved.")
        self.message_user(request, "Selected purchases were successfully approved.", messages.SUCCESS)
    @admin.action(description="Reject selected purchases")
    def reject_purchases(self, request, queryset):
        for purchase in queryset.filter(status=Purchase.Status.PENDING):
            purchase.status = Purchase.Status.REJECTED
            purchase.save()
            send_telegram_message(purchase.user.telegram_profile.telegram_id, f"❌ Your payment for the *{purchase.plan.name}* plan was rejected.")
        self.message_user(request, "Selected purchases were rejected.", messages.WARNING)