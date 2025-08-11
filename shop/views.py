from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.http import JsonResponse
import hashlib
import requests  # For Telegram API
from .models import Plan, Purchase
from django.conf import settings

# Telegram Login View (handles callback from Telegram widget)
def telegram_login(request):
    # This is a simplified version. In production, validate properly.
    # See https://core.telegram.org/widgets/login for details.
    data = request.GET
    bot_token = settings.TELEGRAM_BOT_TOKEN  # Use your bot token
    hash_val = data.get('hash')
    auth_data = {k: v for k, v in data.items() if k != 'hash'}
    data_check_string = '\n'.join([f"{k}={auth_data[k]}" for k in sorted(auth_data)])
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    calculated_hash = hashlib.sha256(data_check_string.encode()).hexdigest()
    h = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if h == hash_val:
        # Valid, create or get user
        telegram_id = data['id']
        username = data.get('username', f"tg_{telegram_id}")
        user, created = User.objects.get_or_create(username=username, defaults={'first_name': data.get('first_name', '')})
        login(request, user)
        return redirect('home')
    else:
        return JsonResponse({'error': 'Invalid login'})

@login_required
def home(request):
    plans = Plan.objects.all()
    return render(request, 'home.html', {'plans': plans})

@login_required
def purchase_plan(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    if request.method == 'POST':
        receipt = request.FILES.get('receipt')
        purchase = Purchase.objects.create(user=request.user, plan=plan, receipt_image=receipt)
        # Send notification to owner via Telegram Bot
        send_telegram_notification(purchase)
        return redirect('purchases')
    return render(request, 'purchase.html', {'plan': plan})

@login_required
def purchases(request):
    purchases = Purchase.objects.filter(user=request.user)
    return render(request, 'purchases.html', {'purchases': purchases})

# Function to confirm purchase (called from admin or separate view)
# For simplicity, assume owner confirms via admin panel, then this triggers VPN creation
def confirm_purchase(request, purchase_id):
    if request.user.is_superuser:  # Only owner can confirm
        purchase = get_object_or_404(Purchase, id=purchase_id)
        purchase.confirmed = True
        purchase.vpn_config = create_vpn_config(purchase)  # Stub function
        purchase.save()
        # Send config to user via Telegram? Or display in app.
        return redirect('admin:vpn_sales_purchase_changelist')
    return redirect('home')

def create_vpn_config(purchase):
    # Stub: Later implement actual VPN creation, e.g., using OpenVPN API or script
    return "Your VPN config: server=example.com, port=1194, etc."  # Placeholder

def send_telegram_notification(purchase):
    bot_token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_OWNER_CHAT_ID
    message = f"New purchase: {purchase.user.username} bought {purchase.plan.name}. Receipt: {purchase.receipt_image.url if purchase.receipt_image else 'No receipt'}"
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={message}"
    requests.get(url)
    if purchase.receipt_image:
        # Send photo if receipt
        photo_url = f"https://api.telegram.org/bot{bot_token}/sendPhoto?chat_id={chat_id}"
        requests.post(photo_url, files={'photo': open(purchase.receipt_image.path, 'rb')})