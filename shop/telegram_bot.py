import telegram
from telegram import Bot
from django.conf import settings
import asyncio

async def send_payment_notification_async(purchase):
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    admin_chat_id = settings.TELEGRAM_ADMIN_CHAT_ID

    message = f"""
🔔 پرداخت جدید دریافت شد!

👤 کاربر: {purchase.user.telegram_username or purchase.user.username}
📱 آیدی تلگرام: {purchase.user.telegram_id}
📦 پلن: {purchase.plan.name}
💰 مبلغ: {purchase.plan.price:,} تومان
🆔 شناسه تراکنش: {purchase.transaction_id}
📅 زمان: {purchase.created_at.strftime('%Y-%m-%d %H:%M')}

برای تایید یا رد، به پنل ادمین مراجعه کنید.
    """

    if purchase.payment_receipt:
        await bot.send_photo(
            chat_id=admin_chat_id,
            photo=purchase.payment_receipt.file,
            caption=message
        )
    else:
        await bot.send_message(chat_id=admin_chat_id, text=message)

def send_payment_notification(purchase):
    asyncio.run(send_payment_notification_async(purchase))

async def send_approval_notification_async(purchase):
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

    message = f"""
✅ پرداخت شما تایید شد!

📦 پلن: {purchase.plan.name}
🕐 مدت اعتبار: {purchase.plan.get_duration_days_display()}
📅 تاریخ انقضا: {purchase.expires_at.strftime('%Y-%m-%d')}

کانفیگ VPN شما در پنل کاربری قابل دریافت است.
    """

    try:
        await bot.send_message(chat_id=purchase.user.telegram_id, text=message)
    except:
        pass

def send_approval_notification(purchase):
    asyncio.run(send_approval_notification_async(purchase))

async def send_rejection_notification_async(purchase):
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

    message = f"""
❌ پرداخت شما رد شد!

📦 پلن: {purchase.plan.name}
📝 دلیل: {purchase.admin_note or 'رسید پرداخت معتبر نیست'}

لطفا مجددا با رسید معتبر اقدام کنید.
    """

    try:
        await bot.send_message(chat_id=purchase.user.telegram_id, text=message)
    except:
        pass

def send_rejection_notification(purchase):
    asyncio.run(send_rejection_notification_async(purchase))