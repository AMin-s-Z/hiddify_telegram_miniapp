from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Plan, Order, VPNAccount
from .telegram_bot import TelegramBot, send_to_telegram
from django.utils import timezone
import string
import random

@login_required
def home(request):
    active_plans = Plan.objects.filter(is_active=True)
    user_orders = Order.objects.filter(user=request.user)
    user_accounts = VPNAccount.objects.filter(user=request.user, is_active=True)

    context = {
        'plans': active_plans,
        'user_orders': user_orders,
        'user_accounts': user_accounts,
    }

    return render(request, 'shop/index.html', context)