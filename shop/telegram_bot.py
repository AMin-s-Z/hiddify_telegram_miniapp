import asyncio
from telegram import Bot
from django.conf import settings

class TelegramBot:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.admin_id = settings.ADMIN_TELEGRAM_ID

    async def send_receipt_notification(self, order):
        """ارسال اعلان رسید به ادمین"""
        bot = Bot(token=self.token)

        message = f"""
🧾 *رسید جدید دریافت شد!*

👤 کاربر: {order.user.telegram_username or 'ناشناس'}
🆔 آیدی تلگرام: `{order.user.telegram_id}`
💰 مبلغ: `{order.amount_irr:,}` ریال
📦 پلن: *{order.plan.name}*
🔢 شماره سفارش: `#{order.id}`

برای تایید یا رد از پنل ادمین استفاده کنید.
        """

        try:
            # ارسال تصویر رسید به همراه پیام
            if order.receipt_image:
                await bot.send_photo(
                    chat_id=self.admin_id,
                    photo=order.receipt_image.path,
                    caption=message,
                    parse_mode='Markdown'
                )
            else:
                await bot.send_message(
                    chat_id=self.admin_id,
                    text=message,
                    parse_mode='Markdown'
                )

            return True
        except Exception as e:
            print(f"خطا در ارسال پیام تلگرام: {e}")
            return False

    async def send_vpn_account_to_user(self, vpn_account):
        """ارسال اطلاعات اکانت VPN به کاربر"""
        bot = Bot(token=self.token)

        message = f"""
✅ *اکانت VPN شما فعال شد!*

👤 نام کاربری: `{vpn_account.username}`
🔑 رمز عبور: `{vpn_account.password}`
🌐 آدرس سرور: `{vpn_account.server_address}`
📅 تاریخ انقضا: `{vpn_account.expires_at.strftime('%Y-%m-%d')}`

لطفاً این اطلاعات را در جایی امن نگهداری کنید.
        """

        try:
            await bot.send_message(
                chat_id=vpn_account.user.telegram_id,
                text=message,
                parse_mode='Markdown'
            )
            return True
        except Exception as e:
            print(f"خطا در ارسال پیام تلگرام: {e}")
            return False

def send_to_telegram(func):
    """دکوراتور برای اجرای توابع ارسال تلگرام به صورت غیرهمزمان"""
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(func(*args, **kwargs))
        loop.close()
        return result
    return wrapper