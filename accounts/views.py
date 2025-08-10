from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
from .models import User
from .telegram_auth import verify_telegram_auth
import json

def login_view(request):
    if request.user.is_authenticated:
        return redirect('shop:home')

    context = {
        'bot_username': settings.TELEGRAM_BOT_USERNAME
    }
    return render(request, 'accounts/login.html', context)

@csrf_exempt
def telegram_login_callback(request):
    if request.method == 'POST':
        try:
            auth_data = json.loads(request.body)

            if not verify_telegram_auth(auth_data):
                return JsonResponse({'error': 'احراز هویت نامعتبر است'}, status=400)

            telegram_id = auth_data.get('id')

            # بررسی یا ایجاد کاربر
            user, created = User.objects.get_or_create(
                telegram_id=telegram_id,
                defaults={
                    'username': f"tg_{telegram_id}",
                    'telegram_username': auth_data.get('username'),
                    'telegram_first_name': auth_data.get('first_name'),
                    'telegram_last_name': auth_data.get('last_name'),
                    'telegram_photo_url': auth_data.get('photo_url'),
                }
            )

            if not created:
                # به‌روزرسانی اطلاعات کاربر
                user.telegram_username = auth_data.get('username')
                user.telegram_first_name = auth_data.get('first_name')
                user.telegram_last_name = auth_data.get('last_name')
                user.telegram_photo_url = auth_data.get('photo_url')
                user.save()

            # ورود کاربر
            login(request, user)

            return JsonResponse({'success': True, 'redirect': '/shop/'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'روش غیرمجاز'}, status=405)

def logout_view(request):
    logout(request)
    return redirect('accounts:login')