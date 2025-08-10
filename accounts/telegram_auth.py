import hashlib
import hmac
import time
from urllib.parse import parse_qsl
from django.conf import settings

def verify_telegram_auth(auth_data):
    """تایید اعتبار داده‌های احراز هویت تلگرام"""
    check_hash = auth_data.get('hash')
    if not check_hash:
        return False

    auth_data = auth_data.copy()
    auth_hash = auth_data.pop('hash')

    data_check_arr = []
    for k, v in sorted(auth_data.items()):
        data_check_arr.append(f"{k}={v}")
    data_check_string = '\n'.join(data_check_arr)

    secret_key = hashlib.sha256(settings.TELEGRAM_BOT_TOKEN.encode()).digest()

    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    if calculated_hash != auth_hash:
        return False

    # اختیاری: بررسی تاریخ احراز هویت (نباید قدیمی‌تر از 24 ساعت باشد)
    auth_date = int(auth_data.get('auth_date', 0))
    if (time.time() - auth_date) > 86400:
        return False

    return True

def verify_telegram_webapp(init_data):
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