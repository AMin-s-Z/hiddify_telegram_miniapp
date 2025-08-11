import hashlib
import hmac
import json
import time
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import HttpResponseBadRequest
from django.urls import reverse
from .models import TelegramUser, VPNPlan, Order
from .telegram_bot import send_receipt_to_admin

def plan_list_view(request):
    user = None
    if request.session.get('user_id'):
        user = TelegramUser.objects.get(pk=request.session.get('user_id'))

    plans = VPNPlan.objects.all()
    context = {
        'plans': plans,
        'user': user,
        'telegram_bot_username': settings.TELEGRAM_BOT_USERNAME,
        'redirect_url': request.build_absolute_uri(reverse('telegram_login_callback')),
    }
    return render(request, 'store/plan_list.html', context)

def telegram_login_callback(request):
    data_check_string = []
    for key, value in sorted(request.GET.items()):
        if key != 'hash':
            data_check_string.append(f'{key}={value}')

    data_check_string = '\n'.join(data_check_string)

    secret_key = hashlib.sha256(settings.TELEGRAM_BOT_TOKEN.encode()).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if calculated_hash != request.GET.get('hash'):
        return HttpResponseBadRequest("Authentication failed.")

    auth_date = int(request.GET.get('auth_date'))
    if time.time() - auth_date > 3600: # 1 hour
        return HttpResponseBadRequest("Data is outdated.")

    user_data = json.loads(json.dumps(request.GET))
    user_id = user_data.get('id')

    user, created = TelegramUser.objects.update_or_create(
        telegram_id=user_id,
        defaults={
            'first_name': user_data.get('first_name'),
            'last_name': user_data.get('last_name', ''),
            'username': user_data.get('username', ''),
        }
    )

    request.session['user_id'] = user.telegram_id
    return redirect('plan_list')

def logout_view(request):
    if 'user_id' in request.session:
        del request.session['user_id']
    return redirect('plan_list')

def purchase_history_view(request):
    if not request.session.get('user_id'):
        return redirect('plan_list')

    user = get_object_or_404(TelegramUser, pk=request.session.get('user_id'))
    orders = user.orders.all().order_by('-created_at')

    return render(request, 'store/purchase_history.html', {'orders': orders, 'user': user})

def buy_plan_view(request, plan_id):
    if not request.session.get('user_id'):
        return redirect('plan_list')

    user = get_object_or_404(TelegramUser, pk=request.session.get('user_id'))
    plan = get_object_or_404(VPNPlan, pk=plan_id)

    if request.method == 'POST':
        receipt_file = request.FILES.get('receipt')
        if receipt_file:
            order = Order.objects.create(
                user=user,
                plan=plan,
                status='verifying',
                receipt=receipt_file
            )
            # ارسال رسید برای ادمین
            send_receipt_to_admin(order)
            return redirect('purchase_history')

    # اطلاعات کارت به کارت شما
    card_info = {
        'card_number': '6037-9977-1234-5678',
        'card_holder': 'اسم شما'
    }

    context = {
        'plan': plan,
        'user': user,
        'card_info': card_info,
    }
    return render(request, 'store/buy_plan.html', context)

# ... import های قبلی
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import telegram

# تابع پردازش آپدیت که از ویو فراخوانی می‌شود
def process_telegram_update(update_data):
    update = telegram.Update.de_json(update_data, telegram.Bot(settings.TELEGRAM_BOT_TOKEN))

    # اگر آپدیت از نوع کلیک روی دکمه بود
    if update.callback_query:
        query = update.callback_query

        # بررسی امنیتی: فقط ادمین
        if query.from_user.id != int(settings.ADMIN_TELEGRAM_ID):
            return

        action, order_id = query.data.split('_')
        order_id = int(order_id)

        try:
            order = Order.objects.get(id=order_id)
            # بقیه منطق تایید و رد کردن سفارش که قبلا نوشتیم
            # ... (کد مشابه داخل handle_callback_query)

            new_status_text = ""
            user_message = ""

            if action == "approve":
                order.status = 'completed'
                order.save()
                new_status_text = f"✅ سفارش {order.id} تایید شد."
                user_message = "سفارش شما تایید شد. متن خاص شما: ..."
            elif action == "reject":
                order.status = 'failed'
                order.save()
                new_status_text = f"❌ سفارش {order.id} رد شد."
                user_message = "سفارش شما رد شد. با پشتیبانی تماس بگیرید."

            # ویرایش پیام ادمین
            bot = telegram.Bot(settings.TELEGRAM_BOT_TOKEN)
            bot.edit_message_caption(chat_id=query.message.chat_id, message_id=query.message.message_id, caption=query.message.caption + f"\n\n---\nوضعیت: {new_status_text}")
            # ارسال پیام به کاربر
            bot.send_message(chat_id=order.user.telegram_id, text=user_message)

        except Order.DoesNotExist:
            print(f"Order with id {order_id} not found.")

# ویو اصلی برای دریافت وب‌هوک
@csrf_exempt # برای اینکه تلگرام بتواند به این URL دسترسی داشته باشد
def telegram_webhook_view(request):
    if request.method == "POST":
        update_data = json.loads(request.body.decode('utf-8'))
        process_telegram_update(update_data)
        return JsonResponse({"ok": "POST request processed"})
    return JsonResponse({"ok": "GET request received"})