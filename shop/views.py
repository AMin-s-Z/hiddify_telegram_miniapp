import json, hmac, hashlib, logging, datetime
from urllib.parse import parse_qsl
from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
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

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

@csrf_exempt
def telegram_seamless_auth(request):
    if request.method == 'POST':
        try:
            init_data = json.loads(request.body).get('init_data')

            # در اینجا باید از کتابخانه telethon استفاده کنید
            # یا روشی دیگر برای تأیید init_data داشته باشید

            # مثال ساده:
            print(f"Received init_data: {init_data}")

            # تأیید که init_data معتبر است و از تلگرام آمده است
            # مدیریت خطا

            # تأیید کاربر
            user_data = parse_telegram_init_data(init_data)

            if user_data:
                # ورود کاربر به سیستم
                login_user(user_data)

                return JsonResponse({
                    'success': True,
                    'message': 'Authentication successful'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid authentication data'
                }, status=400)

        except Exception as e:
            print(f"Authentication error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

def parse_telegram_init_data(init_data):
    """
    این تابع init_data را تجزیه کرده و اطلاعات کاربر را استخراج می‌کند
    """
    try:
        # در اینجا باید logika مناسب برای تجزیه init_data داشته باشید
        # با استفاده از متدهای موجود در telegraph

        # مثال ساده:
        # parsed_data = parse_web_app_data(init_data)
        # return {
        #     'id': parsed_data.user.id,
        #     'username': parsed_data.user.username,
        #     'first_name': parsed_data.user.first_name
        # }

        return None

    except Exception as e:
        print(f"Error parsing init_data: {str(e)}")
        return None
# core/views.py

# ... keep all your existing imports and add these ...
from django.http import HttpResponse
from .utils.telegram import send_telegram_message # Ensure this is imported
from .admin import generate_vpn_config # We can reuse the function from admin.py

# ... keep all your existing views (home_view, plan_list_view, etc.) ...

@csrf_exempt
@require_POST
def telegram_callback_webhook(request, token):
    # Simple security check
    if token != settings.TELEGRAM_BOT_TOKEN:
        return HttpResponse(status=403)

    try:
        data = json.loads(request.body)
        if 'callback_query' not in data:
            return HttpResponse(status=200) # Not a callback, ignore

        callback_data = data['callback_query']['data']
        action, purchase_id_str = callback_data.split(':')
        purchase_id = int(purchase_id_str)

        purchase = Purchase.objects.get(id=purchase_id)

        # Prevent re-approving/rejecting
        if purchase.status != 'pending':
            return HttpResponse(status=200)

        if action == 'approve':
            purchase.status = 'approved'
            purchase.vpn_config = generate_vpn_config(purchase)
            purchase.save()

            # Create the secure link to the details page for the user
            details_url = request.build_absolute_uri(
                reverse('core:purchase_detail', kwargs={'purchase_uuid': purchase.uuid})
            )

            user_message = (
                f"✅ Your purchase for the *{purchase.plan.name}* plan has been approved!\n\n"
                f"You can view your VPN details and configuration at the link below:\n\n"
                f"{details_url}"
            )
            send_telegram_message(purchase.user.telegram_profile.telegram_id, user_message)

        elif action == 'reject':
            purchase.status = 'rejected'
            purchase.save()
            user_message = f"❌ Unfortunately, your payment for the *{purchase.plan.name}* plan was rejected. Please contact support."
            send_telegram_message(purchase.user.telegram_profile.telegram_id, user_message)

    except (Purchase.DoesNotExist, ValueError, KeyError) as e:
        logger.error(f"Error in webhook: {e}")
        # Return 200 even on error to prevent Telegram from retrying
        return HttpResponse(status=200)

    return HttpResponse(status=200)


@login_required
def purchase_detail_view(request, purchase_uuid):
    # Fetch the purchase using the secure UUID, ensuring only the owner can see it
    purchase = get_object_or_404(Purchase, uuid=purchase_uuid, user=request.user)
    return render(request, 'purchase_detail.html', {'purchase': purchase})