from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('orders/create/', views.CreateOrderView.as_view(), name='create_order'),
    path('orders/upload_receipt/', views.UploadReceiptView.as_view(), name='upload_receipt'),
    path('orders/status/<int:order_id>/', views.OrderStatusView.as_view(), name='order_status'),
]