import json
import hmac
import hashlib
import logging
from datetime import datetime
from urllib.parse import parse_qsl

from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import make_aware
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .forms import PurchaseForm
from .models import Plan, Purchase, TelegramProfile
from .utils.telegram import notify_admin_on_purchase

logger = logging.getLogger(__name__)

# --- ویوهای قبلی بدون تغییر باقی می‌مانند ---

def home_view(request):
    # اگر کاربر لاگین است مستقیم به لیست پلن‌ها برود
    if request.user.is_authenticated:
        return redirect('core:plan_list')
    # در غیر اینصورت صفحه لاگین خودکار را نمایش بده
    return render(request, 'home.html')

@login_required
def plan_list_view(request):
    plans = Plan.objects.all()
    return render(request, 'plan_list.html', {'plans': plans})

@login_required
def purchase_create_view(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    if request.method == 'POST':
        form = PurchaseForm(request.POST, request.FILES)
        if form.is_valid():
            purchase = form.save(commit=False)
            purchase.user = request.user
            purchase.plan = plan
            purchase.save()
            notify_admin_on_purchase(purchase)
            return redirect('core:purchase_list')
    else:
        form = PurchaseForm()
    return render(request, 'purchase_form.html', {'form': form, 'plan': plan})

@login_required
def purchase_list_view(request):
    purchases = Purchase.objects.filter(user=request.user)
    return render(request, 'purchase_list.html', {'purchases': purchases})

@login_required
@require_POST
def logout_view(request):
    logout(request)
    return redirect('core:home')

# --- ویو جدید برای لاگین خودکار ---

def validate_init_data(init_data_str: str, bot_token: str) -> (bool, dict):
    """
    اعتبارسنجی رشته initData از مینی‌اپ تلگرام.
    """
    try:
        # ساخت کلید مخفی برای اعتبارسنجی
        secret_key = hmac.new("WebAppData".encode(), bot_token.encode(), hashlib.sha256).digest()

        parsed_data = dict(parse_qsl(init_data_str))
        received_hash = parsed_data.pop('hash', None)

        if not received_hash:
            return False, {}

        # ساخت رشته data-check-string برای مقایسه
        data_check_string = "\n".join(sorted([f"{k}={v}" for k, v in parsed_data.items()]))

        # محاسبه هش خودمان
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        # مقایسه هش‌ها
        if calculated_hash == received_hash:
            user_info = json.loads(parsed_data.get('user', '{}'))
            return True, user_info

    except Exception as e:
        logger.error(f"Could not validate initData: {e}")

    return False, {}

@csrf_exempt
@require_POST
def telegram_seamless_auth_view(request):
    try:
        payload = json.loads(request.body)
        init_data_str = payload.get('init_data')

        if not init_data_str:
            return JsonResponse({'success': False, 'error': 'init_data is missing'}, status=400)

        is_valid, user_data = validate_init_data(init_data_str, settings.TELEGRAM_BOT_TOKEN)

        if not is_valid:
            return JsonResponse({'success': False, 'error': 'Validation failed'}, status=403)

        telegram_id = user_data['id']
        username = f"tg_{telegram_id}"

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': user_data.get('first_name', ''),
                'last_name': user_data.get('last_name', '')
            }
        )

        # به‌روزرسانی یا ساخت پروفایل تلگرام
        TelegramProfile.objects.update_or_create(
            user=user,
            defaults={
                'telegram_id': telegram_id,
                'username': user_data.get('username'),
                'first_name': user_data.get('first_name'),
                'last_name': user_data.get('last_name'),
                'photo_url': user_data.get('photo_url'),
                'auth_date': make_aware(datetime.fromtimestamp(int(json.loads(init_data_str.split('auth_date=')[1].split('&')[0]))))
            }
        )

        login(request, user)
        return JsonResponse({'success': True})

    except Exception as e:
        logger.error(f"Error in seamless auth: {e}")
        return JsonResponse({'success': False, 'error': 'Server error'}, status=500)