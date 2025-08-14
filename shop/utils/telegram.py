import requests, logging
from django.conf import settings
from django.urls import reverse

logger = logging.getLogger(__name__)

def send_telegram_message(chat_id, text):
    api_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'}
    try: requests.post(api_url, json=payload, timeout=10)
    except requests.RequestException as e: logger.error(f"Error sending message: {e}")

def notify_admin_on_purchase(purchase):
    user_info = purchase.user.telegram_profile.username or purchase.user.telegram_profile.telegram_id
    admin_url = settings.SITE_URL + reverse('admin:core_purchase_change', args=[purchase.id])
    caption = f"🧾 *خرید جدید*\n👤 *کاربر:* @{user_info}\n📦 *پلن:* {purchase.plan.name}\n🔗 [لینک مدیریت]({admin_url})"
    api_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendPhoto"
    payload = {'chat_id': settings.TELEGRAM_ADMIN_CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}
    try:
        with open(purchase.receipt_image.path, 'rb') as photo_file:
            requests.post(api_url, data=payload, files={'photo': photo_file}, timeout=15)
    except Exception as e: logger.error(f"Error sending receipt: {e}")