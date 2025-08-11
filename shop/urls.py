from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('telegram_login/', views.telegram_login, name='telegram_login'),
    path('purchase/<int:plan_id>/', views.purchase_plan, name='purchase_plan'),
    path('purchases/', views.purchases, name='purchases'),
    path('confirm/<int:purchase_id>/', views.confirm_purchase, name='confirm_purchase'),
]