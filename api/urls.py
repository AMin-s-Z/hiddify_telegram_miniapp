from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    # سفارشات
    path('orders/create/', views.CreateOrderView.as_view(), name='create_order'),
    path('orders/upload_receipt/', views.UploadReceiptView.as_view(), name='upload_receipt'),
    path('orders/status/<int:order_id>/', views.OrderStatusView.as_view(), name='order_status'),
    path('orders/list/', views.UserOrdersListView.as_view(), name='user_orders_list'),

    # اکانت‌های VPN
    path('vpn-accounts/', views.UserVPNAccountsView.as_view(), name='user_vpn_accounts'),

    # پلن‌ها
    path('plans/', views.PlansListView.as_view(), name='plans_list'),

    # سلامت API
    path('health/', views.HealthCheckView.as_view(), name='health_check'),
]