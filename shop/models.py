from django.db import models
from django.conf import settings
from django.utils import timezone
import string
import random

class Plan(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price_irr = models.IntegerField()
    duration_days = models.IntegerField()
    data_gb = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.price_irr:,} ریال"

    class Meta:
        ordering = ['price_irr']

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در انتظار پرداخت'),
        ('submitted', 'رسید ارسال شده'),
        ('approved', 'تایید شده'),
        ('rejected', 'رد شده'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    amount_irr = models.IntegerField()
    receipt_image = models.ImageField(upload_to='receipts/', null=True, blank=True)
    admin_note = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"سفارش #{self.id} - {self.user.telegram_username} - {self.status}"

    class Meta:
        ordering = ['-created_at']

class VPNAccount(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='vpn_accounts')
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='vpn_account')
    username = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    server_address = models.CharField(max_length=255)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"اکانت VPN: {self.username}"

    def generate_credentials(self):
        """ایجاد نام کاربری و رمز عبور منحصر به فرد"""
        self.username = f"user_{self.user.id}_{self.order.id}_{random.randint(1000, 9999)}"
        self.password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        self.server_address = "vpn.example.com:443"
        self.expires_at = timezone.now() + timezone.timedelta(days=self.order.plan.duration_days)
        self.save()