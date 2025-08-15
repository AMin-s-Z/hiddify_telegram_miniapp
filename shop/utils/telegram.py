# core/utils/telegram.py
import requests
import logging
import json # Add this import
from django.conf import settings
from django.urls import reverse

logger = logging.getLogger(__name__)

def send_telegram_message(chat_id, text, keyboard=None):
    """Sends a message to Telegram, optionally with an inline keyboard."""
    api_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'}
    if keyboard:
        payload['reply_markup'] = json.dumps({'inline_keyboard': keyboard})

    try:
        requests.post(api_url, json=payload, timeout=10)
    except requests.RequestException as e:
        logger.error(f"Error sending message: {e}")

def notify_admin_on_purchase(purchase):
    """Sends a notification to the admin with Approve/Reject buttons."""
    user_info = purchase.user.telegram_profile.username or purchase.user.telegram_profile.telegram_id

    caption = (
        f"🧾 *New Purchase*\n\n"
        f"👤 *User:* @{user_info}\n"
        f"📦 *Plan:* {purchase.plan.name}\n"
        f"💰 *Price:* {purchase.plan.price} Toman"
    )

    # Define the inline keyboard buttons
    # The callback_data contains the action and the purchase ID
    keyboard = [
        [
            {'text': '✅ Approve', 'callback_data': f'approve:{purchase.id}'},
            {'text': '❌ Reject', 'callback_data': f'reject:{purchase.id}'}
        ]
    ]

    # Send the purchase receipt image as a separate message first
    api_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendPhoto"
    payload = {'chat_id': settings.TELEGRAM_ADMIN_CHAT_ID, 'caption': "Receipt attached"}
    try:
        with open(purchase.receipt_image.path, 'rb') as photo_file:
            requests.post(api_url, data=payload, files={'photo': photo_file}, timeout=15)
    except Exception as e:
        logger.error(f"Error sending receipt photo: {e}")

    # Then send the main message with the action buttons
    send_telegram_message(settings.TELEGRAM_ADMIN_CHAT_ID, caption, keyboard)

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
