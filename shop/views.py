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

def validate_init_data(init_data_str: str, bot_token: str) -> tuple[bool, dict]:
    try:
        secret_key = hmac.new("WebAppData".encode(), bot_token.encode(), hashlib.sha256).digest()
        parsed_data = dict(parse_qsl(init_data_str))
        received_hash = parsed_data.pop('hash', None)
        if not received_hash: return False, {}
        data_check_string = "\n".join(sorted([f"{k}={v}" for k, v in parsed_data.items()]))
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        if calculated_hash == received_hash:
            user_info = json.loads(parsed_data.get('user', '{}'))
            user_info['auth_date'] = parsed_data.get('auth_date')
            return True, user_info
    except Exception as e:
        logger.error(f"Could not validate initData: {e}")
    return False, {}

@csrf_exempt
@require_POST
def telegram_seamless_auth_view(request):
    try:
        payload = json.loads(request.body)
        is_valid, user_data = validate_init_data(payload.get('init_data', ''), settings.TELEGRAM_BOT_TOKEN)
        if not is_valid: return JsonResponse({'success': False, 'error': 'Validation failed'}, status=403)
        user, _ = User.objects.get_or_create(username=f"tg_{user_data['id']}", defaults={'first_name': user_data.get('first_name', ''), 'last_name': user_data.get('last_name', '')})
        TelegramProfile.objects.update_or_create(user=user, defaults={'telegram_id': user_data['id'], 'username': user_data.get('username'), 'first_name': user_data.get('first_name'), 'last_name': user_data.get('last_name'), 'photo_url': user_data.get('photo_url'), 'auth_date': make_aware(datetime.datetime.fromtimestamp(int(user_data['auth_date'])))})
        login(request, user)
        return JsonResponse({'success': True})
    except Exception as e:
        logger.error(f"Error in seamless auth: {e}")
        return JsonResponse({'success': False, 'error': 'Server error'}, status=500)