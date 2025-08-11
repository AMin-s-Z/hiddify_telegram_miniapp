from django.db import models

class TelegramUser(models.Model):
    telegram_id = models.BigIntegerField(unique=True, primary_key=True)
    username = models.CharField(max_length=100, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.first_name or str(self.telegram_id)

class VPNPlan(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.PositiveIntegerField() # قیمت به تومان
    duration_days = models.PositiveIntegerField() # مدت زمان به روز

    def __str__(self):
        return f"{self.name} - {self.price} تومان"

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در انتظار پرداخت'),
        ('verifying', 'در انتظار تایید'),
        ('completed', 'تکمیل شده'),
        ('failed', 'ناموفق'),
    ]

    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, related_name='orders')
    plan = models.ForeignKey(VPNPlan, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    receipt = models.ImageField(upload_to='receipts/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"سفارش {self.id} برای {self.user}"