from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('plans/', views.plan_list_view, name='plan_list'),
    path('purchase/<int:plan_id>/', views.purchase_create_view, name='purchase_create'),
    path('purchases/', views.purchase_list_view, name='purchase_list'),
    path('logout/', views.logout_view, name='logout'),
    path('auth/telegram-seamless/', views.telegram_seamless_auth_view, name='telegram_seamless_auth'),
]