from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from shop.models import Plan, Order, VPNAccount
from .serializers import OrderSerializer, PlanSerializer, VPNAccountSerializer
from shop.telegram_bot import send_telegram_notification, send_vpn_to_user
import os
import logging

logger = logging.getLogger(__name__)

class CreateOrderView(APIView):
    """
    ایجاد سفارش جدید
    POST /api/orders/create/
    Body: {"plan_id": 1}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            plan_id = request.data.get('plan_id')

            # Validation
            if not plan_id:
                return Response({
                    "detail": "شناسه پلن الزامی است",
                    "status": "error"
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                plan_id = int(plan_id)
            except (ValueError, TypeError):
                return Response({
                    "detail": "شناسه پلن باید عدد باشد",
                    "status": "error"
                }, status=status.HTTP_400_BAD_REQUEST)

            # بررسی وجود پلن
            try:
                plan = Plan.objects.get(id=plan_id, is_active=True)
            except Plan.DoesNotExist:
                return Response({
                    "detail": "پلن مورد نظر یافت نشد یا غیرفعال است",
                    "status": "error"
                }, status=status.HTTP_404_NOT_FOUND)

            # بررسی اینکه کاربر سفارش pending نداشته باشد
            existing_order = Order.objects.filter(
                user=request.user,
                status__in=['pending', 'submitted']
            ).first()

            if existing_order:
                return Response({
                    "detail": f"شما یک سفارش در انتظار دارید (#{existing_order.id}). لطفاً آن را تکمیل کنید.",
                    "status": "error",
                    "existing_order_id": existing_order.id
                }, status=status.HTTP_400_BAD_REQUEST)

            # ایجاد سفارش جدید
            order = Order.objects.create(
                user=request.user,
                plan=plan,
                amount_irr=plan.price_irr,
                status='pending'
            )

            logger.info(f"Order {order.id} created for user {request.user.id}")

            return Response({
                "order_id": order.id,
                "amount_irr": order.amount_irr,
                "plan_name": plan.name,
                "status": "success",
                "message": "سفارش با موفقیت ایجاد شد"
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Unexpected error in CreateOrderView: {e}")
            return Response({
                "detail": "خطا در ایجاد سفارش. لطفاً دوباره تلاش کنید.",
                "status": "error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UploadReceiptView(APIView):
    """
    آپلود رسید پرداخت
    POST /api/orders/upload_receipt/
    Body: FormData with order_id and receipt file
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        try:
            order_id = request.data.get('order_id')
            receipt = request.FILES.get('receipt')

            # Validation - Order ID
            if not order_id:
                return Response({
                    "detail": "شناسه سفارش الزامی است",
                    "status": "error"
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                order_id = int(order_id)
            except (ValueError, TypeError):
                return Response({
                    "detail": "شناسه سفارش نامعتبر است",
                    "status": "error"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Validation - Receipt File
            if not receipt:
                return Response({
                    "detail": "فایل رسید الزامی است",
                    "status": "error"
                }, status=status.HTTP_400_BAD_REQUEST)

            # بررسی سایز فایل (حداکثر 10MB)
            max_size = 10 * 1024 * 1024  # 10MB
            if receipt.size > max_size:
                return Response({
                    "detail": "حجم فایل نباید بیشتر از 10 مگابایت باشد",
                    "status": "error"
                }, status=status.HTTP_400_BAD_REQUEST)

            # بررسی نوع فایل
            allowed_types = [
                'image/jpeg', 'image/jpg', 'image/png',
                'image/gif', 'image/webp', 'application/pdf'
            ]
            if receipt.content_type not in allowed_types:
                return Response({
                    "detail": "فقط فایل‌های تصویری (JPG, PNG, GIF, WebP) و PDF مجاز هستند",
                    "status": "error"
                }, status=status.HTTP_400_BAD_REQUEST)

            # بررسی پسوند فایل
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf']
            file_extension = os.path.splitext(receipt.name)[1].lower()
            if file_extension not in allowed_extensions:
                return Response({
                    "detail": "پسوند فایل مجاز نیست",
                    "status": "error"
                }, status=status.HTTP_400_BAD_REQUEST)

            # بررسی سفارش
            try:
                order = Order.objects.get(id=order_id, user=request.user)
            except Order.DoesNotExist:
                return Response({
                    "detail": "سفارش یافت نشد یا متعلق به شما نیست",
                    "status": "error"
                }, status=status.HTTP_404_NOT_FOUND)

            # بررسی وضعیت سفارش
            if order.status not in ['pending', 'rejected']:
                status_messages = {
                    'submitted': 'این سفارش قبلاً رسید ارسال شده است',
                    'approved': 'این سفارش قبلاً تایید شده است'
                }
                return Response({
                    "detail": status_messages.get(order.status, "وضعیت سفارش اجازه آپلود رسید را نمی‌دهد"),
                    "status": "error",
                    "order_status": order.status
                }, status=status.HTTP_400_BAD_REQUEST)

            # بررسی و ایجاد پوشه media
            media_dir = os.path.join(settings.MEDIA_ROOT, 'receipts')
            if not os.path.exists(media_dir):
                try:
                    os.makedirs(media_dir, mode=0o755)
                    logger.info(f"Created media directory: {media_dir}")
                except Exception as e:
                    logger.error(f"Failed to create media directory: {e}")
                    return Response({
                        "detail": "خطا در ایجاد پوشه ذخیره‌سازی",
                        "status": "error"
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # بررسی دسترسی نوشتن
            if not os.access(media_dir, os.W_OK):
                logger.error(f"No write permission for directory: {media_dir}")
                return Response({
                    "detail": "عدم دسترسی برای ذخیره فایل",
                    "status": "error"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # ذخیره رسید
            try:
                # حذف رسید قبلی اگر وجود دارد
                if order.receipt_image:
                    try:
                        if os.path.exists(order.receipt_image.path):
                            os.remove(order.receipt_image.path)
                    except Exception as e:
                        logger.warning(f"Could not remove old receipt: {e}")

                # ذخیره رسید جدید
                order.receipt_image = receipt
                order.status = 'submitted'
                order.save()

                logger.info(f"Receipt uploaded for order {order.id}")

            except Exception as e:
                logger.error(f"Failed to save receipt for order {order.id}: {e}")
                return Response({
                    "detail": f"خطا در ذخیره رسید: {str(e)}",
                    "status": "error"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # ارسال اعلان به ادمین
            try:
                telegram_result = send_telegram_notification(order)
                if telegram_result:
                    logger.info(f"Telegram notification sent for order {order.id}")
                else:
                    logger.warning(f"Failed to send telegram notification for order {order.id}")
            except Exception as e:
                logger.error(f"Error sending telegram notification for order {order.id}: {e}")
                # ادامه می‌دهیم حتی اگر تلگرام کار نکند

            return Response({
                "message": "رسید با موفقیت ارسال شد و در انتظار تایید ادمین است",
                "status": "success",
                "order_id": order.id,
                "order_status": order.status
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Unexpected error in UploadReceiptView: {e}")
            return Response({
                "detail": "خطا در آپلود رسید. لطفاً دوباره تلاش کنید.",
                "status": "error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class OrderStatusView(APIView):
    """
    بررسی وضعیت سفارش
    GET /api/orders/status/{order_id}/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        try:
            # Validation
            try:
                order_id = int(order_id)
            except (ValueError, TypeError):
                return Response({
                    "detail": "شناسه سفارش نامعتبر است",
                    "status": "error"
                }, status=status.HTTP_400_BAD_REQUEST)

            # بررسی سفارش
            try:
                order = Order.objects.select_related('plan', 'user').get(
                    id=order_id,
                    user=request.user
                )
            except Order.DoesNotExist:
                return Response({
                    "detail": "سفارش یافت نشد یا متعلق به شما نیست",
                    "status": "error"
                }, status=status.HTTP_404_NOT_FOUND)

            # سریالایز کردن سفارش
            order_data = {
                "id": order.id,
                "plan": {
                    "id": order.plan.id,
                    "name": order.plan.name,
                    "price_irr": order.plan.price_irr,
                    "duration_days": order.plan.duration_days,
                    "data_gb": order.plan.data_gb
                },
                "status": order.status,
                "status_display": order.get_status_display(),
                "amount_irr": order.amount_irr,
                "created_at": order.created_at.isoformat(),
                "updated_at": order.updated_at.isoformat(),
                "admin_note": order.admin_note
            }

            # اضافه کردن اطلاعات VPN اگر وجود دارد
            try:
                vpn_account = VPNAccount.objects.get(order=order)
                order_data["vpn_account"] = {
                    "id": vpn_account.id,
                    "username": vpn_account.username,
                    "password": vpn_account.password,
                    "server_address": vpn_account.server_address,
                    "expires_at": vpn_account.expires_at.isoformat(),
                    "is_active": vpn_account.is_active
                }
            except VPNAccount.DoesNotExist:
                order_data["vpn_account"] = None

            logger.info(f"Order status checked for order {order.id}")

            return Response({
                "order": order_data,
                "status": "success"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Unexpected error in OrderStatusView: {e}")
            return Response({
                "detail": "خطا در دریافت وضعیت سفارش",
                "status": "error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserOrdersListView(APIView):
    """
    لیست سفارشات کاربر
    GET /api/orders/list/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # دریافت سفارشات کاربر
            orders = Order.objects.filter(user=request.user).select_related('plan').order_by('-created_at')

            orders_data = []
            for order in orders:
                order_data = {
                    "id": order.id,
                    "plan_name": order.plan.name,
                    "status": order.status,
                    "status_display": order.get_status_display(),
                    "amount_irr": order.amount_irr,
                    "created_at": order.created_at.isoformat(),
                    "has_vpn_account": hasattr(order, 'vpn_account')
                }
                orders_data.append(order_data)

            return Response({
                "orders": orders_data,
                "total_count": len(orders_data),
                "status": "success"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in UserOrdersListView: {e}")
            return Response({
                "detail": "خطا در دریافت لیست سفارشات",
                "status": "error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserVPNAccountsView(APIView):
    """
    لیست اکانت‌های VPN کاربر
    GET /api/vpn-accounts/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # دریافت اکانت‌های VPN فعال کاربر
            vpn_accounts = VPNAccount.objects.filter(
                user=request.user,
                is_active=True
            ).select_related('order', 'order__plan').order_by('-created_at')

            accounts_data = []
            for account in vpn_accounts:
                account_data = {
                    "id": account.id,
                    "username": account.username,
                    "password": account.password,
                    "server_address": account.server_address,
                    "expires_at": account.expires_at.isoformat(),
                    "is_active": account.is_active,
                    "plan_name": account.order.plan.name,
                    "order_id": account.order.id,
                    "created_at": account.created_at.isoformat()
                }
                accounts_data.append(account_data)

            return Response({
                "vpn_accounts": accounts_data,
                "total_count": len(accounts_data),
                "status": "success"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in UserVPNAccountsView: {e}")
            return Response({
                "detail": "خطا در دریافت اکانت‌های VPN",
                "status": "error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PlansListView(APIView):
    """
    لیست پلن‌های فعال
    GET /api/plans/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # دریافت پلن‌های فعال
            plans = Plan.objects.filter(is_active=True).order_by('price_irr')

            plans_data = []
            for plan in plans:
                plan_data = {
                    "id": plan.id,
                    "name": plan.name,
                    "description": plan.description,
                    "price_irr": plan.price_irr,
                    "duration_days": plan.duration_days,
                    "data_gb": plan.data_gb,
                    "is_active": plan.is_active
                }
                plans_data.append(plan_data)

            return Response({
                "plans": plans_data,
                "total_count": len(plans_data),
                "status": "success"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in PlansListView: {e}")
            return Response({
                "detail": "خطا در دریافت لیست پلن‌ها",
                "status": "error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class HealthCheckView(APIView):
    """
    بررسی سلامت API
    GET /api/health/
    """
    permission_classes = []

    def get(self, request):
        return Response({
            "status": "healthy",
            "message": "API is working properly",
            "timestamp": timezone.now().isoformat()
        }, status=status.HTTP_200_OK)