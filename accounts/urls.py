from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('auth/telegram/callback/', views.telegram_login_callback, name='telegram_callback'),
    path('logout/', views.logout_view, name='logout'),
]