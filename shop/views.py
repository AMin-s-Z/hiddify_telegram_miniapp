import json, hmac, hashlib, logging, datetime
from urllib.parse import parse_qsl
from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import make_aware
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .forms import PurchaseForm
from .models import Plan, Purchase, TelegramProfile
from .utils.telegram import notify_admin_on_purchase

logger = logging.getLogger(__name__)


def home_view(request):
    return redirect('shop:plan_list') if request.user.is_authenticated else render(request, 'home.html')

@login_required
def plan_list_view(request):
    return render(request, 'plan_list.html', {'plans': Plan.objects.all()})

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
            return redirect('shop:purchase_list')
    else:
        form = PurchaseForm()
    return render(request, 'purchase_form.html', {'form': form, 'plan': plan})

@login_required
def purchase_list_view(request):
    return render(request, 'purchase_list.html', {'purchases': Purchase.objects.filter(user=request.user)})

@login_required
@require_POST
def logout_view(request):
    logout(request)
    return redirect('shop:home')

import hmac
import hashlib
from urllib.parse import parse_qs

def validate_init_data(init_data, bot_token):
    try:
        parsed_data = parse_qs(init_data)
        hash_value = parsed_data.get('hash', [None])[0]

        if not hash_value:
            return False, {}

        # Create data check string
        data_check_arr = []
        for key, value in parsed_data.items():
            if key != 'hash':
                data_check_arr.append(f"{key}={value[0]}")

        data_check_string = '\n'.join(sorted(data_check_arr))

        # Calculate hash
        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if calculated_hash != hash_value:
            return False, {}

        # Parse user data
        user_data = json.loads(parsed_data.get('user', ['{}'])[0])
        user_data['auth_date'] = parsed_data.get('auth_date', [None])[0]

        return True, user_data
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return False, {}
@csrf_exempt
@require_POST
def telegram_seamless_auth_view(request):
    try:
        # لاگ کردن درخواست دریافتی
        logger.info(f"Received request body: {request.body}")

        payload = json.loads(request.body)
        init_data = payload.get('init_data', '')

        logger.info(f"Init data: {init_data}")

        is_valid, user_data = validate_init_data(init_data, settings.TELEGRAM_BOT_TOKEN)

        logger.info(f"Validation result: {is_valid}, User data: {user_data}")

        if not is_valid:
            return JsonResponse({'success': False, 'error': 'Validation failed'}, status=403)

        # بررسی وجود user_data['id']
        if 'id' not in user_data:
            logger.error("No 'id' in user_data")
            return JsonResponse({'success': False, 'error': 'Invalid user data'}, status=400)

        user, created = User.objects.get_or_create(
            username=f"tg_{user_data['id']}",
            defaults={
                'first_name': user_data.get('first_name', ''),
                'last_name': user_data.get('last_name', '')
            }
        )

        logger.info(f"User created/retrieved: {user.username}, Created: {created}")

        TelegramProfile.objects.update_or_create(
            user=user,
            defaults={
                'telegram_id': user_data['id'],
                'username': user_data.get('username'),
                'first_name': user_data.get('first_name'),
                'last_name': user_data.get('last_name'),
                'photo_url': user_data.get('photo_url'),
                'auth_date': make_aware(datetime.datetime.fromtimestamp(int(user_data['auth_date'])))
            }
        )

        # لاگین کاربر با backend مشخص
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        logger.info(f"User logged in successfully: {user.username}")

        return JsonResponse({'success': True})

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error in seamless auth: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)