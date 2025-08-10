import hashlib
import hmac
import time
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