# core/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # ... your existing paths ...
    path('', views.home_view, name='home'),
    path('plans/', views.plan_list_view, name='plan_list'),
    path('purchase/<int:plan_id>/', views.purchase_create_view, name='purchase_create'),
    path('purchases/', views.purchase_list_view, name='purchase_list'),
    path('logout/', views.logout_view, name='logout'),
    path('auth/telegram-seamless/', views.telegram_seamless_auth_view, name='telegram_seamless_auth'),

    # New URL for the purchase detail page
    path('purchase/details/<uuid:purchase_uuid>/', views.purchase_detail_view, name='purchase_detail'),

    # New URL for the Telegram webhook
    # The token makes it a secret URL only you and Telegram should know
    path('telegram-webhook/<str:token>/', views.telegram_callback_webhook, name='telegram_webhook'),
]