from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.conf import settings
import json

from .models import TelegramProfile
from .utils import verify_telegram_init_data

User = get_user_model()


def home(request):
    return render(request, "index.html")


@login_required
def dashboard(request):
    return render(request, "dashboard.html")


@csrf_exempt
def telegram_auth_view(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    try:
        payload = json.loads(request.body.decode())
        init_data_str = payload.get("init_data", "")
        verified = verify_telegram_init_data(init_data_str, settings.TELEGRAM_BOT_TOKEN, max_age_seconds=120)
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
