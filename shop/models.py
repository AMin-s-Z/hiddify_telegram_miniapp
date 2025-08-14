from django.db import models
from django.contrib.auth.models import User

class Plan(models.Model):
    name = models.CharField("نام پلن", max_length=100)
    price = models.PositiveIntegerField("قیمت (تومان)")
    duration = models.PositiveIntegerField("مدت زمان (روز)")
    description = models.TextField("توضیحات", blank=True)
    def __str__(self): return self.name
    class Meta: verbose_name, verbose_name_plural = "پلن", "پلن‌ها"

class TelegramProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="telegram_profile")
    telegram_id = models.BigIntegerField("شناسه تلگرام", unique=True)
    username = models.CharField("نام کاربری تلگرام", max_length=100, null=True, blank=True)
    first_name = models.CharField("نام", max_length=100, null=True, blank=True)
    last_name = models.CharField("نام خانوادگی", max_length=100, null=True, blank=True)
    photo_url = models.URLField("آدرس عکس پروفایل", max_length=500, null=True, blank=True)
    auth_date = models.DateTimeField("تاریخ احراز هویت")
    def __str__(self): return self.username or str(self.telegram_id)
    class Meta: verbose_name, verbose_name_plural = "پروفایل تلگرام", "پروفایل‌های تلگرام"

class Purchase(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'در انتظار تایید'
        APPROVED = 'approved', 'تایید شده'
        REJECTED = 'rejected', 'رد شده'
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="purchases", verbose_name="کاربر")
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name="purchases", verbose_name="پلن")
    purchase_date = models.DateTimeField("تاریخ خرید", auto_now_add=True)
    status = models.CharField("وضعیت", max_length=10, choices=Status.choices, default=Status.PENDING)
    receipt_image = models.ImageField("تصویر رسید", upload_to="receipts/")
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    vpn_config = models.TextField("کانفیگ VPN", blank=True)
    def __str__(self): return f"خرید {self.plan.name} توسط {self.user.username}"
    class Meta:
        verbose_name, verbose_name_plural = "خرید", "خریدها"
        ordering = ['-purchase_date']