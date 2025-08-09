import os
import json
import requests
from django.conf import settings
from django.urls import reverse
from .models import Order

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


def format_amount(irr: int) -> str:
    s = f"{irr:,}".replace(",", "٬")
    return s + " ریال"


def notify_admin_order_submitted(order: Order) -> None:
    token = settings.TELEGRAM_BOT_TOKEN
    admin_chat_id = getattr(settings, "ADMIN_TELEGRAM_CHAT_ID", None)
    if not token or not admin_chat_id:
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

    if order.receipt:
        url = TELEGRAM_API.format(token=token, method="sendDocument")
        files = {"document": (os.path.basename(order.receipt.name), order.receipt.open("rb"))}
        data = {
            "chat_id": admin_chat_id,
            "caption": caption,
            "reply_markup": json.dumps(keyboard),
        }
        try:
            r = requests.post(url, data=data, files=files, timeout=30)
            r.raise_for_status()
        finally:
            try:
                files["document"][1].close()
            except Exception:
                pass
    else:
        url = TELEGRAM_API.format(token=token, method="sendMessage")
        payload = {"chat_id": admin_chat_id, "text": caption, "reply_markup": keyboard}
        r = requests.post(url, json=payload, timeout=15)
        r.raise_for_status()


def handle_admin_callback(update: dict, on_approve):
    if "callback_query" not in update:
        return
    cq = update["callback_query"]
    data = cq.get("data") or ""
    if not data or ":" not in data:
        return
    action, id_str = data.split(":", 1)
    try:
        order_id = int(id_str)
    except ValueError:
        return

    try:
        order = Order.objects.select_related("plan", "user").get(id=order_id)
    except Order.DoesNotExist:
        return

    if action == "approve":
        if order.status != Order.Status.APPROVED:
            order.status = Order.Status.APPROVED
            order.save(update_fields=["status", "updated_at"])
            on_approve(order)
    elif action == "reject":
        order.status = Order.Status.REJECTED
        order.save(update_fields=["status", "updated_at"])

    token = settings.TELEGRAM_BOT_TOKEN
    requests.post(TELEGRAM_API.format(token=token, method="answerCallbackQuery"), json={
        "callback_query_id": cq.get("id"),
        "text": "انجام شد",
        "show_alert": False,
    }, timeout=15) 