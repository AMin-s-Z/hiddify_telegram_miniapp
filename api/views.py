from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from shop.models import Plan, Order, VPNAccount
from .serializers import OrderSerializer
from shop.telegram_bot import TelegramBot, send_to_telegram

class CreateOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        plan_id = request.data.get('plan_id')
        if not plan_id:
            return Response({"detail": "شناسه پلن الزامی است"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            plan = Plan.objects.get(id=plan_id, is_active=True)
        except Plan.DoesNotExist:
            return Response({"detail": "پلن مورد نظر یافت نشد"}, status=status.HTTP_404_NOT_FOUND)

        # ایجاد سفارش
        order = Order.objects.create(
            user=request.user,
            plan=plan,
            amount_irr=plan.price_irr,
            status='pending'
        )

        return Response({
            "order_id": order.id,
            "amount_irr": order.amount_irr
        }, status=status.HTTP_201_CREATED)

class UploadReceiptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_id = request.data.get('order_id')
        receipt = request.FILES.get('receipt')

        if not order_id or not receipt:
            return Response({"detail": "شناسه سفارش و تصویر رسید الزامی است"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"detail": "سفارش مورد نظر یافت نشد"}, status=status.HTTP_404_NOT_FOUND)

        if order.status != 'pending':
            return Response({"detail": "این سفارش قبلاً پرداخت شده است"}, status=status.HTTP_400_BAD_REQUEST)

        # ذخیره رسید
        order.receipt_image = receipt
        order.status = 'submitted'
        order.save()

        # ارسال اعلان به ادمین
        bot = TelegramBot()
        send_to_telegram(bot.send_receipt_notification)(order)

        return Response({"message": "رسید با موفقیت آپلود شد و در انتظار تایید است"}, status=status.HTTP_200_OK)

class OrderStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user)
        serializer = OrderSerializer(order)
        return Response({"order": serializer.data}, status=status.HTTP_200_OK)