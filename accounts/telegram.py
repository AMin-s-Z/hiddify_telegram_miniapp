import os
import json
import logging
import requests
from django.conf import settings
from django.db import transaction
from .models import Order, VPNAccount

# It's best practice to define the logger at the module level
logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


def format_amount(irr: int) -> str:
    """Formats an integer amount into a Persian-formatted string with a currency label."""
    s = f"{irr:,}".replace(",", "٬")
    return s + " ریال"


def notify_admin_order_submitted(order: Order) -> None:
    """Sends a powerful notification to the admin with enhanced capabilities."""
    token = settings.TELEGRAM_BOT_TOKEN
    admin_chat_id = getattr(settings, "ADMIN_TELEGRAM_CHAT_ID", None)

    if not token or not admin_chat_id:
        logger.warning("Telegram bot token or admin chat ID is not configured.")
        return

    # Enhanced admin message with emojis and formatting
    caption = (
        f"🚀 *سفارش جدید ثبت شد!* \n\n"
        f"🆔 کد سفارش: `{order.id}`\n"
        f"🗒️ پلن: {order.plan.name}\n"
        f"💰 مبلغ: {format_amount(order.amount_irr)}\n"
        f"👤 کاربر: [{order.user.username}](tg://user?id={order.user.telegram_profile.telegram_id})\n"
        f"⏰ زمان ثبت: {order.created_at.strftime('%Y-%m-%d %H:%M')}\n"
    )

    keyboard = {
        "inline_keyboard": [
            [
                {"text": "تأیید و فعال‌سازی ✅", "callback_data": f"approve:{order.id}"},
                {"text": "رد سفارش ❌", "callback_data": f"reject:{order.id}"}
            ],
            [
                {"text": "مشاهده جزئیات", "callback_data": f"details:{order.id}"}
            ]
        ]
    }

    try:
        if order.receipt:
            url = TELEGRAM_API.format(token=token, method="sendPhoto")
            receipt_url = f"{settings.MEDIA_URL}{order.receipt.name}"

            # Try sending as photo if it's an image
            if order.receipt.name.lower().endswith(('.png', '.jpg', '.jpeg')):
                with order.receipt.open("rb") as receipt_file:
                    files = {"photo": receipt_file}
                    data = {
                        "chat_id": admin_chat_id,
                        "caption": caption,
                        "parse_mode": "Markdown",
                        "reply_markup": json.dumps(keyboard),
                    }
                    response = requests.post(url, data=data, files=files, timeout=30)
            else:
                # Send as document for non-image types
                url = TELEGRAM_API.format(token=token, method="sendDocument")
                with order.receipt.open("rb") as receipt_file:
                    files = {"document": receipt_file}
                    data = {
                        "chat_id": admin_chat_id,
                        "caption": caption,
                        "parse_mode": "Markdown",
                        "reply_markup": json.dumps(keyboard),
                    }
                    response = requests.post(url, data=data, files=files, timeout=30)
        else:
            url = TELEGRAM_API.format(token=token, method="sendMessage")
            payload = {
                "chat_id": admin_chat_id,
                "text": "⚠️ سفارش جدید بدون رسید ثبت شد!\n\n" + caption,
                "parse_mode": "Markdown",
                "reply_markup": json.dumps(keyboard)
            }
            response = requests.post(url, json=payload, timeout=15)

        response_data = response.json()
        # Edit original message to include receipt if document was sent
        if order.receipt and response_data.get("ok") and not order.receipt.name.lower().endswith(('.png', '.jpg', '.jpeg')):
            caption += "\n\n📎 فایل رسید در پیام اول ارسال شد."
            edit_url = TELEGRAM_API.format(token=token, method="editMessageCaption")
            edit_payload = {
                "chat_id": admin_chat_id,
                "message_id": response_data["result"]["message_id"],
                "caption": caption,
                "parse_mode": "Markdown",
                "reply_markup": json.dumps(keyboard)
            }
            requests.post(edit_url, json=edit_payload)

        logger.info(f"Admin notification sent successfully for Order #{order.id}. Message ID: {response_data.get('result', {}).get('message_id')}")
        return response_data.get('result', {}).get('message_id')
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Telegram notification for Order #{order.id}: {str(e)}", exc_info=True)
    except Exception as e:
        logger.error(f"An unexpected error occurred while sending Telegram notification for Order #{order.id}: {str(e)}", exc_info=True)


