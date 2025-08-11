from django.urls import path
from . import views

urlpatterns = [
    path('', views.plan_list_view, name='plan_list'),
    path('login/callback/', views.telegram_login_callback, name='telegram_login_callback'),
    path('logout/', views.logout_view, name='logout'),
    path('history/', views.purchase_history_view, name='purchase_history'),
    path('buy/<int:plan_id>/', views.buy_plan_view, name='buy_plan'),

    path('telegram/webhook/3{*yvX02`n:o;Nc@x=noXd&342],/(c[b|N:X+v(hotaT+Kv:2h5ec]HiI&3O/', views.telegram_webhook_view, name='telegram_webhook'),
]