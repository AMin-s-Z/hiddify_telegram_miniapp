import os
from django.db import models
from django.conf import settings
from django.utils import timezone
import string
import random

def receipt_upload_path(instance, filename):
    """تولید مسیر منحصر به فرد برای ذخیره رسید"""
    # گرفتن پسوند فایل
    ext = filename.split('.')[-1]
    # ایجاد نام منحصر به فرد
    filename = f"receipt_{instance.user.id}_{instance.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
    return os.path.join('receipts', filename)

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در انتظار پرداخت'),
        ('submitted', 'رسید ارسال شده'),
        ('approved', 'تایید شده'),
        ('rejected', 'رد شده'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    plan = models.ForeignKey('Plan', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    amount_irr = models.IntegerField()
    receipt_image = models.ImageField(
        upload_to=receipt_upload_path,  # استفاده از تابع سفارشی
        null=True,
        blank=True,
        max_length=500  # افزایش طول مسیر
    )
    admin_note = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"سفارش #{self.id} - {self.user} - {self.status}"

    class Meta:
        ordering = ['-created_at']