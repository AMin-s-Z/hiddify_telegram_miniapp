import os
import json
import logging
import requests
from django.conf import settings
from .models import Order

# It's best practice to define the logger at the module level
logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


def format_amount(irr: int) -> str:
    """Formats an integer amount into a Persian-formatted string with a currency label."""
    s = f"{irr:,}".replace(",", "٬")
    return s + " ریال"


def notify_admin_order_submitted(order: Order) -> None:
    """Sends a notification to the admin about a new submitted order."""
    token = settings.TELEGRAM_BOT_TOKEN
    admin_chat_id = getattr(settings, "ADMIN_TELEGRAM_CHAT_ID", None)

    if not token or not admin_chat_id:
        logger.warning("Telegram bot token or admin chat ID is not configured.")
        return

    caption = (
        f"سفارش جدید\n"
        f"Order #{order.id}\n"
        f"Plan: {order.plan.name}\n"
        f"Amount: {format_amount(order.amount_irr)}\n"
        f"User: {order.user.username}\n"
    )
    keyboard = {
        "inline_keyboard": [[
            {"text": "تایید ✅", "callback_data": f"approve:{order.id}"},
            {"text": "رد ❌", "callback_data": f"reject:{order.id}"}
        ]]
    }

    try:
        if order.receipt:
            url = TELEGRAM_API.format(token=token, method="sendDocument")
            # Use a context manager for handling files to ensure they are always closed
            with order.receipt.open("rb") as receipt_file:
                files = {"document": (os.path.basename(order.receipt.name), receipt_file)}
                data = {
                    "chat_id": admin_chat_id,
                    "caption": caption,
                    "reply_markup": json.dumps(keyboard),
                }
                response = requests.post(url, data=data, files=files, timeout=30)
        else:
            url = TELEGRAM_API.format(token=token, method="sendMessage")
            payload = {
                "chat_id": admin_chat_id,
                "text": caption,
                "reply_markup": json.dumps(keyboard)
            }
            response = requests.post(url, json=payload, timeout=15)

        response.raise_for_status()
        logger.info(f"Admin notification sent successfully for Order #{order.id}.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Telegram notification for Order #{order.id}: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while sending Telegram notification for Order #{order.id}: {e}")


def handle_admin_callback(update: dict, on_approve):
    """
    Handles callback queries from the admin's inline keyboard.
    This function is more robust with logging and error handling.
    """
    if "callback_query" not in update:
        return

    logger.info("Handling admin callback...")
    cq = update["callback_query"]
    data = cq.get("data") or ""

    if not data or ":" not in data:
        logger.warning(f"Callback data is invalid: {data}")
        return

    action, id_str = data.split(":", 1)
    try:
        order_id = int(id_str)
    except ValueError:
        logger.error(f"Invalid order ID in callback data: {id_str}")
        return

    try:
        order = Order.objects.select_related("plan", "user").get(id=order_id)
    except Order.DoesNotExist:
        logger.error(f"Order with ID {order_id} not found.")
        return

    # Default text for the popup notification in Telegram
    alert_text = "انجام شد!"

    # --- Action Logic ---
    if action == "approve":
        if order.status != Order.Status.APPROVED:
            order.status = Order.Status.APPROVED
            order.save(update_fields=["status", "updated_at"])
            logger.info(f"Order {order.id} status changed to APPROVED.")
            try:
                # The most critical part: execute the main approval logic
                on_approve(order)
                logger.info(f"on_approve callback executed successfully for order {order.id}.")
            except Exception as e:
                # If the main logic fails, log it and inform the admin
                logger.error(f"Error in on_approve for order {order.id}: {e}", exc_info=True)
                alert_text = "تایید با خطا مواجه شد!"
        else:
            logger.warning(f"Order {order.id} is already approved. Ignoring duplicate callback.")
            alert_text = "این سفارش قبلاً تایید شده است."

    elif action == "reject":
        if order.status != Order.Status.REJECTED:
            order.status = Order.Status.REJECTED
            order.save(update_fields=["status", "updated_at"])
            logger.info(f"Order {order.id} status changed to REJECTED.")
        else:
            alert_text = "این سفارش قبلاً رد شده است."

    # --- Answer Callback Query ---
    # Send a response to Telegram to remove the loading spinner on the button
    token = settings.TELEGRAM_BOT_TOKEN
    try:
        requests.post(
            TELEGRAM_API.format(token=token, method="answerCallbackQuery"),
            json={
                "callback_query_id": cq.get("id"),
                "text": alert_text,
                "show_alert": False, # Set to True if you want a bigger popup
            },
            timeout=15
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send answerCallbackQuery for Order #{order.id}: {e}")