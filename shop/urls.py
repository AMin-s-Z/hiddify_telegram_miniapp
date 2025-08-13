from django.urls import path
from . import views

urlpatterns = [
    path('', views.plans_list, name='home'),
    path('plans/', views.plans_list, name='plans'),
    path('purchase/<int:plan_id>/', views.purchase_plan, name='purchase_plan'),
    path('payment/<int:purchase_id>/', views.payment, name='payment'),
    path('history/', views.purchase_history, name='purchase_history'),
    path('download/<int:purchase_id>/', views.download_vpn_config, name='download_config'),
]