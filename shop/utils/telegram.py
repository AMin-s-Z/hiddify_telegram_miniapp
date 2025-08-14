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