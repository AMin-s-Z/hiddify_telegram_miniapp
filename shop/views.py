from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.base import ContentFile
from django.conf import settings
from .models import VPNPlan, Purchase, PaymentCard
from .telegram_bot import send_payment_notification
import base64

@login_required
def plans_list(request):
    plans = VPNPlan.objects.filter(is_active=True)
    return render(request, 'shop/plans.html', {'plans': plans})

@login_required
def purchase_plan(request, plan_id):
    plan = get_object_or_404(VPNPlan, id=plan_id, is_active=True)

    if request.method == 'POST':
        # ایجاد خرید جدید
        purchase = Purchase.objects.create(
            user=request.user,
            plan=plan,
            status='pending'
        )
        return redirect('payment', purchase_id=purchase.id)

    return render(request, 'shop/purchase_confirm.html', {'plan': plan})

@login_required
def payment(request, purchase_id):
    purchase = get_object_or_404(Purchase, id=purchase_id, user=request.user)

    if purchase.status != 'pending':
        messages.error(request, 'این سفارش قبلا پردازش شده است.')
        return redirect('purchase_history')

    payment_cards = PaymentCard.objects.filter(is_active=True)

    if request.method == 'POST':
        receipt_file = request.FILES.get('receipt')
        if receipt_file:
            purchase.payment_receipt = receipt_file
            purchase.status = 'waiting_approval'
            purchase.save()

            # ارسال نوتیفیکیشن به تلگرام
            send_payment_notification(purchase)

            messages.success(request, 'رسید پرداخت شما ارسال شد و در انتظار تایید است.')
            return redirect('purchase_history')
        else:
            messages.error(request, 'لطفا رسید پرداخت را آپلود کنید.')

    context = {
        'purchase': purchase,
        'payment_cards': payment_cards,
    }
    return render(request, 'shop/payment.html', context)

@login_required
def purchase_history(request):
    purchases = Purchase.objects.filter(user=request.user)
    return render(request, 'shop/purchase_history.html', {'purchases': purchases})

@login_required
def download_vpn_config(request, purchase_id):
    purchase = get_object_or_404(Purchase, id=purchase_id, user=request.user)

    if purchase.status != 'approved' or not purchase.vpn_config:
        messages.error(request, 'کانفیگ VPN در دسترس نیست.')
        return redirect('purchase_history')

    response = HttpResponse(purchase.vpn_config, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="vpn_config_{purchase.id}.txt"'
    return response