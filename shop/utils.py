import requests
from django.conf import settings

def create_hiddify_user(plan, user):
    """
    Creates a new user in the Hiddify panel based on a Plan object.

    Args:
        plan: The Plan object the user purchased.
        user: The User object who made the purchase.

    Returns:
        The new user's UUID from Hiddify if successful, otherwise None.
    """
    try:
        # ساخت URL و هدرهای لازم
        api_url = f"{settings.HIDDIFY_URL}/{settings.HIDDIFY_ADMIN_SECRET}/api/v2/admin/user/"
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Hiddify-API-Key': settings.HIDDIFY_ADMIN_SECRET
        }

        # ساخت دیکشنری داده‌ها بر اساس پلن و کاربر
        # **توجه**: فرض شده که مدل Plan شما فیلدهای duration و data_limit_gb را دارد.
        data_payload = {
            "name": user.username,  # نام کاربر
            "package_days": plan.duration,  # مدت زمان پلن به روز
            "usage_limit_GB": plan.data_limit_gb,  # حجم پلن به گیگابایت
            "telegram_id": user.telegram_id or None,  # آیدی تلگرام کاربر (اختیاری)
            "comment": f"Plan: {plan.name}",  # یک کامنت برای شناسایی بهتر
            "mode": "no_reset" # یا هر حالتی که مد نظر شماست
        }

        # ارسال درخواست POST برای ساخت کاربر
        response = requests.post(api_url, headers=headers, json=data_payload, timeout=15)
        response.raise_for_status() # اگر خطا بود، متوقف شو

        response_data = response.json()

        # برگرداندن UUID کاربر جدید از پاسخ API
        return response_data.get('uuid')

    except requests.exceptions.RequestException as e:
        print(f"Error creating Hiddify user for {user.username}: {e}")
        return None