def handle_admin_callback(update: dict, on_approve):
    """
    Advanced admin callback handler with detailed response options.
    """
    if "callback_query" not in update:
        return

    logger.info("Handling admin callback...")
    cq = update["callback_query"]
    data = cq.get("data") or ""
    message_id = cq["message"]["message_id"]
    admin_chat_id = cq["message"]["chat"]["id"]

    # Initialize a text for response
    alert_text = ""
    edit_text = ""
    delete_previous = False
    send_new_message = False
    new_message = ""

    # Parse callback data
    try:
        action, id_str = data.split(":", 1)
        order_id = int(id_str)
    except (ValueError, AttributeError):
        logger.error(f"Invalid callback data format: {data}")
        alert_text = "خطا در پردازش! پارامتر نامعتبر."
        action = "invalid"

    try:
        if action in ["approve", "reject", "details"]:
            order = Order.objects.select_related("plan", "user").select_for_update().get(id=order_id)
    except Order.DoesNotExist:
        logger.error(f"Order with ID {order_id} not found.")
        alert_text = f"❌ سفارش #{order_id} یافت نشد!"
        action = "invalid"

    # Handle different actions
    if action == "approve":
        if order.status == Order.Status.SUBMITTED:
            try:
                # Execute the main approval logic in transaction
                with transaction.atomic():
                    # Directly mark as approved
                    order.status = Order.Status.APPROVED
                    order.save(update_fields=["status", "updated_at"])

                    # Create VPN account
                    vpn_account = VPNAccount.objects.create(
                        user=order.user,
                        order=order,
                        username=generate_vpn_username(),
                        password=generate_password(12),
                        server_address=getattr(settings, 'VPN_SERVER_ADDRESS', 'vpn.albabovpn.ir'),
                        expires_at=order.created_at + timedelta(days=order.plan.duration_days)
                    )

                    logger.info(f"Created VPN account {vpn_account.username} for order #{order.id}")

                # Notify user
                notify_user_approved(order, vpn_account)

                # Update admin interface
                edit_text = f"✅ سفارش #{order.id} توسط ادمین تأیید شد!\n\nاکانت VPN ایجاد شد:"
                edit_text += f"\n🔑 نام کاربری: `{vpn_account.username}`"
                edit_text += f"\n🔒 رمز عبور: ||{vpn_account.password}||"
                edit_text += f"\n🛜 سرور: `{vpn_account.server_address}`"

                delete_previous = True
                alert_text = "فعال‌سازی اکانت انجام شد!"

            except Exception as e:
                logger.error(f"Error approving order {order.id}: {str(e)}", exc_info=True)
                order.status = Order.Status.REVIEW_NEEDED
                order.save(update_fields=["status", "updated_at"])
                alert_text = f"❌ خطا در فعال‌سازی: {str(e)}"
                edit_text = f"⚠️ خطا در فعال‌سازی سفارش #{order.id}\n\n{str(e)}"
        else:
            alert_text = "⚠️ این سفارش قبلاً پردازش شده"
            edit_text = f"توجه: سفارش #{order.id} قبلاً پردازش شده است!"

    elif action == "reject":
        if order.status == Order.Status.SUBMITTED:
            order.status = Order.Status.REJECTED
            order.save(update_fields=["status", "updated_at"])
            notify_user_rejected(order)
            edit_text = f"❌ سفارش #{order.id} توسط ادمین رد شد."
            delete_previous = True
        else:
            alert_text = "⚠️ وضعیت سفارش تغییر کرده است"
            edit_text = "⚠️ وضعیت سفارش تغییر کرده و قابل تغییر نیست"

    elif action == "details":
        # Display order details
        user = order.user
        alert_text = f"جزئیات سفارش #{order.id}:"
        alert_text += f"\nپلن: {order.plan.name}"
        alert_text += f"\nمقدار: {format_amount(order.amount_irr)}"
        alert_text += f"\nوضعیت: {order.get_status_display()}"
        alert_text += f"\nکاربر: @{user.telegram_profile.telegram_username or user.username}"
        alert_text += f"\nزمان: {order.created_at.strftime('%Y-%m-%d %H:%M')}"

    # --- Response Actions ---
    token = settings.TELEGRAM_BOT_TOKEN
    try:
        # Answer callback to remove loading state
        requests.post(
            TELEGRAM_API.format(token=token, method="answerCallbackQuery"),
            json={
                "callback_query_id": cq.get("id"),
                "text": alert_text,
                "show_alert": action == "details"
            },
            timeout=15
        )

        # Update message if needed
        if edit_text:
            # Add keyboard if not deleting
            if delete_previous:
                # Delete previous message and send new one
                requests.post(
                    TELEGRAM_API.format(token=token, method="deleteMessage"),
                    json={"chat_id": admin_chat_id, "message_id": message_id}
                )
                # Send new message instead of editing
                requests.post(
                    TELEGRAM_API.format(token=token, method="sendMessage"),
                    json={
                        "chat_id": admin_chat_id,
                        "text": edit_text,
                        "parse_mode": "Markdown"
                    }
                )
            else:
                # Edit existing message
                requests.post(
                    TELEGRAM_API.format(token=token, method="editMessageText"),
                    json={
                        "chat_id": admin_chat_id,
                        "message_id": message_id,
                        "text": edit_text,
                        "parse_mode": "Markdown"
                    }
                )

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to handle callback response: {str(e)}")