import hashlib
import hmac
import time
from urllib.parse import parse_qsl
from django.conf import settings

def verify_telegram_auth(init_data):
    """تأیید اعتبار داده‌های دریافتی از تلگرام WebApp"""
    # جدا کردن پارامترها
    data_items = dict(parse_qsl(init_data))

    if 'hash' not in data_items:
        return False

    # حذف hash برای محاسبه
    check_hash = data_items.pop('hash')

    # مرتب‌سازی پارامترها
    data_check_arr = []
    for k, v in sorted(data_items.items()):
        data_check_arr.append(f"{k}={v}")

    # ایجاد رشته برای بررسی
    data_check_string = '\n'.join(data_check_arr)

    # ساخت کلید مخفی
    secret_key = hashlib.sha256(settings.TELEGRAM_BOT_TOKEN.encode()).digest()

    # محاسبه hash
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    # مقایسه hash ها
    return calculated_hash == check_hash