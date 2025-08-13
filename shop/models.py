from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()

class VPNPlan(models.Model):
    DURATION_CHOICES = [
        (30, '1 ماه'),
        (90, '3 ماه'),
        (180, '6 ماه'),
        (365, '1 سال'),
    ]

    name = models.CharField(max_length=100, verbose_name='نام پلن')
    duration_days = models.IntegerField(choices=DURATION_CHOICES, verbose_name='مدت زمان')
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name='قیمت (تومان)')
    description = models.TextField(verbose_name='توضیحات')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'پلن VPN'
        verbose_name_plural = 'پلن‌های VPN'

    def __str__(self):
        return f"{self.name} - {self.get_duration_days_display()}"

class Purchase(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در انتظار پرداخت'),
        ('waiting_approval', 'در انتظار تایید'),
        ('approved', 'تایید شده'),
        ('rejected', 'رد شده'),
        ('expired', 'منقضی شده'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    plan = models.ForeignKey(VPNPlan, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    payment_receipt = models.ImageField(upload_to='receipts/', null=True, blank=True)
    vpn_config = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    admin_note = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'خرید'
        verbose_name_plural = 'خریدها'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.plan} - {self.get_status_display()}"

    def approve(self):
        self.status = 'approved'
        self.approved_at = timezone.now()
        self.expires_at = timezone.now() + timezone.timedelta(days=self.plan.duration_days)
        self.save()

    def reject(self, note=''):
        self.status = 'rejected'
        self.admin_note = note
        self.save()

    @property
    def is_active(self):
        if self.status == 'approved' and self.expires_at:
            return timezone.now() < self.expires_at
        return False

class PaymentCard(models.Model):
    card_number = models.CharField(max_length=20, verbose_name='شماره کارت')
    card_holder = models.CharField(max_length=100, verbose_name='نام صاحب کارت')
    is_active = models.BooleanField(default=True, verbose_name='فعال')

    class Meta:
        verbose_name = 'کارت پرداخت'
        verbose_name_plural = 'کارت‌های پرداخت'

    def __str__(self):
        return f"{self.card_number} - {self.card_holder}"