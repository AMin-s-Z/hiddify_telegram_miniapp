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
        payload = json.loads(request.body)
        init_data = payload.get('init_data', '')

        is_valid, user_data = validate_init_data(init_data, settings.TELEGRAM_BOT_TOKEN)

        if not is_valid:
            return JsonResponse({'success': False, 'error': 'Validation failed'}, status=403)

        # بررسی وجود user_data['id']
        if 'id' not in user_data:
            return JsonResponse({'success': False, 'error': 'Invalid user data'}, status=400)

        user, created = User.objects.get_or_create(
            username=f"tg_{user_data['id']}",
            defaults={
                'first_name': user_data.get('first_name', ''),
                'last_name': user_data.get('last_name', '')
            }
        )

        # تبدیل auth_date به datetime با مدیریت خطا
        try:
            auth_timestamp = int(user_data.get('auth_date', 0))
            # بررسی معقول بودن timestamp
            current_timestamp = int(datetime.datetime.now().timestamp())
            if auth_timestamp > current_timestamp:
                # اگر تاریخ در آینده است، از زمان فعلی استفاده کن
                auth_date = make_aware(datetime.datetime.now())
            else:
                auth_date = make_aware(datetime.datetime.fromtimestamp(auth_timestamp))
        except (ValueError, TypeError):
            auth_date = make_aware(datetime.datetime.now())

        TelegramProfile.objects.update_or_create(
            user=user,
            defaults={
                'telegram_id': user_data['id'],
                'username': user_data.get('username'),
                'first_name': user_data.get('first_name'),
                'last_name': user_data.get('last_name'),
                'photo_url': user_data.get('photo_url'),
                'auth_date': auth_date
            }
        )

        # لاگین کاربر با backend مشخص
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        return JsonResponse({'success': True})

    except Exception as e:
        logger.error(f"Error in seamless auth: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


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



from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.template.loader import render_to_string

def approve_purchase(purchase):
    purchase.status = 'approved'
    # ... save purchase and generate vpn_config ...
    purchase.save()

    # Get the channel layer
    channel_layer = get_channel_layer()

    # Render the new HTML snippet
    html_snippet = render_to_string('partials/purchase_status_approved.html', {'purchase': purchase})

    # Send a message to the group
    async_to_sync(channel_layer.group_send)(
        f'purchase_{purchase.uuid}',
        {
            'type': 'purchase_update', # This calls the purchase_update method in the consumer
            'status': 'approved',
            'html': html_snippet
        }
    )