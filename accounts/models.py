from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class TelegramProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="telegram_profile")
    telegram_id = models.BigIntegerField(unique=True, db_index=True)
    telegram_username = models.CharField(max_length=255, blank=True, null=True)
    photo_url = models.URLField(blank=True, null=True)
    language_code = models.CharField(max_length=16, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.telegram_id})"


class Plan(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    price_irr = models.PositiveIntegerField(help_text="Price in IRR (Toman x10)")
    duration_days = models.PositiveIntegerField(default=30)
    data_gb = models.PositiveIntegerField(default=0, help_text="0 for unlimited or specify in GB")
    is_active = models.BooleanField(default=True)
    order_index = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return self.name


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING_PAYMENT = "pending", "Pending Payment"
        SUBMITTED = "submitted", "Submitted"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="orders")
    amount_irr = models.PositiveIntegerField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING_PAYMENT)
    receipt = models.FileField(upload_to="receipts/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    admin_note = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self) -> str:
        return f"Order #{self.id} - {self.user} - {self.plan.name} - {self.status}"


class VPNAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="vpn_accounts")
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, blank=True)
    username = models.CharField(max_length=64)
    password = models.CharField(max_length=128)
    server_address = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    order = models.OneToOneField(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name="vpn_account")

    def __str__(self) -> str:
        return f"VPNAccount {self.username}"
