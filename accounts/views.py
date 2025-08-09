from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.conf import settings
import json

from .models import TelegramProfile, Plan, Order, VPNAccount
from .utils import verify_telegram_init_data
from .telegram import notify_admin_order_submitted, handle_admin_callback
from .vpn import create_vpn_account_for_order

User = get_user_model()


def home(request):
    return render(request, "index.html")


@login_required
def dashboard(request):
    plans = Plan.objects.filter(is_active=True).order_by("order_index", "id")
    user_accounts = VPNAccount.objects.filter(user=request.user).order_by("-created_at")[:5]
    user_orders = Order.objects.filter(user=request.user).order_by("-created_at")[:10]
    return render(request, "dashboard.html", {
        "plans": plans,
        "user_accounts": user_accounts,
        "user_orders": user_orders,
        "bank_card_number": getattr(settings, 'BANK_CARD_NUMBER', None),
    })


@csrf_exempt
def telegram_auth_view(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    try:
        payload = json.loads(request.body.decode())
        init_data_str = payload.get("init_data", "")
        max_age = getattr(settings, 'TELEGRAM_INIT_MAX_AGE_SECONDS', 120)
        verified = verify_telegram_init_data(init_data_str, settings.TELEGRAM_BOT_TOKEN, max_age_seconds=max_age)
        tg_user = verified["user"]
        telegram_id = int(tg_user["id"])
        first_name = tg_user.get("first_name", "")
        last_name = tg_user.get("last_name", "")
        telegram_username = tg_user.get("username")
        photo_url = tg_user.get("photo_url")
        language_code = tg_user.get("language_code")

        with transaction.atomic():
            profile = TelegramProfile.objects.select_related("user").filter(telegram_id=telegram_id).first()
            if profile:
                user = profile.user
                profile.telegram_username = telegram_username
                profile.photo_url = photo_url
                profile.language_code = language_code
                profile.save(update_fields=["telegram_username", "photo_url", "language_code"])
            else:
                username = f"tg_{telegram_id}"
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        "first_name": first_name,
                        "last_name": last_name,
                    },
                )
                if created:
                    user.set_unusable_password()
                    user.save(update_fields=["password"])
                TelegramProfile.objects.create(
                    user=user,
                    telegram_id=telegram_id,
                    telegram_username=telegram_username,
                    photo_url=photo_url,
                    language_code=language_code,
                )

        login(request, user)
        return JsonResponse({"ok": True, "user_id": user.id})
    except Exception as e:
        return HttpResponseBadRequest(str(e))


@login_required
def api_plans(request):
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])
    plans = list(Plan.objects.filter(is_active=True).order_by("order_index", "id").values(
        "id", "name", "description", "price_irr", "duration_days", "data_gb"
    ))
    return JsonResponse({"ok": True, "plans": plans})


@csrf_exempt
@login_required
def api_create_order(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        payload = json.loads(request.body.decode())
        plan_id = int(payload.get("plan_id"))
        plan = get_object_or_404(Plan, id=plan_id, is_active=True)
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                plan=plan,
                amount_irr=plan.price_irr,
                status=Order.Status.PENDING_PAYMENT,
            )
        return JsonResponse({
            "ok": True,
            "order_id": order.id,
            "bank_card_number": getattr(settings, 'BANK_CARD_NUMBER', None),
            "amount_irr": order.amount_irr,
        })
    except Exception as e:
        return HttpResponseBadRequest(str(e))


@csrf_exempt
@login_required
def api_upload_receipt(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    order_id = request.POST.get("order_id")
    file = request.FILES.get("receipt")
    if not order_id or not file:
        return HttpResponseBadRequest("order_id and receipt are required")
    order = get_object_or_404(Order, id=order_id, user=request.user)
    try:
        with transaction.atomic():
            order.receipt = file
            order.status = Order.Status.SUBMITTED
            order.save(update_fields=["receipt", "status", "updated_at"])
        notify_admin_order_submitted(order)
        return JsonResponse({"ok": True, "message": "رسید ارسال شد. منتظر تایید ادمین بمانید."})
    except Exception as e:
        return HttpResponseBadRequest(str(e))


@login_required
def api_order_status(request, order_id: int):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    data = {
        "id": order.id,
        "status": order.status,
    }
    if order.status == Order.Status.APPROVED and hasattr(order, 'vpn_account') and order.vpn_account:
        data["vpn_account"] = {
            "username": order.vpn_account.username,
            "password": order.vpn_account.password,
            "server_address": order.vpn_account.server_address,
        }
    return JsonResponse({"ok": True, "order": data})


@csrf_exempt
def telegram_webhook(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        update = json.loads(request.body.decode())
        handle_admin_callback(update, on_approve=create_vpn_account_for_order)
        return JsonResponse({"ok": True})
    except Exception:
        return JsonResponse({"ok": True})
