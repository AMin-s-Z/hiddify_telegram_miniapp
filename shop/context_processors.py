from django.conf import settings
def global_settings(request):
    return {'BOT_USERNAME': settings.BOT_USERNAME, 'ADMIN_BANK_CARD': settings.ADMIN_BANK_CARD, 'ADMIN_BANK_NAME': settings.ADMIN_BANK_NAME}