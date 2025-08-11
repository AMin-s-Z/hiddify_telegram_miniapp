import telegram
from django.conf import settings

def send_receipt_to_admin(order):
    try:
        bot = telegram.Bot(token=settings.TELEGRAM_BOT_TOKEN)

        user = order.user
        plan = order.plan

        caption = (
            f"✅ سفارش جدید ثبت شد!\n\n"
            f"کاربر: {user.first_name} (ID: {user.telegram_id})\n"
            f"پلن: {plan.name}\n"
            f"مبلغ: {plan.price} تومان\n"
            f"شماره سفارش: {order.id}\n\n"
            f"لطفا رسید را بررسی و اقدام کنید:"
        )

        # ساخت دکمه‌های شیشه‌ای (Inline Keyboard)
        # ما آیدی سفارش را در callback_data قرار می‌دهیم تا بدانیم کدام سفارش باید آپدیت شود
        keyboard = [
            [
                telegram.InlineKeyboardButton("✅ تایید خرید", callback_data=f"approve_{order.id}"),
                telegram.InlineKeyboardButton("❌ رد کردن", callback_data=f"reject_{order.id}"),
            ]
        ]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)

        # ارسال عکس رسید به همراه کپشن و دکمه‌ها
        with open(order.receipt.path, 'rb') as photo_file:
            bot.send_photo(
                chat_id=settings.ADMIN_TELEGRAM_ID,
                photo=photo_file,
                caption=caption,
                reply_markup=reply_markup
            )
    except Exception as e:
        print(f"Error sending telegram notification: {e}")