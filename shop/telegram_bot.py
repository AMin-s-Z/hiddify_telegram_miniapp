import asyncio
import logging
from telegram import Bot
from telegram.error import TelegramError
from django.conf import settings
import os

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.admin_id = settings.ADMIN_TELEGRAM_ID

        # لاگ کردن تنظیمات برای دیباگ
        logger.info(f"Bot Token: {self.token[:10]}...")
        logger.info(f"Admin ID: {self.admin_id}")

    async def send_receipt_notification(self, order):
        """ارسال اعلان رسید به ادمین"""
        try:
            bot = Bot(token=self.token)

            # آماده‌سازی پیام
            message = f"""
🧾 <b>رسید جدید دریافت شد!</b>

👤 کاربر: {order.user.telegram_username or 'ناشناس'}
🆔 آیدی تلگرام: <code>{order.user.telegram_id}</code>
💰 مبلغ: <code>{order.amount_irr:,}</code> ریال
📦 پلن: <b>{order.plan.name}</b>
🔢 شماره سفارش: <code>#{order.id}</code>

برای تایید یا رد از پنل ادمین استفاده کنید.
/admin
            """

            logger.info(f"Sending receipt notification for order {order.id} to {self.admin_id}")

            # ارسال تصویر رسید به همراه پیام
            if order.receipt_image and os.path.exists(order.receipt_image.path):
                logger.info(f"Sending photo: {order.receipt_image.path}")

                # باز کردن فایل و ارسال
                with open(order.receipt_image.path, 'rb') as photo:
                    result = await bot.send_photo(
                        chat_id=self.admin_id,
                        photo=photo,
                        caption=message,
                        parse_mode='HTML'  # تغییر به HTML که پایدارتر است
                    )
                    logger.info(f"Photo sent successfully: {result.message_id}")
            else:
                # ارسال فقط متن
                result = await bot.send_message(
                    chat_id=self.admin_id,
                    text=message,
                    parse_mode='HTML'
                )
                logger.info(f"Message sent successfully: {result.message_id}")

            return True

        except TelegramError as e:
            logger.error(f"Telegram API error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending telegram message: {e}")
            return False

    async def send_vpn_account_to_user(self, vpn_account):
        """ارسال اطلاعات اکانت VPN به کاربر"""
        try:
            bot = Bot(token=self.token)

            message = f"""
✅ <b>اکانت VPN شما فعال شد!</b>

👤 نام کاربری: <code>{vpn_account.username}</code>
🔑 رمز عبور: <code>{vpn_account.password}</code>
🌐 آدرس سرور: <code>{vpn_account.server_address}</code>
📅 تاریخ انقضا: <code>{vpn_account.expires_at.strftime('%Y-%m-%d')}</code>

لطفاً این اطلاعات را در جایی امن نگهداری کنید.
            """

            logger.info(f"Sending VPN credentials to user {vpn_account.user.telegram_id}")

            result = await bot.send_message(
                chat_id=vpn_account.user.telegram_id,
                text=message,
                parse_mode='HTML'
            )

            logger.info(f"VPN credentials sent successfully: {result.message_id}")
            return True

        except TelegramError as e:
            logger.error(f"Telegram API error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending VPN credentials: {e}")
            return False

def send_telegram_notification(order):
    """تابع ساده برای ارسال نوتیفیکیشن"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        bot = TelegramBot()
        result = loop.run_until_complete(bot.send_receipt_notification(order))
        loop.close()
        return result
    except Exception as e:
        logger.error(f"Error in send_telegram_notification: {e}")
        return False

def send_vpn_to_user(vpn_account):
    """تابع ساده برای ارسال اطلاعات VPN"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        bot = TelegramBot()
        result = loop.run_until_complete(bot.send_vpn_account_to_user(vpn_account))
        loop.close()
        return result
    except Exception as e:
        logger.error(f"Error in send_vpn_to_user: {e}")
        return False