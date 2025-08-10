from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('auth/telegram/callback/', views.telegram_login_callback, name='telegram_callback'),
    path('auth/telegram/webapp/', views.telegram_webapp_auth, name='telegram_webapp_auth'),
    path('logout/', views.logout_view, name='logout'),
]