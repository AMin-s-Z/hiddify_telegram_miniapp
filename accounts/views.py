from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import hashlib
import hmac
import json
from .models import User

def verify_telegram_auth(auth_data, bot_token):
    check_hash = auth_data.pop('hash', None)
    if not check_hash:
        return False

    data_check_arr = []
    for key, value in sorted(auth_data.items()):
        data_check_arr.append(f'{key}={value}')

    data_check_string = '\n'.join(data_check_arr)
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    hash_check = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    return hash_check == check_hash

def telegram_login(request):
    if request.method == 'POST':
        auth_data = json.loads(request.body)

        # تایید اطلاعات تلگرام
        bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
        if not verify_telegram_auth(auth_data.copy(), bot_token):
            return JsonResponse({'error': 'Invalid authentication'}, status=400)

        # ایجاد یا بروزرسانی کاربر
        telegram_id = auth_data.get('id')
        user, created = User.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={
                'username': f"tg_{telegram_id}",
                'telegram_username': auth_data.get('username', ''),
                'telegram_first_name': auth_data.get('first_name', ''),
                'telegram_last_name': auth_data.get('last_name', ''),
            }
        )

        if not created:
            user.telegram_username = auth_data.get('username', '')
            user.telegram_first_name = auth_data.get('first_name', '')
            user.telegram_last_name = auth_data.get('last_name', '')
            user.save()

        login(request, user)
        return JsonResponse({'success': True})

    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'با موفقیت خارج شدید.')
    return redirect('login')